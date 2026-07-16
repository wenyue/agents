#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
import tempfile
import tomllib
import urllib.request
import zipfile
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
_DEFAULT_SOURCE_REF = 'master'
_ASSET_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+$')
_RULE_FILENAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+\.md$')
_RETIRED_ASSET_KINDS = ('rules', 'skills', 'agents')
_CODEX_RUNTIME_FIELDS = ('model', 'model_reasoning_effort', 'sandbox_mode')
_CURSOR_RUNTIME_FIELDS = ('model', 'readonly')
_GITHUB_RUNTIME_FIELDS = ('model',)
_AGENT_WRAPPER_MODEL_FIELDS = {
    'agent_wrapper.codex.toml': (
        ('codex_model', 'model'),
        ('codex_model_reasoning_effort', 'model_reasoning_effort'),
    ),
    'agent_wrapper.cursor.md': (('cursor_model', 'model'),),
    'agent_wrapper.github.agent.md': (('github_model', 'model'),),
}
_PUBLIC_AGENT_MODEL_FIELDS = {
    'codex': ('model', 'model_reasoning_effort'),
    'cursor': ('model',),
    'github': ('model',),
}
_CONFIG_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')
_MISSING = object()


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


def _validate_codex_agent_config_references(
    config_path: Path,
    config: dict[str, Any],
) -> None:
    agents = config.get('agents') or {}
    if not isinstance(agents, dict):
        raise SyncError('Codex native config agents must be a table')
    for name, agent in agents.items():
        if not isinstance(agent, dict) or 'config_file' not in agent:
            continue
        config_file = agent['config_file']
        if not isinstance(config_file, str) or not config_file.strip():
            raise SyncError(f'Codex agent {name} config_file must be a non-empty string')
        referenced_path = config_path.parent / config_file
        if not referenced_path.is_file():
            display_path = (Path('.codex') / config_file).as_posix()
            raise SyncError(
                f'Codex agent {name} references missing config file {display_path}'
            )


