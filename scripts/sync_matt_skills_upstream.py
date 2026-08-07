#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import NamedTuple


REPOSITORY = 'mattpocock/skills'
REPOSITORY_URL = f'https://github.com/{REPOSITORY}.git'
LATEST_RELEASE_URL = f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
MANIFEST_PATH = PurePosixPath('.claude-plugin/plugin.json')
LICENSE_PATH = PurePosixPath('LICENSE')
LOCK_PATH = PurePosixPath('vendor/mattpocock-skills.lock.json')
VENDORED_LICENSE_PATH = PurePosixPath('licenses/mattpocock-skills-LICENSE.txt')
RESERVED_SKILL_NAMES = frozenset({'setup-project-agents'})
STABLE_TAG = re.compile(
    r'^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
)
COMMIT = re.compile(r'^[0-9a-f]{40}$')
FRONTMATTER_NAME = re.compile(r'(?m)^name:\s*["\']?([^\s"\']+)["\']?\s*$')


class SyncError(RuntimeError):
    pass


class SkillRecord(NamedTuple):
    name: str
    source_path: str


class UpstreamSnapshot(NamedTuple):
    source_root: Path
    version: str
    tag: str
    commit: str
    skills: tuple[SkillRecord, ...]
    license_bytes: bytes
    lock: dict[str, object]


class DriftReport(NamedTuple):
    clean: bool
    drift_paths: tuple[str, ...]


class UpdateResult(NamedTuple):
    changed_paths: tuple[str, ...]
    removed_paths: tuple[str, ...]


ReplacePath = Callable[[Path | None, Path], None]


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except OSError as error:
        raise SyncError(f'cannot read {path}') from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SyncError(f'{path} is not valid UTF-8 JSON') from error


