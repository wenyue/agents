from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from .catalog import safe_field_key
from .models import Change, ChangeKind, ContractError, DesiredField, DesiredFile, Plan
from .project import ProjectError, confined_target


class PlanningError(ValueError):
    """Raised when a desired project state cannot be planned safely."""


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, 'is_junction') and path.is_junction()
    )


def _path_key(path: PurePosixPath) -> str:
    return path.as_posix()


def _desired_files(files: Sequence[DesiredFile]) -> dict[PurePosixPath, DesiredFile]:
    result: dict[PurePosixPath, DesiredFile] = {}
    for desired in files:
        if not isinstance(desired.content, bytes):
            raise PlanningError(
                f'desired file content must be bytes: {_path_key(desired.path)}'
            )
        if desired.path in result:
            raise PlanningError(f'duplicate desired file path: {_path_key(desired.path)}')
        result[desired.path] = desired
    return result


def _validate_fields(
    fields: Sequence[DesiredField], files: dict[PurePosixPath, DesiredFile]
) -> None:
    seen: set[tuple[PurePosixPath, str]] = set()
    for field in fields:
        try:
            key = safe_field_key(field.key, 'desired field key')
        except ContractError as error:
            raise PlanningError(str(error)) from error
        identity = (field.path, key)
        if identity in seen:
            raise PlanningError(
                f'duplicate desired field: {_path_key(field.path)}:{field.key}'
            )
        if field.path not in files:
            raise PlanningError(
                f'desired field requires a rendered desired file: {_path_key(field.path)}'
            )
        seen.add(identity)


def _read_current(target: Path, path: PurePosixPath) -> bytes | None:
    try:
        current = confined_target(target, path)
    except ProjectError as error:
        raise PlanningError(str(error)) from error
    if not current.exists():
        return None
    if not current.is_file():
        raise PlanningError(f'target path is not a regular file: {_path_key(path)}')
    try:
        return current.read_bytes()
    except OSError as error:
        raise PlanningError(f'cannot read target path: {_path_key(path)}') from error


def _files_under(target: Path, root: PurePosixPath) -> set[PurePosixPath]:
    try:
        directory = confined_target(target, root)
    except ProjectError as error:
        raise PlanningError(str(error)) from error
    if not directory.exists():
        return set()
    if not directory.is_dir():
        raise PlanningError(f'managed root is not a directory: {_path_key(root)}')
    result: set[PurePosixPath] = set()
    for path in directory.rglob('*'):
        if _is_link_like(path):
            raise PlanningError(f'managed root contains a symlink: {path}')
        if path.is_file():
            result.add(root / path.relative_to(directory).as_posix())
    return result


def build_plan(
    target_root: Path,
    desired_files: Sequence[DesiredFile],
    desired_fields: Sequence[DesiredField] = (),
    *,
    delete_paths: Sequence[PurePosixPath] = (),
    replace_roots: Sequence[PurePosixPath] = (),
) -> Plan:
    """Build a deterministic force-convergence plan from current and desired content."""
    files = _desired_files(desired_files)
    _validate_fields(desired_fields, files)
    removals = set(delete_paths)
    for root in replace_roots:
        removals.update(_files_under(target_root, root) - set(files))
    if removals.intersection(files):
        path = min(removals.intersection(files), key=_path_key)
        raise PlanningError(f'desired and deleted path overlap: {_path_key(path)}')

    changes: list[Change] = []
    for path in sorted(set(files) | removals, key=_path_key):
        current = _read_current(target_root, path)
        desired = files.get(path)
        if desired is None:
            if current is not None:
                changes.append(Change(ChangeKind.DELETE, path, None))
            continue
        if current is None:
            changes.append(Change(ChangeKind.CREATE, path, desired.content))
        elif current == desired.content:
            changes.append(Change(ChangeKind.UNCHANGED, path, desired.content))
        else:
            changes.append(Change(ChangeKind.UPDATE, path, desired.content))
    return Plan(tuple(changes))
