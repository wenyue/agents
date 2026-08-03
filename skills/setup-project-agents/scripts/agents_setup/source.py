from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping

from .catalog import ContractError, load_catalog


CANONICAL_REPOSITORY = 'https://github.com/wenyue/agents.git'
_COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')
_ENTRYPOINT = PurePosixPath(
    'skills/setup-project-agents/scripts/setup_project_agents.py'
)
_MANIFESTS = (
    (PurePosixPath('.codex-plugin/plugin.json'), {'skills': './skills/'}),
    (
        PurePosixPath('.cursor-plugin/plugin.json'),
        {'skills': './skills/', 'rules': './rules/', 'agents': './agents/'},
    ),
    (PurePosixPath('plugin.json'), {'skills': './skills/', 'agents': './agents/'}),
)
_ROOT_FIELDS = frozenset({'skills', 'rules', 'agents'})
_INCOMPLETE_MARKER = '.agents-setup-incomplete-v1'
_INCOMPLETE_MARKER_BYTES = b'agents-setup-incomplete-v1\n'


class SourceUnavailable(RuntimeError):
    """Raised when Git cannot provide a source snapshot."""


class InvalidFetchedSource(ValueError):
    """Raised when a fetched or installed source fails the source contract."""


@dataclass(frozen=True)
class SourceSnapshot:
    root: Path
    commit: str


@dataclass
class _Workspace:
    path: Path
    fd: int | None
    identity: tuple[int, int] | None = None

    def close(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


@dataclass
class _HeldSource:
    fd: int
    identity: tuple[int, int]

    def close(self) -> None:
        os.close(self.fd)


def _safe_root(value: Path, label: str) -> Path:
    root = Path(value).absolute()
    current = Path(root.anchor)
    for part in root.parts[1:]:
        current /= part
        if current.is_symlink():
            raise InvalidFetchedSource(f'{label} contains a symlink: {current}')
    if not root.is_dir():
        raise InvalidFetchedSource(f'{label} is not a directory: {root}')
    return root


def _safe_required(root: Path, relative: PurePosixPath, *, directory: bool = False) -> Path:
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise InvalidFetchedSource(f'source path contains a symlink: {current}')
    if directory:
        if not current.is_dir():
            raise InvalidFetchedSource(f'source directory is missing: {relative.as_posix()}')
    elif not current.is_file():
        raise InvalidFetchedSource(f'source file is missing: {relative.as_posix()}')
    return current


def _reject_source_symlinks(root: Path) -> None:
    for directory, directories, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in (*directories, *files):
            candidate = parent / name
            if candidate.is_symlink():
                raise InvalidFetchedSource(f'source path contains a symlink: {candidate}')


def _load_manifest(path: Path, version: str, expected_roots: Mapping[str, str]) -> None:
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise InvalidFetchedSource(f'invalid native manifest: {path}') from error
    if not isinstance(document, Mapping):
        raise InvalidFetchedSource(f'invalid native manifest: {path}')
    if document.get('name') != 'agents' or document.get('version') != version:
        raise InvalidFetchedSource(f'native manifest identity/version mismatch: {path}')
    for field, expected in expected_roots.items():
        if document.get(field) != expected:
            raise InvalidFetchedSource(f'native manifest root mismatch: {path}:{field}')
    if any(field in document for field in _ROOT_FIELDS - set(expected_roots)):
        raise InvalidFetchedSource(f'native manifest has unsupported root: {path}')


def _validate_catalog_sources(root: Path, catalog_sources: tuple[PurePosixPath, ...]) -> None:
    for relative in catalog_sources:
        current = root
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                raise InvalidFetchedSource(f'source path contains a symlink: {current}')
        if not current.exists():
            raise InvalidFetchedSource(f'catalog source is missing: {relative.as_posix()}')


def _validate_source(source_root: Path, *, fd_root: bool) -> Path:
    """Validate a local plugin root before it can control project setup."""
    root = Path(source_root) if fd_root else _safe_root(source_root, 'source root')
    if fd_root and not root.is_dir():
        raise InvalidFetchedSource('held source root is not a directory')
    _reject_source_symlinks(root)
    version_path = _safe_required(root, PurePosixPath('VERSION'))
    try:
        version = version_path.read_text(encoding='utf-8').strip()
    except OSError as error:
        raise InvalidFetchedSource('cannot read source VERSION') from error

    for relative, expected_roots in _MANIFESTS:
        _load_manifest(_safe_required(root, relative), version, expected_roots)

    git_dir = root / '.git'
    if git_dir.exists() or git_dir.is_symlink():
        _safe_required(root, PurePosixPath('.git'), directory=True)

    entrypoint = _safe_required(root, _ENTRYPOINT)
    try:
        catalog = load_catalog(root)
    except ContractError as error:
        raise InvalidFetchedSource(f'invalid source catalog: {error}') from error
    if (
        catalog.plugin_id != 'agents'
        or catalog.plugin_version != version
        or catalog.repository != CANONICAL_REPOSITORY
        or catalog.ref != 'main'
    ):
        raise InvalidFetchedSource('source catalog identity/version/ref mismatch')
    _validate_catalog_sources(root, tuple(asset.source for asset in catalog.assets))
    control_plane = [
        asset
        for asset in catalog.assets
        if asset.id == 'setup-project-agents'
        and asset.control_plane
        and asset.target is None
        and asset.source == PurePosixPath('skills/setup-project-agents')
    ]
    if len(control_plane) != 1 or not entrypoint.is_relative_to(root / control_plane[0].source):
        raise InvalidFetchedSource('setup entrypoint is not in the control plane')
    return root


def validate_source(source_root: Path) -> Path:
    return _validate_source(source_root, fd_root=False)


def _validate_held_source(fd: int) -> None:
    _validate_source(Path(f'/proc/self/fd/{fd}'), fd_root=True)


def _run_git(
    argv: tuple[str, ...],
    *,
    failure: type[SourceUnavailable] | type[InvalidFetchedSource],
    pass_fds: tuple[int, ...] = (),
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            argv,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=_git_environment(),
            pass_fds=pass_fds,
        )
    except OSError as error:
        raise SourceUnavailable('Git is unavailable') from error
    if completed.returncode != 0:
        raise failure('Git could not produce a valid canonical source')
    return completed


def _git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith('GIT_')
    }
    environment.update(
        {
            'GIT_TERMINAL_PROMPT': '0',
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': os.devnull,
        }
    )
    return environment


