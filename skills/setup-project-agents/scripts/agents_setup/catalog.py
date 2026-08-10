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
    ExternalSourceSpec,
    ExternalSkillSpec,
    McpOverride,
    McpServerSpec,
    McpTransport,
    OperatingSystem,
    Platform,
    ProjectConfig,
)
from .external_contract import (
    ExternalContractError,
    validate_ref,
)


_SEMVER = re.compile(
    r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
    r'(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)'
    r'(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?'
    r'(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$'
)
_NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
_GITHUB_SOURCE = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
_FIELD_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_@-]*$')
_WINDOWS_RESERVED_CHARACTERS = frozenset('<>:"\\|?*')
_WINDOWS_RESERVED_NAMES = frozenset(
    {'CON', 'PRN', 'AUX', 'NUL', 'COM¹', 'COM²', 'COM³', 'LPT¹', 'LPT²', 'LPT³'}
    | {f'COM{number}' for number in range(1, 10)}
    | {f'LPT{number}' for number in range(1, 10)}
)
_ASSET_FIELDS = frozenset({'id', 'kind', 'source', 'target', 'platforms', 'mode', 'control_plane', 'metadata'})
_CATALOG_FIELDS = frozenset({'plugin', 'assets'})
_PLUGIN_FIELDS = frozenset({'id', 'version', 'repository', 'ref'})
_PROJECT_CONFIG_FIELDS = frozenset({'$schema', 'version', 'skills', 'mcp'})
_EXTERNAL_SOURCE_FIELDS = frozenset({'source', 'ref', 'include'})
_MCP_SERVER_FIELDS = frozenset({
    'id', 'platforms', 'command', 'args', 'cwd', 'env', 'url', 'overrides',
})
_MCP_OVERRIDE_FIELDS = frozenset({'when', 'set'})
_MCP_OVERRIDE_SELECTOR_FIELDS = frozenset({'platforms', 'operatingSystems'})
_MCP_OVERRIDE_VALUE_FIELDS = frozenset({'command', 'args', 'cwd', 'env', 'url'})
_ENVIRONMENT_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_MATT_BLUEPRINTS = {
    PurePosixPath('docs/agents/issue-tracker.md'): PurePosixPath(
        'skills/setup-matt-pocock-skills/issue-tracker-local.md'
    ),
    PurePosixPath('docs/agents/triage-labels.md'): PurePosixPath(
        'skills/setup-matt-pocock-skills/triage-labels.md'
    ),
    PurePosixPath('docs/agents/domain.md'): PurePosixPath(
        'skills/setup-matt-pocock-skills/domain.md'
    ),
}


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
    if value == '$schema':
        return value
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


