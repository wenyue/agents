from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .catalog import load_lock, load_project_config
from .models import Catalog, LockState, ProjectConfig


class ProjectError(ValueError):
    """Raised when a target project cannot be inspected safely."""


@dataclass(frozen=True)
class ProjectState:
    root: Path
    config: ProjectConfig
    lock: LockState


def _confined_root(root: Path) -> Path:
    candidate = Path(root).absolute()
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ProjectError(f'target path contains symlink: {current}')
    return candidate


def confined_target(root: Path, relative: PurePosixPath) -> Path:
    """Return a target path only when every existing component is non-symlinked."""
    if not isinstance(relative, PurePosixPath):
        raise ProjectError('target path must be a relative POSIX path')
    if relative.is_absolute() or not relative.parts or '..' in relative.parts:
        raise ProjectError('target path must be relative and cannot contain ..')

    confined_root = _confined_root(root)
    target = confined_root.joinpath(*relative.parts)
    current = confined_root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ProjectError(f'target path contains symlink: {current}')
    return target


def inspect_project(target_root: Path, *, catalog: Catalog) -> ProjectState:
    """Load target-owned setup state without changing the target project."""
    root = _confined_root(target_root)
    config_path = confined_target(root, PurePosixPath('.agents/config.json'))
    lock_path = confined_target(root, PurePosixPath('.agents/lock.json'))
    return ProjectState(
        root=root,
        config=load_project_config(config_path, catalog=catalog),
        lock=load_lock(lock_path),
    )