def _secure_dirfd_supported() -> bool:
    return os.name == 'posix' and all(
        hasattr(os, name) for name in ('O_DIRECTORY', 'O_NOFOLLOW')
    )


def _secure_fetch_supported() -> bool:
    return (
        _secure_dirfd_supported()
        and Path('/proc/self/fd').is_dir()
    )


def _directory_identity(path: Path) -> tuple[int, int] | None:
    try:
        status = path.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        return None
    return status.st_dev, status.st_ino


def _identity(status: os.stat_result) -> tuple[int, int]:
    return status.st_dev, status.st_ino


def _entry_status(fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _entry_identity(fd: int, name: str) -> tuple[int, int] | None:
    status = _entry_status(fd, name)
    if status is None or stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        return None
    return _identity(status)


def _open_safe_workspace_fallback(value: Path) -> _Workspace:
    path = Path(os.path.abspath(value))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            status = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir()
            except FileExistsError:
                pass
            except OSError as error:
                raise InvalidFetchedSource('cannot create source workspace') from error
            try:
                status = current.lstat()
            except OSError as error:
                raise InvalidFetchedSource('cannot validate source workspace') from error
        except OSError as error:
            raise InvalidFetchedSource('cannot validate source workspace') from error
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise InvalidFetchedSource(f'source workspace contains unsafe path: {current}')
    return _Workspace(path, None)


def _open_safe_workspace(value: Path) -> _Workspace:
    """Create or open a workspace without following any existing ancestor symlink."""
    if not _secure_dirfd_supported():
        return _open_safe_workspace_fallback(value)
    path = Path(os.path.abspath(value))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        fd = os.open(path.anchor, flags)
    except OSError as error:
        raise InvalidFetchedSource('cannot open source workspace anchor') from error
    try:
        for part in path.parts[1:]:
            try:
                child = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                except OSError as error:
                    raise InvalidFetchedSource('cannot create source workspace') from error
                try:
                    child = os.open(part, flags, dir_fd=fd)
                except OSError as error:
                    raise InvalidFetchedSource('cannot validate source workspace') from error
            except OSError as error:
                raise InvalidFetchedSource('source workspace contains unsafe path') from error
            try:
                status = os.fstat(child)
                if not stat.S_ISDIR(status.st_mode):
                    raise InvalidFetchedSource('source workspace contains a non-directory')
            except BaseException:
                os.close(child)
                raise
            os.close(fd)
            fd = child
        return _Workspace(path, fd, _identity(os.fstat(fd)))
    except BaseException:
        os.close(fd)
        raise


def _open_directory_nofollow(fd: int, name: str) -> int:
    return os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=fd,
    )