def _write_json(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), 'st_file_attributes', 0)
    except OSError as error:
        raise SyncError(f'cannot inspect upstream path: {path}') from error
    return bool(attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def _validate_regular_tree(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    if _is_link_or_reparse(root) or not root.is_dir():
        raise SyncError(f'upstream skill is not a regular directory: {root}')
    for path in sorted(root.rglob('*')):
        if _is_link_or_reparse(path):
            raise SyncError(f'upstream skill contains a link or reparse point: {path}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise SyncError(f'upstream skill contains a non-regular file: {path}')
        files.append(path)
    return tuple(files)


def validate_release(release: object) -> str:
    if not isinstance(release, dict):
        raise SyncError('GitHub release response must be an object')
    tag = release.get('tag_name')
    if release.get('draft') is not False or release.get('prerelease') is not False:
        raise SyncError('latest GitHub release must be stable')
    if not isinstance(tag, str) or STABLE_TAG.fullmatch(tag) is None:
        raise SyncError('release tag must be a complete stable semantic version')
    return tag


def _normalize_source_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise SyncError('manifest skill path must be a non-empty string')
    normalized = value[2:] if value.startswith('./') else value
    path = PurePosixPath(normalized)
    if path.is_absolute() or '..' in path.parts or '.' in path.parts:
        raise SyncError(f'manifest skill path escapes the repository: {value}')
    if len(path.parts) < 3 or path.parts[0] != 'skills':
        raise SyncError(f'manifest skill path must be below skills/: {value}')
    return path


def _frontmatter_name(skill_path: Path) -> str:
    try:
        text = skill_path.read_text(encoding='utf-8')
    except OSError as error:
        raise SyncError(f'missing SKILL.md: {skill_path}') from error
    except UnicodeDecodeError as error:
        raise SyncError(f'SKILL.md is not UTF-8: {skill_path}') from error
    if not text.startswith('---\n'):
        raise SyncError(f'SKILL.md has no YAML frontmatter: {skill_path}')
    end = text.find('\n---', 4)
    if end < 0:
        raise SyncError(f'SKILL.md has unterminated YAML frontmatter: {skill_path}')
    match = FRONTMATTER_NAME.search(text[4:end])
    if match is None:
        raise SyncError(f'SKILL.md frontmatter has no name: {skill_path}')
    return match.group(1)


def _build_lock(
    source_root: Path,
    *,
    version: str,
    tag: str,
    commit: str,
    skills: tuple[SkillRecord, ...],
) -> dict[str, object]:
    hashes: dict[str, str] = {}
    for skill in skills:
        source = source_root.joinpath(*PurePosixPath(skill.source_path).parts)
        for path in _validate_regular_tree(source):
            relative = path.relative_to(source).as_posix()
            hashes[f'skills/{skill.name}/{relative}'] = _sha256(path)
    return {
        'schema_version': 1,
        'repository': REPOSITORY,
        'upstream_version': version,
        'tag': tag,
        'commit': commit,
        'manifest_path': MANIFEST_PATH.as_posix(),
        'license_path': LICENSE_PATH.as_posix(),
        'skills': [skill._asdict() for skill in skills],
        'files': dict(sorted(hashes.items())),
    }


def load_upstream(source_root: Path, *, tag: str, commit: str) -> UpstreamSnapshot:
    source_root = source_root.resolve()
    match = STABLE_TAG.fullmatch(tag)
    if match is None:
        raise SyncError('tag must be a complete stable semantic version')
    if COMMIT.fullmatch(commit) is None:
        raise SyncError('resolved commit must be a 40-character lowercase SHA')
    manifest = _read_json(source_root.joinpath(*MANIFEST_PATH.parts))
    if not isinstance(manifest, dict):
        raise SyncError('upstream plugin manifest must contain an object')
    version = tag[1:]
    if manifest.get('name') != 'mattpocock-skills':
        raise SyncError('upstream plugin manifest name is invalid')
    if manifest.get('version') != version:
        raise SyncError('upstream plugin manifest version does not match the tag')
    if manifest.get('license') != 'MIT':
        raise SyncError('upstream plugin manifest license must be MIT')
    manifest_skills = manifest.get('skills')
    if not isinstance(manifest_skills, list) or not manifest_skills:
        raise SyncError('upstream plugin manifest skills must be a non-empty array')

    skills: list[SkillRecord] = []
    names: set[str] = set()
    for raw_path in manifest_skills:
        source_path = _normalize_source_path(raw_path)
        name = source_path.name
        if name in RESERVED_SKILL_NAMES:
            raise SyncError(f'upstream skill conflicts with SmartKit ownership: {name}')
        if name in names:
            raise SyncError(f'upstream manifest has duplicate target name: {name}')
        names.add(name)
        skill_root = source_root.joinpath(*source_path.parts)
        _validate_regular_tree(skill_root)
        actual_name = _frontmatter_name(skill_root / 'SKILL.md')
        if actual_name != name:
            raise SyncError(
                f'upstream skill name mismatch for {source_path.as_posix()}: {actual_name}'
            )
        if not (skill_root / 'agents' / 'openai.yaml').is_file():
            raise SyncError(f'upstream skill has no agents/openai.yaml: {name}')
        skills.append(SkillRecord(name=name, source_path=source_path.as_posix()))

    try:
        license_bytes = source_root.joinpath(*LICENSE_PATH.parts).read_bytes()
    except OSError as error:
        raise SyncError('upstream LICENSE is missing') from error
    lock = _build_lock(
        source_root,
        version=version,
        tag=tag,
        commit=commit,
        skills=tuple(skills),
    )
    return UpstreamSnapshot(
        source_root=source_root,
        version=version,
        tag=tag,
        commit=commit,
        skills=tuple(skills),
        license_bytes=license_bytes,
        lock=lock,
    )


def _load_local_lock(root: Path) -> dict[str, object] | None:
    path = root.joinpath(*LOCK_PATH.parts)
    if not path.exists():
        return None
    value = _read_json(path)
    if not isinstance(value, dict):
        raise SyncError('vendor lock must contain an object')
    return value


def _managed_names(lock: dict[str, object] | None) -> set[str]:
    if lock is None:
        return set()
    items = lock.get('skills')
    if not isinstance(items, list):
        raise SyncError('vendor lock skills must be an array')
    names: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str):
            raise SyncError('vendor lock has an invalid skill record')
        name = item['name']
        if name in RESERVED_SKILL_NAMES or name in names or '/' in name or '\\' in name:
            raise SyncError(f'vendor lock has an invalid managed skill name: {name}')
        names.add(name)
    return names


def check_repository(root: Path, upstream: UpstreamSnapshot) -> DriftReport:
    root = root.resolve()
    drift: set[str] = set()
    lock_path = root.joinpath(*LOCK_PATH.parts)
    try:
        local_lock = _load_local_lock(root)
    except SyncError:
        local_lock = None
        drift.add(LOCK_PATH.as_posix())
    if local_lock != upstream.lock:
        drift.add(LOCK_PATH.as_posix())

    expected_files = upstream.lock['files']
    if not isinstance(expected_files, dict):
        raise SyncError('generated upstream lock files must be an object')
    for relative, expected_hash in expected_files.items():
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file() or _is_link_or_reparse(path):
            drift.add(relative)
        else:
            try:
                if _sha256(path) != expected_hash:
                    drift.add(relative)
            except OSError:
                drift.add(relative)

    new_names = {skill.name for skill in upstream.skills}
    for name in new_names:
        skill_root = root / 'skills' / name
        actual = {
            path.relative_to(root).as_posix()
            for path in skill_root.rglob('*')
            if path.is_file() or path.is_symlink()
        } if skill_root.is_dir() else set()
        expected = {
            relative for relative in expected_files if relative.startswith(f'skills/{name}/')
        }
        drift.update(actual - expected)
    for stale_name in _managed_names(local_lock) - new_names:
        if (root / 'skills' / stale_name).exists():
            drift.add(f'skills/{stale_name}')

    license_path = root.joinpath(*VENDORED_LICENSE_PATH.parts)
    try:
        if license_path.read_bytes() != upstream.license_bytes:
            drift.add(VENDORED_LICENSE_PATH.as_posix())
    except OSError:
        drift.add(VENDORED_LICENSE_PATH.as_posix())
    return DriftReport(clean=not drift, drift_paths=tuple(sorted(drift)))


def replace_path(staged: Path | None, target: Path) -> None:
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    if staged is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged), str(target))


