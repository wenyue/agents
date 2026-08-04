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
    ExternalSkillSpec,
    Platform,
    ProjectConfig,
)


_SEMVER = re.compile(
    r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
    r'(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)'
    r'(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?'
    r'(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$'
)
_NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
_REPOSITORY = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
_GIT_REF = re.compile(r'^[A-Za-z0-9._/-]+$')
_FIELD_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_@-]*$')
_WINDOWS_RESERVED_CHARACTERS = frozenset('<>:"\\|?*')
_WINDOWS_RESERVED_NAMES = frozenset(
    {'CON', 'PRN', 'AUX', 'NUL', 'COM¹', 'COM²', 'COM³', 'LPT¹', 'LPT²', 'LPT³'}
    | {f'COM{number}' for number in range(1, 10)}
    | {f'LPT{number}' for number in range(1, 10)}
)
_ASSET_FIELDS = frozenset({'id', 'kind', 'source', 'target', 'platforms', 'mode', 'control_plane', 'metadata'})
_CATALOG_FIELDS = frozenset({'plugin', 'assets', 'retired_assets'})
_PLUGIN_FIELDS = frozenset({'id', 'version', 'repository', 'ref'})
_PROJECT_CONFIG_FIELDS = frozenset(
    {'$schema', 'version', 'platforms', 'selected_rules', 'selected_skills', 'selected_agents', 'skills'}
)
_SKILLS_FIELDS = frozenset({'external'})
_EXTERNAL_SKILL_FIELDS = frozenset({'name', 'repository', 'ref', 'path'})


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


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f'{label} must be a non-empty string')
    return value


def _rule_metadata(value: object, *, project_blueprint: bool) -> Mapping[str, object]:
    metadata = _object(value, 'asset metadata')
    _fields(metadata, frozenset({'section', 'read_when', 'strength', 'cursor', 'github'}), 'rule metadata')
    for field in ('section', 'read_when', 'strength', 'cursor', 'github'):
        _required(metadata, field, 'rule metadata')
    section = _nonempty_string(metadata['section'], 'rule metadata section')
    if section not in {'global', 'base', 'project'} or (project_blueprint and section != 'project'):
        raise ContractError('rule metadata section is unsupported')
    strength = _nonempty_string(metadata['strength'], 'rule metadata strength')
    if strength not in {'Mandatory', 'Default', 'Advisory'}:
        raise ContractError('rule metadata strength is unsupported')
    _nonempty_string(metadata['read_when'], 'rule metadata read_when')
    cursor = _object(metadata['cursor'], 'rule metadata cursor')
    allowed_cursor = {'alwaysApply'} if project_blueprint else {'description', 'globs', 'alwaysApply'}
    _fields(cursor, frozenset(allowed_cursor), 'rule metadata cursor')
    _required(cursor, 'alwaysApply', 'rule metadata cursor')
    if type(cursor['alwaysApply']) is not bool:
        raise ContractError('rule metadata cursor alwaysApply must be a boolean')
    if not project_blueprint:
        _nonempty_string(_required(cursor, 'description', 'rule metadata cursor'), 'rule metadata cursor description')
        if not cursor['alwaysApply']:
            _nonempty_string(_required(cursor, 'globs', 'rule metadata cursor'), 'rule metadata cursor globs')
        elif 'globs' in cursor:
            _nonempty_string(cursor['globs'], 'rule metadata cursor globs')
    github = _object(metadata['github'], 'rule metadata github')
    _fields(github, frozenset({'applyTo'}), 'rule metadata github')
    _nonempty_string(_required(github, 'applyTo', 'rule metadata github'), 'rule metadata github applyTo')
    return dict(metadata)


