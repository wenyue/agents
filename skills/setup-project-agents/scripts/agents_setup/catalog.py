from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

from .models import (
    AssetSpec,
    Catalog,
    ContractError,
    LockState,
    ManagedField,
    ManagedFile,
    Platform,
    ProjectConfig,
)


_SEMVER = re.compile(
    r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
    r'(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)'
    r'(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?'
    r'(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$'
)
_HEX_40 = re.compile(r'^[0-9a-fA-F]{40}$')
_HEX_64 = re.compile(r'^[0-9a-fA-F]{64}$')
_NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
_FIELD_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_@-]*$')
_WINDOWS_RESERVED_CHARACTERS = frozenset('<>:"\\|?*')
_WINDOWS_RESERVED_NAMES = frozenset(
    {'CON', 'PRN', 'AUX', 'NUL', 'COM¹', 'COM²', 'COM³', 'LPT¹', 'LPT²', 'LPT³'}
    | {f'COM{number}' for number in range(1, 10)}
    | {f'LPT{number}' for number in range(1, 10)}
)
_ASSET_FIELDS = frozenset({'id', 'kind', 'source', 'target', 'platforms', 'mode', 'control_plane'})
_CATALOG_FIELDS = frozenset({'plugin', 'assets'})
_PLUGIN_FIELDS = frozenset({'id', 'version', 'repository', 'ref'})
_PROJECT_CONFIG_FIELDS = frozenset({'version', 'platforms', 'hooks_enabled', 'selected_rules', 'selected_skills', 'selected_agents'})
_LOCK_FIELDS = frozenset({'version', 'source_commit', 'managed_files', 'managed_fields'})
_MANAGED_FILE_FIELDS = frozenset({'path', 'sha256'})
_MANAGED_FIELD_FIELDS = frozenset({'path', 'key', 'sha256'})


def safe_relative(value: str, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or '\\' in value:
        raise ContractError(f'{label} must be a relative path')
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or re.match(r'^[A-Za-z]:', value)
        or value == '.'
        or any(part in {'.', '..'} for part in value.split('/'))
    ):
        raise ContractError(f'{label} must be a relative path')
    for part in value.split('/'):
        if (
            any(unicodedata.category(character) == 'Cc' for character in part)
            or any(character in _WINDOWS_RESERVED_CHARACTERS for character in part)
            or part.endswith((' ', '.'))
            or part.split('.', 1)[0].upper() in _WINDOWS_RESERVED_NAMES
        ):
            raise ContractError(f'{label} must be a portable relative path')
    return path


def _name(value: object, label: str) -> str:
    if not isinstance(value, str) or not _NAME.fullmatch(value):
        raise ContractError(f'{label} must be a safe name')
    return value


