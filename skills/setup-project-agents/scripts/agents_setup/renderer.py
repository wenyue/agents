from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .catalog import load_lock, safe_field_key
from .host_adapters.base import CapabilityResult, HostAdapter
from .models import Catalog, DesiredField, DesiredFile, Platform, ProjectConfig
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
    capabilities: Mapping[Platform, CapabilityResult]

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


def _set_dotted(document: dict[str, object], key: str, value: object) -> None:
    current = document
    parts = key.split('.')
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def _remove_dotted(document: dict[str, object], key: str) -> None:
    current: dict[str, object] = document
    parents: list[tuple[dict[str, object], str]] = []
    for part in key.split('.')[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            return
        parents.append((current, part))
        current = child
    current.pop(key.split('.')[-1], None)
    for parent, part in reversed(parents):
        if isinstance(parent.get(part), dict) and not parent[part]:
            del parent[part]


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


def _metadata(source_root: Path) -> Mapping[str, object]:
    try:
        value = json.loads(
            (source_root / 'skills/setup-project-agents/references/public_assets.json').read_text(
                encoding='utf-8'
            )
        )
    except (OSError, json.JSONDecodeError) as error:
        raise RenderError('cannot read public asset metadata') from error
    if not isinstance(value, dict):
        raise RenderError('public asset metadata must be an object')
    return value


def _copy_file(files: dict[PurePosixPath, bytes], path: PurePosixPath, content: bytes) -> None:
    if path in files:
        raise RenderError(f'duplicate rendered path: {path.as_posix()}')
    files[path] = content


_TRANSIENT_NAMES = frozenset({
    '__pycache__', '.DS_Store', 'Thumbs.db', '.pytest_cache', '.mypy_cache', '.ruff_cache'
})


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


def _rule_rows(metadata: Mapping[str, object], section: str) -> str:
    rules = metadata.get('rules', [])
    if not isinstance(rules, list):
        return ''
    rows = []
    for rule in rules:
        if isinstance(rule, dict) and rule.get('section') == section:
            rows.append(
                f"| {rule.get('read_when', '')} | `.agents/rules/{rule.get('file', '')}` | {rule.get('strength', '')} |"
            )
    return '\n'.join(rows)


def _render_text(template: str, values: Mapping[str, object]) -> bytes:
    for key, value in values.items():
        rendered = str(value).lower() if isinstance(value, bool) else str(value)
        template = template.replace('{{' + key + '}}', rendered)
    return template.encode()


def _agent_values(metadata: Mapping[str, object], agent_id: str, target: PurePosixPath, models: Mapping[str, object]) -> dict[str, object]:
    agents = metadata.get('agent_prompts', [])
    agent = next((item for item in agents if isinstance(item, dict) and item.get('name') == agent_id), {})
    if not isinstance(agent, dict):
        agent = {}
    selected = models.get('agents', {})
    model = selected.get(agent_id, {}) if isinstance(selected, Mapping) else {}
    codex = model.get('codex', {}) if isinstance(model, Mapping) else {}
    cursor = model.get('cursor', {}) if isinstance(model, Mapping) else {}
    github = model.get('github', {}) if isinstance(model, Mapping) else {}
    defaults = agent.get('codex', {}) if isinstance(agent.get('codex'), dict) else {}
    cursor_defaults = agent.get('cursor', {}) if isinstance(agent.get('cursor'), dict) else {}
    return {
        'agent.name': agent_id,
        'agent.description': agent.get('description', ''),
        'agent.apply_ref': target.as_posix(),
        'agent.codex_model': codex.get('model', ''),
        'agent.codex_model_reasoning_effort': codex.get('model_reasoning_effort', ''),
        'agent.codex_sandbox_mode': codex.get('sandbox_mode', defaults.get('sandbox_mode', 'workspace-write')),
        'agent.cursor_model': cursor.get('model', ''),
        'agent.cursor_readonly': cursor.get('readonly', cursor_defaults.get('readonly', False)),
        'agent.github_model': github.get('model', ''),
    }


def render_desired_state(
    source_root: Path,
    target_root: Path,
    catalog: Catalog,
    config: ProjectConfig,
    generated_root: Path,
    models: Mapping[str, object],
    adapters: Mapping[Platform, HostAdapter],
) -> RenderedState:
    """Render only catalog-owned project assets without mutating the target."""
    metadata = _metadata(source_root)
    files: dict[PurePosixPath, bytes] = {}
    fields: list[DesiredField] = []
    native_documents: dict[PurePosixPath, dict[str, object]] = {}
    native_templates: dict[PurePosixPath, dict[str, object]] = {}
    try:
        lock_path = confined_target(target_root, PurePosixPath('.agents/lock.json'))
    except ProjectError as error:
        raise RenderError(str(error)) from error
    lock = load_lock(lock_path)
    old_fields = {(item.path, item.key) for item in lock.managed_fields}

    for asset in catalog.assets:
        if asset.control_plane or asset.target is None or not set(asset.platforms).intersection(config.platforms):
            continue
        if asset.kind == 'rule' and asset.id not in config.selected_rules:
            continue
        if asset.kind == 'skill' and asset.id not in config.selected_skills:
            continue
        if asset.kind == 'agent' and asset.id not in config.selected_agents:
            continue
        if asset.id.startswith('hook-') and not config.hooks_enabled:
            continue
        if asset.kind in {'rule', 'skill', 'agent'}:
            _copy_asset(files, source_root / asset.source, asset.target)
            continue
        if asset.id.startswith('hook-'):
            _copy_file(files, asset.target, (source_root / asset.source).read_bytes())
            continue
        if asset.kind == 'template' and asset.target and _format_for(asset.target):
            format_name = _format_for(asset.target)
            assert format_name is not None
            if asset.id == 'config-codex-dart-mcp' and not any(target_root.rglob('pubspec.yaml')):
                continue
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
                    'global_rule_rows': _rule_rows(metadata, 'global'),
                    'base_rule_rows': _rule_rows(metadata, 'base'),
                    'project_rule_rows': _rule_rows(metadata, 'project'),
                })
            _copy_file(files, asset.target, content)
            continue
        if asset.kind == 'wrapper':
            template = (source_root / asset.source).read_text(encoding='utf-8')
            if 'agent' in asset.id:
                for agent_id in config.selected_agents:
                    source = next(item for item in catalog.assets if item.id == agent_id)
                    assert source.target is not None
                    path = PurePosixPath(asset.target.as_posix().replace('{agent-name}', agent_id))
                    _copy_file(files, path, _render_text(template, _agent_values(metadata, agent_id, source.target, models)))
            else:
                rule_metadata = metadata.get('rules', [])
                for rule_id in config.selected_rules:
                    source = next(item for item in catalog.assets if item.id == rule_id)
                    assert source.target is not None
                    item = next((rule for rule in rule_metadata if isinstance(rule, dict) and rule.get('file') == source.source.name), {})
                    if not isinstance(item, dict):
                        item = {}
                    name = source.source.stem
                    path = PurePosixPath(asset.target.as_posix().replace('{rule-name}', name))
                    _copy_file(files, path, _render_text(template, {
                        'rule.apply_ref': source.target.as_posix(),
                        'rule.cursor_description': item.get('cursor', {}).get('description', '') if isinstance(item.get('cursor'), dict) else '',
                        'rule.cursor_globs': json.dumps(item.get('cursor', {}).get('globs', '**')) if isinstance(item.get('cursor'), dict) else '"**"',
                        'rule.cursor_always_apply': item.get('cursor', {}).get('alwaysApply', False) if isinstance(item.get('cursor'), dict) else False,
                        'rule.github_apply_to': item.get('github', {}).get('applyTo', '**') if isinstance(item.get('github'), dict) else '**',
                    }))

    for path in sorted(
        (
            item
            for item in generated_root.rglob('*')
            if item.is_file() and not _is_transient(item)
        ),
        key=lambda item: item.as_posix(),
    ):
        relative = PurePosixPath(path.relative_to(generated_root).as_posix())
        _copy_file(files, relative, path.read_bytes())

    for platform in config.platforms:
        adapter = adapters.get(platform)
        if adapter is None:
            raise RenderError(f'missing adapter for {platform.value}')
        hook_values = adapter.hook_fields(config.hooks_enabled)
        field_path = {
            Platform.CODEX: PurePosixPath('.codex/config.toml'),
            Platform.COPILOT: PurePosixPath('.github/copilot/settings.json'),
        }.get(platform)
        if field_path is not None and field_path in native_documents:
            if config.hooks_enabled:
                for key, value in hook_values.items():
                    _set_dotted(native_documents[field_path], key, value)
            else:
                for key in ('features.hooks', 'disableAllHooks'):
                    if (field_path, key) in old_fields:
                        _remove_dotted(native_documents[field_path], key)

    for path, document in native_documents.items():
        format_name = _format_for(path)
        assert format_name is not None
        _copy_file(files, path, _dump_structured(document, format_name))
        for key, value in _safe_leaves(native_templates[path]):
            fields.append(DesiredField(path, key, value, format_name))
        for platform in config.platforms:
            adapter = adapters[platform]
            for key, value in adapter.hook_fields(config.hooks_enabled).items():
                owned_path = {
                    Platform.CODEX: PurePosixPath('.codex/config.toml'),
                    Platform.COPILOT: PurePosixPath('.github/copilot/settings.json'),
                }.get(platform)
                if owned_path == path:
                    fields.append(DesiredField(path, key, value, format_name))

    runner = models.get('runner')
    capabilities = {platform: adapters[platform].check_multi_agent(runner) for platform in config.platforms}
    desired_files = tuple(DesiredFile(path, content) for path, content in sorted(files.items(), key=lambda item: item[0].as_posix()))
    desired_fields = tuple(sorted(fields, key=lambda item: (item.path.as_posix(), item.key)))
    return RenderedState(desired_files, desired_fields, capabilities)