def _string_array(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ContractError(f'{label} must be an array of non-empty strings')
    return tuple(value)


def _mcp_text(value: object, label: str) -> str:
    text = _nonempty_string(value, label)
    if any(unicodedata.category(character) == 'Cc' for character in text):
        raise ContractError(f'{label} contains control characters')
    return text


def _mcp_env(value: object, label: str) -> tuple[str, ...]:
    names = _string_array(value, label)
    if len(names) != len(set(names)):
        raise ContractError(f'{label} has duplicate values')
    if any(_ENVIRONMENT_NAME.fullmatch(name) is None for name in names):
        raise ContractError(f'{label} contains an invalid environment variable name')
    return names


def _mcp_override(
    value: object,
    *,
    label: str,
    transport: McpTransport,
    enabled_platforms: tuple[Platform, ...],
) -> McpOverride:
    document = _object(value, label)
    _fields(document, _MCP_OVERRIDE_FIELDS, label)
    selector = _object(_required(document, 'when', label), f'{label}.when')
    _fields(selector, _MCP_OVERRIDE_SELECTOR_FIELDS, f'{label}.when')
    if not selector:
        raise ContractError(f'{label}.when must select platforms or operatingSystems')
    platforms = None
    if 'platforms' in selector:
        platforms = _platforms(selector['platforms'], f'{label}.when.platforms', ())
        if not platforms:
            raise ContractError(f'{label}.when.platforms must not be empty')
        if set(platforms) - set(enabled_platforms):
            raise ContractError(
                f'{label}.when.platforms includes a platform not enabled by the server'
            )
    operating_systems = None
    if 'operatingSystems' in selector:
        operating_systems = _operating_systems(
            selector['operatingSystems'], f'{label}.when.operatingSystems'
        )

    values = _object(_required(document, 'set', label), f'{label}.set')
    _fields(values, _MCP_OVERRIDE_VALUE_FIELDS, f'{label}.set')
    if not values:
        raise ContractError(f'{label}.set must override at least one field')
    if transport is McpTransport.HTTP:
        if set(values) - {'url'}:
            raise ContractError(f'{label} HTTP override may declare only url')
    elif 'url' in values:
        raise ContractError(f'{label} stdio override cannot declare url')
    command = _mcp_text(values['command'], f'{label}.set.command') if 'command' in values else None
    args = _string_array(values['args'], f'{label}.set.args') if 'args' in values else None
    cwd = _mcp_text(values['cwd'], f'{label}.set.cwd') if 'cwd' in values else None
    env = _mcp_env(values['env'], f'{label}.set.env') if 'env' in values else None
    url = _mcp_text(values['url'], f'{label}.set.url') if 'url' in values else None
    if url is not None and not url.startswith(('https://', 'http://')):
        raise ContractError(f'{label}.set.url must be an HTTP URL')
    return McpOverride(platforms, operating_systems, command, args, cwd, env, url)


def parse_mcp_servers(value: object) -> tuple[McpServerSpec, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ContractError('project config mcp must be an array')
    raw_servers = value
    result: list[McpServerSpec] = []
    for index, raw_server in enumerate(raw_servers):
        label = f'project config mcp[{index}]'
        document = _object(raw_server, label)
        _fields(document, _MCP_SERVER_FIELDS, label)
        server_id = _name(_required(document, 'id', label), f'{label}.id')
        platforms = _platforms(document.get('platforms'), f'{label}.platforms', tuple(Platform))
        if not platforms:
            raise ContractError(f'{label}.platforms must not be empty')
        has_command = 'command' in document
        has_url = 'url' in document
        if has_command == has_url:
            raise ContractError(f'{label} requires exactly one of command or url')
        transport = McpTransport.STDIO if has_command else McpTransport.HTTP
        command = args = cwd = env = url = None
        if transport is McpTransport.STDIO:
            if 'url' in document:
                raise ContractError(f'{label} stdio server cannot declare url')
            command = _mcp_text(_required(document, 'command', label), f'{label}.command')
            args = _string_array(document.get('args', []), f'{label}.args')
            cwd = _mcp_text(document['cwd'], f'{label}.cwd') if 'cwd' in document else None
            env = _mcp_env(document.get('env', []), f'{label}.env')
        else:
            if set(document).intersection({'command', 'args', 'cwd', 'env'}):
                raise ContractError(f'{label} HTTP server cannot declare stdio fields')
            url = _mcp_text(_required(document, 'url', label), f'{label}.url')
            if not url.startswith(('https://', 'http://')):
                raise ContractError(f'{label}.url must be an HTTP URL')
        raw_overrides = document.get('overrides', [])
        if not isinstance(raw_overrides, list):
            raise ContractError(f'{label}.overrides must be an array')
        overrides = tuple(
            _mcp_override(
                raw_override,
                label=f'{label}.overrides[{override_index}]',
                transport=transport,
                enabled_platforms=platforms,
            )
            for override_index, raw_override in enumerate(raw_overrides)
        )
        result.append(McpServerSpec(
            server_id,
            transport,
            platforms,
            command=command,
            args=args or (),
            cwd=cwd,
            env=env or (),
            url=url,
            overrides=overrides,
        ))
    ids = [server.id for server in result]
    if len(ids) != len(set(ids)):
        raise ContractError('project config mcp has duplicate ids')
    return tuple(result)


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


def _operating_systems(value: object, label: str) -> tuple[OperatingSystem, ...]:
    if not isinstance(value, list):
        raise ContractError(f'{label} must be an array')
    result: list[OperatingSystem] = []
    for item in value:
        try:
            operating_system = OperatingSystem(item)
        except (TypeError, ValueError) as error:
            raise ContractError(f'{label} has an unsupported operating system') from error
        if operating_system in result:
            raise ContractError(f'{label} has duplicate operating systems')
        result.append(operating_system)
    if not result:
        raise ContractError(f'{label} must not be empty')
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
    for asset in assets:
        if asset.control_plane:
            continue
        if asset.source.parts[:1] == ('setup-assets',):
            continue
        if (
            asset.kind == 'blueprint'
            and asset.target is not None
            and _MATT_BLUEPRINTS.get(asset.target) == asset.source
        ):
            continue
        raise ContractError(
            f'catalog asset source is outside an allowed ownership root: {asset.source}'
        )
    return Catalog(
        plugin_id,
        plugin_version,
        repository,
        ref,
        assets,
    )


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


def parse_external_skills(value: object, catalog: Catalog) -> tuple[ExternalSourceSpec, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ContractError('project config skills must be an array')
    external = value
    reserved = {asset.id for asset in catalog.assets if asset.kind == 'skill'}
    result: list[ExternalSourceSpec] = []
    for index, item in enumerate(external):
        document = _object(item, f'project config skills[{index}]')
        _fields(document, _EXTERNAL_SOURCE_FIELDS, 'external source')
        source_id = _nonempty_string(
            _required(document, 'source', 'external source'), 'external source source'
        )
        if _GITHUB_SOURCE.fullmatch(source_id) is None:
            raise ContractError('external source must use owner/repository form')
        url = f'https://github.com/{source_id}'
        ref_value = document.get('ref')
        ref = None if ref_value is None else _nonempty_string(ref_value, 'external source ref')
        try:
            validate_ref(ref)
        except ExternalContractError as error:
            raise ContractError('external source ref must be a safe Git argument') from error
        source_skills: list[ExternalSkillSpec] = []
        raw_skills = document.get('include')
        if not isinstance(raw_skills, list) or not raw_skills:
            raise ContractError('external source include must be a non-empty array')
        if not all(isinstance(item, str) for item in raw_skills):
            raise ContractError('external source include must contain paths')
        if len(raw_skills) != len(set(raw_skills)):
            raise ContractError('external source include has duplicate paths')
        owner = source_id.split('/', 1)[0]
        for raw_skill in raw_skills:
            path = safe_relative(raw_skill, 'external skill path')
            name = _name(path.name, 'external skill path basename')
            if name in reserved:
                raise ContractError(f'external skill conflicts with shared skill: {name}')
            skill_id = f'{owner}/{name}'
            source_skills.append(ExternalSkillSpec(skill_id, name, path))
        result.append(ExternalSourceSpec(source_id, url, ref, tuple(source_skills)))
    source_ids = [source.id.casefold() for source in result]
    if len(source_ids) != len(set(source_ids)):
        raise ContractError('project config skills has duplicate sources')
    names = [item.name for source in result for item in source.skills]
    if len(set(names)) != len(names):
        raise ContractError('project config skills has duplicate names')
    return tuple(result)


def load_project_config(
    path: Path | None,
    *,
    catalog: Catalog,
) -> ProjectConfig:
    document: Mapping[str, object]
    if path is None or not path.exists():
        document = {}
    else:
        document = _load_json(path, 'project config')
    _fields(document, _PROJECT_CONFIG_FIELDS, 'project config')
    version = document.get('version', 1)
    if type(version) is not int or version != 1:
        raise ContractError('project config version must be 1')
    project_external_skills = parse_external_skills(document.get('skills'), catalog)
    mcp_servers = parse_mcp_servers(document.get('mcp'))
    return ProjectConfig(
        version,
        _selected(None, 'selected_rules', catalog, 'rule'),
        _selected(None, 'selected_skills', catalog, 'skill'),
        _selected(None, 'selected_agents', catalog, 'agent'),
        project_external_skills,
        mcp_servers,
    )
