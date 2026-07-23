#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import tomllib
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
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


@dataclass(frozen=True)
class ExternalSkillSpec:
    name: str
    repository: str
    ref: str
    path: PurePosixPath


@dataclass(frozen=True)
class ExternalSkillWarning:
    name: str
    message: str


@dataclass
class ExternalSkillPreflight:
    ready: dict[str, Path]
    warnings: list[ExternalSkillWarning]
    temporary_roots: list[Path]


_TEMPLATE_PATTERN = re.compile(r'{{\s*([a-zA-Z0-9_.]+)\s*}}')
_DEFAULT_SOURCE_REF = 'master'
_PUBLIC_SOURCE_DIRECTORY = 'agents'
_ASSET_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+$')
_RULE_FILENAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+\.md$')
_RETIRED_ASSET_KINDS = ('rules', 'skills', 'agents')
_CODEX_RUNTIME_FIELDS = ('model', 'model_reasoning_effort', 'sandbox_mode')
_CURSOR_RUNTIME_FIELDS = ('model', 'readonly')
_GITHUB_RUNTIME_FIELDS = ('model',)
_AGENT_WRAPPER_MODEL_FIELDS = {
    'agent-wrappers/codex.toml': (
        ('codex_model', 'model'),
        ('codex_model_reasoning_effort', 'model_reasoning_effort'),
    ),
    'agent-wrappers/cursor.md': (('cursor_model', 'model'),),
    'agent-wrappers/github.agent.md': (('github_model', 'model'),),
}
_PUBLIC_AGENT_MODEL_FIELDS = {
    'codex': ('model', 'model_reasoning_effort'),
    'cursor': ('model',),
    'github': ('model',),
}
_CONFIG_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')
_GITHUB_REPOSITORY_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')


