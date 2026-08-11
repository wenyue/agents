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
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import NamedTuple


SETUP_SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/setup-project-agents/scripts'
if str(SETUP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SETUP_SCRIPTS))

from agents_setup.external_contract import (  # noqa: E402
    COMMIT,
    LICENSE_MARKERS,
    ExternalContractError,
    license_matches,
    resolve_ref,
    snapshot_skill_tree,
    source_path,
    validate_ref,
    validate_source_identity,
)
from agents_setup.skill_registry import (  # noqa: E402
    CustomSkill,
    SkillRegistryError,
    load_skill_registry,
)


LOCK_PATH = PurePosixPath('vendor/external-skills.lock.json')
NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
STABLE_ID = re.compile(r'^[A-Za-z0-9_.-]+/[a-z0-9][a-z0-9-]*$')
FRONTMATTER_NAME = re.compile(r'(?m)^name:\s*["\']?([^\s"\']+)["\']?\s*$')


class UpdateError(RuntimeError):
    """Raised when configured external Skills cannot converge safely."""


class ExternalSkill(NamedTuple):
    id: str
    name: str
    path: PurePosixPath


class LicenseSpec(NamedTuple):
    spdx: str
    path: PurePosixPath


class ExternalSource(NamedTuple):
    id: str
    url: str
    ref: str | None
    license: LicenseSpec
    skills: tuple[ExternalSkill, ...]


class Registry(NamedTuple):
    custom: tuple[CustomSkill, ...]
    external_sources: tuple[ExternalSource, ...]


class ResolvedCheckout(NamedTuple):
    root: Path
    resolved_ref: str
    commit: str
    ref_kind: str = 'branch'


class SourceSnapshot(NamedTuple):
    source: ExternalSource
    checkout: ResolvedCheckout
    license_bytes: bytes
    lock: dict[str, object]


class UpdateResult(NamedTuple):
    changed_paths: tuple[str, ...]
    removed_paths: tuple[str, ...]


Resolver = Callable[[ExternalSource], ResolvedCheckout]
ReplacePath = Callable[[Path | None, Path], None]


