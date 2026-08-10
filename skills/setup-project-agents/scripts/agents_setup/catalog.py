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
    McpReadinessCheck,
    McpServerSpec,
    McpTransport,
    Platform,
    ProjectConfig,
    RetiredFieldSpec,
)
from .external_contract import (
    ExternalContractError,
    validate_ref,
    validate_source_identity,
)


_SEMVER = re.compile(
    r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
    r'(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)'
    r'(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?'
    r'(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$'
)
_NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
_STABLE_ID = re.compile(r'^[A-Za-z0-9_.-]+/[a-z0-9][a-z0-9-]*$')
_FIELD_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_@-]*$')
_WINDOWS_RESERVED_CHARACTERS = frozenset('<>:"\\|?*')
_WINDOWS_RESERVED_NAMES = frozenset(
    {'CON', 'PRN', 'AUX', 'NUL', 'COM¹', 'COM²', 'COM³', 'LPT¹', 'LPT²', 'LPT³'}
    | {f'COM{number}' for number in range(1, 10)}
    | {f'LPT{number}' for number in range(1, 10)}
)
_ASSET_FIELDS = frozenset({'id', 'kind', 'source', 'target', 'platforms', 'mode', 'control_plane', 'metadata'})
_CATALOG_FIELDS = frozenset(
    {'plugin', 'assets', 'retired_assets', 'retired_fields', 'external_skill_sources'}
)
_PLUGIN_FIELDS = frozenset({'id', 'version', 'repository', 'ref'})
_PROJECT_CONFIG_FIELDS = frozenset(
    {'$schema', 'version', 'selected_rules', 'selected_skills', 'selected_agents', 'skills', 'mcp'}
)
_SKILLS_FIELDS = frozenset({'external_sources'})
_EXTERNAL_SOURCE_FIELDS = frozenset({'id', 'url', 'ref', 'skills'})
_EXTERNAL_SKILL_FIELDS = frozenset({'id', 'path'})
_MCP_FIELDS = frozenset({'servers'})
_MCP_SERVER_FIELDS = frozenset({
    'id', 'transport', 'platforms', 'command', 'args', 'cwd', 'env', 'url',
    'overrides', 'readiness',
})
_MCP_OVERRIDE_FIELDS = frozenset({'command', 'args', 'cwd', 'env', 'url'})
_MCP_READINESS_FIELDS = frozenset({'checks'})
_MCP_CHECK_FIELDS = {
    'command-exists': frozenset({'kind', 'command'}),
    'runtime-version': frozenset({'kind', 'runtime', 'minimum'}),
    'workspace-path': frozenset({'kind', 'path', 'executable'}),
    'environment-variable': frozenset({'kind', 'name'}),
}
_ENVIRONMENT_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_NUMERIC_VERSION = re.compile(r'^(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*)){2}$')
_RETIRED_FIELD_FIELDS = frozenset({'path', 'key'})
_STRUCTURED_SUFFIXES = frozenset({'.json', '.jsonc', '.toml'})
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
) -> McpOverride:
    document = _object(value, label)
    _fields(document, _MCP_OVERRIDE_FIELDS, label)
    if transport is McpTransport.HTTP:
        if set(document) - {'url'}:
            raise ContractError(f'{label} HTTP override may declare only url')
    elif 'url' in document:
        raise ContractError(f'{label} stdio override cannot declare url')
    command = _mcp_text(document['command'], f'{label}.command') if 'command' in document else None
    args = _string_array(document['args'], f'{label}.args') if 'args' in document else None
    cwd = _mcp_text(document['cwd'], f'{label}.cwd') if 'cwd' in document else None
    env = _mcp_env(document['env'], f'{label}.env') if 'env' in document else None
    url = _mcp_text(document['url'], f'{label}.url') if 'url' in document else None
    if url is not None and not url.startswith(('https://', 'http://')):
        raise ContractError(f'{label}.url must be an HTTP URL')
    return McpOverride(command, args, cwd, env, url)