def _catalog_digest(public_config: dict[str, Any]) -> str:
    encoded = json.dumps(
        public_config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return f'sha256:{hashlib.sha256(encoded).hexdigest()}'


def build_model_request(
    public_config: dict[str, Any],
    local_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agents: dict[str, Any] = {}
    public_agents = _require_items(public_config, 'agent_prompts')
    local_agents = _require_items(local_config or {}, 'agent_prompts')
    for index, agent in enumerate(public_agents + local_agents):
        name = agent.get('name')
        if not isinstance(name, str) or not _ASSET_NAME_PATTERN.fullmatch(name):
            raise SyncError(f'Invalid agent prompt name: {name!r}')
        if name in agents:
            raise SyncError(f'Duplicate agent prompt name: {name}')
        required_intelligence = agent.get('required_intelligence')
        if index >= len(public_agents) and not required_intelligence:
            required_intelligence = agent.get('description')
        if not isinstance(required_intelligence, str) or not required_intelligence.strip():
            raise SyncError(f'Agent {name} requires a non-empty required_intelligence description')
        agents[name] = {
            'required_intelligence': required_intelligence.strip(),
            'codex': {
                'model': None,
                'model_reasoning_effort': None,
            },
            'cursor': {'model': None},
            'github': {'model': None},
        }
    return {
        'schema_version': 1,
        'catalog_digest': _catalog_digest(public_config),
        'agents': agents,
    }


def _model_config_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SyncError(f'{label} must be a non-empty string')
    return value.strip()


def _reject_unknown_fields(value: dict[str, Any], supported: set[str], label: str) -> None:
    unknown = sorted(set(value) - supported)
    if unknown:
        raise SyncError(f"{label} contains unsupported fields: {', '.join(unknown)}")


def load_model_config(
    path: Path,
    public_config: dict[str, Any],
    local_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    supplied = load_json(path)
    expected = build_model_request(public_config, local_config)
    _reject_unknown_fields(
        supplied,
        {'schema_version', 'catalog_digest', 'agents'},
        'Model config',
    )
    if supplied.get('schema_version') != expected['schema_version']:
        raise SyncError('Model config schema_version does not match the current script')
    if supplied.get('catalog_digest') != expected['catalog_digest']:
        raise SyncError('Model config catalog_digest does not match the current catalog')
    supplied_agents = supplied.get('agents')
    if not isinstance(supplied_agents, dict):
        raise SyncError('Model config agents must be an object')
    if set(supplied_agents) != set(expected['agents']):
        raise SyncError('Model config agents must exactly match the current catalog')

    codex_overrides: dict[str, dict[str, str]] = {}
    cursor_overrides: dict[str, dict[str, str]] = {}
    github_overrides: dict[str, dict[str, str]] = {}
    for name, expected_agent in expected['agents'].items():
        supplied_agent = supplied_agents[name]
        if not isinstance(supplied_agent, dict):
            raise SyncError(f'Model config agent {name} must be an object')
        _reject_unknown_fields(
            supplied_agent,
            {'required_intelligence', 'codex', 'cursor', 'github'},
            f'Model config agent {name}',
        )
        if supplied_agent.get('required_intelligence') != expected_agent['required_intelligence']:
            raise SyncError(f'Model config agent {name} changed required_intelligence')
        codex = supplied_agent.get('codex')
        cursor = supplied_agent.get('cursor')
        github = supplied_agent.get('github')
        if not isinstance(codex, dict):
            raise SyncError(f'Model config agent {name}.codex must be an object')
        if not isinstance(cursor, dict):
            raise SyncError(f'Model config agent {name}.cursor must be an object')
        if not isinstance(github, dict):
            raise SyncError(f'Model config agent {name}.github must be an object')
        _reject_unknown_fields(
            codex,
            {'model', 'model_reasoning_effort'},
            f'Model config agent {name}.codex',
        )
        _reject_unknown_fields(cursor, {'model'}, f'Model config agent {name}.cursor')
        _reject_unknown_fields(github, {'model'}, f'Model config agent {name}.github')
        codex_overrides[name] = {
            'model': _model_config_string(codex.get('model'), f'{name}.codex.model'),
            'model_reasoning_effort': _model_config_string(
                codex.get('model_reasoning_effort'),
                f'{name}.codex.model_reasoning_effort',
            ),
        }
        cursor_overrides[name] = {
            'model': _model_config_string(cursor.get('model'), f'{name}.cursor.model'),
        }
        github_overrides[name] = {
            'model': _model_config_string(github.get('model'), f'{name}.github.model'),
        }
    return {
        'codex_agent_runtime_overrides': codex_overrides,
        'cursor_agent_runtime_overrides': cursor_overrides,
        'github_agent_runtime_overrides': github_overrides,
    }


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


def _toml_scalar(value: Any, label: str) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return f'[{", ".join(_toml_scalar(item, label) for item in value)}]'
    if isinstance(value, dict):
        entries = []
        for key, child in value.items():
            if not isinstance(key, str):
                raise SyncError(f'{label} uses a non-string TOML key')
            rendered_key = key if _CONFIG_KEY_PATTERN.fullmatch(key) else json.dumps(key)
            entries.append(f'{rendered_key} = {_toml_scalar(child, label)}')
        return f'{{ {", ".join(entries)} }}'
    raise SyncError(f'{label} uses a value that cannot be written to TOML')


def _toml_line_comment(line: str) -> tuple[str, str]:
    quote = ''
    escaped = False
    for index, char in enumerate(line):
        if quote:
            if escaped:
                escaped = False
            elif quote == '"' and char == '\\':
                escaped = True
            elif char == quote:
                quote = ''
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == '#':
            assignment = line[:index].rstrip()
            spacing = line[len(assignment) : index]
            return assignment, spacing + line[index:]
    return line.rstrip(), ''


def _set_nested_mapping_value(
    mapping: dict[str, Any],
    parts: tuple[str, ...],
    value: Any,
) -> None:
    current = mapping
    for part in parts[:-1]:
        child = current.get(part)
        if child is None:
            child = {}
            current[part] = child
        if not isinstance(child, dict):
            raise SyncError('Cannot update an inline TOML table through a non-table value')
        current = child
    current[parts[-1]] = value


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
        dotted_pattern = r'\s*\.\s*'.join(
            rf'(?:{re.escape(part)}|"{re.escape(part)}"|\'{re.escape(part)}\')'
            for part in parts
        )
        dotted_assignment = re.compile(rf'^\s*{dotted_pattern}\s*=')
        for index in range(root_end):
            if dotted_assignment.match(lines[index]):
                indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
                _, comment = _toml_line_comment(lines[index])
                lines[index] = (
                    f'{indent}{dotted_key} = {_toml_scalar(value, label)}{comment}'
                )
                return '\n'.join(lines) + '\n'
        section_pattern = r'\s*\.\s*'.join(
            rf'(?:{re.escape(part)}|"{re.escape(part)}"|\'{re.escape(part)}\')'
            for part in parts[:-1]
        )
        header = re.compile(
            rf'^\s*\[\s*{section_pattern}\s*\]\s*(?:#.*)?$'
        )
        section_index = next(
            (index for index, line in enumerate(lines) if header.match(line)),
            None,
        )
        if section_index is None:
            root_key = parts[0]
            for index in range(root_end):
                assignment_text, comment = _toml_line_comment(lines[index])
                if '=' not in assignment_text:
                    continue
                left_hand_side = assignment_text.split('=', 1)[0].strip()
                root_assignment = re.fullmatch(
                    rf'(?:{re.escape(root_key)}|"{re.escape(root_key)}"|'
                    rf"'{re.escape(root_key)}')",
                    left_hand_side,
                )
                if root_assignment is None:
                    continue
                try:
                    parsed_assignment = tomllib.loads(assignment_text)
                except tomllib.TOMLDecodeError:
                    continue
                inline_value = parsed_assignment.get(root_key)
                if not isinstance(inline_value, dict):
                    continue
                updated_inline = copy.deepcopy(inline_value)
                _set_nested_mapping_value(updated_inline, parts[1:], value)
                lines[index] = (
                    f'{left_hand_side} = {_toml_scalar(updated_inline, label)}{comment}'
                )
                return '\n'.join(lines) + '\n'
            dotted_section_assignment = re.compile(
                rf'^\s*{section_pattern}\s*\.\s*'
                r'(?:[A-Za-z0-9_-]+|"[^"]+"|\'[^\']+\')\s*='
            )
            if any(dotted_section_assignment.match(line) for line in lines[:root_end]):
                lines.insert(
                    root_end,
                    f'{dotted_key} = {_toml_scalar(value, label)}',
                )
                return '\n'.join(lines) + '\n'
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
    assignment = re.compile(
        rf'^\s*(?:{re.escape(key)}|"{re.escape(key)}"|\'{re.escape(key)}\')\s*='
    )
    for index in range(section_start, section_end):
        if assignment.match(lines[index]):
            indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
            _, comment = _toml_line_comment(lines[index])
            lines[index] = f'{indent}{rendered}{comment}'
            return '\n'.join(lines) + '\n'
    insertion = section_end
    while insertion > section_start and not lines[insertion - 1].strip():
        insertion -= 1
    lines.insert(insertion, rendered)
    return '\n'.join(lines) + '\n'


def _config_template_condition_applies(
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


def _owned_list_rules(value: Any) -> dict[tuple[str, ...], str]:
    if value is None:
        return {}
    if not isinstance(value, list):
        raise SyncError('list_merges must be an array')
    rules: dict[tuple[str, ...], str] = {}
    for index, item in enumerate(value):
        label = f'list_merges[{index}]'
        if not isinstance(item, dict) or set(item) != {'path', 'owned_marker'}:
            raise SyncError(f'{label} requires only path and owned_marker')
        path = item['path']
        marker = item['owned_marker']
        if not isinstance(path, str) or not path or not isinstance(marker, str) or not marker:
            raise SyncError(f'{label} path and owned_marker must be non-empty strings')
        parts = tuple(path.split('.'))
        if any(not _CONFIG_KEY_PATTERN.fullmatch(part) for part in parts):
            raise SyncError(f'{label}.path contains an unsupported key')
        rules[parts] = marker
    return rules


def _contains_marker(value: Any, marker: str) -> bool:
    if isinstance(value, str):
        return marker in value
    if isinstance(value, dict):
        return any(_contains_marker(child, marker) for child in value.values())
    if isinstance(value, list):
        return any(_contains_marker(child, marker) for child in value)
    return False


def _deep_merge_template(
    current: Any,
    desired: Any,
    list_merges: Any = None,
    _path: tuple[str, ...] = (),
) -> Any:
    rules = list_merges if isinstance(list_merges, dict) else _owned_list_rules(list_merges)
    if isinstance(desired, list) and _path in rules:
        if current is None:
            current = []
        if not isinstance(current, list):
            raise SyncError('Cannot merge an owned list through a non-list value')
        marker = rules[_path]
        if not all(_contains_marker(item, marker) for item in desired):
            raise SyncError('Every owned template list item must contain its owned marker')
        first_owned = next(
            (index for index, item in enumerate(current) if _contains_marker(item, marker)),
            len(current),
        )
        unrelated = [item for item in current if not _contains_marker(item, marker)]
        insertion = min(first_owned, len(unrelated))
        return copy.deepcopy(unrelated[:insertion] + desired + unrelated[insertion:])
    if not isinstance(desired, dict):
        return copy.deepcopy(desired)
    if current is None:
        current = {}
    if not isinstance(current, dict):
        raise SyncError('Cannot merge an object template through a non-object value')
    merged = copy.deepcopy(current)
    for key, value in desired.items():
        merged[key] = _deep_merge_template(
            merged.get(key),
            value,
            rules,
            _path + (key,),
        )
    return merged


def _strip_jsonc(content: str) -> str:
    without_comments: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(content):
        char = content[index]
        if in_string:
            without_comments.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            without_comments.append(char)
            index += 1
            continue
        following = content[index + 1] if index + 1 < len(content) else ''
        if char == '/' and following == '/':
            index += 2
            while index < len(content) and content[index] not in '\r\n':
                index += 1
            continue
        if char == '/' and following == '*':
            index += 2
            while index + 1 < len(content) and content[index : index + 2] != '*/':
                if content[index] in '\r\n':
                    without_comments.append(content[index])
                index += 1
            if index + 1 >= len(content):
                raise SyncError('Invalid JSONC: unterminated block comment')
            index += 2
            continue
        without_comments.append(char)
        index += 1

    stripped = ''.join(without_comments)
    without_trailing_commas: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(stripped):
        char = stripped[index]
        if in_string:
            without_trailing_commas.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            without_trailing_commas.append(char)
            index += 1
            continue
        if char == ',':
            following = index + 1
            while following < len(stripped) and stripped[following].isspace():
                following += 1
            if following < len(stripped) and stripped[following] in '}]':
                index += 1
                continue
        without_trailing_commas.append(char)
        index += 1
    return ''.join(without_trailing_commas)


def _parse_native_config(content: str, file_format: str, label: str) -> dict[str, Any]:
    try:
        if file_format == 'toml':
            value = tomllib.loads(content)
        elif file_format == 'json':
            value = json.loads(content)
        elif file_format == 'jsonc':
            value = json.loads(_strip_jsonc(content))
        else:
            raise SyncError(f'{label}.format must be json, jsonc, or toml')
    except (json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        raise SyncError(f'Invalid native platform config {label}: {error}') from error
    if not isinstance(value, dict):
        raise SyncError(f'Native platform config {label} must contain an object')
    return value


def _external_skill_items(project_config: dict[str, Any]) -> list[dict[str, Any]]:
    skills = project_config.get('skills', {})
    if not isinstance(skills, dict):
        raise SyncError('.agents/config.json skills must be an object')
    return _require_items(skills, 'external')


def load_external_skill_specs(
    target_root: Path,
    public_config: dict[str, Any],
) -> list[ExternalSkillSpec]:
    config_path = target_root / '.agents' / 'config.json'
    if not config_path.is_file():
        return []
    project_config = load_json(config_path)
    if project_config.get('version') != 1:
        raise SyncError('.agents/config.json version must be 1')
    reserved = {
        entry.get('name')
        for key in ('skills', 'skill_blueprints')
        for entry in _require_items(public_config, key)
        if isinstance(entry.get('name'), str)
    }
    seen: set[str] = set()
    result: list[ExternalSkillSpec] = []
    for index, item in enumerate(_external_skill_items(project_config)):
        label = f'.agents/config.json skills.external[{index}]'
        _reject_unknown_fields(item, {'name', 'repository', 'ref', 'path'}, label)
        name = item.get('name')
        repository = item.get('repository')
        ref = item.get('ref')
        raw_path = item.get('path')
        if not isinstance(name, str) or not _ASSET_NAME_PATTERN.fullmatch(name):
            raise SyncError(f'{label} has an invalid name')
        if name in reserved or name in seen:
            raise SyncError(f'Duplicate or reserved external skill name: {name}')
        if (
            not isinstance(repository, str)
            or not _GITHUB_REPOSITORY_PATTERN.fullmatch(repository)
        ):
            raise SyncError(f'{label} repository must use owner/repo')
        if not isinstance(ref, str) or not ref.strip():
            raise SyncError(f'{label} ref must be a non-empty branch')
        if not isinstance(raw_path, str) or '\\' in raw_path:
            raise SyncError(f'{label} path must be a safe relative path')
        path = PurePosixPath(raw_path)
        if path.is_absolute() or not path.parts or any(
            part in {'', '.', '..'} for part in path.parts
        ):
            raise SyncError(f'{label} path must be a safe relative path')
        seen.add(name)
        result.append(ExternalSkillSpec(name, repository, ref.strip(), path))
    return result


def _toml_template_leaves(
    value: dict[str, Any],
    prefix: tuple[str, ...] = (),
) -> list[tuple[tuple[str, ...], Any]]:
    leaves: list[tuple[tuple[str, ...], Any]] = []
    for key, child in value.items():
        if not isinstance(key, str) or not _CONFIG_KEY_PATTERN.fullmatch(key):
            raise SyncError(f'TOML template contains an unsupported key: {key}')
        parts = prefix + (key,)
        if isinstance(child, dict):
            leaves.extend(_toml_template_leaves(child, parts))
        else:
            leaves.append((parts, child))
    return leaves


def _render_native_config(
    original: str,
    current: dict[str, Any],
    desired: dict[str, Any],
    file_format: str,
    label: str,
    list_merges: Any = None,
) -> str:
    if file_format in {'json', 'jsonc'}:
        merged = _deep_merge_template(current, desired, list_merges)
        return json.dumps(merged, indent=2, ensure_ascii=False) + '\n'
    content = original
    for parts, value in _toml_template_leaves(desired):
        content = _set_toml_config_value(content, parts, value, label)
    _parse_native_config(content, 'toml', label)
    return content


def _mapping_at_path(config: dict[str, Any], dotted_path: str, label: str) -> dict[str, Any]:
    current: Any = config
    if not dotted_path:
        return config
    for part in dotted_path.split('.'):
        if not isinstance(current, dict) or part not in current:
            return {}
        current = current[part]
    if not isinstance(current, dict):
        raise SyncError(f'{label} path {dotted_path} must resolve to an object')
    return current


def _validate_config_template(
    context: SyncContext,
    config: dict[str, Any],
    validations: Any,
    label: str,
) -> None:
    if validations is None:
        return
    if not isinstance(validations, list):
        raise SyncError(f'{label}.validations must be an array')
    for index, validation in enumerate(validations):
        validation_label = f'{label}.validations[{index}]'
        required_fields = {'kind', 'objects_path', 'field', 'base_path'}
        if not isinstance(validation, dict) or set(validation) != required_fields:
            raise SyncError(
                f'{validation_label} requires only {", ".join(sorted(required_fields))}'
            )
        if validation['kind'] != 'relative-paths-exist':
            raise SyncError(f'{validation_label}.kind is unsupported')
        objects_path = validation['objects_path']
        field = validation['field']
        base_path = validation['base_path']
        if not all(isinstance(value, str) and value for value in (objects_path, field)):
            raise SyncError(f'{validation_label} paths and field must be non-empty strings')
        if not isinstance(base_path, str):
            raise SyncError(f'{validation_label}.base_path must be a string')
        base_relative = Path(base_path)
        if base_relative.is_absolute() or '..' in base_relative.parts:
            raise SyncError(f'{validation_label}.base_path must stay inside the target repository')
        objects = _mapping_at_path(config, objects_path, validation_label)
        for object_name, object_value in objects.items():
            if not isinstance(object_value, dict) or field not in object_value:
                continue
            reference = object_value[field]
            if not isinstance(reference, str) or not reference:
                raise SyncError(
                    f'{label} object {object_name} field {field} must be a non-empty string'
                )
            relative_reference = Path(reference)
            if relative_reference.is_absolute():
                raise SyncError(
                    f'{label} object {object_name} field {field} must be relative'
                )
            candidate = (context.target_root / base_relative / relative_reference).resolve()
            try:
                candidate.relative_to(context.target_root.resolve())
            except ValueError as error:
                raise SyncError(
                    f'{label} object {object_name} field {field} escapes the target repository'
                ) from error
            if not candidate.is_file():
                raise SyncError(
                    f'{label} object {object_name} field {field} references missing path '
                    f'{candidate.relative_to(context.target_root.resolve())}'
                )


def _safe_config_target(target_root: Path, relative: Path, label: str) -> Path:
    resolved_root = target_root.resolve()
    candidate = target_root
    for part in relative.parts:
        candidate /= part
        if candidate.is_symlink():
            raise SyncError(f'{label}.path crosses a symbolic link: {candidate}')
    try:
        candidate.resolve(strict=False).relative_to(resolved_root)
    except ValueError as error:
        raise SyncError(f'{label}.path resolves outside the target repository') from error
    return candidate


def _reconcile_config_templates(
    context: SyncContext,
    public_config: dict[str, Any],
) -> None:
    for index, config_template in enumerate(_require_items(public_config, 'config_templates')):
        label = f'config_templates[{index}]'
        if not isinstance(config_template, dict):
            raise SyncError(f'{label} must be an object')
        unknown_fields = sorted(
            set(config_template)
            - {
                'path',
                'template',
                'format',
                'merge',
                'when',
                'validations',
                'list_merges',
            }
        )
        if unknown_fields:
            raise SyncError(f'{label} contains unsupported fields: {", ".join(unknown_fields)}')
        relative_path = config_template.get('path')
        if not isinstance(relative_path, str) or not relative_path:
            raise SyncError(f'{label}.path must be a non-empty string')
        relative = Path(relative_path)
        if relative.is_absolute() or '..' in relative.parts:
            raise SyncError(f'{label}.path must stay inside the target repository')
        template_name = config_template.get('template')
        if not isinstance(template_name, str) or not template_name:
            raise SyncError(f'{label}.template must be a non-empty string')
        template_relative = Path(template_name)
        if template_relative.is_absolute() or '..' in template_relative.parts:
            raise SyncError(f'{label}.template must stay inside assets/templates')
        file_format = config_template.get('format')
        if file_format not in {'json', 'jsonc', 'toml'}:
            raise SyncError(f'{label}.format must be json, jsonc, or toml')
        if config_template.get('merge') != 'deep-overwrite':
            raise SyncError(f'{label}.merge must be deep-overwrite')
        if not _config_template_condition_applies(
            context,
            config_template.get('when'),
            label,
        ):
            continue

        template_path = context.skill_root / 'assets' / 'templates' / template_relative
        try:
            desired_content = template_path.read_text(encoding='utf-8')
        except FileNotFoundError as error:
            raise SyncError(f'Missing config template: {template_path}') from error
        desired = _parse_native_config(desired_content, file_format, template_name)
        target = _safe_config_target(context.target_root, relative, label)
        if target.is_file():
            try:
                original = target.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError) as error:
                raise SyncError(f'Unable to read native platform config {relative_path}: {error}') from error
            current = _parse_native_config(original, file_format, relative_path)
        else:
            original = '' if file_format == 'toml' else '{}\n'
            current = {}
        rendered = _render_native_config(
            original,
            current,
            desired,
            file_format,
            relative_path,
            config_template.get('list_merges'),
        )
        rendered_config = _parse_native_config(rendered, file_format, relative_path)
        _validate_config_template(
            context,
            rendered_config,
            config_template.get('validations'),
            label,
        )
        _write_bytes(context, target, rendered.encode('utf-8'))


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
    if len(candidates) == 1 and (candidates[0] / _PUBLIC_SOURCE_DIRECTORY).is_dir():
        return candidates[0]
    if (extract_root / _PUBLIC_SOURCE_DIRECTORY).is_dir():
        return extract_root
    for candidate in candidates:
        if (candidate / _PUBLIC_SOURCE_DIRECTORY).is_dir():
            return candidate
    raise SyncError(
        f'Downloaded source archive does not contain an '
        f'{_PUBLIC_SOURCE_DIRECTORY} directory: {extract_root}'
    )


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
    if not (source_root / _PUBLIC_SOURCE_DIRECTORY).is_dir():
        shutil.rmtree(source_dir, ignore_errors=True)
        raise SyncError(
            f'Downloaded source archive is missing '
            f'{_PUBLIC_SOURCE_DIRECTORY}: {archive_url}'
        )
    return source_root


def resolve_source(public_config: dict[str, Any]) -> Path:
    return _fetch_archive_source(public_config)


def _external_archive_url(repository: str, ref: str) -> str:
    encoded_ref = urllib.parse.quote(ref, safe='')
    return f'https://github.com/{repository}/archive/refs/heads/{encoded_ref}.zip'


def _extract_safe_archive(archive_path: Path, extract_root: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            mode = (item.external_attr >> 16) & 0o170000
            if (
                '\\' in item.filename
                or path.is_absolute()
                or '..' in path.parts
                or mode == stat.S_IFLNK
            ):
                raise SyncError(f'Unsafe archive entry: {item.filename}')
        archive.extractall(extract_root)


def _fetch_external_repository(repository: str, ref: str) -> tuple[Path, Path]:
    temporary = Path(tempfile.mkdtemp(prefix='setup-project-skill-'))
    archive_path = temporary / 'source.zip'
    extract_root = temporary / 'extract'
    url = _external_archive_url(repository, ref)
    try:
        urllib.request.urlretrieve(url, archive_path)
        _extract_safe_archive(archive_path, extract_root)
        roots = [path for path in extract_root.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise SyncError(f'GitHub archive must contain one repository root: {url}')
        return roots[0], temporary
    except (OSError, zipfile.BadZipFile, SyncError) as error:
        shutil.rmtree(temporary, ignore_errors=True)
        if isinstance(error, SyncError):
            raise
        raise SyncError(f'Failed to fetch external skill source {url}: {error}') from error


def _external_skill_installed(target_root: Path, name: str) -> bool:
    target = target_root / '.agents' / 'skills' / name
    return target.exists() and (target / 'SKILL.md').is_file()


def _external_skill_source(repo_root: Path, spec: ExternalSkillSpec) -> Path:
    source = repo_root.joinpath(*spec.path.parts)
    current = repo_root
    for part in spec.path.parts:
        current = current / part
        if current.is_symlink():
            raise SyncError(f'External skill {spec.name} path contains a symbolic link')
    if not source.is_dir() or not (source / 'SKILL.md').is_file():
        raise SyncError(f'External skill {spec.name} is missing SKILL.md at {spec.path}')
    try:
        source.resolve().relative_to(repo_root.resolve())
    except ValueError as error:
        raise SyncError(f'External skill {spec.name} escapes its repository') from error
    return source


def preflight_external_skills(
    target_root: Path,
    specs: list[ExternalSkillSpec],
) -> ExternalSkillPreflight:
    grouped: dict[tuple[str, str], list[ExternalSkillSpec]] = {}
    for spec in specs:
        grouped.setdefault((spec.repository, spec.ref), []).append(spec)
    ready: dict[str, Path] = {}
    warnings: list[ExternalSkillWarning] = []
    temporary_roots: list[Path] = []
    fatal: list[str] = []
    for (repository, ref), group in grouped.items():
        try:
            repo_root, temporary = _fetch_external_repository(repository, ref)
            temporary_roots.append(temporary)
        except SyncError as error:
            for spec in group:
                if _external_skill_installed(target_root, spec.name):
                    warnings.append(ExternalSkillWarning(spec.name, str(error)))
                else:
                    fatal.append(f'{spec.name}: {error}')
            continue
        for spec in group:
            try:
                ready[spec.name] = _external_skill_source(repo_root, spec)
            except SyncError as error:
                if _external_skill_installed(target_root, spec.name):
                    warnings.append(ExternalSkillWarning(spec.name, str(error)))
                else:
                    fatal.append(f'{spec.name}: {error}')
    preflight = ExternalSkillPreflight(ready, warnings, temporary_roots)
    if fatal:
        cleanup_external_skill_preflight(preflight)
        raise SyncError('Missing required external skills:\n' + '\n'.join(fatal))
    return preflight


def cleanup_external_skill_preflight(preflight: ExternalSkillPreflight) -> None:
    for path in preflight.temporary_roots:
        shutil.rmtree(path, ignore_errors=True)


def _require_items(config: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = config.get(key, [])
    if not isinstance(value, list):
        raise SyncError(f'{key} must be a list')
    for item in value:
        if not isinstance(item, dict):
            raise SyncError(f'{key} entries must be objects')
    return value


def _entry_file_specs(public_config: dict[str, Any]) -> list[tuple[str, str]]:
    specs = []
    for index, entry_file in enumerate(_require_items(public_config, 'entry_files')):
        label = f'entry_files[{index}]'
        template_name = entry_file.get('template')
        if not isinstance(template_name, str) or not template_name:
            raise SyncError(f'{label}.template must be a non-empty string')
        template_relative = Path(template_name)
        if template_relative.is_absolute() or '..' in template_relative.parts:
            raise SyncError(f'{label}.template must stay inside assets/templates')
        target_path = entry_file.get('path')
        if not isinstance(target_path, str) or not target_path:
            raise SyncError(f'{label}.path must be a non-empty string')
        target_relative = Path(target_path)
        if target_relative.is_absolute() or '..' in target_relative.parts:
            raise SyncError(f'{label}.path must stay inside the target repository')
        specs.append((template_name, target_path))
    return specs


def _file_template_specs(public_config: dict[str, Any]) -> list[tuple[str, str]]:
    specs = []
    for index, file_template in enumerate(_require_items(public_config, 'file_templates')):
        label = f'file_templates[{index}]'
        if set(file_template) != {'template', 'path'}:
            raise SyncError(f'{label} requires only path and template')
        template_name = file_template.get('template')
        if not isinstance(template_name, str) or not template_name:
            raise SyncError(f'{label}.template must be a non-empty string')
        template_relative = Path(template_name)
        if template_relative.is_absolute() or '..' in template_relative.parts:
            raise SyncError(f'{label}.template must stay inside assets/templates')
        target_path = file_template.get('path')
        if not isinstance(target_path, str) or not target_path:
            raise SyncError(f'{label}.path must be a non-empty string')
        target_relative = Path(target_path)
        if target_relative.is_absolute() or '..' in target_relative.parts:
            raise SyncError(f'{label}.path must stay inside the target repository')
        specs.append((template_name, target_path))
    return specs


def _reconcile_file_templates(
    context: SyncContext,
    public_config: dict[str, Any],
) -> None:
    for index, (template_name, target_path) in enumerate(
        _file_template_specs(public_config)
    ):
        label = f'file_templates[{index}]'
        template_path = context.skill_root / 'assets' / 'templates' / template_name
        try:
            content = template_path.read_bytes()
        except FileNotFoundError as error:
            raise SyncError(f'Missing file template: {template_path}') from error
        target = _safe_config_target(context.target_root, Path(target_path), label)
        _write_bytes(context, target, content)


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
            for key in ('rules', 'rule_blueprints')
            for rule in _require_items(config, key)
            if isinstance(rule.get('file'), str)
        },
        'skills': {
            skill.get('name')
            for key in ('skills', 'skill_blueprints')
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


def _directory_snapshot(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob('*')
        if path.is_file()
    }


def _remove_tree_or_link(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.exists():
        shutil.rmtree(path)


def _replace_external_skill(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    transaction = Path(
        tempfile.mkdtemp(prefix=f'.{target.name}.', dir=target.parent)
    )
    staged = transaction / 'new'
    backup = transaction / 'old'
    had_old = target.exists() or target.is_symlink()
    try:
        shutil.copytree(source, staged)
        if had_old:
            os.replace(target, backup)
        try:
            os.replace(staged, target)
        except OSError:
            if had_old and backup.exists():
                os.replace(backup, target)
            raise
        _remove_tree_or_link(backup)
    finally:
        _remove_tree_or_link(staged)
        _remove_tree_or_link(transaction)


def sync_external_skills(
    context: SyncContext,
    preflight: ExternalSkillPreflight,
) -> list[ExternalSkillWarning]:
    warnings = list(preflight.warnings)
    for name, source in preflight.ready.items():
        target = context.target_root / '.agents' / 'skills' / name
        installed = target.exists() and (target / 'SKILL.md').is_file()
        unchanged = (
            installed
            and not target.is_symlink()
            and _directory_snapshot(source) == _directory_snapshot(target)
        )
        if unchanged:
            _record_file(context, 'unchanged', target)
            continue
        action = 'updated' if installed or target.is_symlink() else 'created'
        if context.check:
            _record_file(context, action, target)
            continue
        try:
            _replace_external_skill(source, target)
        except OSError as error:
            if installed:
                warnings.append(ExternalSkillWarning(name, str(error)))
                continue
            raise SyncError(
                f'Failed to install required external skill {name}: {error}'
            ) from error
        _record_file(context, action, target)
    return warnings


def _write_bytes(context: SyncContext, target: Path, content: bytes) -> None:
    exists = target.exists()
    if exists and target.read_bytes() == content:
        _record_file(context, 'unchanged', target)
        return
    action = 'created' if not exists else 'updated'
    if not context.check:
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f'.{target.name}.',
            suffix='.tmp',
            dir=target.parent,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            mode = target.stat().st_mode & 0o777 if exists else 0o644
            os.chmod(temporary, mode)
            os.replace(temporary, target)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
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
    cursor_description = _scalar_value(cursor.get('description'), '')
    if not cursor_description:
        strength = _scalar_value(rule.get('strength'), 'Default').lower()
        read_when = _scalar_value(rule.get('read_when'), filename.removesuffix('.md'))
        cursor_description = f'[{strength}] {read_when}'
    return {
        'rule': {
            **rule,
            'path': f'.agents/rules/{filename}',
            'apply_ref': f'.agents/rules/{filename}',
            'name': filename.removesuffix('.md'),
            'cursor_description': cursor_description,
            'cursor_globs': _scalar_value(cursor.get('globs'), '""'),
            'cursor_always_apply': str(bool(cursor.get('alwaysApply', False))).lower(),
            'github_apply_to': _scalar_value(github.get('applyTo'), '**'),
        },
    }


def _agent_data(
    agent: dict[str, Any],
    agent_defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    name = agent['name']
    agent_defaults = agent_defaults or {}
    if not isinstance(agent_defaults, dict):
        raise SyncError('platforms.agent_defaults must be an object')
    codex_defaults = agent_defaults.get('codex') or {}
    cursor_defaults = agent_defaults.get('cursor') or {}
    if not isinstance(codex_defaults, dict) or not isinstance(cursor_defaults, dict):
        raise SyncError('platform agent defaults must contain objects')
    codex = agent.get('codex') or {}
    cursor = agent.get('cursor') or {}
    github = agent.get('github') or {}
    if not isinstance(codex, dict):
        raise SyncError(f'Agent codex config for {name} must be an object')
    if not isinstance(cursor, dict):
        raise SyncError(f'Agent cursor config for {name} must be an object')
    if not isinstance(github, dict):
        raise SyncError(f'Agent github config for {name} must be an object')
    codex_model = _optional_config_string(codex, 'model', f'Agent codex config {name}')
    codex_model_reasoning_effort = _optional_config_string(
        codex,
        'model_reasoning_effort',
        f'Agent codex config {name}',
    )
    cursor_model = _optional_config_string(cursor, 'model', f'Agent cursor config {name}')
    github_model = _optional_config_string(github, 'model', f'Agent github config {name}')
    cursor_readonly = cursor.get('readonly', cursor_defaults.get('readonly'))
    if cursor_readonly is not None and not isinstance(cursor_readonly, bool):
        raise SyncError(f'Agent cursor config {name}.readonly must be a boolean')
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
                codex_defaults.get('sandbox_mode'),
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
    source = context.source_root / _PUBLIC_SOURCE_DIRECTORY / 'skills' / name
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
    agent_defaults = platforms.get('agent_defaults') or {}
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
        agent_data = _agent_data({'name': name}, agent_defaults)
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


def _read_entry_rule_rows(
    target_root: Path,
    public_config: dict[str, Any],
) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    pattern = re.compile(
        r'^\|\s*(?P<read_when>.*?)\s*\|\s*`\.agents/rules/(?P<file>[^`]+)`\s*\|\s*`(?P<strength>[^`]+)`\s*\|$'
    )
    for _, target_path in _entry_file_specs(public_config):
        entry_path = target_root / target_path
        if not entry_path.is_file():
            continue
        for line in entry_path.read_text(encoding='utf-8').splitlines():
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
    agents_rows = _read_entry_rule_rows(target_root, public_config)
    blueprint_rule_metadata = {
        rule.get('file'): rule
        for rule in _require_items(public_config, 'rule_blueprints')
        if isinstance(rule.get('file'), str)
    }
    if rules_root.exists():
        for rule_path in sorted(rules_root.glob('*.md')):
            if rule_path.name in public_rule_files:
                continue
            blueprint_metadata = blueprint_rule_metadata.get(rule_path.name)
            if blueprint_metadata:
                rules.append({**blueprint_metadata})
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
            agent_prompts.append({'name': name, 'description': description})
    return {
        'rules': rules,
        'agent_prompts': agent_prompts,
        'codex_agent_runtime_overrides': {},
        'cursor_agent_runtime_overrides': {},
        'github_agent_runtime_overrides': {},
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
    agent_defaults = platforms.get('agent_defaults') or {}
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
            agent_data = _agent_data(effective_agent, agent_defaults)
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


def _generate_entry_files(
    context: SyncContext,
    public_config: dict[str, Any],
    local_config: dict[str, Any],
) -> None:
    all_rules = _require_items(public_config, 'rules') + _require_items(local_config, 'rules')
    template_data = {
        'global_rule_rows': _rows_for_section(all_rules, 'global'),
        'base_rule_rows': _rows_for_section(all_rules, 'base'),
        'project_rule_rows': _rows_for_section(all_rules, 'project'),
    }
    for template_name, target_path in _entry_file_specs(public_config):
        _render_to_target(
            context,
            template_name,
            target_path,
            template_data,
        )


def _record_missing_generated_outputs(
    context: SyncContext,
    public_config: dict[str, Any],
) -> None:
    if not context.check:
        return
    for rule in _require_items(public_config, 'rule_blueprints'):
        filename = rule.get('file')
        if not isinstance(filename, str) or not _RULE_FILENAME_PATTERN.fullmatch(filename):
            raise SyncError('Each Rule blueprint requires a safe output file name')
        target = context.target_root / '.agents' / 'rules' / filename
        if not target.is_file():
            _record_file(context, 'missing', target)
    for skill in _require_items(public_config, 'skill_blueprints'):
        name = skill.get('name')
        if not isinstance(name, str) or not _ASSET_NAME_PATTERN.fullmatch(name):
            raise SyncError('Each Skill blueprint requires a safe output name')
        target = context.target_root / '.agents' / 'skills' / name / 'SKILL.md'
        if not target.is_file():
            _record_file(context, 'missing', target)


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
            context.source_root / _PUBLIC_SOURCE_DIRECTORY / 'rules' / filename,
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
            context.source_root / _PUBLIC_SOURCE_DIRECTORY / 'agents' / f'{name}.md',
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
    _reconcile_config_templates(context, public_config)
    _reconcile_file_templates(context, public_config)
    _generate_entry_files(context, public_config, merged_local_config)
    _record_missing_generated_outputs(context, public_config)
    return context.changes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Sync public agent assets from wenyue/agents.')
    parser.add_argument('--check', action='store_true', help='Report drift without writing files.')
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument(
        '--model-request',
        metavar='PATH',
        help='Write the first-stage model-selection request JSON to PATH.',
    )
    model_group.add_argument(
        '--model-config',
        metavar='PATH',
        help='Read completed second-stage model-selection JSON from PATH.',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.check and not args.model_config:
        print('ERROR: --check requires --model-config PATH', file=sys.stderr)
        return 2
    if not args.model_request and not args.model_config:
        print(
            'ERROR: synchronization requires --model-request or --model-config with a PATH',
            file=sys.stderr,
        )
        return 2
    target_root = Path.cwd()
    installed_skill_root = Path(__file__).resolve().parents[1]
    changes: list[Change] = []
    warnings: list[ExternalSkillWarning] = []
    preflight: ExternalSkillPreflight | None = None
    try:
        installed_config = load_json(
            installed_skill_root / 'references' / 'public_assets.json'
        )
        source_root = resolve_source(installed_config)
        source_skill_root = (
            source_root / _PUBLIC_SOURCE_DIRECTORY / 'skills' / 'setup-project-agents'
        )
        public_config = load_json(
            source_skill_root / 'references' / 'public_assets.json'
        )
        external_specs = load_external_skill_specs(target_root, public_config)
        preflight = preflight_external_skills(target_root, external_specs)
        local_config = discover_local_assets(target_root, public_config)
        if args.model_config:
            local_config = {
                **local_config,
                **load_model_config(Path(args.model_config), public_config, local_config),
            }
        context = SyncContext(
            target_root=target_root,
            source_root=source_root,
            skill_root=source_skill_root,
            check=args.check,
            changes=[],
        )
        changes = sync_public_assets(
            context,
            public_config,
            local_config,
            require_agent_runtime=bool(args.model_config),
        )
        warnings = sync_external_skills(context, preflight)
        if args.model_request:
            request_path = Path(args.model_request)
            try:
                request_path.write_text(
                    json.dumps(
                        build_model_request(public_config, local_config),
                        indent=2,
                        ensure_ascii=False,
                    )
                    + '\n',
                    encoding='utf-8',
                )
            except OSError as error:
                raise SyncError(f'Unable to write model request {request_path}: {error}') from error
    except SyncError as error:
        print(f'ERROR: {error}')
        return 2
    finally:
        if preflight is not None:
            cleanup_external_skill_preflight(preflight)
    for change in changes:
        print(f'{change.action} {change.path}')
    for warning in warnings:
        print(f'WARNING: {warning.name}: {warning.message}')
    if args.check and warnings:
        return 1
    if args.check and any(
        change.action in {'created', 'updated', 'deleted', 'missing'}
        for change in changes
    ):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
