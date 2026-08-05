from __future__ import annotations

import datetime as datetime_types
import json
import math
import re
from collections.abc import Mapping
from pathlib import PurePosixPath

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.11+ provides the standard library module.
    from _vendor import tomli as tomllib


class StructuredConfigError(ValueError):
    """Raised when a structured native configuration cannot be parsed or rendered."""


_BARE_TOML_KEY = re.compile(r'^[A-Za-z0-9_-]+$')


def format_for_path(path: PurePosixPath) -> str | None:
    if path.suffix == '.toml':
        return 'toml'
    if path.suffix == '.json':
        return 'jsonc' if path.as_posix().endswith('copilot/settings.json') else 'json'
    return None


def parse_jsonc(value: str) -> object:
    result: list[str] = []
    quoted = False
    escaped = False
    index = 0
    while index < len(value):
        char = value[index]
        next_char = value[index + 1] if index + 1 < len(value) else ''
        if quoted:
            result.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
            index += 1
        elif char == '"':
            quoted = True
            result.append(char)
            index += 1
        elif char == '/' and next_char == '/':
            index = value.find('\n', index)
            if index < 0:
                break
        elif char == '/' and next_char == '*':
            end = value.find('*/', index + 2)
            if end < 0:
                raise StructuredConfigError('unterminated JSONC comment')
            index = end + 2
        else:
            result.append(char)
            index += 1
    without_comments = ''.join(result)
    clean: list[str] = []
    quoted = False
    escaped = False
    index = 0
    while index < len(without_comments):
        char = without_comments[index]
        if quoted:
            clean.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
            index += 1
            continue
        if char == '"':
            quoted = True
            clean.append(char)
            index += 1
            continue
        if char == ',':
            following = index + 1
            while following < len(without_comments) and without_comments[following].isspace():
                following += 1
            if following < len(without_comments) and without_comments[following] in '}]':
                index += 1
                continue
        clean.append(char)
        index += 1
    without_trailing_commas = ''.join(clean)
    return json.loads(without_trailing_commas)


def parse_document(content: bytes | str, format_name: str) -> dict[str, object]:
    text = content.decode() if isinstance(content, bytes) else content
    try:
        value = tomllib.loads(text) if format_name == 'toml' else parse_jsonc(text)
    except (ValueError, json.JSONDecodeError) as error:
        raise StructuredConfigError(f'invalid {format_name} configuration') from error
    if not isinstance(value, dict):
        raise StructuredConfigError(f'{format_name} configuration must be an object')
    return value


def field_value(document: Mapping[str, object], key: str) -> tuple[bool, object | None]:
    current: object = document
    for part in key.split('.'):
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def canonical_value_bytes(value: object) -> bytes:
    def encode_special(item: object) -> object:
        if isinstance(item, (datetime_types.datetime, datetime_types.date, datetime_types.time)):
            return {
                '$toml_type': type(item).__name__,
                'value': item.isoformat(),
            }
        raise TypeError(f'unsupported canonical value: {type(item).__name__}')

    return json.dumps(
        value,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        default=encode_special,
    ).encode()


def _toml_key(value: str) -> str:
    return value if _BARE_TOML_KEY.fullmatch(value) else json.dumps(value)


def _toml_inline_table(value: Mapping[str, object]) -> str:
    return '{ ' + ', '.join(
        f'{_toml_key(str(key))} = {_toml_scalar(item)}'
        for key, item in value.items()
    ) + ' }'


def _toml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return 'nan'
        if math.isinf(value):
            return 'inf' if value > 0 else '-inf'
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (datetime_types.datetime, datetime_types.date, datetime_types.time)):
        return value.isoformat()
    if isinstance(value, list):
        return '[' + ', '.join(_toml_scalar(item) for item in value) + ']'
    if isinstance(value, Mapping):
        return _toml_inline_table(value)
    raise StructuredConfigError(f'unsupported TOML value: {type(value).__name__}')


def dump_toml(document: Mapping[str, object]) -> bytes:
    lines: list[str] = []

    def emit(table: Mapping[str, object], prefix: tuple[str, ...]) -> None:
        scalar_items = [
            (str(key), value) for key, value in table.items() if not isinstance(value, Mapping)
        ]
        table_items = [
            (str(key), value) for key, value in table.items() if isinstance(value, Mapping)
        ]
        if prefix and (scalar_items or not table_items):
            lines.append('[' + '.'.join(_toml_key(part) for part in prefix) + ']')
        for key, value in scalar_items:
            lines.append(f'{_toml_key(key)} = {_toml_scalar(value)}')
        if scalar_items and table_items:
            lines.append('')
        for position, (key, value) in enumerate(table_items):
            emit(value, (*prefix, key))
            if position + 1 != len(table_items):
                lines.append('')

    emit(document, ())
    return ('\n'.join(lines).rstrip() + '\n').encode()


def dump_document(document: Mapping[str, object], format_name: str) -> bytes:
    if format_name == 'toml':
        return dump_toml(document)
    return (json.dumps(document, indent=2, ensure_ascii=False) + '\n').encode()
