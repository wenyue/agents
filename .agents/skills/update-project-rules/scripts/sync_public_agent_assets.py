#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SyncError(Exception):
    pass


@dataclass(frozen=True)
class Change:
    action: str
    path: str


@dataclass
class SyncContext:
    target_root: Path
    source_root: Path
    skill_root: Path
    check: bool
    changes: list[Change]


_TEMPLATE_PATTERN = re.compile(r'{{\s*([a-zA-Z0-9_.]+)\s*}}')


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise SyncError(f'Missing config file: {path}') from error
    except json.JSONDecodeError as error:
        raise SyncError(f'Invalid JSON in {path}: {error}') from error
    if not isinstance(data, dict):
        raise SyncError(f'{path} must contain a JSON object')
    return data


def resolve_source(target_root: Path, source_arg: str | None, public_config: dict[str, Any]) -> Path:
    raw_source = source_arg or public_config.get('source_default')
    if not isinstance(raw_source, str) or not raw_source:
        raise SyncError('public_assets.json requires a non-empty source_default')
    source = Path(raw_source)
    if not source.is_absolute():
        source = target_root / source
    source = source.resolve()
    if not source.exists():
        raise SyncError(f'Source repository does not exist: {source}')
    return source


def _require_items(config: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = config.get(key, [])
    if not isinstance(value, list):
        raise SyncError(f'{key} must be a list')
    for item in value:
        if not isinstance(item, dict):
            raise SyncError(f'{key} entries must be objects')
    return value


def _ignore_patterns(config: dict[str, Any]) -> list[str]:
    value = config.get('ignore', [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SyncError('ignore must be a list of strings')
    return value


def _is_ignored(relative: Path, ignore_patterns: list[str]) -> bool:
    path = relative.as_posix()
    return any(fnmatch.fnmatch(path, pattern) for pattern in ignore_patterns)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _record_file(context: SyncContext, action: str, path: Path) -> None:
    context.changes.append(Change(action, _relative(path, context.target_root)))


def _write_bytes(context: SyncContext, target: Path, content: bytes) -> None:
    exists = target.exists()
    if exists and target.read_bytes() == content:
        _record_file(context, 'unchanged', target)
        return
    action = 'created' if not exists else 'updated'
    if not context.check:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    _record_file(context, action, target)


def _prune_empty_dirs(
    context: SyncContext,
    target: Path,
    ignore_patterns: list[str] | None = None,
) -> None:
    if not target.exists():
        return
    directories = sorted((path for path in target.rglob('*') if path.is_dir()), reverse=True)
    for directory in directories:
        if ignore_patterns and _is_ignored(directory.relative_to(target), ignore_patterns):
            continue
        if directory.exists() and not any(directory.iterdir()):
            if not context.check:
                directory.rmdir()
            _record_file(context, 'deleted', directory)


def _delete_path(context: SyncContext, target: Path) -> None:
    if not target.exists():
        return
    if target.is_dir():
        for child in sorted(target.rglob('*'), reverse=True):
            if child.is_file() or child.is_symlink():
                if not context.check:
                    child.unlink()
                _record_file(context, 'deleted', child)
            elif child.is_dir() and not any(child.iterdir()):
                if not context.check:
                    child.rmdir()
        if target.exists() and not any(target.iterdir()):
            if not context.check:
                target.rmdir()
        return
    if not context.check:
        target.unlink()
    _record_file(context, 'deleted', target)


def _copy_file(context: SyncContext, source: Path, target: Path) -> None:
    if not source.is_file():
        raise SyncError(f'Missing public asset: {source}')
    _write_bytes(context, target, source.read_bytes())


def _lookup_template_value(data: dict[str, Any], expression: str, template_name: str) -> str:
    value: Any = data
    for part in expression.split('.'):
        if not isinstance(value, dict) or part not in value:
            raise SyncError(f'Missing template variable {expression} in {template_name}')
        value = value[part]
    if isinstance(value, (dict, list)):
        raise SyncError(f'Template variable {expression} in {template_name} is not scalar')
    return str(value)


def render_template(template: str, data: dict[str, Any], template_name: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return _lookup_template_value(data, match.group(1), template_name)

    rendered = _TEMPLATE_PATTERN.sub(replace, template)
    if not rendered.strip():
        raise SyncError(f'Template rendered empty output: {template_name}')
    return rendered


def _template_text(context: SyncContext, template_name: str) -> str:
    template_path = context.skill_root / 'templates' / template_name
    if not template_path.is_file():
        raise SyncError(f'Missing template: {template_path}')
    return template_path.read_text(encoding='utf-8')


def _render_to_target(
    context: SyncContext,
    template_name: str,
    target_pattern: str,
    data: dict[str, Any],
) -> None:
    target_relative = render_template(target_pattern, data, target_pattern)
    rendered = render_template(_template_text(context, template_name), data, template_name)
    _write_bytes(context, context.target_root / target_relative, rendered.encode('utf-8'))


def _wrapper_root(target_pattern: str) -> Path:
    static_prefix = target_pattern.split('{{', 1)[0].rstrip('/\\')
    return Path(static_prefix)


def _delete_stale_wrapper_files(
    context: SyncContext,
    target_pattern: str,
    desired_paths: set[str],
) -> None:
    root = context.target_root / _wrapper_root(target_pattern)
    if not root.exists():
        return
    existing_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob('*')
        if path.is_file()
    }
    for relative_path in sorted(existing_paths - desired_paths):
        _delete_path(context, root / relative_path)
    _prune_empty_dirs(context, root)


def _mirror_dir(
    context: SyncContext,
    source: Path,
    target: Path,
    ignore_patterns: list[str],
) -> None:
    if not source.is_dir():
        raise SyncError(f'Missing public asset directory: {source}')
    source_files = {
        path.relative_to(source)
        for path in source.rglob('*')
        if path.is_file() and not _is_ignored(path.relative_to(source), ignore_patterns)
    }
    target_files = set()
    if target.exists():
        target_files = {
            path.relative_to(target)
            for path in target.rglob('*')
            if path.is_file() and not _is_ignored(path.relative_to(target), ignore_patterns)
        }
    for relative in sorted(source_files):
        _copy_file(context, source / relative, target / relative)
    for relative in sorted(target_files - source_files):
        _delete_path(context, target / relative)
    _prune_empty_dirs(context, target, ignore_patterns)


def _yaml_list(values: list[str]) -> str:
    if not values:
        return '  []'
    return ''.join(f'  - "{value}"\n' for value in values).rstrip()


def _rule_data(rule: dict[str, Any]) -> dict[str, Any]:
    filename = rule['file']
    cursor = rule.get('cursor', {})
    claude = rule.get('claude', {})
    github = rule.get('github', {})
    return {
        'rule': {
            **rule,
            'path': f'.agents/rules/{filename}',
            'apply_ref': f'.agents/rules/{filename}',
            'name': filename.removesuffix('.md'),
            'cursor_description': cursor.get('description', ''),
            'cursor_globs': cursor.get('globs', '""'),
            'cursor_always_apply': str(bool(cursor.get('alwaysApply', False))).lower(),
            'claude_paths': _yaml_list(claude.get('paths', [])),
            'github_apply_to': github.get('applyTo', '**'),
        },
    }


def _agent_data(agent: dict[str, Any]) -> dict[str, Any]:
    name = agent['name']
    return {
        'agent': {
            **agent,
            'path': f'.agents/agents/{name}.md',
            'apply_ref': f'.agents/agents/{name}.md',
        },
    }


def _rule_row(rule: dict[str, Any]) -> str:
    return f"| {rule['read_when']} | `.agents/rules/{rule['file']}` | `{rule['strength']}` |"


def _rows_for_section(rules: list[dict[str, Any]], section: str) -> str:
    rows = [_rule_row(rule) for rule in rules if rule.get('section') == section]
    return '\n'.join(rows)


def _generate_wrappers(
    context: SyncContext,
    public_config: dict[str, Any],
    local_config: dict[str, Any],
) -> None:
    platforms = public_config.get('platforms') or {}
    rule_wrappers = _require_items(platforms, 'rule_wrappers')
    agent_wrappers = _require_items(platforms, 'agent_wrappers')
    all_rules = _require_items(public_config, 'rules') + _require_items(local_config, 'rules')
    all_agents = _require_items(public_config, 'agent_prompts') + _require_items(
        local_config,
        'agent_prompts',
    )
    desired_rule_paths_by_wrapper = {wrapper['path']: set() for wrapper in rule_wrappers}
    desired_agent_paths_by_wrapper = {wrapper['path']: set() for wrapper in agent_wrappers}
    for rule in all_rules:
        for wrapper in rule_wrappers:
            rendered_target = render_template(wrapper['path'], _rule_data(rule), wrapper['path'])
            desired_rule_paths_by_wrapper[wrapper['path']].add(
                Path(rendered_target).relative_to(_wrapper_root(wrapper['path'])).as_posix()
            )
            _render_to_target(context, wrapper['template'], wrapper['path'], _rule_data(rule))
    for agent in all_agents:
        for wrapper in agent_wrappers:
            rendered_target = render_template(wrapper['path'], _agent_data(agent), wrapper['path'])
            desired_agent_paths_by_wrapper[wrapper['path']].add(
                Path(rendered_target).relative_to(_wrapper_root(wrapper['path'])).as_posix()
            )
            _render_to_target(context, wrapper['template'], wrapper['path'], _agent_data(agent))
    for wrapper in rule_wrappers:
        _delete_stale_wrapper_files(context, wrapper['path'], desired_rule_paths_by_wrapper[wrapper['path']])
    for wrapper in agent_wrappers:
        _delete_stale_wrapper_files(
            context,
            wrapper['path'],
            desired_agent_paths_by_wrapper[wrapper['path']],
        )


def _generate_agents_entry(
    context: SyncContext,
    public_config: dict[str, Any],
    local_config: dict[str, Any],
) -> None:
    template_path = context.skill_root / 'templates' / 'AGENTS.md'
    if not template_path.is_file():
        return
    all_rules = _require_items(public_config, 'rules') + _require_items(local_config, 'rules')
    template = template_path.read_text(encoding='utf-8')
    rendered = render_template(
        template,
        {
            'global_rule_rows': _rows_for_section(all_rules, 'global'),
            'base_rule_rows': _rows_for_section(all_rules, 'base'),
            'project_rule_rows': _rows_for_section(all_rules, 'project'),
        },
        'AGENTS.md',
    )
    _write_bytes(context, context.target_root / 'AGENTS.md', rendered.encode('utf-8'))


def sync_public_assets(
    context: SyncContext,
    public_config: dict[str, Any],
    local_config: dict[str, Any],
) -> list[Change]:
    ignore_patterns = _ignore_patterns(public_config)
    for rule in _require_items(public_config, 'rules'):
        filename = rule.get('file')
        if not isinstance(filename, str) or not filename:
            raise SyncError('Each public rule requires file')
        _copy_file(
            context,
            context.source_root / '.agents' / 'rules' / filename,
            context.target_root / '.agents' / 'rules' / filename,
        )
    for skill in _require_items(public_config, 'skills'):
        name = skill.get('name')
        if not isinstance(name, str) or not name:
            raise SyncError('Each public skill requires name')
        _mirror_dir(
            context,
            context.source_root / '.agents' / 'skills' / name,
            context.target_root / '.agents' / 'skills' / name,
            ignore_patterns,
        )
    for agent in _require_items(public_config, 'agent_prompts'):
        name = agent.get('name')
        if not isinstance(name, str) or not name:
            raise SyncError('Each public agent prompt requires name')
        _copy_file(
            context,
            context.source_root / '.agents' / 'agents' / f'{name}.md',
            context.target_root / '.agents' / 'agents' / f'{name}.md',
        )
    _generate_wrappers(context, public_config, local_config)
    _generate_agents_entry(context, public_config, local_config)
    return context.changes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Sync public agent assets from wenyue/agents.')
    parser.add_argument('--source', help='Path to the public source repository.')
    parser.add_argument('--check', action='store_true', help='Report drift without writing files.')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target_root = Path.cwd()
    skill_root = Path(__file__).resolve().parents[1]
    try:
        public_config = load_json(skill_root / 'public_assets.json')
        local_config = load_json(skill_root / 'local_assets.json')
        source_root = resolve_source(target_root, args.source, public_config)
        context = SyncContext(
            target_root=target_root,
            source_root=source_root,
            skill_root=skill_root,
            check=args.check,
            changes=[],
        )
        changes = sync_public_assets(context, public_config, local_config)
    except SyncError as error:
        print(f'ERROR: {error}')
        return 2
    for change in changes:
        print(f'{change.action} {change.path}')
    if args.check and any(change.action in {'created', 'updated', 'deleted'} for change in changes):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