def _mcp_readiness(value: object, label: str) -> tuple[McpReadinessCheck, ...]:
    if value is None:
        return ()
    document = _object(value, label)
    _fields(document, _MCP_READINESS_FIELDS, label)
    raw_checks = _required(document, 'checks', label)
    if not isinstance(raw_checks, list):
        raise ContractError(f'{label}.checks must be an array')
    result: list[McpReadinessCheck] = []
    for index, raw_check in enumerate(raw_checks):
        check_label = f'{label}.checks[{index}]'
        check = _object(raw_check, check_label)
        kind = check.get('kind')
        if not isinstance(kind, str) or kind not in _MCP_CHECK_FIELDS:
            raise ContractError(f'{check_label}.kind is unsupported')
        _fields(check, _MCP_CHECK_FIELDS[kind], check_label)
        if kind == 'command-exists':
            result.append(McpReadinessCheck(
                kind,
                command=_mcp_text(_required(check, 'command', check_label), f'{check_label}.command'),
            ))
        elif kind == 'runtime-version':
            minimum = _mcp_text(
                _required(check, 'minimum', check_label), f'{check_label}.minimum'
            )
            if _NUMERIC_VERSION.fullmatch(minimum) is None:
                raise ContractError(f'{check_label}.minimum must be a numeric version')
            runtime = _mcp_text(
                _required(check, 'runtime', check_label), f'{check_label}.runtime'
            )
            if runtime != 'node':
                raise ContractError(f'{check_label}.runtime is unsupported')
            result.append(McpReadinessCheck(
                kind,
                runtime=runtime,
                minimum=minimum,
            ))
        elif kind == 'workspace-path':
            executable = check.get('executable', False)
            if type(executable) is not bool:
                raise ContractError(f'{check_label}.executable must be a boolean')
            result.append(McpReadinessCheck(
                kind,
                path=safe_relative(_required(check, 'path', check_label), f'{check_label}.path'),
                executable=executable,
            ))
        else:
            name = _mcp_text(_required(check, 'name', check_label), f'{check_label}.name')
            if _ENVIRONMENT_NAME.fullmatch(name) is None:
                raise ContractError(f'{check_label}.name must be an environment variable name')
            result.append(McpReadinessCheck(kind, name=name))
    return tuple(result)


def parse_mcp_servers(value: object) -> tuple[McpServerSpec, ...]:
    if value is None:
        return ()
    root = _object(value, 'project config mcp')
    _fields(root, _MCP_FIELDS, 'project config mcp')
    raw_servers = root.get('servers', [])
    if not isinstance(raw_servers, list):
        raise ContractError('project config mcp.servers must be an array')
    result: list[McpServerSpec] = []
    for index, raw_server in enumerate(raw_servers):
        label = f'project config mcp.servers[{index}]'
        document = _object(raw_server, label)
        _fields(document, _MCP_SERVER_FIELDS, label)
        server_id = _name(_required(document, 'id', label), f'{label}.id')
        try:
            transport = McpTransport(_required(document, 'transport', label))
        except (TypeError, ValueError) as error:
            raise ContractError(f'{label}.transport is unsupported') from error
        platforms = _platforms(document.get('platforms'), f'{label}.platforms', tuple(Platform))
        if not platforms:
            raise ContractError(f'{label}.platforms must not be empty')
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
        raw_overrides = document.get('overrides', {})
        overrides_doc = _object(raw_overrides, f'{label}.overrides')
        overrides: dict[Platform, McpOverride] = {}
        for key, raw_override in overrides_doc.items():
            try:
                platform = Platform(key)
            except (TypeError, ValueError) as error:
                raise ContractError(f'{label}.overrides has an unsupported platform') from error
            if platform not in platforms:
                raise ContractError(f'{label}.overrides platform is not enabled')
            overrides[platform] = _mcp_override(
                raw_override, label=f'{label}.overrides.{platform.value}', transport=transport
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
            readiness=_mcp_readiness(document.get('readiness'), f'{label}.readiness'),
        ))
    ids = [server.id for server in result]
    if len(ids) != len(set(ids)):
        raise ContractError('project config mcp.servers has duplicate ids')
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