def _copy_for_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir() and not source.is_symlink():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def update_repository(
    root: Path,
    upstream: UpstreamSnapshot,
    *,
    replace: ReplacePath = replace_path,
) -> UpdateResult:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    old_lock = _load_local_lock(root)
    old_names = _managed_names(old_lock)
    new_names = {skill.name for skill in upstream.skills}
    for name in new_names - old_names:
        target = root / 'skills' / name
        if target.exists() or target.is_symlink():
            raise SyncError(f'refusing to overwrite non-vendor skill directory: skills/{name}')

    transaction_root = Path(
        tempfile.mkdtemp(prefix='.matt-skills-sync-', dir=root.parent)
    )
    staging = transaction_root / 'staging'
    backup = transaction_root / 'backup'
    operations: list[tuple[Path | None, Path, str]] = []
    originals: dict[str, bool] = {}
    try:
        for skill in upstream.skills:
            source = upstream.source_root.joinpath(
                *PurePosixPath(skill.source_path).parts
            )
            destination = staging / 'skills' / skill.name
            shutil.copytree(source, destination)
            operations.append((destination, root / 'skills' / skill.name, f'skills/{skill.name}'))
        for name in sorted(old_names - new_names):
            operations.append((None, root / 'skills' / name, f'skills/{name}'))

        staged_lock = staging.joinpath(*LOCK_PATH.parts)
        _write_json(staged_lock, upstream.lock)
        operations.append((staged_lock, root.joinpath(*LOCK_PATH.parts), LOCK_PATH.as_posix()))
        staged_license = staging.joinpath(*VENDORED_LICENSE_PATH.parts)
        staged_license.parent.mkdir(parents=True, exist_ok=True)
        staged_license.write_bytes(upstream.license_bytes)
        operations.append(
            (
                staged_license,
                root.joinpath(*VENDORED_LICENSE_PATH.parts),
                VENDORED_LICENSE_PATH.as_posix(),
            )
        )

        for _, target, relative in operations:
            exists = target.exists() or target.is_symlink()
            originals[relative] = exists
            if exists:
                _copy_for_backup(target, backup.joinpath(*PurePosixPath(relative).parts))

        for staged, target, _ in operations:
            replace(staged, target)
    except Exception as error:
        rollback_errors: list[str] = []
        for _, target, relative in reversed(operations):
            try:
                replace_path(None, target)
                if originals.get(relative):
                    saved = backup.joinpath(*PurePosixPath(relative).parts)
                    replace_path(saved, target)
            except Exception as rollback_error:
                rollback_errors.append(f'{relative}: {rollback_error}')
        detail = f'transaction failed: {error}'
        if rollback_errors:
            detail += f'; rollback failed: {"; ".join(rollback_errors)}'
        raise SyncError(detail) from error
    finally:
        shutil.rmtree(transaction_root, ignore_errors=True)

    removed = tuple(f'skills/{name}' for name in sorted(old_names - new_names))
    changed = tuple(relative for _, _, relative in operations)
    return UpdateResult(changed_paths=changed, removed_paths=removed)