def _remove_directory_contents(fd: int) -> None:
    for name in os.listdir(fd):
        status = _entry_status(fd, name)
        if status is None:
            continue
        expected = _identity(status)
        if stat.S_ISDIR(status.st_mode) and not stat.S_ISLNK(status.st_mode):
            try:
                child = _open_directory_nofollow(fd, name)
            except OSError:
                continue
            try:
                if _identity(os.fstat(child)) != expected:
                    continue
                _remove_directory_contents(child)
            finally:
                os.close(child)
            current = _entry_status(fd, name)
            if current is not None and _identity(current) == expected:
                try:
                    os.rmdir(name, dir_fd=fd)
                except OSError:
                    continue
        else:
            current = _entry_status(fd, name)
            if current is not None and _identity(current) == expected:
                try:
                    os.unlink(name, dir_fd=fd)
                except OSError:
                    continue


def _assert_workspace_namespace(workspace: _Workspace) -> None:
    if workspace.fd is None or workspace.identity is None:
        raise SourceUnavailable('secure source namespace guard is unavailable')
    if _identity(os.fstat(workspace.fd)) != workspace.identity:
        raise InvalidFetchedSource('source workspace changed during fetch')
    if _directory_identity(workspace.path) != workspace.identity:
        raise InvalidFetchedSource('source workspace namespace changed during fetch')


def _write_incomplete_marker(fd: int) -> None:
    marker = os.open(
        _INCOMPLETE_MARKER,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=fd,
    )
    try:
        remaining = _INCOMPLETE_MARKER_BYTES
        while remaining:
            written = os.write(marker, remaining)
            remaining = remaining[written:]
    finally:
        os.close(marker)


def _has_valid_marker(fd: int) -> bool:
    status = _entry_status(fd, _INCOMPLETE_MARKER)
    if (
        status is None
        or stat.S_ISLNK(status.st_mode)
        or not stat.S_ISREG(status.st_mode)
        or stat.S_IMODE(status.st_mode) != 0o600
    ):
        return False
    try:
        marker = os.open(
            _INCOMPLETE_MARKER,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=fd,
        )
        try:
            return os.read(marker, len(_INCOMPLETE_MARKER_BYTES) + 1) == _INCOMPLETE_MARKER_BYTES
        finally:
            os.close(marker)
    except OSError:
        return False


def _is_marker_only(fd: int) -> bool:
    return os.listdir(fd) == [_INCOMPLETE_MARKER] and _has_valid_marker(fd)


def _open_held_source(workspace: _Workspace) -> _HeldSource:
    if workspace.fd is None:
        raise SourceUnavailable('secure held source is unavailable')
    status = _entry_status(workspace.fd, 'source')
    if status is None:
        try:
            os.mkdir('source', mode=0o700, dir_fd=workspace.fd)
            source_fd = _open_directory_nofollow(workspace.fd, 'source')
        except OSError as error:
            raise InvalidFetchedSource('cannot create named source directory') from error
        held = _HeldSource(source_fd, _identity(os.fstat(source_fd)))
        try:
            _write_incomplete_marker(source_fd)
        except OSError as error:
            held.close()
            raise InvalidFetchedSource('cannot mark named source directory') from error
        return held
    identity = _entry_identity(workspace.fd, 'source')
    if identity is None:
        raise InvalidFetchedSource('source checkout is not a safe directory')
    try:
        source_fd = _open_directory_nofollow(workspace.fd, 'source')
    except OSError as error:
        raise InvalidFetchedSource('cannot open source checkout') from error
    held = _HeldSource(source_fd, _identity(os.fstat(source_fd)))
    if held.identity != identity or not _is_marker_only(source_fd):
        held.close()
        raise InvalidFetchedSource('source checkout is not an incomplete retry marker')
    return held


