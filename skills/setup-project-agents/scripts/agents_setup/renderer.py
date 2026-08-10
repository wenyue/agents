from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .catalog import safe_field_key
from .discovery import (
    DiscoveryError,
    discover_generated_skill_resources,
    discover_project_rules,
    discover_project_skills,
)
from .models import (
    Catalog,
    DesiredField,
    DesiredFile,
    McpOverride,
    McpServerSpec,
    McpTransport,
    Platform,
    ProjectConfig,
)
from .project import ProjectError, confined_target
from .structured import (
    StructuredConfigError,
    dump_document as _dump_structured,
    format_for_path as _format_for,
    parse_document,
)


class RenderError(ValueError):
    """Raised when catalog assets cannot form a deterministic desired state."""


@dataclass(frozen=True)
class RenderedState:
    files: tuple[DesiredFile, ...]
    fields: tuple[DesiredField, ...]
    delete_paths: tuple[PurePosixPath, ...] = ()
    replace_roots: tuple[PurePosixPath, ...] = ()
    preserved_paths: tuple[PurePosixPath, ...] = ()

    @property
    def files_by_path(self) -> Mapping[str, bytes]:
        return {item.path.as_posix(): item.content for item in self.files}

    @property
    def fields_by_key(self) -> Mapping[tuple[str, str], object]:
        return {(item.path.as_posix(), item.key): item.value for item in self.fields}


def _deep_merge(current: object, overlay: object) -> object:
    if isinstance(current, dict) and isinstance(overlay, dict):
        merged = dict(current)
        for key, value in overlay.items():
            merged[key] = _deep_merge(merged[key], value) if key in merged else value
        return merged
    return overlay


def _remove_template_fields(current: object, template: object) -> object:
    if not isinstance(current, dict) or not isinstance(template, dict):
        return current
    remaining = dict(current)
    for key, template_value in template.items():
        if key not in remaining:
            continue
        current_value = remaining[key]
        if isinstance(current_value, dict) and isinstance(template_value, dict):
            child = _remove_template_fields(current_value, template_value)
            if child:
                remaining[key] = child
            else:
                remaining.pop(key)
        else:
            remaining.pop(key)
    return remaining


def _safe_leaves(value: object, prefix: str = '') -> Iterable[tuple[str, object]]:
    if isinstance(value, dict):
        for key, child in value.items():
            dotted = f'{prefix}.{key}' if prefix else key
            yield from _safe_leaves(child, dotted)
    elif prefix:
        try:
            yield safe_field_key(prefix, 'template field'), value
        except ValueError as error:
            raise RenderError(f'unsafe template field: {prefix}') from error


def _load_structured(path: Path, format_name: str) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        value = parse_document(path.read_bytes(), format_name)
    except (OSError, StructuredConfigError) as error:
        raise RenderError(f'cannot parse existing native config: {path}') from error
    return value


def _copy_file(files: dict[PurePosixPath, bytes], path: PurePosixPath, content: bytes) -> None:
    if path in files:
        raise RenderError(f'duplicate rendered path: {path.as_posix()}')
    files[path] = content


_TRANSIENT_NAMES = frozenset({
    '__pycache__', '.DS_Store', 'Thumbs.db', '.pytest_cache', '.mypy_cache', '.ruff_cache'
})
_EXTERNAL_ID = re.compile(r'^[A-Za-z0-9_.-]+/[a-z0-9][a-z0-9-]*$')
_EXTERNAL_LOCK = PurePosixPath('.agents/external-skills.lock.json')
_MCP_LOCK = PurePosixPath('.agents/project-mcp.lock.json')
_MCP_NATIVE = {
    Platform.CODEX: (PurePosixPath('.codex/config.toml'), 'mcp_servers'),
    Platform.CURSOR: (PurePosixPath('.cursor/mcp.json'), 'mcpServers'),
    Platform.COPILOT: (PurePosixPath('.vscode/mcp.json'), 'servers'),
}


def _is_transient(path: Path) -> bool:
    return (
        any(part in _TRANSIENT_NAMES for part in path.parts)
        or path.suffix in {'.pyc', '.pyo'}
    )


