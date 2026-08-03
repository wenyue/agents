from __future__ import annotations

import re
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path, PurePosixPath

from .catalog import safe_field_key
from .models import (
    Change,
    ChangeKind,
    DesiredField,
    DesiredFile,
    ContractError,
    LockState,
    ManagedField,
    ManagedFile,
    Plan,
)
from .project import ProjectError, confined_target
from .structured import (
    StructuredConfigError,
    canonical_value_bytes,
    field_value,
    format_for_path,
    parse_document,
)


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
        result.append(field)
    return tuple(sorted(result, key=lambda field: (_path_key(field.path), field.key)))


def _group_desired_fields(
    fields: Sequence[DesiredField],
) -> dict[PurePosixPath, tuple[DesiredField, ...]]:
    paths: dict[PurePosixPath, list[DesiredField]] = {}
    for field in fields:
        paths.setdefault(field.path, []).append(field)
    return {path: tuple(items) for path, items in paths.items()}


def _group_managed_fields(lock: LockState) -> dict[PurePosixPath, tuple[ManagedField, ...]]:
    paths: dict[PurePosixPath, list[ManagedField]] = {}
    for field in lock.managed_fields:
        paths.setdefault(field.path, []).append(field)
    return {path: tuple(items) for path, items in paths.items()}


def _field_document(
    content: bytes,
    path: PurePosixPath,
    desired_fields: Sequence[DesiredField],
) -> dict[str, object]:
    format_name = desired_fields[0].format if desired_fields else format_for_path(path)
    if format_name not in {'json', 'jsonc', 'toml'}:
        raise PlanningError(f'cannot parse managed fields: {_path_key(path)}')
    try:
        return parse_document(content, format_name)
    except StructuredConfigError as error:
        raise PlanningError(f'cannot parse managed fields: {_path_key(path)}') from error


def _value_digest(value: object) -> str:
    return sha256_bytes(canonical_value_bytes(value))


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
    field_paths = {
        field.path for field in fields if field.path.suffix in {'.json', '.toml'}
    }
    managed_files = tuple(
        ManagedFile(path, sha256_bytes(desired.content))
        for path, desired in sorted(files.items(), key=lambda item: _path_key(item[0]))
        if path not in field_paths
    )
    managed_fields = tuple(
        ManagedField(field.path, field.key, _value_digest(field.value))
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
    managed_file_digests = {item.path: item.sha256 for item in lock.managed_files}
    desired_fields_by_path = _group_desired_fields(fields)
    managed_fields_by_path = _group_managed_fields(lock)
    paths = sorted(
        set(files) | set(managed_file_digests) | set(managed_fields_by_path),
        key=_path_key,
    )
    changes: list[Change] = []

    for path in paths:
        current = _read_current(target_root, path)
        desired = files.get(path)
        managed_file_digest = managed_file_digests.get(path)
        old_fields = managed_fields_by_path.get(path, ())
        new_fields = desired_fields_by_path.get(path, ())

        if managed_file_digest is not None:
            if current is None or sha256_bytes(current) != managed_file_digest:
                raise PlanningError(f'managed content changed: {_path_key(path)}')
        elif current is None:
            if old_fields:
                raise PlanningError(f'managed field changed: {_path_key(path)}')
            if desired is None:
                raise PlanningError(f'missing desired content: {_path_key(path)}')
            changes.append(Change(ChangeKind.CREATE, path, desired.content))
            continue
        elif old_fields or new_fields:
            document = _field_document(current, path, new_fields)
            old_keys = {field.key for field in old_fields}
            for field in old_fields:
                exists, value = field_value(document, field.key)
                if not exists or _value_digest(value) != field.sha256:
                    raise PlanningError(
                        f'managed field changed: {_path_key(path)}:{field.key}'
                    )
            for field in new_fields:
                if field.key in old_keys:
                    continue
                exists, value = field_value(document, field.key)
                if exists and _value_digest(value) != _value_digest(field.value):
                    raise PlanningError(
                        f'unmanaged field collision: {_path_key(path)}:{field.key}'
                    )
        else:
            raise PlanningError(f'unmanaged collision: {_path_key(path)}')

        if desired is None:
            if managed_file_digest is None:
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
