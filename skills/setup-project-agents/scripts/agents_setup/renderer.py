from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .catalog import safe_field_key
from .external import ExternalSkillError, validated_snapshot_metadata
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
    McpServerSpec,
    McpTransport,
    OperatingSystem,
    Platform,
    ProjectAgentSpec,
    ProjectConfig,
)
from .project import ProjectError, confined_target
from .ownership import (
    OWNERSHIP_PATH,
    OwnershipError,
    load_ownership,
    reconcile_ownership,
    verify_ownership,
)
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


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _project_agent_source(target_root: Path, agent: ProjectAgentSpec) -> Path:
    try:
        source = confined_target(target_root, agent.source)
    except ProjectError as error:
        raise RenderError(str(error)) from error
    if not source.exists() or not source.is_file():
        raise RenderError(f'project Agent source is missing: {agent.source.as_posix()}')
    try:
        content = source.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise RenderError(
            f'project Agent source is not readable UTF-8: {agent.source.as_posix()}'
        ) from error
    if not content.strip():
        raise RenderError(f'project Agent source is empty: {agent.source.as_posix()}')
    return source


def _render_project_agents(
    files: dict[PurePosixPath, bytes],
    target_root: Path,
    config: ProjectConfig,
) -> tuple[PurePosixPath, ...]:
    preserved: list[PurePosixPath] = []
    for agent in config.agents:
        _project_agent_source(target_root, agent)
        preserved.append(agent.source)
        reference = agent.source.as_posix()
        if agent.codex is not None:
            target = PurePosixPath('.codex/agents') / f'{agent.id}.toml'
            if target in files:
                raise RenderError(
                    f'Project Agent id conflicts with Codex Plugin Agent default: '
                    f'{agent.id}'
                )
            lines = [
                f'name = {_quoted(agent.id)}',
                f'description = {_quoted(agent.description)}',
            ]
            if agent.codex.model is not None:
                lines.append(f'model = {_quoted(agent.codex.model)}')
            if agent.codex.model_reasoning_effort is not None:
                lines.append(
                    'model_reasoning_effort = '
                    f'{_quoted(agent.codex.model_reasoning_effort)}'
                )
            lines.extend((
                f'sandbox_mode = {_quoted(agent.codex.sandbox_mode)}',
                'developer_instructions = """',
                f'Follow `{reference}`.',
                'Keep this file thin and use the shared agent prompt as the source of truth.',
                '"""',
            ))
            _copy_file(
                files,
                target,
                ('\n'.join(lines) + '\n').encode(),
            )
        if agent.cursor is not None:
            lines = [
                '---',
                f'name: {_quoted(agent.id)}',
                f'description: {_quoted(agent.description)}',
            ]
            if agent.cursor.model is not None:
                lines.append(f'model: {_quoted(agent.cursor.model)}')
            lines.extend((
                f'readonly: {str(agent.cursor.readonly).lower()}',
                '---',
                '',
                f'Apply @{reference}',
            ))
            _copy_file(
                files,
                PurePosixPath('.cursor/agents') / f'{agent.id}.md',
                ('\n'.join(lines) + '\n').encode(),
            )
        if agent.copilot is not None:
            lines = [
                '---',
                f'name: {_quoted(agent.id)}',
                f'description: {_quoted(agent.description)}',
            ]
            if agent.copilot.model is not None:
                lines.append(f'model: {_quoted(agent.copilot.model)}')
            lines.extend((
                'disable-model-invocation: '
                f'{str(agent.copilot.disable_model_invocation).lower()}',
                '---',
                '',
                f'Apply @{reference}',
            ))
            _copy_file(
                files,
                PurePosixPath('.github/agents') / f'{agent.id}.agent.md',
                ('\n'.join(lines) + '\n').encode(),
            )
    return tuple(preserved)


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


def _effective_mcp_server(
    server: McpServerSpec,
    platform: Platform,
    operating_system: OperatingSystem | None,
) -> tuple[str | None, tuple[str, ...], str | None, tuple[str, ...], str | None]:
    command, args, cwd, env, url = (
        server.command, server.args, server.cwd, server.env, server.url,
    )
    for override in server.overrides:
        if override.platforms is not None and platform not in override.platforms:
            continue
        if (
            override.operating_systems is not None
            and operating_system not in override.operating_systems
        ):
            continue
        command = override.command if override.command is not None else command
        args = override.args if override.args is not None else args
        cwd = override.cwd if override.cwd is not None else cwd
        env = override.env if override.env is not None else env
        url = override.url if override.url is not None else url
    return command, args, cwd, env, url


