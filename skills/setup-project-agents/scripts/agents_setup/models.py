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
    selected_rules: tuple[str, ...]
    selected_skills: tuple[str, ...]
    selected_agents: tuple[str, ...]
    external_sources: tuple[ExternalSourceSpec, ...] = ()

    @property
    def external_skills(self) -> tuple[ExternalSkillSpec, ...]:
        return tuple(skill for source in self.external_sources for skill in source.skills)


@dataclass(frozen=True)
class ExternalSkillSpec:
    id: str
    name: str
    path: PurePosixPath


@dataclass(frozen=True)
class ExternalLicenseSpec:
    spdx: str
    path: PurePosixPath


@dataclass(frozen=True)
class ExternalSourceSpec:
    id: str
    url: str
    ref: str | None
    license: ExternalLicenseSpec
    skills: tuple[ExternalSkillSpec, ...]


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
    DELETE_DIRECTORY = 'delete-directory'
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
class RetiredFieldSpec:
    path: PurePosixPath
    key: str


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
    external_sources: tuple[ExternalSourceSpec, ...] = ()

    @property
    def external_skills(self) -> tuple[ExternalSkillSpec, ...]:
        return tuple(skill for source in self.external_sources for skill in source.skills)
    retired_fields: tuple[RetiredFieldSpec, ...] = ()
