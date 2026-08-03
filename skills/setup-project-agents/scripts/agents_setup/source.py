from __future__ import annotations

import json
import os
import re
import secrets
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

    def close(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


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


def validate_source(source_root: Path) -> Path:
    """Validate a local plugin root before it can control project setup."""
    root = _safe_root(source_root, 'source root')
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


def _run_git(
    argv: tuple[str, ...],
    *,
    failure: type[SourceUnavailable] | type[InvalidFetchedSource],
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            argv,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=_git_environment(),
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
        return _Workspace(path, fd)
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


_before_cleanup_quarantine = lambda: None


def _safe_remove_created_checkout(
    workspace: _Workspace,
    identity: tuple[int, int] | None,
) -> None:
    """Safely remove only the inode this call created, preserving every replacement."""
    try:
        if identity is None or workspace.fd is None:
            return
        if _entry_identity(workspace.fd, 'source') != identity:
            return
        _before_cleanup_quarantine()
        quarantine = f'.agents-setup-quarantine-{secrets.token_hex(16)}'
        if _entry_status(workspace.fd, quarantine) is not None:
            return
        os.rename(
            'source',
            quarantine,
            src_dir_fd=workspace.fd,
            dst_dir_fd=workspace.fd,
        )
        if _entry_identity(workspace.fd, quarantine) != identity:
            return
        directory = _open_directory_nofollow(workspace.fd, quarantine)
        try:
            if _identity(os.fstat(directory)) != identity:
                return
            _remove_directory_contents(directory)
        finally:
            os.close(directory)
        if _entry_identity(workspace.fd, quarantine) == identity:
            os.rmdir(quarantine, dir_fd=workspace.fd)
    except Exception:
        return


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
    workspace = _open_safe_workspace(work_root)
    checkout = workspace.path / 'source'
    checkout_identity: tuple[int, int] | None = None
    try:
        if workspace.fd is not None:
            source_exists = _entry_status(workspace.fd, 'source') is not None
        else:
            source_exists = checkout.exists() or checkout.is_symlink()
        if source_exists:
            raise InvalidFetchedSource(f'source checkout already exists: {checkout}')
        try:
            _run_git(
                ('git', 'init', '--quiet', str(checkout)),
                failure=SourceUnavailable,
            )
        except (SourceUnavailable, InvalidFetchedSource):
            checkout_identity = (
                _entry_identity(workspace.fd, 'source')
                if workspace.fd is not None else _directory_identity(checkout)
            )
            raise
        checkout_identity = (
            _entry_identity(workspace.fd, 'source')
            if workspace.fd is not None else _directory_identity(checkout)
        )
        _run_git(
            ('git', '-C', str(checkout), 'remote', 'add', 'origin', repository),
            failure=SourceUnavailable,
        )
        _run_git(
            ('git', '-C', str(checkout), 'fetch', '--depth=1', 'origin', 'main'),
            failure=SourceUnavailable,
        )
        _run_git(
            ('git', '-C', str(checkout), 'checkout', '--quiet', '--detach', 'FETCH_HEAD'),
            failure=InvalidFetchedSource,
        )
        commit = _run_git(
            ('git', '-C', str(checkout), 'rev-parse', 'HEAD'),
            failure=InvalidFetchedSource,
        ).stdout.strip()
        if not _COMMIT.fullmatch(commit):
            raise InvalidFetchedSource('Git returned an invalid source commit')
        return SourceSnapshot(validate_source(checkout), commit.lower())
    except (SourceUnavailable, InvalidFetchedSource):
        try:
            _safe_remove_created_checkout(workspace, checkout_identity)
        except Exception:
            pass
        raise
    finally:
        try:
            workspace.close()
        except OSError:
            pass
