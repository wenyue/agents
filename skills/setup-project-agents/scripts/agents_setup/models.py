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


@dataclass(frozen=True)
class ManagedFile:
    path: PurePosixPath
    sha256: str


@dataclass(frozen=True)
class ManagedField:
    path: PurePosixPath
    key: str
    sha256: str


@dataclass(frozen=True)
class LockState:
    version: int
    source_commit: str | None
    managed_files: tuple[ManagedFile, ...]
    managed_fields: tuple[ManagedField, ...]

    @classmethod
    def empty(cls) -> LockState:
        return cls(1, None, (), ())

    @classmethod
    def from_files(cls, files: Mapping[str, str]) -> LockState:
        return cls(
            version=1,
            source_commit=None,
            managed_files=tuple(
                ManagedFile(PurePosixPath(path), sha256)
                for path, sha256 in sorted(files.items())
            ),
            managed_fields=(),
        )


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
    next_lock: LockState


@dataclass(frozen=True)
class Catalog:
    plugin_id: str
    plugin_version: str
    repository: str
    ref: str
    assets: tuple[AssetSpec, ...]
