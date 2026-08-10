from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .catalog import safe_field_key, safe_relative
from .models import ContractError, DesiredField, DesiredFile
from .project import ProjectError, confined_target
from .structured import StructuredConfigError, format_for_path, parse_document


OWNERSHIP_PATH = PurePosixPath('.agents/smartkit.lock.json')
SEEDED_PATHS = frozenset({
    PurePosixPath('docs/agents/domain.md'),
    PurePosixPath('docs/agents/issue-tracker.md'),
    PurePosixPath('docs/agents/triage-labels.md'),
})
_ASSET_FIELDS = frozenset({'kind', 'role', 'path', 'key', 'digest', 'source', 'source_path'})
_ASSET_KINDS = frozenset({'file', 'tree', 'field'})
_SOURCE_FIELDS = frozenset({
    'id', 'url', 'requested_ref', 'resolved_ref', 'ref_kind', 'commit', 'license', 'skills',
})
_LICENSE_FIELDS = frozenset({'spdx', 'path', 'sha256'})
_SOURCE_SKILL_FIELDS = frozenset({'id', 'path'})
_SEEDED_FIELDS = frozenset({'path', 'digest'})


class OwnershipError(ValueError):
    """Raised when SmartKit cannot safely reconcile managed project assets."""


@dataclass(frozen=True)
class OwnedAsset:
    kind: str
    role: str
    path: PurePosixPath
    digest: str
    key: str | None = None
    source: str | None = None
    source_path: PurePosixPath | None = None

    @property
    def identity(self) -> tuple[str, PurePosixPath, str | None]:
        return self.kind, self.path, self.key


@dataclass(frozen=True)
class OwnershipState:
    sources: tuple[Mapping[str, object], ...]
    assets: tuple[OwnedAsset, ...]


@dataclass(frozen=True)
class OwnershipResult:
    files: tuple[DesiredFile, ...]
    manifest: bytes
    delete_paths: tuple[PurePosixPath, ...]
    remove_fields: tuple[tuple[PurePosixPath, str], ...]


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _is_digest(value: object, length: int = 64) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in '0123456789abcdef' for character in value)
    )


def _value_digest(value: object) -> str:
    return _digest(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8'))


def _tree_digest_from_files(
    root: PurePosixPath,
    files: Mapping[PurePosixPath, bytes],
) -> str:
    entries = (
        (path.relative_to(root).as_posix(), content)
        for path, content in files.items()
        if root in path.parents
    )
    return _tree_digest_entries(entries)


def _tree_digest_entries(entries) -> str:
    digest = hashlib.sha256()
    for relative, content in sorted(entries, key=lambda item: item[0]):
        digest.update(relative.encode('utf-8'))
        digest.update(b'\0')
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def _target(target_root: Path, path: PurePosixPath) -> Path:
    try:
        return confined_target(target_root, path)
    except ProjectError as error:
        raise OwnershipError(str(error)) from error


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, 'is_junction') and path.is_junction()
    )


def _actual_file_digest(target_root: Path, path: PurePosixPath) -> str | None:
    target = _target(target_root, path)
    if not target.exists():
        return None
    if _is_link_like(target) or not target.is_file():
        raise OwnershipError(f'managed file is unsafe: {path.as_posix()}')
    try:
        return _digest(target.read_bytes())
    except OSError as error:
        raise OwnershipError(f'cannot read managed file: {path.as_posix()}') from error


def _actual_tree_digest(target_root: Path, root: PurePosixPath) -> str | None:
    target = _target(target_root, root)
    if not target.exists():
        return None
    if _is_link_like(target) or not target.is_dir():
        raise OwnershipError(f'managed tree is unsafe: {root.as_posix()}')
    entries: list[tuple[str, bytes]] = []
    for child in target.rglob('*'):
        relative = child.relative_to(target).as_posix()
        if _is_link_like(child):
            raise OwnershipError(f'managed tree contains a symlink: {root / relative}')
        if child.is_file():
            try:
                entries.append((relative, child.read_bytes()))
            except OSError as error:
                raise OwnershipError(f'cannot read managed tree: {root.as_posix()}') from error
        elif not child.is_dir():
            raise OwnershipError(f'managed tree contains an unsafe entry: {root / relative}')
    return _tree_digest_entries(entries)


def _dotted_value(document: Mapping[str, object], key: str) -> tuple[bool, object | None]:
    current: object = document
    for segment in key.split('.'):
        if not isinstance(current, Mapping) or segment not in current:
            return False, None
        current = current[segment]
    return True, current