def _agent_metadata(value: object) -> Mapping[str, object]:
    metadata = _object(value, 'asset metadata')
    _fields(metadata, frozenset({'description', 'codex', 'cursor'}), 'agent metadata')
    _nonempty_string(_required(metadata, 'description', 'agent metadata'), 'agent metadata description')
    codex = _object(_required(metadata, 'codex', 'agent metadata'), 'agent metadata codex')
    _fields(codex, frozenset({'sandbox_mode'}), 'agent metadata codex')
    _nonempty_string(_required(codex, 'sandbox_mode', 'agent metadata codex'), 'agent metadata codex sandbox_mode')
    cursor = _object(_required(metadata, 'cursor', 'agent metadata'), 'agent metadata cursor')
    _fields(cursor, frozenset({'readonly'}), 'agent metadata cursor')
    if type(_required(cursor, 'readonly', 'agent metadata cursor')) is not bool:
        raise ContractError('agent metadata cursor readonly must be a boolean')
    return dict(metadata)


def _metadata(value: object, kind: str, target: PurePosixPath | None) -> Mapping[str, object]:
    if kind == 'rule':
        return _rule_metadata(value, project_blueprint=False)
    if kind == 'agent':
        return _agent_metadata(value)
    is_project_rule_blueprint = (
        kind == 'blueprint'
        and target is not None
        and target.parts[:2] == ('.agents', 'rules')
    )
    if is_project_rule_blueprint:
        return _rule_metadata(value, project_blueprint=True)
    if value is not None:
        metadata = _object(value, 'asset metadata')
        if metadata:
            raise ContractError(f'asset kind {kind} cannot declare metadata')
    return {}


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
    return AssetSpec(
        asset_id, kind, source, target, platforms, mode, control_plane,
        _metadata(asset.get('metadata'), kind, target),
    )


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
    document = _load_json(root / 'setup-assets' / 'catalog' / 'assets.json', 'catalog')
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
    retired_value = document.get('retired_assets', [])
    if not isinstance(retired_value, list) or not all(
        isinstance(item, str) for item in retired_value
    ):
        raise ContractError('catalog retired_assets must be an array of paths')
    retired_assets = tuple(
        safe_relative(item, 'catalog retired asset') for item in retired_value
    )
    if len(set(retired_assets)) != len(retired_assets):
        raise ContractError('catalog has duplicate retired assets')
    if set(retired_assets).intersection(targets):
        raise ContractError('catalog asset cannot be active and retired')
    return Catalog(plugin_id, plugin_version, repository, ref, assets, retired_assets)


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


def parse_external_skills(value: object, catalog: Catalog) -> tuple[ExternalSkillSpec, ...]:
    if value is None:
        return ()
    skills = _object(value, 'project config skills')
    _fields(skills, _SKILLS_FIELDS, 'project config skills')
    external = skills.get('external', [])
    if not isinstance(external, list):
        raise ContractError('project config skills.external must be an array')
    reserved = {asset.id for asset in catalog.assets if asset.kind == 'skill'}
    result: list[ExternalSkillSpec] = []
    for index, item in enumerate(external):
        document = _object(item, f'project config skills.external[{index}]')
        _fields(document, _EXTERNAL_SKILL_FIELDS, 'external skill')
        name = _name(_required(document, 'name', 'external skill'), 'external skill name')
        repository = _nonempty_string(
            _required(document, 'repository', 'external skill'),
            'external skill repository',
        )
        if not _REPOSITORY.fullmatch(repository):
            raise ContractError('external skill repository must be owner/name')
        ref = _nonempty_string(_required(document, 'ref', 'external skill'), 'external skill ref')
        if ref.startswith('-') or not _GIT_REF.fullmatch(ref):
            raise ContractError('external skill ref must be a safe Git argument')
        path_value = _required(document, 'path', 'external skill')
        if not isinstance(path_value, str):
            raise ContractError('external skill path must be a relative path')
        path = safe_relative(path_value, 'external skill path')
        if name in reserved:
            raise ContractError(f'external skill conflicts with shared skill: {name}')
        result.append(ExternalSkillSpec(name, repository, ref, path))
    names = [item.name for item in result]
    if len(set(names)) != len(names):
        raise ContractError('project config skills.external has duplicate names')
    return tuple(result)


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
    return ProjectConfig(
        version, platforms,
        _selected(document.get('selected_rules'), 'selected_rules', catalog, 'rule'),
        _selected(document.get('selected_skills'), 'selected_skills', catalog, 'skill'),
        _selected(document.get('selected_agents'), 'selected_agents', catalog, 'agent'),
        parse_external_skills(document.get('skills'), catalog),
    )