def safe_field_key(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ContractError(f'{label} must be a dotted safe name')
    for segment in value.split('.'):
        if not _FIELD_NAME.fullmatch(segment):
            raise ContractError(f'{label} must be a dotted safe name')
    return value


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ContractError(f'{label} must be an object')
    return value


def _fields(value: Mapping[str, object], allowed: frozenset[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        names = ', '.join(sorted(str(item) for item in unknown))
        raise ContractError(f'unknown {label} fields: {names}')


def _required(value: Mapping[str, object], key: str, label: str) -> object:
    if key not in value:
        raise ContractError(f'{label} requires {key}')
    return value[key]


def _platforms(value: object, label: str, default: tuple[Platform, ...]) -> tuple[Platform, ...]:
    if value is None:
        return default
    if not isinstance(value, list):
        raise ContractError(f'{label} must be an array')
    result: list[Platform] = []
    for item in value:
        try:
            platform = Platform(item)
        except (TypeError, ValueError) as error:
            raise ContractError(f'{label} has an unsupported platform') from error
        if platform in result:
            raise ContractError(f'{label} has duplicate platforms')
        result.append(platform)
    return tuple(result)


def parse_asset(value: Mapping[str, object]) -> AssetSpec:
    asset = _object(value, 'asset')
    _fields(asset, _ASSET_FIELDS, 'asset')
    asset_id = _name(_required(asset, 'id', 'asset'), 'asset id')
    kind = _name(_required(asset, 'kind', 'asset'), 'asset kind')
    source_value = _required(asset, 'source', 'asset')
    if not isinstance(source_value, str):
        raise ContractError('asset source must be a relative path')
    source = safe_relative(source_value, 'asset source')
    target_value = asset.get('target')
    if target_value is not None and not isinstance(target_value, str):
        raise ContractError('asset target must be a relative path')
    target = safe_relative(target_value, 'asset target') if target_value is not None else None
    platforms = _platforms(asset.get('platforms'), 'asset platforms', tuple(Platform))
    mode = _name(asset.get('mode', 'copy'), 'asset mode')
    control_plane = asset.get('control_plane', False)
    if type(control_plane) is not bool:
        raise ContractError('asset control_plane must be a boolean')
    if control_plane and target is not None:
        raise ContractError('a control-plane asset cannot have a project target')
    return AssetSpec(asset_id, kind, source, target, platforms, mode, control_plane)


def _load_json(path: Path, label: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except OSError as error:
        raise ContractError(f'cannot read {label}: {path}') from error
    except json.JSONDecodeError as error:
        raise ContractError(f'{label} is not valid JSON') from error
    return _object(value, label)


def load_catalog(source_root: Path) -> Catalog:
    root = source_root.resolve()
    try:
        version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    except OSError as error:
        raise ContractError(f'cannot read VERSION: {root / "VERSION"}') from error
    if not _SEMVER.fullmatch(version):
        raise ContractError('VERSION must be semantic version')
    document = _load_json(root / 'catalog' / 'project-assets.json', 'catalog')
    _fields(document, _CATALOG_FIELDS, 'catalog')
    plugin = _object(_required(document, 'plugin', 'catalog'), 'catalog plugin')
    _fields(plugin, _PLUGIN_FIELDS, 'catalog plugin')
    plugin_id = _name(_required(plugin, 'id', 'catalog plugin'), 'catalog plugin id')
    plugin_version = _required(plugin, 'version', 'catalog plugin')
    if not isinstance(plugin_version, str) or not _SEMVER.fullmatch(plugin_version):
        raise ContractError('catalog plugin version must be semantic version')
    if plugin_version != version:
        raise ContractError('catalog plugin version must match VERSION')
    repository = _required(plugin, 'repository', 'catalog plugin')
    ref = _required(plugin, 'ref', 'catalog plugin')
    if not isinstance(repository, str) or not repository:
        raise ContractError('catalog plugin repository must be a string')
    if not isinstance(ref, str) or not ref:
        raise ContractError('catalog plugin ref must be a string')
    asset_values = _required(document, 'assets', 'catalog')
    if not isinstance(asset_values, list):
        raise ContractError('catalog assets must be an array')
    assets = tuple(parse_asset(_object(item, 'catalog asset')) for item in asset_values)
    if len({asset.id for asset in assets}) != len(assets):
        raise ContractError('catalog has duplicate asset ids')
    targets = [asset.target for asset in assets if asset.target is not None]
    if len(set(targets)) != len(targets):
        raise ContractError('catalog has duplicate asset targets')
    return Catalog(plugin_id, plugin_version, repository, ref, assets)


def _selected(value: object, label: str, catalog: Catalog, kind: str) -> tuple[str, ...]:
    available = {
        asset.id
        for asset in catalog.assets
        if asset.kind == kind and not asset.control_plane
    }
    if value is None:
        return tuple(
            asset.id
            for asset in catalog.assets
            if asset.kind == kind and not asset.control_plane
        )
    if not isinstance(value, list):
        raise ContractError(f'{label} must be an array')
    selected = tuple(_name(item, label) for item in value)
    if len(set(selected)) != len(selected):
        raise ContractError(f'{label} has duplicate ids')
    if set(selected) - available:
        raise ContractError(f'{label} contains unknown ids')
    return selected


def load_project_config(path: Path | None, *, catalog: Catalog) -> ProjectConfig:
    document: Mapping[str, object]
    if path is None or not path.exists():
        document = {}
    else:
        document = _load_json(path, 'project config')
    _fields(document, _PROJECT_CONFIG_FIELDS, 'project config')
    version = document.get('version', 1)
    if type(version) is not int or version != 1:
        raise ContractError('project config version must be 1')
    platforms = _platforms(document.get('platforms'), 'project config platforms', tuple(Platform))
    hooks_enabled = document.get('hooks_enabled', False)
    if type(hooks_enabled) is not bool:
        raise ContractError('project config hooks_enabled must be a boolean')
    return ProjectConfig(
        version, platforms, hooks_enabled,
        _selected(document.get('selected_rules'), 'selected_rules', catalog, 'rule'),
        _selected(document.get('selected_skills'), 'selected_skills', catalog, 'skill'),
        _selected(document.get('selected_agents'), 'selected_agents', catalog, 'agent'),
    )


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise ContractError(f'{label} must be a 64-character hexadecimal SHA-256')
    return value


def _managed_file(value: object) -> ManagedFile:
    item = _object(value, 'managed file')
    _fields(item, _MANAGED_FILE_FIELDS, 'managed file')
    path = _required(item, 'path', 'managed file')
    if not isinstance(path, str):
        raise ContractError('managed file path must be a relative path')
    return ManagedFile(safe_relative(path, 'managed file path'), _sha256(_required(item, 'sha256', 'managed file'), 'managed file sha256'))


def _managed_field(value: object) -> ManagedField:
    item = _object(value, 'managed field')
    _fields(item, _MANAGED_FIELD_FIELDS, 'managed field')
    path = _required(item, 'path', 'managed field')
    if not isinstance(path, str):
        raise ContractError('managed field path must be a relative path')
    return ManagedField(
        safe_relative(path, 'managed field path'),
        safe_field_key(_required(item, 'key', 'managed field'), 'managed field key'),
        _sha256(_required(item, 'sha256', 'managed field'), 'managed field sha256'),
    )


def validate_lock_state(lock: LockState) -> LockState:
    """Validate an in-memory lock with the same contract as a parsed lock document."""
    if not isinstance(lock, LockState):
        raise ContractError('lock state must be a LockState')
    if type(lock.version) is not int or lock.version != 1:
        raise ContractError('lock version must be 1')
    if lock.source_commit is not None and (
        not isinstance(lock.source_commit, str) or not _HEX_40.fullmatch(lock.source_commit)
    ):
        raise ContractError('lock source_commit must be a 40-character hexadecimal commit')
    files: list[ManagedFile] = []
    fields: list[ManagedField] = []
    for item in lock.managed_files:
        if not isinstance(item, ManagedFile) or not isinstance(item.path, PurePosixPath):
            raise ContractError('lock managed file must be a ManagedFile')
        path = safe_relative(item.path.as_posix(), 'managed file path')
        files.append(ManagedFile(path, _sha256(item.sha256, 'managed file sha256')))
    for item in lock.managed_fields:
        if not isinstance(item, ManagedField) or not isinstance(item.path, PurePosixPath):
            raise ContractError('lock managed field must be a ManagedField')
        path = safe_relative(item.path.as_posix(), 'managed field path')
        fields.append(
            ManagedField(
                path,
                safe_field_key(item.key, 'managed field key'),
                _sha256(item.sha256, 'managed field sha256'),
            )
        )
    if len({item.path for item in files}) != len(files):
        raise ContractError('lock has duplicate managed file paths')
    if len({(item.path, item.key) for item in fields}) != len(fields):
        raise ContractError('lock has duplicate managed fields')
    return LockState(lock.version, lock.source_commit, tuple(files), tuple(fields))


def load_lock(path: Path | None) -> LockState:
    if path is None or not path.exists():
        return LockState.empty()
    document = _load_json(path, 'lock')
    _fields(document, _LOCK_FIELDS, 'lock')
    version = _required(document, 'version', 'lock')
    if type(version) is not int or version != 1:
        raise ContractError('lock version must be 1')
    source_commit = _required(document, 'source_commit', 'lock')
    if source_commit is not None and (not isinstance(source_commit, str) or not _HEX_40.fullmatch(source_commit)):
        raise ContractError('lock source_commit must be a 40-character hexadecimal commit')
    file_values = _required(document, 'managed_files', 'lock')
    field_values = _required(document, 'managed_fields', 'lock')
    if not isinstance(file_values, list) or not isinstance(field_values, list):
        raise ContractError('lock managed collections must be arrays')
    files = tuple(_managed_file(item) for item in file_values)
    fields = tuple(_managed_field(item) for item in field_values)
    if len({item.path for item in files}) != len(files):
        raise ContractError('lock has duplicate managed file paths')
    if len({(item.path, item.key) for item in fields}) != len(fields):
        raise ContractError('lock has duplicate managed fields')
    return validate_lock_state(LockState(version, source_commit, files, fields))