def _actual_field_digest(
    target_root: Path,
    path: PurePosixPath,
    key: str,
) -> str | None:
    target = _target(target_root, path)
    if not target.exists():
        return None
    format_name = format_for_path(path)
    if format_name is None or target.is_symlink() or not target.is_file():
        raise OwnershipError(f'managed field path is unsafe: {path.as_posix()}')
    try:
        document = parse_document(target.read_bytes(), format_name)
    except (OSError, StructuredConfigError) as error:
        raise OwnershipError(f'cannot parse managed field path: {path.as_posix()}') from error
    exists, value = _dotted_value(document, key)
    return _value_digest(value) if exists else None


def _actual_digest(target_root: Path, asset: OwnedAsset) -> str | None:
    if asset.kind == 'file':
        return _actual_file_digest(target_root, asset.path)
    if asset.kind == 'tree':
        return _actual_tree_digest(target_root, asset.path)
    assert asset.key is not None
    return _actual_field_digest(target_root, asset.path, asset.key)


def _parse_asset(raw: object, index: int) -> OwnedAsset:
    if not isinstance(raw, Mapping) or set(raw) - _ASSET_FIELDS:
        raise OwnershipError(f'SmartKit ownership manifest asset {index} is invalid')
    kind = raw.get('kind')
    role = raw.get('role')
    digest = raw.get('digest')
    if kind not in _ASSET_KINDS or not isinstance(role, str) or not role:
        raise OwnershipError(f'SmartKit ownership manifest asset {index} is invalid')
    if not _is_digest(digest):
        raise OwnershipError(f'SmartKit ownership manifest asset {index} is invalid')
    try:
        path = safe_relative(raw.get('path'), 'ownership asset path')
    except ContractError as error:
        raise OwnershipError(str(error)) from error
    key = raw.get('key')
    if kind == 'field':
        try:
            key = safe_field_key(key, 'ownership asset key')
        except ContractError as error:
            raise OwnershipError(str(error)) from error
    elif key is not None:
        raise OwnershipError(f'SmartKit ownership manifest asset {index} is invalid')
    source = raw.get('source')
    source_path = raw.get('source_path')
    if source is not None and not isinstance(source, str):
        raise OwnershipError(f'SmartKit ownership manifest asset {index} is invalid')
    if source_path is not None:
        try:
            source_path = safe_relative(source_path, 'ownership asset source_path')
        except ContractError as error:
            raise OwnershipError(str(error)) from error
    if (source is None) != (source_path is None) or (
        source is not None and (kind != 'tree' or role != 'skill')
    ):
        raise OwnershipError(f'SmartKit ownership manifest asset {index} provenance is invalid')
    return OwnedAsset(kind, role, path, digest, key, source, source_path)


def _parse_source(raw: object, index: int) -> Mapping[str, object]:
    if not isinstance(raw, Mapping) or set(raw) != _SOURCE_FIELDS:
        raise OwnershipError(f'SmartKit ownership manifest source {index} is invalid')
    required_strings = ('id', 'url', 'resolved_ref', 'commit')
    if any(not isinstance(raw.get(key), str) or not raw[key] for key in required_strings):
        raise OwnershipError(f'SmartKit ownership manifest source {index} is invalid')
    if len(raw['commit']) != 40 or any(
        character not in '0123456789abcdef' for character in raw['commit']
    ):
        raise OwnershipError(f'SmartKit ownership manifest source {index} is invalid')
    if raw.get('requested_ref') is not None and (
        not isinstance(raw['requested_ref'], str) or not raw['requested_ref']
    ):
        raise OwnershipError(f'SmartKit ownership manifest source {index} is invalid')
    if raw.get('ref_kind') not in {'branch', 'tag', 'commit'}:
        raise OwnershipError(f'SmartKit ownership manifest source {index} is invalid')
    license_item = raw.get('license')
    if not isinstance(license_item, Mapping) or set(license_item) != _LICENSE_FIELDS:
        raise OwnershipError(f'SmartKit ownership manifest source {index} license is invalid')
    if (
        not isinstance(license_item.get('spdx'), str)
        or not license_item['spdx']
        or not isinstance(license_item.get('path'), str)
        or not license_item['path']
        or not _is_digest(license_item.get('sha256'))
    ):
        raise OwnershipError(f'SmartKit ownership manifest source {index} license is invalid')
    skills = raw.get('skills')
    if not isinstance(skills, list) or not skills:
        raise OwnershipError(f'SmartKit ownership manifest source {index} Skills are invalid')
    normalized_skills: list[Mapping[str, object]] = []
    for skill_index, item in enumerate(skills):
        if not isinstance(item, Mapping) or set(item) != _SOURCE_SKILL_FIELDS:
            raise OwnershipError(
                f'SmartKit ownership manifest source {index} Skill {skill_index} is invalid'
            )
        if not isinstance(item.get('id'), str) or not item['id']:
            raise OwnershipError(
                f'SmartKit ownership manifest source {index} Skill {skill_index} is invalid'
            )
        try:
            skill_path = safe_relative(item.get('path'), 'ownership source Skill path')
        except ContractError as error:
            raise OwnershipError(str(error)) from error
        normalized_skills.append({'id': item['id'], 'path': skill_path.as_posix()})
    skill_ids = [item['id'] for item in normalized_skills]
    if len(skill_ids) != len(set(skill_ids)):
        raise OwnershipError(f'SmartKit ownership manifest source {index} has duplicate Skills')
    return {
        'id': raw['id'],
        'url': raw['url'],
        'requested_ref': raw['requested_ref'],
        'resolved_ref': raw['resolved_ref'],
        'ref_kind': raw['ref_kind'],
        'commit': raw['commit'],
        'license': dict(license_item),
        'skills': normalized_skills,
    }


