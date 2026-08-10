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


class OperatingSystem(str, Enum):
    WINDOWS = 'windows'
    LINUX = 'linux'


class McpTransport(str, Enum):
    STDIO = 'stdio'
    HTTP = 'http'


@dataclass(frozen=True)
class McpOverride:
    platforms: tuple[Platform, ...] | None = None
    operating_systems: tuple[OperatingSystem, ...] | None = None
    command: str | None = None
    args: tuple[str, ...] | None = None
    cwd: str | None = None
    env: tuple[str, ...] | None = None
    url: str | None = None


@dataclass(frozen=True)
class McpServerSpec:
    id: str
    transport: McpTransport
    platforms: tuple[Platform, ...]
    command: str | None = None
    args: tuple[str, ...] = ()
    cwd: str | None = None
    env: tuple[str, ...] = ()
    url: str | None = None
    overrides: tuple[McpOverride, ...] = ()


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
    mcp_servers: tuple[McpServerSpec, ...] = ()

    @property
    def external_skills(self) -> tuple[ExternalSkillSpec, ...]:
        return tuple(skill for source in self.external_sources for skill in source.skills)


@dataclass(frozen=True)
class ExternalSkillSpec:
    id: str
    name: str
    path: PurePosixPath


@dataclass(frozen=True)
class ExternalSourceSpec:
    id: str
    url: str
    ref: str | None
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