def _existing_external_names(target_root: Path) -> frozenset[str]:
    try:
        lock = confined_target(target_root, _EXTERNAL_LOCK)
    except ProjectError as error:
        raise RenderError(str(error)) from error
    if not lock.exists():
        return frozenset()
    if lock.is_symlink() or not lock.is_file():
        raise RenderError('existing external Skill lock is unsafe')
    try:
        document = json.loads(lock.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RenderError('existing external Skill lock is invalid') from error
    if not isinstance(document, dict) or document.get('version') != 1:
        raise RenderError('existing external Skill lock is invalid')
    sources = document.get('sources')
    if not isinstance(sources, list):
        raise RenderError('existing external Skill lock is invalid')
    names: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get('skills'), list):
            raise RenderError('existing external Skill lock is invalid')
        for skill in source['skills']:
            skill_id = skill.get('id') if isinstance(skill, dict) else None
            if not isinstance(skill_id, str) or _EXTERNAL_ID.fullmatch(skill_id) is None:
                raise RenderError('existing external Skill lock is invalid')
            name = skill_id.rsplit('/', 1)[1]
            if name in names:
                raise RenderError('existing external Skill lock has duplicate destinations')
            names.add(name)
    return frozenset(names)


def _copy_asset(files: dict[PurePosixPath, bytes], source: Path, target: PurePosixPath) -> None:
    if source.is_file():
        _copy_file(files, target, source.read_bytes())
        return
    if source.is_dir():
        for child in sorted(
            path for path in source.rglob('*') if path.is_file() and not _is_transient(path)
        ):
            _copy_file(files, target / child.relative_to(source).as_posix(), child.read_bytes())
        return
    raise RenderError(f'catalog source is missing: {source}')


def _rule_rows(catalog: Catalog, config: ProjectConfig, section: str, project_rules) -> str:
    rows = []
    for asset in catalog.assets:
        metadata = asset.metadata
        if (
            asset.kind in {'rule', 'blueprint'}
            and metadata.get('section') == section
            and (asset.kind != 'rule' or asset.id in config.selected_rules)
        ):
            rows.append(
                f'| {metadata.get("read_when", "")} | `{asset.target.as_posix() if asset.target else ""}` | {metadata.get("strength", "")} |'
            )
    for rule in project_rules:
        if rule.section == section:
            rows.append(
                f'| {rule.read_when} | `{rule.path.as_posix()}` | {rule.strength} |'
            )
    return '\n'.join(rows)


def _render_text(template: str, values: Mapping[str, object]) -> bytes:
    for key, value in values.items():
        rendered = str(value).lower() if isinstance(value, bool) else str(value)
        template = template.replace('{{' + key + '}}', rendered)
    return template.encode()


def _agent_values(asset, models: Mapping[str, object]) -> dict[str, object]:
    agent_id = asset.id
    target = asset.target
    assert target is not None
    agent = asset.metadata
    selected = models.get('agents', {})
    model = selected.get(agent_id, {}) if isinstance(selected, Mapping) else {}
    codex = model.get('codex', {}) if isinstance(model, Mapping) else {}
    cursor = model.get('cursor', {}) if isinstance(model, Mapping) else {}
    github = model.get('github', {}) if isinstance(model, Mapping) else {}
    codex_defaults = agent['codex']
    cursor_defaults = agent['cursor']
    if not isinstance(codex_defaults, Mapping) or not isinstance(cursor_defaults, Mapping):
        raise RenderError(f'agent metadata is invalid: {agent_id}')
    return {
        'agent.name': agent_id,
        'agent.description': agent['description'],
        'agent.apply_ref': target.as_posix(),
        'agent.codex_model': codex.get('model', ''),
        'agent.codex_model_reasoning_effort': codex.get('model_reasoning_effort', ''),
        'agent.codex_sandbox_mode': codex.get('sandbox_mode', codex_defaults['sandbox_mode']),
        'agent.cursor_model': cursor.get('model', ''),
        'agent.cursor_readonly': cursor.get('readonly', cursor_defaults['readonly']),
        'agent.github_model': github.get('model', ''),
    }