def _parse_seeded(raw: object, index: int) -> tuple[PurePosixPath, str]:
    if not isinstance(raw, Mapping) or set(raw) != _SEEDED_FIELDS:
        raise OwnershipError(f'SmartKit ownership manifest seeded asset {index} is invalid')
    try:
        path = safe_relative(raw.get('path'), 'ownership seeded path')
    except ContractError as error:
        raise OwnershipError(str(error)) from error
    digest = raw.get('digest')
    if path not in SEEDED_PATHS or not _is_digest(digest):
        raise OwnershipError(f'SmartKit ownership manifest seeded asset {index} is invalid')
    return path, digest


def _parse_ownership_document(document: object) -> OwnershipState:
    if not isinstance(document, Mapping) or set(document) != {'version', 'sources', 'assets', 'seeded'}:
        raise OwnershipError('SmartKit ownership manifest is invalid')
    if document.get('version') != 1 or not isinstance(document.get('sources'), list):
        raise OwnershipError('SmartKit ownership manifest is invalid')
    if not isinstance(document.get('assets'), list) or not isinstance(document.get('seeded'), list):
        raise OwnershipError('SmartKit ownership manifest is invalid')
    sources = tuple(_parse_source(item, index) for index, item in enumerate(document['sources']))
    source_ids = [item['id'] for item in sources]
    if len(source_ids) != len(set(source_ids)):
        raise OwnershipError('SmartKit ownership manifest has duplicate sources')
    assets = tuple(_parse_asset(item, index) for index, item in enumerate(document['assets']))
    identities = [item.identity for item in assets]
    if len(identities) != len(set(identities)):
        raise OwnershipError('SmartKit ownership manifest has duplicate assets')
    declared_provenance = {
        (source['id'], skill['path'], str(skill['id']).rsplit('/', 1)[-1])
        for source in sources
        for skill in source['skills']
    }
    actual_provenance = {
        (asset.source, asset.source_path.as_posix(), asset.path.name)
        for asset in assets
        if asset.source is not None and asset.source_path is not None
    }
    if declared_provenance != actual_provenance:
        raise OwnershipError('SmartKit ownership manifest Skill provenance is invalid')
    seeded = tuple(_parse_seeded(item, index) for index, item in enumerate(document['seeded']))
    seeded_paths = [item[0] for item in seeded]
    if len(seeded_paths) != len(set(seeded_paths)):
        raise OwnershipError('SmartKit ownership manifest has duplicate seeded assets')
    return OwnershipState(sources, assets)


def load_ownership_file(path: Path) -> OwnershipState | None:
    if not path.exists():
        return None
    if _is_link_like(path) or not path.is_file():
        raise OwnershipError('SmartKit ownership manifest is unsafe')
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OwnershipError('SmartKit ownership manifest is invalid') from error
    return _parse_ownership_document(document)


def load_ownership(target_root: Path) -> OwnershipState | None:
    return load_ownership_file(_target(target_root, OWNERSHIP_PATH))


def verify_ownership(target_root: Path, state: OwnershipState | None) -> None:
    if state is None:
        return
    for asset in state.assets:
        if _actual_digest(target_root, asset) != asset.digest:
            suffix = f':{asset.key}' if asset.key is not None else ''
            raise OwnershipError(
                f'SmartKit-managed asset was modified outside setup: '
                f'{asset.path.as_posix()}{suffix}'
            )


def _role(path: PurePosixPath, key: str | None = None) -> str:
    if key is not None and key.split('.', 1)[0] in {'mcp_servers', 'mcpServers', 'servers'}:
        return 'mcp'
    if 'rules' in path.parts or 'instructions' in path.parts:
        return 'rule'
    if 'skills' in path.parts:
        return 'skill'
    if 'agents' in path.parts and path.name != 'config.json':
        return 'agent'
    return 'config'


