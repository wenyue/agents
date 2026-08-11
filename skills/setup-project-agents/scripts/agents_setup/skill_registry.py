from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


_STABLE_ID = re.compile(r'^[A-Za-z0-9_.-]+/[a-z0-9][a-z0-9-]*$')
_NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')


class SkillRegistryError(ValueError):
    """Raised when the Plugin Skill registry violates its structural contract."""


@dataclass(frozen=True)
class CustomSkill:
    id: str
    name: str
    path: PurePosixPath


@dataclass(frozen=True)
class SkillRegistry:
    custom: tuple[CustomSkill, ...]
    external_sources: tuple[Mapping[str, object], ...]


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SkillRegistryError(f'{label} must be an object')
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise SkillRegistryError(f'{label} must be an array')
    return value


def _fields(value: Mapping[str, object], allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise SkillRegistryError(
            f'unknown {label} fields: {", ".join(sorted(str(item) for item in unknown))}'
        )


def _required(value: Mapping[str, object], key: str, label: str) -> object:
    if key not in value:
        raise SkillRegistryError(f'{label} requires {key}')
    return value[key]


def _stable_id(value: object, label: str) -> str:
    if not isinstance(value, str) or _STABLE_ID.fullmatch(value) is None:
        raise SkillRegistryError(f'{label} must use owner/name form')
    return value


def _custom_path(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or '\\' in value:
        raise SkillRegistryError(f'{label} must be one directory below skills')
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or len(path.parts) != 1
        or path.parts[0] in {'.', '..'}
        or _NAME.fullmatch(path.name) is None
    ):
        raise SkillRegistryError(f'{label} must be one directory below skills')
    return path


def load_skill_registry(root: Path) -> SkillRegistry:
    path = root / 'skills/registry.json'
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except OSError as error:
        raise SkillRegistryError(f'cannot read Skill registry: {path}') from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SkillRegistryError(f'Skill registry is not valid UTF-8 JSON: {path}') from error
    registry = _object(document, 'Skill registry')
    _fields(registry, {'version', 'custom', 'external_sources'}, 'Skill registry')
    if registry.get('version') != 1:
        raise SkillRegistryError('Skill registry version must be 1')

    custom: list[CustomSkill] = []
    for index, raw in enumerate(
        _array(_required(registry, 'custom', 'Skill registry'), 'custom')
    ):
        label = f'custom[{index}]'
        item = _object(raw, label)
        _fields(item, {'id', 'path'}, 'custom Skill')
        skill_id = _stable_id(_required(item, 'id', label), 'custom Skill id')
        skill_path = _custom_path(_required(item, 'path', label), 'custom Skill path')
        name = skill_id.rsplit('/', 1)[1]
        if name != skill_path.name:
            raise SkillRegistryError('custom Skill id name and path basename must match')
        custom.append(CustomSkill(skill_id, name, skill_path))

    ids = [item.id for item in custom]
    names = [item.name for item in custom]
    if len(ids) != len(set(ids)):
        raise SkillRegistryError('Skill registry has duplicate custom Skill ids')
    if len(names) != len(set(names)):
        raise SkillRegistryError('Skill registry has duplicate custom Skill names')

    external = tuple(
        _object(item, f'external_sources[{index}]')
        for index, item in enumerate(
            _array(
                _required(registry, 'external_sources', 'Skill registry'),
                'external_sources',
            )
        )
    )
    return SkillRegistry(tuple(custom), external)