def parse_retired_field(value: object) -> RetiredFieldSpec:
    item = _object(value, 'retired field')
    _fields(item, _RETIRED_FIELD_FIELDS, 'retired field')
    path_value = _required(item, 'path', 'retired field')
    if not isinstance(path_value, str):
        raise ContractError('retired field path must be a relative path')
    path = safe_relative(path_value, 'retired field path')
    if path.suffix.lower() not in _STRUCTURED_SUFFIXES:
        raise ContractError('retired field path must use a structured format')
    key = safe_field_key(_required(item, 'key', 'retired field'), 'retired field key')
    return RetiredFieldSpec(path, key)


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
    retired_fields_value = document.get('retired_fields', [])
    if not isinstance(retired_fields_value, list):
        raise ContractError('catalog retired_fields must be an array')
    retired_fields = tuple(parse_retired_field(item) for item in retired_fields_value)
    retired_field_keys = {(item.path, item.key) for item in retired_fields}
    if len(retired_field_keys) != len(retired_fields):
        raise ContractError('catalog has duplicate retired fields')
    catalog = Catalog(
        plugin_id,
        plugin_version,
        repository,
        ref,
        assets,
        retired_assets=retired_assets,
        retired_fields=retired_fields,
    )
    external_sources = parse_external_skills(
        {'external_sources': document.get('external_skill_sources', [])},
        catalog,
    )
    return Catalog(
        plugin_id,
        plugin_version,
        repository,
        ref,
        assets,
        retired_assets=retired_assets,
        external_sources=external_sources,
        retired_fields=retired_fields,
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
    skills = _object(value, 'project config skills')
    _fields(skills, _SKILLS_FIELDS, 'project config skills')
    external = skills.get('external_sources', [])
    if not isinstance(external, list):
        raise ContractError('project config skills.external_sources must be an array')
    reserved = {asset.id for asset in catalog.assets if asset.kind == 'skill'}
    result: list[ExternalSourceSpec] = []
    for index, item in enumerate(external):
        document = _object(item, f'project config skills.external_sources[{index}]')
        _fields(document, _EXTERNAL_SOURCE_FIELDS, 'external source')
        source_id = _nonempty_string(_required(document, 'id', 'external source'), 'external source id')
        url = _nonempty_string(_required(document, 'url', 'external source'), 'external source url')
        try:
            validate_source_identity(source_id, url)
        except ExternalContractError as error:
            raise ContractError('external source id and GitHub url must match') from error
        ref_value = document.get('ref')
        ref = None if ref_value is None else _nonempty_string(ref_value, 'external source ref')
        try:
            validate_ref(ref)
        except ExternalContractError as error:
            raise ContractError('external source ref must be a safe Git argument') from error
        source_skills: list[ExternalSkillSpec] = []
        raw_skills = _required(document, 'skills', 'external source')
        if not isinstance(raw_skills, list) or not raw_skills:
            raise ContractError('external source skills must be a non-empty array')
        for raw_skill in raw_skills:
            skill_doc = _object(raw_skill, 'external skill')
            _fields(skill_doc, _EXTERNAL_SKILL_FIELDS, 'external skill')
            skill_id = _nonempty_string(_required(skill_doc, 'id', 'external skill'), 'external skill id')
            if not _STABLE_ID.fullmatch(skill_id):
                raise ContractError('external skill id must use owner/name form')
            path = safe_relative(_required(skill_doc, 'path', 'external skill'), 'external skill path')
            name = skill_id.rsplit('/', 1)[1]
            if path.name != name:
                raise ContractError('external skill id and path basename must match')
            if name in reserved:
                raise ContractError(f'external skill conflicts with shared skill: {name}')
            source_skills.append(ExternalSkillSpec(skill_id, name, path))
        result.append(ExternalSourceSpec(source_id, url, ref, tuple(source_skills)))
    names = [item.name for source in result for item in source.skills]
    if len(set(names)) != len(names):
        raise ContractError('project config skills.external_sources has duplicate names')
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
    managed_names = {item.name for item in catalog.external_skills}
    conflicts = sorted(
        item.name for source in project_external_skills for item in source.skills if item.name in managed_names
    )
    if conflicts:
        raise ContractError(
            'project config external skill conflicts with setup-managed skill: '
            + ', '.join(conflicts)
        )
    return ProjectConfig(
        version,
        _selected(document.get('selected_rules'), 'selected_rules', catalog, 'rule'),
        _selected(document.get('selected_skills'), 'selected_skills', catalog, 'skill'),
        _selected(document.get('selected_agents'), 'selected_agents', catalog, 'agent'),
        (*catalog.external_sources, *project_external_skills),
        mcp_servers,
    )