def _desired_assets(
    files: Mapping[PurePosixPath, bytes],
    fields: Sequence[DesiredField],
    trees: Sequence[PurePosixPath],
    external_sources: Mapping[str, tuple[str, PurePosixPath]],
    structured_paths: frozenset[PurePosixPath],
) -> tuple[OwnedAsset, ...]:
    tree_set = tuple(sorted(set(trees), key=lambda item: item.as_posix()))
    assets: list[OwnedAsset] = []
    for root in tree_set:
        source = external_sources.get(root.name)
        assets.append(OwnedAsset(
            'tree', _role(root), root, _tree_digest_from_files(root, files),
            source=source[0] if source else None,
            source_path=source[1] if source else None,
        ))
    for path, content in sorted(files.items(), key=lambda item: item[0].as_posix()):
        if (
            path == OWNERSHIP_PATH
            or path in SEEDED_PATHS
            or path in structured_paths
            or any(root == path or root in path.parents for root in tree_set)
        ):
            continue
        assets.append(OwnedAsset('file', _role(path), path, _digest(content)))
    assets.extend(
        OwnedAsset('field', _role(field.path, field.key), field.path, _value_digest(field.value), field.key)
        for field in fields
    )
    return tuple(sorted(assets, key=lambda item: (
        item.path.as_posix(), item.key or '', item.kind,
    )))


def reconcile_ownership(
    target_root: Path,
    desired_files: Sequence[DesiredFile],
    desired_fields: Sequence[DesiredField],
    managed_trees: Sequence[PurePosixPath],
    *,
    sources: Sequence[Mapping[str, object]] = (),
    external_sources: Mapping[str, tuple[str, PurePosixPath]] | None = None,
    structured_paths: Sequence[PurePosixPath] = (),
    previous: OwnershipState | None = None,
) -> OwnershipResult:
    previous = previous if previous is not None else load_ownership(target_root)
    verify_ownership(target_root, previous)
    files = {item.path: item.content for item in desired_files}
    for path in SEEDED_PATHS.intersection(files):
        target = _target(target_root, path)
        if not target.exists():
            continue
        if target.is_symlink() or not target.is_file():
            raise OwnershipError(f'seeded project file is unsafe: {path.as_posix()}')
        files[path] = target.read_bytes()
    desired_assets = _desired_assets(
        files,
        desired_fields,
        managed_trees,
        external_sources or {},
        frozenset(structured_paths) | frozenset(item.path for item in desired_fields),
    )
    previous_by_id = {
        item.identity: item for item in previous.assets
    } if previous is not None else {}
    desired_by_id = {item.identity: item for item in desired_assets}
    for identity, asset in desired_by_id.items():
        if identity in previous_by_id:
            continue
        actual = _actual_digest(target_root, asset)
        if actual is not None and actual != asset.digest:
            suffix = f':{asset.key}' if asset.key is not None else ''
            raise OwnershipError(
                f'SmartKit cannot adopt conflicting project asset: '
                f'{asset.path.as_posix()}{suffix}'
            )
    removed = [
        asset for identity, asset in previous_by_id.items() if identity not in desired_by_id
    ]
    delete_paths = tuple(
        asset.path for asset in removed if asset.kind in {'file', 'tree'}
    )
    remove_fields = tuple(
        (asset.path, asset.key)
        for asset in removed
        if asset.kind == 'field' and asset.key is not None
    )
    manifest_assets = []
    for asset in desired_assets:
        item: dict[str, object] = {
            'kind': asset.kind,
            'role': asset.role,
            'path': asset.path.as_posix(),
            'digest': asset.digest,
        }
        if asset.key is not None:
            item['key'] = asset.key
        if asset.source is not None:
            item['source'] = asset.source
        if asset.source_path is not None:
            item['source_path'] = asset.source_path.as_posix()
        manifest_assets.append(item)
    seeded = [
        {'path': path.as_posix(), 'digest': _digest(files[path])}
        for path in sorted(SEEDED_PATHS.intersection(files), key=lambda item: item.as_posix())
    ]
    next_document = {
        'version': 1,
        'sources': [dict(item) for item in sources],
        'assets': manifest_assets,
        'seeded': seeded,
    }
    _parse_ownership_document(next_document)
    manifest = (json.dumps(
        next_document, ensure_ascii=False, indent=2,
    ) + '\n').encode('utf-8')
    return OwnershipResult(
        tuple(DesiredFile(path, content) for path, content in sorted(files.items())),
        manifest,
        tuple(sorted(set(delete_paths), key=lambda item: item.as_posix())),
        tuple(sorted(remove_fields, key=lambda item: (item[0].as_posix(), item[1]))),
    )