def _known_wrapper_targets(catalog: Catalog) -> set[PurePosixPath]:
    targets: set[PurePosixPath] = set()
    for wrapper in catalog.assets:
        if wrapper.kind != 'wrapper' or wrapper.target is None:
            continue
        if 'agent' in wrapper.id:
            candidates = (
                asset.id for asset in catalog.assets if asset.kind == 'agent'
            )
            placeholder = '{agent-name}'
        else:
            candidates = (
                asset.source.stem for asset in catalog.assets if asset.kind == 'rule'
            )
            placeholder = '{rule-name}'
        for candidate in candidates:
            targets.add(
                PurePosixPath(wrapper.target.as_posix().replace(placeholder, candidate))
            )
    return targets


def _remove_dotted_field(document: dict[str, object], key: str) -> bool:
    segments = key.split('.')
    current: dict[str, object] = document
    parents: list[tuple[dict[str, object], str]] = []
    for segment in segments[:-1]:
        value = current.get(segment)
        if not isinstance(value, dict):
            return False
        parents.append((current, segment))
        current = value
    leaf = segments[-1]
    if leaf not in current:
        return False
    del current[leaf]
    for parent, segment in reversed(parents):
        child = parent.get(segment)
        if isinstance(child, dict) and not child:
            del parent[segment]
        else:
            break
    return True


def _existing_dotted_field(document: Mapping[str, object], key: str) -> tuple[bool, object | None]:
    current: object = document
    for segment in key.split('.'):
        if not isinstance(current, Mapping) or segment not in current:
            return False, None
        current = current[segment]
    return True, current


def _set_dotted_field(document: dict[str, object], key: str, value: object) -> None:
    segments = key.split('.')
    current = document
    for segment in segments[:-1]:
        child = current.get(segment)
        if child is None:
            child = {}
            current[segment] = child
        if not isinstance(child, dict):
            raise RenderError(f'MCP native parent field is not an object: {key}')
        current = child
    current[segments[-1]] = value


def _load_project_mcp_lock(
    target_root: Path,
) -> dict[str, dict[Platform, tuple[PurePosixPath, str]]]:
    try:
        path = confined_target(target_root, _MCP_LOCK)
    except ProjectError as error:
        raise RenderError(str(error)) from error
    if not path.exists():
        return {}
    if path.is_symlink() or not path.is_file():
        raise RenderError('existing Project MCP lock is unsafe')
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RenderError('existing Project MCP lock is invalid') from error
    if not isinstance(document, dict) or set(document) != {'version', 'servers'}:
        raise RenderError('existing Project MCP lock is invalid')
    if document.get('version') != 1 or not isinstance(document.get('servers'), list):
        raise RenderError('existing Project MCP lock is invalid')
    result: dict[str, dict[Platform, tuple[PurePosixPath, str]]] = {}
    for raw_server in document['servers']:
        if (
            not isinstance(raw_server, dict)
            or set(raw_server) != {'id', 'entries'}
            or not isinstance(raw_server.get('id'), str)
            or not isinstance(raw_server.get('entries'), dict)
        ):
            raise RenderError('existing Project MCP lock is invalid')
        server_id = raw_server['id']
        if server_id in result:
            raise RenderError('existing Project MCP lock has duplicate server ids')
        entries: dict[Platform, tuple[PurePosixPath, str]] = {}
        for raw_platform, raw_entry in raw_server['entries'].items():
            try:
                platform = Platform(raw_platform)
            except (TypeError, ValueError) as error:
                raise RenderError('existing Project MCP lock is invalid') from error
            expected_path, expected_root = _MCP_NATIVE[platform]
            if (
                not isinstance(raw_entry, dict)
                or set(raw_entry) != {'path', 'key'}
                or raw_entry.get('path') != expected_path.as_posix()
                or raw_entry.get('key') != f'{expected_root}.{server_id}'
            ):
                raise RenderError('existing Project MCP lock is invalid')
            entries[platform] = (expected_path, raw_entry['key'])
        result[server_id] = entries
    return result