def _read_json(path: Path, label: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except OSError as error:
        raise UpdateError(f'cannot read {label}: {path}') from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpdateError(f'{label} is not valid UTF-8 JSON: {path}') from error
    if not isinstance(value, Mapping):
        raise UpdateError(f'{label} must contain an object')
    return value


def _write_json(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


def _fields(value: Mapping[str, object], allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise UpdateError(f'unknown {label} fields: {", ".join(sorted(unknown))}')


def _required(value: Mapping[str, object], key: str, label: str) -> object:
    if key not in value:
        raise UpdateError(f'{label} requires {key}')
    return value[key]


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise UpdateError(f'{label} must be an object')
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise UpdateError(f'{label} must be an array')
    return value


def _stable_id(value: object, label: str) -> str:
    if not isinstance(value, str) or STABLE_ID.fullmatch(value) is None:
        raise UpdateError(f'{label} must use owner/name form')
    return value


def _safe_relative(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or '\\' in value:
        raise UpdateError(f'{label} must be a relative POSIX path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {'', '.', '..'} for part in path.parts):
        raise UpdateError(f'{label} must stay inside its declared root')
    return path


def _skill_name(skill_id: str, path: PurePosixPath, label: str) -> str:
    name = skill_id.rsplit('/', 1)[1]
    if path.name != name or NAME.fullmatch(name) is None:
        raise UpdateError(f'{label} id name and path basename must match')
    return name


def load_registry(root: Path) -> Registry:
    try:
        shared = load_skill_registry(root)
    except SkillRegistryError as error:
        raise UpdateError(str(error)) from error

    sources: list[ExternalSource] = []
    for source_index, raw_source in enumerate(shared.external_sources):
        item = _object(raw_source, f'external_sources[{source_index}]')
        _fields(item, {'id', 'url', 'ref', 'license', 'skills'}, 'external source')
        source_id = _stable_id(_required(item, 'id', 'external source'), 'external source id')
        url = _required(item, 'url', 'external source')
        if not isinstance(url, str):
            raise UpdateError('external source url must be a GitHub repository URL')
        try:
            validate_source_identity(source_id, url)
        except ExternalContractError as error:
            raise UpdateError(str(error)) from error
        ref = item.get('ref')
        if ref is not None and not isinstance(ref, str):
            raise UpdateError('external source ref must be a safe Git ref')
        try:
            validate_ref(ref)
        except ExternalContractError as error:
            raise UpdateError(str(error)) from error
        license_item = _object(_required(item, 'license', 'external source'), 'license')
        _fields(license_item, {'spdx', 'path'}, 'license')
        spdx = _required(license_item, 'spdx', 'license')
        if not isinstance(spdx, str) or spdx not in LICENSE_MARKERS:
            raise UpdateError('license spdx is not supported')
        license_spec = LicenseSpec(
            spdx,
            _safe_relative(_required(license_item, 'path', 'license'), 'license path'),
        )
        skills: list[ExternalSkill] = []
        for skill_index, raw_skill in enumerate(
            _array(_required(item, 'skills', 'external source'), 'external source skills')
        ):
            skill_item = _object(
                raw_skill, f'external_sources[{source_index}].skills[{skill_index}]'
            )
            _fields(skill_item, {'id', 'path'}, 'external Skill')
            skill_id = _stable_id(
                _required(skill_item, 'id', 'external Skill'), 'external Skill id'
            )
            path = _safe_relative(
                _required(skill_item, 'path', 'external Skill'), 'external Skill path'
            )
            skills.append(
                ExternalSkill(skill_id, _skill_name(skill_id, path, 'external Skill'), path)
            )
        if not skills:
            raise UpdateError(f'external source has no selected Skills: {source_id}')
        sources.append(ExternalSource(source_id, url, ref, license_spec, tuple(skills)))

    ids = [item.id for item in shared.custom] + [
        item.id for source in sources for item in source.skills
    ]
    names = [item.name for item in shared.custom] + [
        item.name for source in sources for item in source.skills
    ]
    source_ids = [item.id for item in sources]
    if len(ids) != len(set(ids)):
        raise UpdateError('Skill registry has duplicate Skill ids')
    if len(names) != len(set(names)):
        raise UpdateError('Skill registry has duplicate destination names')
    if len(source_ids) != len(set(source_ids)):
        raise UpdateError('Skill registry has duplicate source ids')
    return Registry(shared.custom, tuple(sources))


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), 'st_file_attributes', 0)
    except OSError as error:
        raise UpdateError(f'cannot inspect source path: {path}') from error
    return bool(attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def _regular_files(root: Path, label: str) -> tuple[Path, ...]:
    if _is_link_like(root) or not root.is_dir():
        raise UpdateError(f'{label} is not a regular directory')
    files: list[Path] = []
    for path in sorted(root.rglob('*')):
        if _is_link_like(path):
            raise UpdateError(f'{label} contains a link: {path}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise UpdateError(f'{label} contains a non-regular file: {path}')
        files.append(path)
    return tuple(files)


def _frontmatter_name(path: Path) -> str:
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as error:
        raise UpdateError(f'missing SKILL.md: {path}') from error
    except UnicodeDecodeError as error:
        raise UpdateError(f'SKILL.md is not UTF-8: {path}') from error
    if not text.startswith('---\n'):
        raise UpdateError(f'SKILL.md has no YAML frontmatter: {path}')
    end = text.find('\n---', 4)
    if end < 0:
        raise UpdateError(f'SKILL.md has unterminated YAML frontmatter: {path}')
    match = FRONTMATTER_NAME.search(text[4:end])
    if match is None:
        raise UpdateError(f'SKILL.md frontmatter has no name: {path}')
    return match.group(1)


def _license_matches(spdx: str, content: bytes) -> bool:
    try:
        return license_matches(spdx, content)
    except ExternalContractError as error:
        raise UpdateError(str(error)) from error


def _license_destination(source_id: str) -> PurePosixPath:
    return PurePosixPath('licenses') / f'{source_id.replace("/", "-")}-LICENSE.txt'


def load_source_snapshot(source: ExternalSource, checkout: ResolvedCheckout) -> SourceSnapshot:
    root = checkout.root
    if COMMIT.fullmatch(checkout.commit) is None:
        raise UpdateError(f'external source returned an invalid commit: {source.id}')
    if checkout.ref_kind not in {'branch', 'tag', 'commit'}:
        raise UpdateError(f'external source returned an invalid ref kind: {source.id}')
    try:
        license_path = source_path(root, source.license.path, f'external source {source.id}')
    except ExternalContractError as error:
        raise UpdateError(str(error)) from error
    try:
        license_bytes = license_path.read_bytes()
    except OSError as error:
        raise UpdateError(f'external source license is missing: {source.id}') from error
    if not _license_matches(source.license.spdx, license_bytes):
        raise UpdateError(
            f'external source license does not match {source.license.spdx}: {source.id}'
        )

    skill_records: list[dict[str, object]] = []
    for skill in source.skills:
        try:
            tree = snapshot_skill_tree(
                root, skill.path, skill.name, f'external Skill {skill.id}'
            )
        except ExternalContractError as error:
            raise UpdateError(str(error)) from error
        skill_records.append(
            {
                'id': skill.id,
                'source_path': skill.path.as_posix(),
                'destination': f'skills/{skill.name}',
                'files': dict(sorted(tree.files.items())),
            }
        )
    lock = {
        'id': source.id,
        'url': source.url,
        'requested_ref': source.ref,
        'resolved_ref': checkout.resolved_ref,
        'ref_kind': checkout.ref_kind,
        'commit': checkout.commit,
        'license': {
            'spdx': source.license.spdx,
            'source_path': source.license.path.as_posix(),
            'destination': _license_destination(source.id).as_posix(),
            'sha256': _sha256_bytes(license_bytes),
        },
        'skills': skill_records,
    }
    return SourceSnapshot(source, checkout, license_bytes, lock)


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment['GIT_TERMINAL_PROMPT'] = '0'
    return environment


def _run_git(args: tuple[str, ...], *, timeout: int = 120) -> str:
    try:
        completed = subprocess.run(
            ('git', *args),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_git_environment(),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise UpdateError(f'Git failed: {error}') from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or 'Git command failed'
        raise UpdateError(detail)
    return completed.stdout.strip()


def resolve_source(source: ExternalSource) -> ResolvedCheckout:
    temporary = Path(tempfile.mkdtemp(prefix='smartkit-external-source-'))
    checkout = temporary / 'checkout'
    try:
        _run_git(('init', '--quiet', str(checkout)))
        _run_git(('-C', str(checkout), 'remote', 'add', 'origin', source.url))
        try:
            resolution = resolve_ref(source.url, source.ref, _run_git)
        except ExternalContractError as error:
            raise UpdateError(f'{source.id}: {error}') from error
        _run_git((
            '-C', str(checkout), 'fetch', '--quiet', '--depth=1',
            'origin', resolution.fetch_ref,
        ))
        _run_git(('-C', str(checkout), 'checkout', '--quiet', '--detach', 'FETCH_HEAD'))
        commit = _run_git(('-C', str(checkout), 'rev-parse', 'HEAD'), timeout=30)
        resolved = ResolvedCheckout(
            checkout, resolution.resolved_ref, commit, resolution.ref_kind
        )
        # The caller copies and validates synchronously before this process exits. Attach the
        # temporary root to the checkout path and let the caller remove it after snapshotting.
        return resolved
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _cleanup_checkout(checkout: ResolvedCheckout) -> None:
    root = checkout.root.parent
    if root.name.startswith('smartkit-external-source-'):
        shutil.rmtree(root, ignore_errors=True)


def _load_lock(root: Path) -> dict[str, object] | None:
    path = root.joinpath(*LOCK_PATH.parts)
    if not path.exists():
        return None
    return dict(_read_json(path, 'external Skill lock'))


def _lock_sources(lock: Mapping[str, object] | None) -> dict[str, Mapping[str, object]]:
    if lock is None:
        return {}
    if lock.get('version') != 1 or not isinstance(lock.get('sources'), list):
        raise UpdateError('external Skill lock has an invalid shape')
    result: dict[str, Mapping[str, object]] = {}
    for raw in lock['sources']:
        if not isinstance(raw, Mapping) or not isinstance(raw.get('id'), str):
            raise UpdateError('external Skill lock has an invalid source')
        source_id = raw['id']
        if STABLE_ID.fullmatch(source_id) is None or source_id in result:
            raise UpdateError('external Skill lock has duplicate sources')
        license_item = raw.get('license')
        if (
            not isinstance(license_item, Mapping)
            or license_item.get('destination') != _license_destination(source_id).as_posix()
        ):
            raise UpdateError('external Skill lock has an invalid license destination')
        skills = raw.get('skills')
        if not isinstance(skills, list):
            raise UpdateError('external Skill lock source has invalid Skills')
        destinations: set[str] = set()
        for skill in skills:
            if not isinstance(skill, Mapping) or not isinstance(skill.get('id'), str):
                raise UpdateError('external Skill lock has an invalid Skill')
            skill_id = skill['id']
            if STABLE_ID.fullmatch(skill_id) is None:
                raise UpdateError('external Skill lock has an invalid Skill id')
            expected = f'skills/{skill_id.rsplit("/", 1)[1]}'
            if skill.get('destination') != expected or expected in destinations:
                raise UpdateError('external Skill lock has an invalid destination')
            destinations.add(expected)
        result[source_id] = raw
    return result


def _managed_names(lock: Mapping[str, object] | None) -> set[str]:
    names: set[str] = set()
    for source in _lock_sources(lock).values():
        skills = source.get('skills')
        if not isinstance(skills, list):
            raise UpdateError('external Skill lock source has invalid Skills')
        for skill in skills:
            if not isinstance(skill, Mapping):
                raise UpdateError('external Skill lock has an invalid Skill')
            destination = skill.get('destination')
            if not isinstance(destination, str) or not destination.startswith('skills/'):
                raise UpdateError('external Skill lock has an invalid destination')
            name = PurePosixPath(destination).name
            if not NAME.fullmatch(name) or name in names:
                raise UpdateError('external Skill lock has invalid managed names')
            names.add(name)
    return names


def _validate_custom_skills(root: Path, registry: Registry, old_lock: Mapping[str, object] | None) -> None:
    declared = {item.name for item in registry.custom}
    external = {item.name for source in registry.external_sources for item in source.skills}
    actual = {
        path.name for path in (root / 'skills').iterdir()
        if path.is_dir() and not path.is_symlink()
    }
    undeclared = actual - declared - external - _managed_names(old_lock)
    if undeclared:
        raise UpdateError(f'undeclared plugin Skill directories: {", ".join(sorted(undeclared))}')
    for skill in registry.custom:
        skill_root = root / 'skills' / skill.name
        _regular_files(skill_root, f'custom Skill {skill.id}')
        if _frontmatter_name(skill_root / 'SKILL.md') != skill.name:
            raise UpdateError(f'custom Skill name does not match registry: {skill.id}')


def _snapshot_map(
    registry: Registry,
    *,
    resolver: Resolver,
    selected_source: str | None,
) -> dict[str, SourceSnapshot]:
    snapshots: dict[str, SourceSnapshot] = {}
    for source in registry.external_sources:
        if selected_source is not None and source.id != selected_source:
            continue
        checkout = resolver(source)
        try:
            snapshots[source.id] = load_source_snapshot(source, checkout)
        except Exception:
            if resolver is resolve_source:
                _cleanup_checkout(checkout)
            raise
    return snapshots


def _desired_lock(
    registry: Registry,
    snapshots: Mapping[str, SourceSnapshot],
    old_lock: Mapping[str, object] | None,
    *,
    selected_source: str | None,
) -> dict[str, object]:
    old_sources = _lock_sources(old_lock)
    sources: list[Mapping[str, object]] = []
    for source in registry.external_sources:
        snapshot = snapshots.get(source.id)
        if snapshot is not None:
            record = snapshot.lock
            previous = old_sources.get(source.id)
            if (
                previous is not None
                and record.get('ref_kind') == 'tag'
                and previous.get('requested_ref') == record.get('requested_ref')
                and previous.get('commit') != record.get('commit')
            ):
                raise UpdateError(f'external source tag moved: {source.id}:{source.ref}')
            sources.append(record)
        elif selected_source is not None and source.id in old_sources:
            sources.append(old_sources[source.id])
        else:
            raise UpdateError(f'external source has no resolved snapshot: {source.id}')
    return {'version': 1, 'sources': sources}


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
    registry: Registry,
    snapshots: Mapping[str, SourceSnapshot],
    desired_lock: Mapping[str, object],
    *,
    selected_source: str | None,
    replace: ReplacePath = replace_path,
) -> UpdateResult:
    root = root.resolve()
    old_lock = _load_lock(root)
    old_sources = _lock_sources(old_lock)
    desired_sources = _lock_sources(desired_lock)
    old_names = _managed_names(old_lock)
    desired_names = _managed_names(desired_lock)
    touched_source_ids = (
        {selected_source} if selected_source is not None else set(old_sources) | set(desired_sources)
    )
    touched_old_names = _managed_names({
        'version': 1,
        'sources': [old_sources[item] for item in touched_source_ids if item in old_sources],
    })
    touched_new_names = _managed_names({
        'version': 1,
        'sources': [desired_sources[item] for item in touched_source_ids if item in desired_sources],
    })
    desired_skill_records = {
        PurePosixPath(skill['destination']).name: skill
        for source in desired_sources.values()
        for skill in source.get('skills', [])
        if isinstance(skill, Mapping) and isinstance(skill.get('destination'), str)
    }
    for name in touched_new_names - old_names:
        target = root / 'skills' / name
        if target.exists() or target.is_symlink():
            record = desired_skill_records.get(name, {})
            expected = record.get('files') if isinstance(record, Mapping) else None
            actual = {
                path.relative_to(target).as_posix(): _sha256(path)
                for path in _regular_files(target, f'skills/{name}')
            }
            if actual != expected:
                raise UpdateError(f'refusing to overwrite non-external Skill: skills/{name}')

    transaction_root = Path(tempfile.mkdtemp(prefix='.external-skills-update-', dir=root.parent))
    staging = transaction_root / 'staging'
    backup = transaction_root / 'backup'
    operations: list[tuple[Path | None, Path, str]] = []
    originals: dict[str, bool] = {}
    applied: list[tuple[Path | None, Path, str]] = []
    try:
        for source_id in touched_source_ids:
            snapshot = snapshots.get(source_id)
            if snapshot is None:
                continue
            for skill in snapshot.source.skills:
                source_root = snapshot.checkout.root.joinpath(*skill.path.parts)
                staged = staging / 'skills' / skill.name
                shutil.copytree(source_root, staged)
                operations.append((staged, root / 'skills' / skill.name, f'skills/{skill.name}'))
            license_destination = _license_destination(source_id)
            staged_license = staging.joinpath(*license_destination.parts)
            staged_license.parent.mkdir(parents=True, exist_ok=True)
            staged_license.write_bytes(snapshot.license_bytes)
            operations.append(
                (staged_license, root.joinpath(*license_destination.parts), license_destination.as_posix())
            )
        for name in sorted(touched_old_names - touched_new_names):
            operations.append((None, root / 'skills' / name, f'skills/{name}'))
        for source_id in sorted(touched_source_ids - set(desired_sources)):
            old = old_sources.get(source_id)
            if old is None:
                continue
            license_item = old.get('license')
            if isinstance(license_item, Mapping) and isinstance(license_item.get('destination'), str):
                relative = license_item['destination']
                operations.append((None, root.joinpath(*PurePosixPath(relative).parts), relative))

        staged_lock = staging.joinpath(*LOCK_PATH.parts)
        _write_json(staged_lock, desired_lock)
        operations.append((staged_lock, root.joinpath(*LOCK_PATH.parts), LOCK_PATH.as_posix()))

        for _, target, relative in operations:
            exists = target.exists() or target.is_symlink()
            originals[relative] = exists
            if exists:
                _copy_for_backup(target, backup.joinpath(*PurePosixPath(relative).parts))
        for operation in operations:
            staged, target, _ = operation
            applied.append(operation)
            replace(staged, target)
    except Exception as error:
        rollback_errors: list[str] = []
        for _, target, relative in reversed(applied):
            try:
                replace_path(None, target)
                if originals.get(relative):
                    replace_path(backup.joinpath(*PurePosixPath(relative).parts), target)
            except Exception as rollback_error:
                rollback_errors.append(f'{relative}: {rollback_error}')
        detail = f'transaction failed: {error}'
        if rollback_errors:
            detail += f'; rollback failed: {"; ".join(rollback_errors)}'
        raise UpdateError(detail) from error
    finally:
        shutil.rmtree(transaction_root, ignore_errors=True)
    removed = tuple(f'skills/{name}' for name in sorted(touched_old_names - touched_new_names))
    return UpdateResult(tuple(item[2] for item in operations), removed)


def check_repository(root: Path, desired_lock: Mapping[str, object]) -> tuple[str, ...]:
    drift: set[str] = set()
    try:
        local_lock = _load_lock(root)
    except UpdateError:
        local_lock = None
    if local_lock != desired_lock:
        drift.add(LOCK_PATH.as_posix())
    for source in desired_lock.get('sources', []):
        if not isinstance(source, Mapping):
            continue
        for skill in source.get('skills', []):
            if not isinstance(skill, Mapping) or not isinstance(skill.get('destination'), str):
                continue
            destination = skill['destination']
            expected = skill.get('files', {})
            root_path = root.joinpath(*PurePosixPath(destination).parts)
            actual = {
                path.relative_to(root_path).as_posix(): _sha256(path)
                for path in _regular_files(root_path, destination)
            } if root_path.exists() else {}
            if actual != expected:
                drift.add(destination)
        license_item = source.get('license')
        if isinstance(license_item, Mapping) and isinstance(license_item.get('destination'), str):
            destination = license_item['destination']
            path = root.joinpath(*PurePosixPath(destination).parts)
            if not path.is_file() or _sha256(path) != license_item.get('sha256'):
                drift.add(destination)
    return tuple(sorted(drift))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Check or update SmartKit external plugin Skills.')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--update', action='store_true')
    parser.add_argument('--source')
    parser.add_argument(
        '--root', type=Path, default=Path(__file__).resolve().parents[1], help=argparse.SUPPRESS
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, resolver: Resolver = resolve_source) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    snapshots: dict[str, SourceSnapshot] = {}
    try:
        root = args.root.resolve()
        registry = load_registry(root)
        old_lock = _load_lock(root)
        _validate_custom_skills(root, registry, old_lock)
        source_ids = {item.id for item in registry.external_sources}
        if args.source is not None and args.source not in source_ids:
            raise UpdateError(f'unknown external source: {args.source}')
        snapshots = _snapshot_map(registry, resolver=resolver, selected_source=args.source)
        desired_lock = _desired_lock(
            registry, snapshots, old_lock, selected_source=args.source
        )
        if args.check:
            drift = check_repository(root, desired_lock)
            if drift:
                print('External Skill drift:', file=sys.stderr)
                for path in drift:
                    print(f'  {path}', file=sys.stderr)
                return 1
            print(f'External Skills are up to date: {len(registry.external_sources)} sources.')
            return 0
        result = update_repository(
            root,
            registry,
            snapshots,
            desired_lock,
            selected_source=args.source,
        )
        print(
            f'Updated external Skills: {len(snapshots)} sources, '
            f'{sum(len(item.source.skills) for item in snapshots.values())} skills.'
        )
        if result.removed_paths:
            print(f'Removed: {", ".join(result.removed_paths)}')
        return 0
    except UpdateError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2
    finally:
        if resolver is resolve_source:
            for snapshot in snapshots.values():
                _cleanup_checkout(snapshot.checkout)


if __name__ == '__main__':
    raise SystemExit(main())