def fetch_latest_release() -> object:
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'smartkit'},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SyncError(f'cannot read latest GitHub release: {error}') from error


def checkout_tag(tag: str, destination: Path) -> str:
    try:
        subprocess.run(
            [
                'git',
                'clone',
                '--quiet',
                '--depth',
                '1',
                '--branch',
                tag,
                REPOSITORY_URL,
                str(destination),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        result = subprocess.run(
            ['git', '-C', str(destination), 'rev-parse', 'HEAD'],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SyncError(f'cannot resolve and checkout {tag}: {error}') from error
    commit = result.stdout.strip()
    if COMMIT.fullmatch(commit) is None:
        raise SyncError(f'git returned an invalid commit for {tag}')
    return commit


def resolve_upstream(
    *,
    tag: str | None = None,
    release_reader: Callable[[], object] = fetch_latest_release,
    checkout: Callable[[str, Path], str] = checkout_tag,
) -> tuple[UpstreamSnapshot, tempfile.TemporaryDirectory[str]]:
    if tag is None:
        tag = validate_release(release_reader())
    elif STABLE_TAG.fullmatch(tag) is None:
        raise SyncError('--tag must be a complete stable semantic version')
    temporary = tempfile.TemporaryDirectory(prefix='smartkit-matt-upstream-')
    checkout_root = Path(temporary.name) / 'checkout'
    try:
        commit = checkout(tag, checkout_root)
        upstream = load_upstream(checkout_root, tag=tag, commit=commit)
    except Exception:
        temporary.cleanup()
        raise
    return upstream, temporary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Check or update SmartKit vendored Matt Pocock Skills.'
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--update', action='store_true')
    parser.add_argument('--tag')
    parser.add_argument(
        '--root',
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    if args.check and args.tag is not None:
        parser.error('--tag is supported only with --update')
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        upstream, temporary = resolve_upstream(tag=args.tag)
        try:
            if args.check:
                report = check_repository(args.root, upstream)
                if report.clean:
                    print(
                        f'Matt Skills {upstream.tag} ({upstream.commit}) are up to date: '
                        f'{len(upstream.skills)} skills.'
                    )
                    return 0
                print(
                    f'Matt Skills drift: local repository differs from latest stable '
                    f'{upstream.tag} ({upstream.commit}).',
                    file=sys.stderr,
                )
                for path in report.drift_paths:
                    print(f'  {path}', file=sys.stderr)
                return 1
            old_lock = _load_local_lock(args.root.resolve())
            old_version = old_lock.get('upstream_version') if old_lock else 'none'
            result = update_repository(args.root, upstream)
            print(
                f'Updated Matt Skills {old_version} -> {upstream.version} '
                f'({upstream.tag} {upstream.commit}); {len(upstream.skills)} skills, '
                f'{len(upstream.lock["files"])} files.'
            )
            if result.removed_paths:
                print(f'Removed: {", ".join(result.removed_paths)}')
            return 0
        finally:
            temporary.cleanup()
    except SyncError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