def _render_mcp_entry(
    server: McpServerSpec,
    platform: Platform,
    operating_system: OperatingSystem | None,
) -> dict[str, object]:
    command, args, cwd, env, url = _effective_mcp_server(
        server, platform, operating_system
    )
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


def _render_project_mcp(
    target_root: Path,
    config: ProjectConfig,
    native_documents: dict[PurePosixPath, dict[str, object]],
    native_templates: dict[PurePosixPath, dict[str, object]],
    delete_paths: set[PurePosixPath],
    previous_owned_fields: frozenset[tuple[PurePosixPath, str]],
    operating_system: OperatingSystem | None,
) -> None:
    if not config.mcp_servers:
        return
    if operating_system is None and any(
        override.operating_systems is not None
        for server in config.mcp_servers
        for override in server.overrides
    ):
        if sys.platform == 'win32':
            operating_system = OperatingSystem.WINDOWS
        elif sys.platform.startswith('linux'):
            operating_system = OperatingSystem.LINUX
        else:
            raise RenderError(
                f'unsupported operating system for MCP overrides: {sys.platform}'
            )

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

    touched_paths: set[PurePosixPath] = set()
    for server in config.mcp_servers:
        for platform in server.platforms:
            path, root = _MCP_NATIVE[platform]
            key = f'{root}.{server.id}'
            desired = _render_mcp_entry(server, platform, operating_system)
            document = native_document(path)
            desired_fields = dict(_safe_leaves(desired, key))
            for owned_path, owned_key in previous_owned_fields:
                if owned_path == path and owned_key.startswith(key + '.'):
                    exists, current = _existing_dotted_field(document, owned_key)
                    if owned_key in desired_fields and (
                        not exists or current != desired_fields[owned_key]
                    ):
                        _remove_dotted_field(document, owned_key)
            for desired_key, desired_value in desired_fields.items():
                exists, current = _existing_dotted_field(document, desired_key)
                if exists and current != desired_value:
                    raise RenderError(
                        f'Project MCP entry conflicts with user configuration: '
                        f'{path.as_posix()}:{desired_key}'
                    )
                if not exists:
                    _set_dotted_field(document, desired_key, desired_value)
            template = native_templates.setdefault(path, {})
            _set_dotted_field(template, key, desired)
            touched_paths.add(path)

    for path in touched_paths:
        if not native_documents[path] and path not in native_templates:
            native_documents.pop(path)
            delete_paths.add(path)
        else:
            delete_paths.discard(path)

    return None