def _config_parts(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value:
        raise SyncError(f'{label} must be a non-empty dotted path')
    parts = tuple(value.split('.'))
    if any(not _CONFIG_KEY_PATTERN.fullmatch(part) for part in parts):
        raise SyncError(f'{label} contains an unsupported key: {value}')
    return parts


def _get_config_value(config: dict[str, Any], parts: tuple[str, ...]) -> Any:
    current: Any = config
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _set_json_config_value(
    config: dict[str, Any],
    parts: tuple[str, ...],
    value: Any,
) -> None:
    current = config
    for part in parts[:-1]:
        child = current.get(part)
        if child is None:
            child = {}
            current[part] = child
        if not isinstance(child, dict):
            raise SyncError(f'Cannot lock {".".join(parts)} through non-object key {part}')
        current = child
    current[parts[-1]] = value


def _toml_scalar(value: Any, label: str) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return f'[{", ".join(_toml_scalar(item, label) for item in value)}]'
    raise SyncError(f'{label} uses a value that cannot be written to TOML')


def _set_toml_config_value(
    content: str,
    parts: tuple[str, ...],
    value: Any,
    label: str,
) -> str:
    lines = content.splitlines()
    section = '.'.join(parts[:-1])
    key = parts[-1]
    rendered = f'{key} = {_toml_scalar(value, label)}'
    section_start = 0
    section_end = len(lines)
    if section:
        root_end = next(
            (index for index, line in enumerate(lines) if re.match(r'^\s*\[', line)),
            len(lines),
        )
        dotted_key = '.'.join(parts)
        dotted_assignment = re.compile(rf'^\s*{re.escape(dotted_key)}\s*=')
        for index in range(root_end):
            if dotted_assignment.match(lines[index]):
                indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
                lines[index] = f'{indent}{dotted_key} = {_toml_scalar(value, label)}'
                return '\n'.join(lines) + '\n'
        header = re.compile(rf'^\s*\[{re.escape(section)}\]\s*(?:#.*)?$')
        section_index = next(
            (index for index, line in enumerate(lines) if header.match(line)),
            None,
        )
        if section_index is None:
            if lines and lines[-1].strip():
                lines.append('')
            lines.extend((f'[{section}]', rendered))
            return '\n'.join(lines) + '\n'
        section_start = section_index + 1
        section_end = next(
            (
                index
                for index in range(section_start, len(lines))
                if re.match(r'^\s*\[', lines[index])
            ),
            len(lines),
        )
    else:
        section_end = next(
            (index for index, line in enumerate(lines) if re.match(r'^\s*\[', line)),
            len(lines),
        )
    assignment = re.compile(rf'^\s*{re.escape(key)}\s*=')
    for index in range(section_start, section_end):
        if assignment.match(lines[index]):
            indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
            lines[index] = f'{indent}{rendered}'
            return '\n'.join(lines) + '\n'
    insertion = section_end
    while insertion > section_start and not lines[insertion - 1].strip():
        insertion -= 1
    lines.insert(insertion, rendered)
    return '\n'.join(lines) + '\n'


def _root_config_condition_applies(
    context: SyncContext,
    condition: Any,
    label: str,
) -> bool:
    if condition is None:
        return True
    if not isinstance(condition, dict) or set(condition) != {'path_glob_exists'}:
        raise SyncError(f'{label}.when requires only path_glob_exists')
    pattern = condition['path_glob_exists']
    if not isinstance(pattern, str) or not pattern:
        raise SyncError(f'{label}.when.path_glob_exists must be a non-empty string')
    pattern_path = Path(pattern)
    if pattern_path.is_absolute() or '..' in pattern_path.parts:
        raise SyncError(f'{label}.when.path_glob_exists must stay inside the target repository')
    if any(context.target_root.glob(pattern)):
        return True
    return any(
        change.action != 'deleted' and fnmatch.fnmatch(change.path, pattern)
        for change in context.changes
    )


def _parse_root_config(
    path: Path,
    relative_path: str,
    file_format: str,
) -> tuple[str, dict[str, Any]]:
    try:
        content = path.read_text(encoding='utf-8')
        value = json.loads(content) if file_format == 'json' else tomllib.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        raise SyncError(f'Invalid native platform config {relative_path}: {error}') from error
    if not isinstance(value, dict):
        raise SyncError(f'Native platform config {relative_path} must contain an object')
    return content, value


def _reconcile_root_configs(context: SyncContext, public_config: dict[str, Any]) -> None:
    for index, root_config in enumerate(_require_items(public_config, 'root_configs')):
        label = f'root_configs[{index}]'
        unknown_fields = sorted(
            set(root_config) - {'path', 'format', 'locked_values', 'required_objects'}
        )
        if unknown_fields:
            raise SyncError(f'{label} contains unsupported fields: {", ".join(unknown_fields)}')
        relative_path = root_config.get('path')
        if not isinstance(relative_path, str) or not relative_path:
            raise SyncError(f'{label}.path must be a non-empty string')
        relative = Path(relative_path)
        if relative.is_absolute() or '..' in relative.parts:
            raise SyncError(f'{label}.path must stay inside the target repository')
        file_format = root_config.get('format')
        if file_format not in {'json', 'toml'}:
            raise SyncError(f'{label}.format must be json or toml')
        locked_values = root_config.get('locked_values', [])
        if not isinstance(locked_values, list):
            raise SyncError(f'{label}.locked_values must be an array')
        active_locks: list[tuple[tuple[str, ...], Any, str]] = []
        for lock_index, lock in enumerate(locked_values):
            lock_label = f'{label}.locked_values[{lock_index}]'
            if not isinstance(lock, dict) or 'value' not in lock:
                raise SyncError(f'{lock_label} must contain path and value')
            unknown_lock_fields = sorted(set(lock) - {'path', 'value', 'when'})
            if unknown_lock_fields:
                raise SyncError(
                    f'{lock_label} contains unsupported fields: '
                    f'{", ".join(unknown_lock_fields)}'
                )
            parts = _config_parts(lock.get('path'), f'{lock_label}.path')
            if _root_config_condition_applies(context, lock.get('when'), lock_label):
                active_locks.append((parts, lock['value'], lock_label))

        path = context.target_root / relative
        if not path.is_file() and not active_locks:
            continue
        if path.is_file():
            content, parsed = _parse_root_config(path, relative_path, file_format)
        else:
            content = '' if file_format == 'toml' else '{}\n'
            parsed = {}

        changed = False
        for parts, value, lock_label in active_locks:
            if _get_config_value(parsed, parts) == value:
                continue
            if file_format == 'json':
                _set_json_config_value(parsed, parts, value)
                content = json.dumps(parsed, indent=2, ensure_ascii=False) + '\n'
            else:
                content = _set_toml_config_value(content, parts, value, lock_label)
                try:
                    parsed = tomllib.loads(content)
                except tomllib.TOMLDecodeError as error:
                    raise SyncError(
                        f'Failed to write locked value {lock_label}: {error}'
                    ) from error
            changed = True

        required_objects = root_config.get('required_objects', [])
        if not isinstance(required_objects, list):
            raise SyncError(f'{label}.required_objects must be an array')
        for object_index, object_path in enumerate(required_objects):
            parts = _config_parts(
                object_path,
                f'{label}.required_objects[{object_index}]',
            )
            if not isinstance(_get_config_value(parsed, parts), dict):
                raise SyncError(
                    f'Native platform config {relative_path} requires a top-level '
                    f'{object_path} object'
                )
        if relative_path == '.codex/config.toml':
            _validate_codex_agent_config_references(path, parsed)
        if changed or path.is_file():
            _write_bytes(context, path, content.encode('utf-8'))


def _source_archive_url(public_config: dict[str, Any]) -> str:
    configured_url = public_config.get('source_archive_url')
    if isinstance(configured_url, str) and configured_url:
        return configured_url
    repo = public_config.get('source_repo')
    if not isinstance(repo, str) or not repo:
        raise SyncError('public_assets.json requires source_repo or source_archive_url')
    ref = public_config.get('source_ref')
    if not isinstance(ref, str) or not ref:
        ref = _DEFAULT_SOURCE_REF
    return f'{repo.rstrip("/")}/archive/refs/heads/{ref}.zip'


def _find_archive_repo_root(extract_root: Path) -> Path:
    candidates = [path for path in extract_root.iterdir() if path.is_dir()]
    if len(candidates) == 1 and (candidates[0] / '.agents').is_dir():
        return candidates[0]
    if (extract_root / '.agents').is_dir():
        return extract_root
    for candidate in candidates:
        if (candidate / '.agents').is_dir():
            return candidate
    raise SyncError(f'Downloaded source archive does not contain a .agents directory: {extract_root}')


def _fetch_archive_source(public_config: dict[str, Any]) -> Path:
    archive_url = _source_archive_url(public_config)
    source_dir = Path(tempfile.mkdtemp(prefix='setup-project-agents-'))
    source_root = source_dir / 'source'
    archive_path = source_dir / 'source.zip'
    extract_root = source_dir / 'extract'
    try:
        urllib.request.urlretrieve(archive_url, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_root)
        extracted_source = _find_archive_repo_root(extract_root)
        shutil.move(str(extracted_source), source_root)
    except OSError as error:
        shutil.rmtree(source_dir, ignore_errors=True)
        raise SyncError(f'Failed to fetch source archive {archive_url}: {error}') from error
    except zipfile.BadZipFile as error:
        shutil.rmtree(source_dir, ignore_errors=True)
        raise SyncError(f'Source archive is not a valid zip file: {archive_url}') from error
    if not (source_root / '.agents').is_dir():
        shutil.rmtree(source_dir, ignore_errors=True)
        raise SyncError(f'Downloaded source archive is missing .agents: {archive_url}')
    return source_root


def resolve_source(public_config: dict[str, Any]) -> Path:
    return _fetch_archive_source(public_config)


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


def _mirror_delete_enabled(config: dict[str, Any]) -> bool:
    value = config.get('mirror_delete', True)
    if not isinstance(value, bool):
        raise SyncError('mirror_delete must be a boolean')
    return value


def _retired_assets(config: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    value = config.get('retired_assets', {})
    if not isinstance(value, dict):
        raise SyncError('retired_assets must be an object')
    unknown_kinds = sorted(set(value) - set(_RETIRED_ASSET_KINDS))
    if unknown_kinds:
        raise SyncError(f"retired_assets contains unsupported kinds: {', '.join(unknown_kinds)}")
    retired: dict[str, tuple[str, ...]] = {}
    for kind in _RETIRED_ASSET_KINDS:
        names = value.get(kind, [])
        if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            raise SyncError(f'retired_assets.{kind} must be a list of strings')
        if len(names) != len(set(names)):
            raise SyncError(f'retired_assets.{kind} must not contain duplicate names')
        pattern = _RULE_FILENAME_PATTERN if kind == 'rules' else _ASSET_NAME_PATTERN
        for name in names:
            if (
                not name
                or name in {'.', '..'}
                or Path(name).name != name
                or not pattern.fullmatch(name)
            ):
                raise SyncError(f'Unsafe retired asset name in retired_assets.{kind}: {name!r}')
        retired[kind] = tuple(names)

    active = {
        'rules': {
            rule.get('file')
            for rule in _require_items(config, 'rules')
            if isinstance(rule.get('file'), str)
        },
        'skills': {
            skill.get('name')
            for key in ('skills', 'project_skill_generators')
            for skill in _require_items(config, key)
            if isinstance(skill.get('name'), str)
        },
        'agents': {
            agent.get('name')
            for agent in _require_items(config, 'agent_prompts')
            if isinstance(agent.get('name'), str)
        },
    }
    for kind in _RETIRED_ASSET_KINDS:
        overlap = sorted(active[kind].intersection(retired[kind]))
        if overlap:
            raise SyncError(
                f"Assets cannot be active and retired in {kind}: {', '.join(overlap)}"
            )
    return retired


def _validate_public_agent_model_ownership(config: dict[str, Any]) -> None:
    for agent in _require_items(config, 'agent_prompts'):
        name = agent.get('name')
        if not isinstance(name, str) or not name:
            raise SyncError('Each public agent prompt requires name')
        for platform, model_fields in _PUBLIC_AGENT_MODEL_FIELDS.items():
            platform_config = agent.get(platform) or {}
            if not isinstance(platform_config, dict):
                raise SyncError(f'Agent {platform} config for {name} must be an object')
            forbidden = sorted(set(platform_config).intersection(model_fields))
            if forbidden:
                raise SyncError(
                    f"Public agent {name} must not define target-owned {platform} fields: "
                    f"{', '.join(forbidden)}"
                )


def _codex_agent_runtime_overrides(config: dict[str, Any]) -> dict[str, dict[str, str]]:
    return _platform_runtime_overrides(
        config,
        'codex_agent_runtime_overrides',
        _CODEX_RUNTIME_FIELDS,
    )


def _cursor_agent_runtime_overrides(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _platform_runtime_overrides(
        config,
        'cursor_agent_runtime_overrides',
        _CURSOR_RUNTIME_FIELDS,
        boolean_fields={'readonly'},
    )


def _github_agent_runtime_overrides(config: dict[str, Any]) -> dict[str, dict[str, str]]:
    return _platform_runtime_overrides(
        config,
        'github_agent_runtime_overrides',
        _GITHUB_RUNTIME_FIELDS,
    )


def _platform_runtime_overrides(
    config: dict[str, Any],
    config_key: str,
    supported_fields: tuple[str, ...],
    *,
    boolean_fields: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    value = config.get(config_key, {})
    if not isinstance(value, dict):
        raise SyncError(f'{config_key} must be an object')
    boolean_fields = boolean_fields or set()
    overrides: dict[str, dict[str, Any]] = {}
    for name, fields in value.items():
        if not isinstance(name, str) or not _ASSET_NAME_PATTERN.fullmatch(name):
            raise SyncError(f'Invalid {config_key} name: {name!r}')
        if not isinstance(fields, dict):
            raise SyncError(f'{config_key} for {name} must be an object')
        unknown_fields = sorted(set(fields) - set(supported_fields))
        if unknown_fields:
            raise SyncError(
                f"{config_key} for {name} contains unsupported fields: "
                f"{', '.join(unknown_fields)}"
            )
        normalized: dict[str, Any] = {}
        for field, field_value in fields.items():
            if field in boolean_fields:
                if not isinstance(field_value, bool):
                    raise SyncError(f'{config_key} {name}.{field} must be a boolean')
                normalized[field] = field_value
                continue
            if not isinstance(field_value, str) or not field_value.strip():
                raise SyncError(f'{config_key} {name}.{field} must be a non-empty string')
            normalized[field] = field_value.strip()
        if normalized:
            overrides[name] = normalized
    return overrides


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
    relative_target = _relative(target, context.target_root)
    if any(
        change.action == 'deleted' and change.path == relative_target
        for change in context.changes
    ):
        return
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


def _scalar_value(value: Any, default: str = '') -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list)):
        return default
    text = str(value)
    return text if text else default


def _optional_config_string(config: dict[str, Any], key: str, label: str) -> str:
    if key not in config:
        return ''
    value = config[key]
    if not isinstance(value, str) or not value.strip():
        raise SyncError(f'{label}.{key} must be a non-empty string when present')
    return value.strip()


def render_template(template: str, data: dict[str, Any], template_name: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return _lookup_template_value(data, match.group(1), template_name)

    rendered = _TEMPLATE_PATTERN.sub(replace, template)
    if not rendered.strip():
        raise SyncError(f'Template rendered empty output: {template_name}')
    return rendered


def _template_text(context: SyncContext, template_name: str) -> str:
    template_path = context.skill_root / 'assets' / 'templates' / template_name
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
    mirror_delete: bool,
) -> None:
    if not mirror_delete:
        return
    root = context.target_root / _wrapper_root(target_pattern)
    if not root.exists():
        return
    existing_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob('*')
        if path.is_file()
    }
    for relative_path in sorted(existing_paths - desired_paths):
        stale_path = root / relative_path
        if _is_generated_thin_wrapper(stale_path):
            _delete_path(context, stale_path)
    _prune_empty_dirs(context, root)


def _mirror_dir(
    context: SyncContext,
    source: Path,
    target: Path,
    ignore_patterns: list[str],
    mirror_delete: bool,
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
    if mirror_delete:
        for relative in sorted(target_files - source_files):
            _delete_path(context, target / relative)
        _prune_empty_dirs(context, target, ignore_patterns)


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return text.strip()
    for index, line in enumerate(lines[1:], start=1):
        if line == '---':
            return '\n'.join(lines[index + 1 :]).strip()
    return text.strip()


def _is_generated_thin_wrapper(path: Path) -> bool:
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return False
    body = _strip_frontmatter(text)
    if re.fullmatch(r'Apply @\.agents/(rules|agents)/[A-Za-z0-9_.-]+\.md', body):
        return True
    if (
        'Keep this file thin and use the shared agent prompt as the source of truth.' in text
        and re.search(r'Follow `\.agents/agents/[A-Za-z0-9_.-]+\.md`\.', text)
    ):
        return True
    return False


def _rule_data(rule: dict[str, Any]) -> dict[str, Any]:
    filename = rule['file']
    cursor = rule.get('cursor', {})
    github = rule.get('github', {})
    return {
        'rule': {
            **rule,
            'path': f'.agents/rules/{filename}',
            'apply_ref': f'.agents/rules/{filename}',
            'name': filename.removesuffix('.md'),
            'cursor_description': _scalar_value(cursor.get('description'), ''),
            'cursor_globs': _scalar_value(cursor.get('globs'), '""'),
            'cursor_always_apply': str(bool(cursor.get('alwaysApply', False))).lower(),
            'github_apply_to': _scalar_value(github.get('applyTo'), '**'),
        },
    }


def _agent_data(agent: dict[str, Any]) -> dict[str, Any]:
    name = agent['name']
    codex = agent.get('codex') or {}
    cursor = agent.get('cursor') or {}
    github = agent.get('github') or {}
    if not isinstance(codex, dict):
        raise SyncError(f'Agent codex config for {name} must be an object')
    if not isinstance(cursor, dict):
        raise SyncError(f'Agent cursor config for {name} must be an object')
    if not isinstance(github, dict):
        raise SyncError(f'Agent github config for {name} must be an object')
    cursor_readonly = cursor.get('readonly', False)
    if not isinstance(cursor_readonly, bool):
        raise SyncError(f'Agent cursor config {name}.readonly must be a boolean')
    codex_model = _optional_config_string(codex, 'model', f'Agent codex config {name}')
    codex_model_reasoning_effort = _optional_config_string(
        codex,
        'model_reasoning_effort',
        f'Agent codex config {name}',
    )
    cursor_model = _optional_config_string(cursor, 'model', f'Agent cursor config {name}')
    github_model = _optional_config_string(github, 'model', f'Agent github config {name}')
    return {
        'agent': {
            **agent,
            'description': _scalar_value(
                agent.get('description'),
                f'Project-local agent: {name}',
            ),
            'cursor_model': cursor_model,
            'cursor_readonly': str(cursor_readonly).lower(),
            'github_model': github_model,
            'codex_model': codex_model,
            'codex_model_reasoning_effort': codex_model_reasoning_effort,
            'codex_sandbox_mode': _scalar_value(
                codex.get('sandbox_mode'),
                'workspace-write',
            ),
            'path': f'.agents/agents/{name}.md',
            'apply_ref': f'.agents/agents/{name}.md',
        },
    }


def _agent_with_runtime_overrides(
    agent: dict[str, Any],
    codex_override: dict[str, str] | None,
    cursor_override: dict[str, Any] | None,
    github_override: dict[str, str] | None,
) -> dict[str, Any]:
    effective = {**agent}
    for platform, override in (
        ('codex', codex_override),
        ('cursor', cursor_override),
        ('github', github_override),
    ):
        if not override:
            continue
        platform_config = agent.get(platform) or {}
        if not isinstance(platform_config, dict):
            raise SyncError(
                f"Agent {platform} config for {agent.get('name', '')} must be an object"
            )
        effective[platform] = {**platform_config, **override}
    return effective


def _agent_wrapper_pattern(
    public_config: dict[str, Any],
    template_name: str,
) -> str | None:
    platforms = public_config.get('platforms') or {}
    if not isinstance(platforms, dict):
        raise SyncError('platforms must be an object')
    for wrapper in _require_items(platforms, 'agent_wrappers'):
        if wrapper.get('template') == template_name:
            path = wrapper.get('path')
            if not isinstance(path, str) or not path:
                raise SyncError(f'{template_name} requires path')
            return path
    return None


def _discover_codex_agent_runtime_overrides(
    target_root: Path,
    public_config: dict[str, Any],
    agents: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    target_pattern = _agent_wrapper_pattern(public_config, 'agent_wrapper.codex.toml')
    if not target_pattern:
        return {}
    overrides: dict[str, dict[str, str]] = {}
    for agent in agents:
        name = agent.get('name')
        if not isinstance(name, str) or not name:
            raise SyncError('Each agent prompt requires name')
        relative_target = render_template(target_pattern, _agent_data(agent), target_pattern)
        wrapper_path = target_root / relative_target
        if not wrapper_path.is_file():
            continue
        try:
            wrapper = tomllib.loads(wrapper_path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise SyncError(f'Invalid Codex agent wrapper {wrapper_path}: {error}') from error
        runtime: dict[str, str] = {}
        for field in _CODEX_RUNTIME_FIELDS:
            if field not in wrapper:
                continue
            value = wrapper[field]
            if not isinstance(value, str) or not value.strip():
                raise SyncError(f'Codex agent wrapper field {name}.{field} must be a non-empty string')
            runtime[field] = value.strip()
        if runtime:
            overrides[name] = runtime
    return overrides


def _discover_cursor_agent_runtime_overrides(
    target_root: Path,
    public_config: dict[str, Any],
    agents: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    target_pattern = _agent_wrapper_pattern(public_config, 'agent_wrapper.cursor.md')
    if not target_pattern:
        return {}
    overrides: dict[str, dict[str, Any]] = {}
    for agent in agents:
        name = agent.get('name')
        if not isinstance(name, str) or not name:
            raise SyncError('Each agent prompt requires name')
        relative_target = render_template(target_pattern, _agent_data(agent), target_pattern)
        wrapper_path = target_root / relative_target
        frontmatter = _read_frontmatter(wrapper_path)
        runtime: dict[str, Any] = {}
        if 'model' in frontmatter:
            model = frontmatter['model']
            if not isinstance(model, str) or not model.strip():
                raise SyncError(f'Cursor agent wrapper field {name}.model must be a non-empty string')
            runtime['model'] = model.strip()
        if 'readonly' in frontmatter:
            readonly = frontmatter['readonly']
            if not isinstance(readonly, bool):
                raise SyncError(f'Cursor agent wrapper field {name}.readonly must be a boolean')
            runtime['readonly'] = readonly
        if runtime:
            overrides[name] = runtime
    return overrides


def _discover_github_agent_runtime_overrides(
    target_root: Path,
    public_config: dict[str, Any],
    agents: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    target_pattern = _agent_wrapper_pattern(public_config, 'agent_wrapper.github.agent.md')
    if not target_pattern:
        return {}
    overrides: dict[str, dict[str, str]] = {}
    for agent in agents:
        name = agent.get('name')
        if not isinstance(name, str) or not name:
            raise SyncError('Each agent prompt requires name')
        relative_target = render_template(target_pattern, _agent_data(agent), target_pattern)
        frontmatter = _read_frontmatter(target_root / relative_target)
        if 'model' not in frontmatter:
            continue
        model = frontmatter['model']
        if not isinstance(model, str) or not model.strip():
            raise SyncError(f'GitHub agent wrapper field {name}.model must be a non-empty string')
        overrides[name] = {'model': model.strip()}
    return overrides


def _read_strength(path: Path) -> str:
    if not path.is_file():
        return 'Default'
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('Strength:'):
            return line.split(':', 1)[1].strip().strip('`') or 'Default'
    return 'Default'


def _read_frontmatter(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines or lines[0] != '---':
        return {}
    values: dict[str, Any] = {}
    current_key = ''
    for line in lines[1:]:
        if line == '---':
            break
        if line.startswith('  - ') and current_key:
            current_value = values.setdefault(current_key, [])
            if not isinstance(current_value, list):
                current_value = []
                values[current_key] = current_value
            current_value.append(line.removeprefix('  - ').strip().strip('"'))
            continue
        if ':' in line and not line.startswith(' '):
            key, value = line.split(':', 1)
            current_key = key.strip()
            raw = value.strip()
            if raw == '':
                values[current_key] = ''
            elif raw in {'true', 'false'}:
                values[current_key] = raw == 'true'
            else:
                values[current_key] = raw.strip('"')
    return values


def _read_frontmatter_value(path: Path, key: str) -> str:
    return _scalar_value(_read_frontmatter(path).get(key), '')


def _public_skill_source(context: SyncContext, name: str) -> Path:
    source = context.source_root / '.agents' / 'skills' / name
    if source.is_dir():
        return source
    if context.skill_root.name == name and context.skill_root.is_dir():
        return context.skill_root
    return source


def _delete_retired_assets(
    context: SyncContext,
    public_config: dict[str, Any],
    retired: dict[str, tuple[str, ...]],
    mirror_delete: bool,
) -> None:
    if not mirror_delete:
        return
    platforms = public_config.get('platforms') or {}
    if not isinstance(platforms, dict):
        raise SyncError('platforms must be an object')
    rule_wrappers = _require_items(platforms, 'rule_wrappers')
    agent_wrappers = _require_items(platforms, 'agent_wrappers')
    for filename in retired['rules']:
        rule_data = _rule_data({'file': filename})
        _delete_path(context, context.target_root / '.agents' / 'rules' / filename)
        for wrapper in rule_wrappers:
            target_pattern = wrapper.get('path')
            if not isinstance(target_pattern, str) or not target_pattern:
                raise SyncError('Each rule wrapper requires path')
            relative_target = render_template(target_pattern, rule_data, target_pattern)
            _delete_path(context, context.target_root / relative_target)
    for name in retired['skills']:
        _delete_path(context, context.target_root / '.agents' / 'skills' / name)
    for name in retired['agents']:
        agent_data = _agent_data({'name': name})
        _delete_path(context, context.target_root / '.agents' / 'agents' / f'{name}.md')
        for wrapper in agent_wrappers:
            target_pattern = wrapper.get('path')
            if not isinstance(target_pattern, str) or not target_pattern:
                raise SyncError('Each agent wrapper requires path')
            relative_target = render_template(target_pattern, agent_data, target_pattern)
            _delete_path(context, context.target_root / relative_target)


def _referenced_skill_path(target_root: Path, agent_path: Path) -> Path | None:
    body = _strip_frontmatter(agent_path.read_text(encoding='utf-8'))
    match = re.fullmatch(r'Apply @(?P<path>\.agents/skills/[A-Za-z0-9_.-]+/SKILL\.md)', body)
    if not match:
        return None
    return target_root / Path(match.group('path'))


def _local_agent_description(target_root: Path, agent_path: Path, name: str) -> str:
    description = _read_frontmatter_value(agent_path, 'description')
    if description:
        return description
    skill_path = _referenced_skill_path(target_root, agent_path)
    if skill_path:
        description = _read_frontmatter_value(skill_path, 'description')
        if description:
            return description
    return f'Project-local agent: {name}'


def _read_agents_rule_rows(target_root: Path) -> dict[str, dict[str, str]]:
    agents_path = target_root / 'AGENTS.md'
    if not agents_path.is_file():
        return {}
    rows: dict[str, dict[str, str]] = {}
    pattern = re.compile(
        r'^\|\s*(?P<read_when>.*?)\s*\|\s*`\.agents/rules/(?P<file>[^`]+)`\s*\|\s*`(?P<strength>[^`]+)`\s*\|$'
    )
    for line in agents_path.read_text(encoding='utf-8').splitlines():
        match = pattern.match(line)
        if match:
            rows[match.group('file')] = {
                'read_when': match.group('read_when'),
                'strength': match.group('strength'),
            }
    return rows


def _default_project_read_when(filename: str) -> str:
    defaults = {
        '20-project-tools.md': 'Project tooling, MCP, runtime, or verification',
        '21-project-rules.md': 'Project APIs, generated files, lint, or domain conventions',
        '22-project-structure.md': 'Making structure, module, or dependency-boundary decisions',
    }
    return defaults.get(filename, 'Project-local rule applies')


def _default_project_cursor_description(filename: str) -> str:
    name = filename.removesuffix('.md')
    return f'[project] {name}'


def _local_rule_metadata(target_root: Path, filename: str, agents_rows: dict[str, dict[str, str]]) -> dict[str, Any]:
    name = filename.removesuffix('.md')
    cursor_frontmatter = _read_frontmatter(target_root / '.cursor' / 'rules' / f'{name}.mdc')
    github_frontmatter = _read_frontmatter(
        target_root / '.github' / 'instructions' / f'{name}.instructions.md'
    )
    agents_row = agents_rows.get(filename, {})
    return {
        'read_when': agents_row.get('read_when') or _default_project_read_when(filename),
        'strength': agents_row.get('strength') or _read_strength(target_root / '.agents' / 'rules' / filename),
        'cursor': {
            'description': _scalar_value(
                cursor_frontmatter.get('description'),
                _default_project_cursor_description(filename),
            ),
            'globs': _scalar_value(cursor_frontmatter.get('globs'), '""'),
            'alwaysApply': cursor_frontmatter.get('alwaysApply', True),
        },
        'github': {'applyTo': _scalar_value(github_frontmatter.get('applyTo'), '**')},
    }


def discover_local_assets(target_root: Path, public_config: dict[str, Any]) -> dict[str, Any]:
    retired = _retired_assets(public_config)
    public_rule_files = {
        rule['file'] for rule in _require_items(public_config, 'rules')
    }.union(retired['rules'])
    public_agent_names = {
        agent['name'] for agent in _require_items(public_config, 'agent_prompts')
    }.union(retired['agents'])
    rules = []
    rules_root = target_root / '.agents' / 'rules'
    agents_rows = _read_agents_rule_rows(target_root)
    if rules_root.exists():
        for rule_path in sorted(rules_root.glob('*.md')):
            if rule_path.name in public_rule_files:
                continue
            metadata = _local_rule_metadata(target_root, rule_path.name, agents_rows)
            rules.append(
                {
                    'file': rule_path.name,
                    'read_when': metadata['read_when'],
                    'strength': metadata['strength'],
                    'section': 'project',
                    'cursor': metadata['cursor'],
                    'github': metadata['github'],
                }
            )
    agent_prompts = []
    agents_root = target_root / '.agents' / 'agents'
    if agents_root.exists():
        for agent_path in sorted(agents_root.glob('*.md')):
            name = agent_path.stem
            if name in public_agent_names:
                continue
            description = _local_agent_description(target_root, agent_path, name)
            model = _read_frontmatter_value(agent_path, 'model') or 'sonnet'
            agent_prompts.append({'name': name, 'description': description, 'model': model})
    all_agents = _require_items(public_config, 'agent_prompts') + agent_prompts
    return {
        'rules': rules,
        'agent_prompts': agent_prompts,
        'codex_agent_runtime_overrides': _discover_codex_agent_runtime_overrides(
            target_root,
            public_config,
            all_agents,
        ),
        'cursor_agent_runtime_overrides': _discover_cursor_agent_runtime_overrides(
            target_root,
            public_config,
            all_agents,
        ),
        'github_agent_runtime_overrides': _discover_github_agent_runtime_overrides(
            target_root,
            public_config,
            all_agents,
        ),
    }


def _exclude_retired_local_assets(
    local_config: dict[str, Any],
    retired: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    retired_rules = set(retired['rules'])
    retired_agents = set(retired['agents'])
    return {
        'rules': [
            rule
            for rule in _require_items(local_config, 'rules')
            if rule.get('file') not in retired_rules
        ],
        'agent_prompts': [
            agent
            for agent in _require_items(local_config, 'agent_prompts')
            if agent.get('name') not in retired_agents
        ],
        'codex_agent_runtime_overrides': {
            name: fields
            for name, fields in _codex_agent_runtime_overrides(local_config).items()
            if name not in retired_agents
        },
        'cursor_agent_runtime_overrides': {
            name: fields
            for name, fields in _cursor_agent_runtime_overrides(local_config).items()
            if name not in retired_agents
        },
        'github_agent_runtime_overrides': {
            name: fields
            for name, fields in _github_agent_runtime_overrides(local_config).items()
            if name not in retired_agents
        },
    }


def _merge_local_assets(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    merged_rules = {rule['file']: rule for rule in _require_items(primary, 'rules')}
    for rule in _require_items(secondary, 'rules'):
        merged_rules.setdefault(rule['file'], rule)
    merged_agents = {agent['name']: agent for agent in _require_items(primary, 'agent_prompts')}
    for agent in _require_items(secondary, 'agent_prompts'):
        existing = merged_agents.get(agent['name'])
        if not existing:
            merged_agents[agent['name']] = agent
            continue
        existing_description = _scalar_value(existing.get('description'), '')
        discovered_description = _scalar_value(agent.get('description'), '')
        if (
            discovered_description
            and (
                not existing_description
                or existing_description == f"Project-local agent: {agent['name']}"
            )
        ):
            merged_agents[agent['name']] = {**existing, 'description': discovered_description}
    runtime_overrides = _codex_agent_runtime_overrides(secondary)
    runtime_overrides.update(_codex_agent_runtime_overrides(primary))
    cursor_runtime_overrides = _cursor_agent_runtime_overrides(secondary)
    cursor_runtime_overrides.update(_cursor_agent_runtime_overrides(primary))
    github_runtime_overrides = _github_agent_runtime_overrides(secondary)
    github_runtime_overrides.update(_github_agent_runtime_overrides(primary))
    return {
        'rules': list(merged_rules.values()),
        'agent_prompts': list(merged_agents.values()),
        'codex_agent_runtime_overrides': runtime_overrides,
        'cursor_agent_runtime_overrides': cursor_runtime_overrides,
        'github_agent_runtime_overrides': github_runtime_overrides,
    }


def _rule_row(rule: dict[str, Any]) -> str:
    return f"| {rule['read_when']} | `.agents/rules/{rule['file']}` | `{rule['strength']}` |"


def _rows_for_section(rules: list[dict[str, Any]], section: str) -> str:
    rows = [_rule_row(rule) for rule in rules if rule.get('section') == section]
    return '\n'.join(rows)


def _missing_agent_wrapper_model_fields(
    wrapper: dict[str, Any],
    agent_data: dict[str, Any],
) -> list[str]:
    requirements = _AGENT_WRAPPER_MODEL_FIELDS.get(wrapper.get('template'), ())
    values = agent_data['agent']
    return [display_name for data_key, display_name in requirements if not values[data_key]]


def _generate_wrappers(
    context: SyncContext,
    public_config: dict[str, Any],
    local_config: dict[str, Any],
    mirror_delete: bool,
    require_agent_runtime: bool,
) -> None:
    platforms = public_config.get('platforms') or {}
    rule_wrappers = _require_items(platforms, 'rule_wrappers')
    agent_wrappers = _require_items(platforms, 'agent_wrappers')
    all_rules = _require_items(public_config, 'rules') + _require_items(local_config, 'rules')
    all_agents = _require_items(public_config, 'agent_prompts') + _require_items(
        local_config,
        'agent_prompts',
    )
    runtime_overrides = _codex_agent_runtime_overrides(local_config)
    cursor_runtime_overrides = _cursor_agent_runtime_overrides(local_config)
    github_runtime_overrides = _github_agent_runtime_overrides(local_config)
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
        effective_agent = _agent_with_runtime_overrides(
            agent,
            runtime_overrides.get(agent['name']),
            cursor_runtime_overrides.get(agent['name']),
            github_runtime_overrides.get(agent['name']),
        )
        for wrapper in agent_wrappers:
            agent_data = _agent_data(effective_agent)
            rendered_target = render_template(
                wrapper['path'],
                agent_data,
                wrapper['path'],
            )
            relative_wrapper_path = Path(rendered_target).relative_to(
                _wrapper_root(wrapper['path'])
            ).as_posix()
            desired_agent_paths_by_wrapper[wrapper['path']].add(relative_wrapper_path)
            missing_fields = _missing_agent_wrapper_model_fields(wrapper, agent_data)
            if missing_fields:
                if require_agent_runtime:
                    raise SyncError(
                        f"Agent wrapper {rendered_target} requires reviewed fields: "
                        f"{', '.join(missing_fields)}"
                    )
                continue
            _render_to_target(
                context,
                wrapper['template'],
                wrapper['path'],
                agent_data,
            )
    for wrapper in rule_wrappers:
        _delete_stale_wrapper_files(
            context,
            wrapper['path'],
            desired_rule_paths_by_wrapper[wrapper['path']],
            mirror_delete,
        )
    for wrapper in agent_wrappers:
        _delete_stale_wrapper_files(
            context,
            wrapper['path'],
            desired_agent_paths_by_wrapper[wrapper['path']],
            mirror_delete,
        )


def _generate_agents_entry(
    context: SyncContext,
    public_config: dict[str, Any],
    local_config: dict[str, Any],
) -> None:
    template_path = context.skill_root / 'assets' / 'templates' / 'AGENTS.md'
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
    *,
    require_agent_runtime: bool = False,
) -> list[Change]:
    _validate_public_agent_model_ownership(public_config)
    ignore_patterns = _ignore_patterns(public_config)
    mirror_delete = _mirror_delete_enabled(public_config)
    retired = _retired_assets(public_config)
    _delete_retired_assets(context, public_config, retired, mirror_delete)
    retained_local_config = _exclude_retired_local_assets(local_config, retired)
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
            _public_skill_source(context, name),
            context.target_root / '.agents' / 'skills' / name,
            ignore_patterns,
            mirror_delete,
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
    merged_local_config = _merge_local_assets(
        retained_local_config,
        discover_local_assets(context.target_root, public_config),
    )
    _generate_wrappers(
        context,
        public_config,
        merged_local_config,
        mirror_delete,
        require_agent_runtime,
    )
    _reconcile_root_configs(context, public_config)
    _generate_agents_entry(context, public_config, merged_local_config)
    return context.changes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Sync public agent assets from wenyue/agents.')
    parser.add_argument('--check', action='store_true', help='Report drift without writing files.')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target_root = Path.cwd()
    skill_root = Path(__file__).resolve().parents[1]
    try:
        public_config = load_json(skill_root / 'references' / 'public_assets.json')
        local_config = discover_local_assets(target_root, public_config)
        source_root = resolve_source(public_config)
        context = SyncContext(
            target_root=target_root,
            source_root=source_root,
            skill_root=skill_root,
            check=args.check,
            changes=[],
        )
        changes = sync_public_assets(
            context,
            public_config,
            local_config,
            require_agent_runtime=args.check,
        )
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
