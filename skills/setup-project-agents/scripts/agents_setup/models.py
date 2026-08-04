from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
from typing import Mapping


class ContractError(ValueError):
    """Raised when a setup contract document is invalid."""


class Platform(str, Enum):
    CODEX = 'codex'
    CURSOR = 'cursor'
    COPILOT = 'copilot'


@dataclass(frozen=True)
class AssetSpec:
    id: str
    kind: str
    source: PurePosixPath
    target: PurePosixPath | None
    platforms: tuple[Platform, ...]
    mode: str = 'copy'
    control_plane: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectConfig:
    version: int
    platforms: tuple[Platform, ...]
    selected_rules: tuple[str, ...]
    selected_skills: tuple[str, ...]
    selected_agents: tuple[str, ...]
    external_skills: tuple[ExternalSkillSpec, ...] = ()


@dataclass(frozen=True)
class ExternalSkillSpec:
    name: str
    repository: str
    ref: str
    path: PurePosixPath


@dataclass(frozen=True)
class ProjectRuleSpec:
    path: PurePosixPath
    section: str
    read_when: str
    strength: str


@dataclass(frozen=True)
class ProjectSkillSpec:
    name: str
    path: PurePosixPath


class ChangeKind(str, Enum):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    UNCHANGED = 'unchanged'


@dataclass(frozen=True)
class DesiredFile:
    path: PurePosixPath
    content: bytes


@dataclass(frozen=True)
class DesiredField:
    path: PurePosixPath
    key: str
    value: object
    format: str


@dataclass(frozen=True)
class Change:
    kind: ChangeKind
    path: PurePosixPath
    content: bytes | None


@dataclass(frozen=True)
class Plan:
    changes: tuple[Change, ...]


@dataclass(frozen=True)
class Catalog:
    plugin_id: str
    plugin_version: str
    repository: str
    ref: str
    assets: tuple[AssetSpec, ...]
    retired_assets: tuple[PurePosixPath, ...] = ()
