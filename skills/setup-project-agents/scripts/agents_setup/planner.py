from __future__ import annotations

import re
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path, PurePosixPath

from .models import (
    Change,
    ChangeKind,
    DesiredField,
    DesiredFile,
    LockState,
    ManagedField,
    ManagedFile,
    Plan,
)
from .project import ProjectError, confined_target


_COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')


class PlanningError(ValueError):
    """Raised when a desired project state cannot be applied safely."""


def sha256_bytes(content: bytes) -> str:
    return sha256(content).hexdigest()


def _path_key(path: PurePosixPath) -> str:
    return path.as_posix()


def _desired_files(files: Sequence[DesiredFile]) -> dict[PurePosixPath, DesiredFile]:
    result: dict[PurePosixPath, DesiredFile] = {}
    for desired in files:
        if not isinstance(desired.content, bytes):
            raise PlanningError(f'desired file content must be bytes: {_path_key(desired.path)}')
        if desired.path in result:
            raise PlanningError(f'duplicate desired file path: {_path_key(desired.path)}')
        result[desired.path] = desired
    return result


def _desired_fields(
    fields: Sequence[DesiredField], files: dict[PurePosixPath, DesiredFile]
) -> tuple[DesiredField, ...]:
    result: list[DesiredField] = []
    seen: set[tuple[PurePosixPath, str]] = set()
    for field in fields:
        identity = (field.path, field.key)
        if identity in seen:
            raise PlanningError(
                f'duplicate desired field: {_path_key(field.path)}:{field.key}'
            )
        if field.path not in files:
            raise PlanningError(
                f'desired field requires a rendered desired file: {_path_key(field.path)}'
            )
        seen.add(identity)
        result.append(field)
    return tuple(sorted(result, key=lambda field: (_path_key(field.path), field.key)))


def _managed_digests(lock: LockState) -> dict[PurePosixPath, str]:
    result: dict[PurePosixPath, str] = {}
    for item in (*lock.managed_files, *lock.managed_fields):
        existing = result.setdefault(item.path, item.sha256)
        if existing != item.sha256:
            raise PlanningError(f'conflicting lock digests: {_path_key(item.path)}')
    return result


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


def _next_lock(
    files: dict[PurePosixPath, DesiredFile],
    fields: Sequence[DesiredField],
    source_commit: str | None,
) -> LockState:
    managed_files = tuple(
        ManagedFile(path, sha256_bytes(desired.content))
        for path, desired in sorted(files.items(), key=lambda item: _path_key(item[0]))
    )
    managed_fields = tuple(
        ManagedField(field.path, field.key, sha256_bytes(files[field.path].content))
        for field in fields
    )
    return LockState(1, source_commit, managed_files, managed_fields)


def build_plan(
    target_root: Path,
    desired_files: Sequence[DesiredFile],
    desired_fields: Sequence[DesiredField],
    lock: LockState,
    *,
    source_commit: str | None = None,
) -> Plan:
    """Build the sole deterministic, read-only desired/current/lock diff."""
    if source_commit is not None and (
        not isinstance(source_commit, str) or not _COMMIT.fullmatch(source_commit)
    ):
        raise PlanningError('source_commit must be a 40-character hexadecimal commit')
    files = _desired_files(desired_files)
    fields = _desired_fields(desired_fields, files)
    expected_digests = _managed_digests(lock)
    managed_file_paths = {item.path for item in lock.managed_files}
    paths = sorted(set(files) | set(expected_digests), key=_path_key)
    changes: list[Change] = []

    for path in paths:
        current = _read_current(target_root, path)
        desired = files.get(path)
        expected_digest = expected_digests.get(path)

        if expected_digest is None:
            if current is None:
                changes.append(Change(ChangeKind.CREATE, path, desired.content))
                continue
            raise PlanningError(f'unmanaged collision: {_path_key(path)}')

        if current is None or sha256_bytes(current) != expected_digest:
            raise PlanningError(f'managed content changed: {_path_key(path)}')

        if desired is None:
            if path not in managed_file_paths:
                raise PlanningError(
                    f'cannot delete field-only path without rendered desired file: '
                    f'{_path_key(path)}'
                )
            changes.append(Change(ChangeKind.DELETE, path, None))
        elif current == desired.content:
            changes.append(Change(ChangeKind.UNCHANGED, path, desired.content))
        else:
            changes.append(Change(ChangeKind.UPDATE, path, desired.content))

    return Plan(tuple(changes), _next_lock(files, fields, source_commit))