def _effective_mcp_server(
    server: McpServerSpec,
    platform: Platform,
) -> tuple[str | None, tuple[str, ...], str | None, tuple[str, ...], str | None]:
    override = server.overrides.get(platform, McpOverride())
    return (
        override.command if override.command is not None else server.command,
        override.args if override.args is not None else server.args,
        override.cwd if override.cwd is not None else server.cwd,
        override.env if override.env is not None else server.env,
        override.url if override.url is not None else server.url,
    )


def _render_mcp_entry(server: McpServerSpec, platform: Platform) -> dict[str, object]:
    command, args, cwd, env, url = _effective_mcp_server(server, platform)
    if server.transport is McpTransport.HTTP:
        assert url is not None
        return {
            **({'type': 'http'} if platform is not Platform.CODEX else {}),
            'url': url,
        }
    assert command is not None
    entry: dict[str, object] = {
        **({'type': 'stdio'} if platform is not Platform.CODEX else {}),
        'command': command,
        'args': list(args),
    }
    if cwd is not None:
        entry['cwd'] = cwd
    if env:
        if platform is Platform.CODEX:
            entry['env_vars'] = list(env)
        else:
            entry['env'] = {name: '${env:' + name + '}' for name in env}
    return entry


def _mcp_entries_equal(current: object, desired: object, platform: Platform) -> bool:
    if current == desired:
        return True
    if platform is not Platform.CURSOR or not isinstance(current, Mapping):
        return False
    normalized = dict(current)
    if 'type' not in normalized:
        if 'command' in normalized and 'url' not in normalized:
            normalized['type'] = 'stdio'
        elif 'url' in normalized and 'command' not in normalized:
            normalized['type'] = 'http'
    return normalized == desired


def _render_project_mcp(
    target_root: Path,
    config: ProjectConfig,
    native_documents: dict[PurePosixPath, dict[str, object]],
    native_templates: dict[PurePosixPath, dict[str, object]],
    delete_paths: set[PurePosixPath],
) -> bytes | None:
    previous = _load_project_mcp_lock(target_root)

    def native_document(path: PurePosixPath) -> dict[str, object]:
        if path in native_documents:
            return native_documents[path]
        format_name = _format_for(path)
        assert format_name is not None
        try:
            target_path = confined_target(target_root, path)
        except ProjectError as error:
            raise RenderError(str(error)) from error
        document = _load_structured(target_path, format_name)
        native_documents[path] = document
        return document

    owned = {
        (platform, path, key)
        for entries in previous.values()
        for platform, (path, key) in entries.items()
    }
    touched_paths: set[PurePosixPath] = set()
    for entries in previous.values():
        for path, key in entries.values():
            document = native_document(path)
            _remove_dotted_field(document, key)
            touched_paths.add(path)

    lock_servers: list[dict[str, object]] = []
    for server in config.mcp_servers:
        lock_entries: dict[str, object] = {}
        for platform in server.platforms:
            path, root = _MCP_NATIVE[platform]
            key = f'{root}.{server.id}'
            desired = _render_mcp_entry(server, platform)
            document = native_document(path)
            exists, current = _existing_dotted_field(document, key)
            if exists and (platform, path, key) not in owned:
                if not _mcp_entries_equal(current, desired, platform):
                    raise RenderError(
                        f'Project MCP entry conflicts with user configuration: '
                        f'{path.as_posix()}:{key}'
                    )
                _remove_dotted_field(document, key)
            _set_dotted_field(document, key, desired)
            template = native_templates.setdefault(path, {})
            _set_dotted_field(template, key, desired)
            touched_paths.add(path)
            lock_entries[platform.value] = {'path': path.as_posix(), 'key': key}
        lock_servers.append({'id': server.id, 'entries': lock_entries})

    for path in touched_paths:
        if not native_documents[path] and path not in native_templates:
            native_documents.pop(path)
            delete_paths.add(path)
        else:
            delete_paths.discard(path)

    if not lock_servers:
        return None
    return (json.dumps({'version': 1, 'servers': lock_servers}, indent=2) + '\n').encode()