def _reset_held_source(source: _HeldSource) -> None:
    """Clear only the held source inode and leave the fixed retry marker behind."""
    try:
        if _identity(os.fstat(source.fd)) != source.identity:
            return
        _remove_directory_contents(source.fd)
        _write_incomplete_marker(source.fd)
    except Exception:
        return


def _remove_incomplete_marker(source: _HeldSource) -> None:
    if _identity(os.fstat(source.fd)) != source.identity or not _has_valid_marker(source.fd):
        raise InvalidFetchedSource('source retry marker is invalid')
    os.unlink(_INCOMPLETE_MARKER, dir_fd=source.fd)


def _assert_final_source(workspace: _Workspace, source: _HeldSource) -> None:
    _assert_workspace_namespace(workspace)
    if workspace.fd is None:
        raise SourceUnavailable('secure held source is unavailable')
    if _identity(os.fstat(source.fd)) != source.identity:
        raise InvalidFetchedSource('held source changed during fetch')
    if _entry_identity(workspace.fd, 'source') != source.identity:
        raise InvalidFetchedSource('source name changed during fetch')


_before_first_git = lambda: None
_before_final_source_guard = lambda: None


def _validate_repository(repository: str) -> str:
    if (
        not isinstance(repository, str)
        or not repository
        or repository.startswith('-')
        or any(ord(character) < 32 or ord(character) == 127 for character in repository)
    ):
        raise InvalidFetchedSource('repository must be a safe Git argument')
    return repository


def fetch_main(repository: str, *, work_root: Path) -> SourceSnapshot:
    """Fetch one depth-one `main` snapshot into ``work_root / 'source'``."""
    repository = _validate_repository(repository)
    if not _secure_fetch_supported():
        raise SourceUnavailable('secure remote source fetch is unavailable on this platform')
    workspace = _open_safe_workspace(work_root)
    source: _HeldSource | None = None
    try:
        source = _open_held_source(workspace)
        git_root = f'/proc/self/fd/{source.fd}'
        _before_first_git()
        _assert_final_source(workspace, source)
        try:
            _run_git(
                ('git', 'init', '--quiet', git_root),
                failure=SourceUnavailable,
                pass_fds=(source.fd,),
            )
        except (SourceUnavailable, InvalidFetchedSource):
            raise
        _run_git(
            ('git', '-C', git_root, 'remote', 'add', 'origin', repository),
            failure=SourceUnavailable,
            pass_fds=(source.fd,),
        )
        _run_git(
            ('git', '-C', git_root, 'fetch', '--depth=1', 'origin', 'main'),
            failure=SourceUnavailable,
            pass_fds=(source.fd,),
        )
        _run_git(
            ('git', '-C', git_root, 'checkout', '--quiet', '--detach', 'FETCH_HEAD'),
            failure=InvalidFetchedSource,
            pass_fds=(source.fd,),
        )
        commit = _run_git(
            ('git', '-C', git_root, 'rev-parse', 'HEAD'),
            failure=InvalidFetchedSource,
            pass_fds=(source.fd,),
        ).stdout.strip()
        if not _COMMIT.fullmatch(commit):
            raise InvalidFetchedSource('Git returned an invalid source commit')
        _remove_incomplete_marker(source)
        _assert_final_source(workspace, source)
        _validate_held_source(source.fd)
        _before_final_source_guard()
        _assert_final_source(workspace, source)
        return SourceSnapshot(workspace.path / 'source', commit.lower())
    except (SourceUnavailable, InvalidFetchedSource):
        if source is not None:
            try:
                _reset_held_source(source)
            except Exception:
                pass
        raise
    finally:
        if source is not None:
            try:
                source.close()
            except OSError:
                pass
        try:
            workspace.close()
        except OSError:
            pass