def render_desired_state(
    source_root: Path,
    target_root: Path,
    catalog: Catalog,
    config: ProjectConfig,
    generated_root: Path,
    external_root: Path | None = None,
    operating_system: OperatingSystem | None = None,
) -> RenderedState:
    """Render only catalog-owned project assets without mutating the target."""
    try:
        previous_ownership = load_ownership(target_root)
        verify_ownership(target_root, previous_ownership)
    except OwnershipError as error:
        raise RenderError(str(error)) from error
    files: dict[PurePosixPath, bytes] = {}
    fields: list[DesiredField] = []
    native_documents: dict[PurePosixPath, dict[str, object]] = {}
    native_templates: dict[PurePosixPath, dict[str, object]] = {}
    replace_roots: set[PurePosixPath] = set()
    delete_paths: set[PurePosixPath] = set()
    assets_by_id = {asset.id: asset for asset in catalog.assets}
    for asset in catalog.assets:
        if asset.control_plane or asset.target is None:
            continue
        source = source_root / asset.source
        if asset.kind == 'skill' and source.is_dir():
            replace_roots.add(asset.target)
    previous_rule_paths = frozenset(
        asset.path
        for asset in (previous_ownership.assets if previous_ownership else ())
        if asset.role == 'rule' and asset.path.parts[:2] == ('.agents', 'rules')
    )
    previous_skill_roots = frozenset(
        asset.path if asset.kind == 'tree' else asset.path.parent
        for asset in (previous_ownership.assets if previous_ownership else ())
        if asset.role == 'skill' and asset.path.parts[:2] == ('.agents', 'skills')
    )
    previous_owned_fields = frozenset(
        (asset.path, asset.key)
        for asset in (previous_ownership.assets if previous_ownership else ())
        if asset.kind == 'field' and asset.key is not None
    )
    sources: list[Mapping[str, object]] = []
    external_assets: dict[str, tuple[str, PurePosixPath]] = {}

    def native_document(path: PurePosixPath) -> dict[str, object]:
        if path not in native_documents:
            format_name = _format_for(path)
            assert format_name is not None
            try:
                current = confined_target(target_root, path)
            except ProjectError as error:
                raise RenderError(str(error)) from error
            native_documents[path] = _load_structured(current, format_name)
        return native_documents[path]

    try:
        project_rules = discover_project_rules(
            target_root, catalog, previous_managed=previous_rule_paths,
        )
        project_skills = discover_project_skills(
            target_root,
            catalog,
            previous_managed=previous_skill_roots
            | frozenset(
                PurePosixPath('.agents/skills') / item.name
                for item in config.external_skills
            ),
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
                existing = dict(native_document(asset.target))
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
            existing = dict(native_document(asset.target))
            for key, _ in _safe_leaves(template):
                if (asset.target, key) in previous_owned_fields:
                    _remove_dotted_field(existing, key)
            native_documents[asset.target] = _deep_merge(template, existing)
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

    project_agent_sources = _render_project_agents(files, target_root, config)

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
        try:
            sources = list(validated_snapshot_metadata(config.external_sources, external_root))
        except ExternalSkillError as error:
            raise RenderError(str(error)) from error
        for source in sources:
            for item in source['skills']:
                assert isinstance(item, Mapping)
                name = str(item['id']).rsplit('/', 1)[-1]
                external_assets[name] = (
                    str(source['id']), PurePosixPath(str(item['path'])),
                )
        for skill in config.external_skills:
            source = external_root / skill.name
            if not (source / 'SKILL.md').is_file():
                raise RenderError(f'external Skill is missing SKILL.md: {skill.name}')
            _copy_asset(files, source, PurePosixPath('.agents/skills') / skill.name)
            replace_roots.add(PurePosixPath('.agents/skills') / skill.name)
    _render_project_mcp(
        target_root,
        config,
        native_documents,
        native_templates,
        delete_paths,
        previous_owned_fields,
        operating_system,
    )

    for path, document in native_documents.items():
        if not document:
            delete_paths.add(path)
            continue
        format_name = _format_for(path)
        assert format_name is not None
        _copy_file(files, path, _dump_structured(document, format_name))
        for key, value in _safe_leaves(native_templates.get(path, {})):
            fields.append(DesiredField(path, key, value, format_name))
    desired_files = tuple(DesiredFile(path, content) for path, content in sorted(files.items(), key=lambda item: item[0].as_posix()))
    desired_fields = tuple(sorted(fields, key=lambda item: (item.path.as_posix(), item.key)))
    try:
        ownership = reconcile_ownership(
            target_root,
            desired_files,
            desired_fields,
            tuple(replace_roots),
            sources=sources,
            external_sources=external_assets,
            structured_paths=tuple(native_documents),
            previous=previous_ownership,
        )
    except OwnershipError as error:
        raise RenderError(str(error)) from error
    files = {item.path: item.content for item in ownership.files}
    for path, key in ownership.remove_fields:
        document = native_documents.get(path)
        if document is None:
            document = native_document(path)
        _remove_dotted_field(document, key)
        if document:
            format_name = _format_for(path)
            assert format_name is not None
            files[path] = _dump_structured(document, format_name)
            delete_paths.discard(path)
        else:
            files.pop(path, None)
            delete_paths.add(path)
    files[OWNERSHIP_PATH] = ownership.manifest
    desired_files = tuple(DesiredFile(path, content) for path, content in sorted(files.items()))
    delete_paths.update(ownership.delete_paths)
    delete_paths.difference_update(files)
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
                    *project_agent_sources,
                    *generated_skill_resources,
                ),
                key=lambda item: item.as_posix(),
            )
        ),
    )