def render_desired_state(
    source_root: Path,
    target_root: Path,
    catalog: Catalog,
    config: ProjectConfig,
    generated_root: Path,
    models: Mapping[str, object],
    external_root: Path | None = None,
) -> RenderedState:
    """Render only catalog-owned project assets without mutating the target."""
    files: dict[PurePosixPath, bytes] = {}
    fields: list[DesiredField] = []
    native_documents: dict[PurePosixPath, dict[str, object]] = {}
    native_templates: dict[PurePosixPath, dict[str, object]] = {}
    replace_roots: set[PurePosixPath] = set()
    delete_paths: set[PurePosixPath] = set(catalog.retired_assets)
    known_file_targets = _known_wrapper_targets(catalog)
    known_file_targets.add(_EXTERNAL_LOCK)
    known_file_targets.add(_MCP_LOCK)
    assets_by_id = {asset.id: asset for asset in catalog.assets}
    for asset in catalog.assets:
        if asset.control_plane or asset.target is None:
            continue
        source = source_root / asset.source
        if asset.kind == 'skill' and source.is_dir():
            replace_roots.add(asset.target)
        elif asset.kind in {'rule', 'agent'} or (
            asset.kind == 'template' and _format_for(asset.target) is None
        ):
            known_file_targets.add(asset.target)
    existing_external_names = _existing_external_names(target_root)
    replace_roots.update(
        PurePosixPath('.agents/skills') / name for name in existing_external_names
    )
    try:
        project_rules = discover_project_rules(target_root, catalog)
        project_skills = discover_project_skills(
            target_root,
            catalog,
            external_names=frozenset(item.name for item in config.external_skills)
            | existing_external_names,
        )
        generated_skill_resources = discover_generated_skill_resources(target_root, catalog)
    except DiscoveryError as error:
        raise RenderError(str(error)) from error

    for asset in catalog.assets:
        if asset.control_plane or asset.target is None:
            continue
        asset_selected = (
            (asset.kind != 'rule' or asset.id in config.selected_rules)
            and (asset.kind != 'skill' or asset.id in config.selected_skills)
            and (asset.kind != 'agent' or asset.id in config.selected_agents)
        )
        if not asset.platforms or not asset_selected:
            if asset.kind == 'template' and _format_for(asset.target):
                format_name = _format_for(asset.target)
                assert format_name is not None
                template = _load_structured(source_root / asset.source, format_name)
                try:
                    target_path = confined_target(target_root, asset.target)
                except ProjectError as error:
                    raise RenderError(str(error)) from error
                existing = _load_structured(target_path, format_name)
                if existing:
                    remaining = _remove_template_fields(existing, template)
                    if remaining:
                        native_documents[asset.target] = remaining
                    else:
                        delete_paths.add(asset.target)
            continue
        if asset.kind in {'rule', 'skill', 'agent'}:
            _copy_asset(files, source_root / asset.source, asset.target)
            continue
        if asset.kind == 'template' and asset.target and _format_for(asset.target):
            format_name = _format_for(asset.target)
            assert format_name is not None
            template = _load_structured(source_root / asset.source, format_name)
            try:
                target_path = confined_target(target_root, asset.target)
            except ProjectError as error:
                raise RenderError(str(error)) from error
            existing = _load_structured(target_path, format_name)
            native_documents[asset.target] = _deep_merge(existing, template)
            native_templates[asset.target] = template
            continue
        if asset.kind == 'template':
            content = (source_root / asset.source).read_bytes()
            if asset.id == 'entry-agents':
                content = _render_text(content.decode(), {
                    'project_rule_rows': _rule_rows(catalog, config, 'project', project_rules),
                })
            _copy_file(files, asset.target, content)
            continue
        if asset.kind == 'wrapper':
            template = (source_root / asset.source).read_text(encoding='utf-8')
            if 'agent' in asset.id:
                for agent_id in config.selected_agents:
                    source = assets_by_id[agent_id]
                    assert source.target is not None
                    path = PurePosixPath(asset.target.as_posix().replace('{agent-name}', agent_id))
                    _copy_file(files, path, _render_text(template, _agent_values(source, models)))
            else:
                for rule_id in config.selected_rules:
                    source = assets_by_id[rule_id]
                    assert source.target is not None
                    item = source.metadata
                    cursor = item['cursor']
                    github = item['github']
                    if not isinstance(cursor, Mapping) or not isinstance(github, Mapping):
                        raise RenderError(f'rule metadata is invalid: {rule_id}')
                    name = source.source.stem
                    path = PurePosixPath(asset.target.as_posix().replace('{rule-name}', name))
                    _copy_file(files, path, _render_text(template, {
                        'rule.apply_ref': source.target.as_posix(),
                        'rule.cursor_description': cursor['description'],
                        'rule.cursor_globs': json.dumps(cursor.get('globs', '**')),
                        'rule.cursor_always_apply': cursor['alwaysApply'],
                        'rule.github_apply_to': github['applyTo'],
                    }))

    generated_targets = {
        asset.target
        for asset in catalog.assets
        if asset.kind == 'blueprint'
        and not asset.control_plane
        and asset.target is not None
    }
    for path in sorted(
        (
            item
            for item in generated_root.rglob('*')
            if item.is_file() and not _is_transient(item)
        ),
        key=lambda item: item.as_posix(),
    ):
        relative = PurePosixPath(path.relative_to(generated_root).as_posix())
        if relative not in generated_targets:
            raise RenderError(f'undeclared generated path: {relative.as_posix()}')
        files[relative] = path.read_bytes()

    if config.external_skills:
        if external_root is None or not external_root.is_dir() or external_root.is_symlink():
            raise RenderError('external Skill snapshot directory is missing or unsafe')
        expected_external = {item.name for item in config.external_skills}
        actual_external = {
            item.name for item in external_root.iterdir() if item.is_dir() and not item.is_symlink()
        }
        if actual_external != expected_external:
            raise RenderError('external Skill snapshot does not match project config')
        for skill in config.external_skills:
            source = external_root / skill.name
            if not (source / 'SKILL.md').is_file():
                raise RenderError(f'external Skill is missing SKILL.md: {skill.name}')
            _copy_asset(files, source, PurePosixPath('.agents/skills') / skill.name)
            replace_roots.add(PurePosixPath('.agents/skills') / skill.name)
        lock = external_root / 'external-skills.lock.json'
        if not lock.is_file() or lock.is_symlink():
            raise RenderError('external Skill lock is missing or unsafe')
        files[_EXTERNAL_LOCK] = lock.read_bytes()

    mcp_lock = _render_project_mcp(
        target_root,
        config,
        native_documents,
        native_templates,
        delete_paths,
    )
    if mcp_lock is not None:
        files[_MCP_LOCK] = mcp_lock

    for retired in catalog.retired_fields:
        format_name = _format_for(retired.path)
        if format_name is None:
            raise RenderError(
                f'retired field path has no structured format: {retired.path.as_posix()}'
            )
        if retired.path in native_documents:
            document = native_documents[retired.path]
        else:
            try:
                target_path = confined_target(target_root, retired.path)
            except ProjectError as error:
                raise RenderError(str(error)) from error
            document = _load_structured(target_path, format_name)
        if not _remove_dotted_field(document, retired.key):
            continue
        if document:
            native_documents[retired.path] = document
        else:
            native_documents.pop(retired.path, None)
            native_templates.pop(retired.path, None)
            delete_paths.add(retired.path)

    for path, document in native_documents.items():
        format_name = _format_for(path)
        assert format_name is not None
        _copy_file(files, path, _dump_structured(document, format_name))
        for key, value in _safe_leaves(native_templates.get(path, {})):
            fields.append(DesiredField(path, key, value, format_name))
    delete_paths.update(known_file_targets.difference(files))
    delete_paths.difference_update(files)
    desired_files = tuple(DesiredFile(path, content) for path, content in sorted(files.items(), key=lambda item: item[0].as_posix()))
    desired_fields = tuple(sorted(fields, key=lambda item: (item.path.as_posix(), item.key)))
    return RenderedState(
        desired_files,
        desired_fields,
        tuple(sorted(delete_paths, key=lambda item: item.as_posix())),
        tuple(sorted(replace_roots, key=lambda item: item.as_posix())),
        tuple(
            sorted(
                (
                    *(item.path for item in project_rules),
                    *(item.path / 'SKILL.md' for item in project_skills),
                    *generated_skill_resources,
                ),
                key=lambda item: item.as_posix(),
            )
        ),
    )
