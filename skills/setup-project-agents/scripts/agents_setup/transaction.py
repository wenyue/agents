from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .models import Change, ChangeKind, LockState, Plan
from .project import ProjectError, confined_target


_LOCK_PATH = PurePosixPath('.agents/lock.json')
_replace = os.replace


class TransactionError(RuntimeError):
    """Raised when a plan cannot be applied without preserving the old state."""

    def __init__(self, original_error: BaseException, rollback_errors: tuple[BaseException, ...] = ()):
        self.original_error = original_error
        self.rollback_errors = rollback_errors
        message = f'transaction failed: {original_error}'
        if rollback_errors:
            message += '; rollback failed: ' + '; '.join(str(error) for error in rollback_errors)
        super().__init__(message)


@dataclass(frozen=True)
class _Operation:
    path: PurePosixPath
    target: Path
    kind: ChangeKind
    content: bytes | None


@dataclass(frozen=True)
class _Backup:
    target: Path
    snapshot: Path | None
    mode: int | None


def _path_key(path: PurePosixPath) -> str:
    return path.as_posix()


def _lock_bytes(lock: LockState) -> bytes:
    document = {
        'version': lock.version,
        'source_commit': lock.source_commit,
        'managed_files': [
            {'path': item.path.as_posix(), 'sha256': item.sha256}
            for item in lock.managed_files
        ],
        'managed_fields': [
            {'path': item.path.as_posix(), 'key': item.key, 'sha256': item.sha256}
            for item in lock.managed_fields
        ],
    }
    return (json.dumps(document, sort_keys=True, indent=2) + '\n').encode('utf-8')


def _confined(root: Path, path: PurePosixPath) -> Path:
    try:
        return confined_target(root, path)
    except ProjectError as error:
        raise TransactionError(error) from error


def _validate_change(change: Change) -> None:
    if not isinstance(change, Change):
        raise TransactionError(TypeError('plan change must be a Change'))
    if not isinstance(change.path, PurePosixPath):
        raise TransactionError(TypeError('plan change path must be a relative POSIX path'))
    if not isinstance(change.kind, ChangeKind):
        raise TransactionError(TypeError(f'unsupported change kind: {change.kind!r}'))
    if change.kind is ChangeKind.DELETE:
        if change.content is not None:
            raise TransactionError(TypeError(f'delete change has content: {_path_key(change.path)}'))
    elif not isinstance(change.content, bytes):
        raise TransactionError(TypeError(f'file change content must be bytes: {_path_key(change.path)}'))


def _operations(root: Path, plan: Plan) -> tuple[_Operation, ...]:
    if not isinstance(plan, Plan):
        raise TransactionError(TypeError('plan must be a Plan'))
    if not isinstance(plan.next_lock, LockState):
        raise TransactionError(TypeError('plan next_lock must be a LockState'))

    seen: set[PurePosixPath] = set()
    operations: list[_Operation] = []
    for change in plan.changes:
        _validate_change(change)
        if change.path == _LOCK_PATH:
            raise TransactionError(ValueError('plan cannot change .agents/lock.json directly'))
        if change.path in seen:
            raise TransactionError(ValueError(f'duplicate plan change: {_path_key(change.path)}'))
        seen.add(change.path)
        target = _confined(root, change.path)
        if change.kind is not ChangeKind.UNCHANGED:
            operations.append(_Operation(change.path, target, change.kind, change.content))

    lock_target = _confined(root, _LOCK_PATH)
    operations.sort(key=lambda operation: _path_key(operation.path))
    operations.append(_Operation(_LOCK_PATH, lock_target, ChangeKind.UPDATE, _lock_bytes(plan.next_lock)))
    return tuple(operations)


def _entry_mode(path: Path) -> int | None:
    try:
        entry = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(entry.st_mode):
        raise TransactionError(f'target path contains symlink: {path}')
    if not stat.S_ISREG(entry.st_mode):
        raise TransactionError(f'target path is not a regular file: {path}')
    return stat.S_IMODE(entry.st_mode)


def _check_expected_target(operation: _Operation) -> None:
    mode = _entry_mode(operation.target)
    if operation.path == _LOCK_PATH:
        return
    if operation.kind is ChangeKind.CREATE and mode is not None:
        raise TransactionError(f'create target appeared after planning: {operation.path.as_posix()}')
    if operation.kind in {ChangeKind.UPDATE, ChangeKind.DELETE} and mode is None:
        raise TransactionError(f'target disappeared after planning: {operation.path.as_posix()}')


def _backup(operation: _Operation, backup_root: Path, index: int) -> _Backup:
    mode = _entry_mode(operation.target)
    if mode is None:
        return _Backup(operation.target, None, None)
    snapshot = backup_root / f'{index:04d}'
    try:
        shutil.copy2(operation.target, snapshot)
    except OSError as error:
        raise TransactionError(error) from error
    return _Backup(operation.target, snapshot, mode)


def _ensure_parent(root: Path, relative: PurePosixPath, created: list[Path]) -> None:
    absolute_root = Path(root).absolute()
    current = Path(absolute_root.anchor)
    parts = absolute_root.parts[1:] + relative.parts[:-1]
    for part in parts:
        current /= part
        try:
            entry = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir()
            except OSError as error:
                raise TransactionError(error) from error
            created.append(current)
            continue
        if stat.S_ISLNK(entry.st_mode):
            raise TransactionError(f'target path contains symlink: {current}')
        if not stat.S_ISDIR(entry.st_mode):
            raise TransactionError(f'target parent is not a directory: {current}')
    _confined(root, relative)


def _write_sibling(target: Path, content: bytes, mode: int | None) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode='wb',
        prefix=f'.{target.name}.agents-setup-',
        suffix='.tmp',
        dir=target.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        handle.write(content)
        handle.flush()
    except BaseException:
        handle.close()
        temporary.unlink(missing_ok=True)
        raise
    else:
        handle.close()
    if mode is not None:
        temporary.chmod(mode)
    return temporary


def _apply(operation: _Operation, backup: _Backup) -> None:
    if operation.kind is ChangeKind.DELETE:
        operation.target.unlink()
        return
    assert operation.content is not None
    temporary = _write_sibling(operation.target, operation.content, backup.mode)
    try:
        _replace(temporary, operation.target)
    finally:
        temporary.unlink(missing_ok=True)


def _restore(backup: _Backup) -> None:
    if backup.snapshot is None:
        try:
            entry = backup.target.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(entry.st_mode):
            raise OSError(f'refusing to remove symlink during rollback: {backup.target}')
        if not stat.S_ISREG(entry.st_mode):
            raise OSError(f'refusing to remove non-file during rollback: {backup.target}')
        backup.target.unlink()
        return

    _entry_mode(backup.target)
    content = backup.snapshot.read_bytes()
    temporary = _write_sibling(backup.target, content, backup.mode)
    try:
        os.replace(temporary, backup.target)
    finally:
        temporary.unlink(missing_ok=True)


def _rollback(applied: list[_Backup], created: list[Path]) -> tuple[BaseException, ...]:
    errors: list[BaseException] = []
    for backup in reversed(applied):
        try:
            _restore(backup)
        except BaseException as error:
            errors.append(error)
    for directory in reversed(created):
        try:
            entry = directory.lstat()
            if stat.S_ISLNK(entry.st_mode):
                raise OSError(f'refusing to remove symlink during rollback: {directory}')
            directory.rmdir()
        except FileNotFoundError:
            continue
        except BaseException as error:
            errors.append(error)
    return tuple(errors)


def apply_plan(target_root: Path, plan: Plan) -> None:
    """Apply a validated plan atomically enough to restore every target on failure."""
    root = Path(target_root)
    applied: list[_Backup] = []
    created: list[Path] = []
    try:
        operations = _operations(root, plan)
        # Revalidate every planned destination, including the lock, before target writes.
        for change in plan.changes:
            target = _confined(root, change.path)
            if change.kind is ChangeKind.UNCHANGED and _entry_mode(target) is None:
                raise TransactionError(
                    f'target disappeared after planning: {change.path.as_posix()}'
                )
        for operation in operations:
            _confined(root, operation.path)
            _check_expected_target(operation)
    except BaseException as error:
        original = error.original_error if isinstance(error, TransactionError) else error
        raise TransactionError(original) from error

    with tempfile.TemporaryDirectory(prefix='agents-setup-transaction-') as temporary_root:
        try:
            backup_root = Path(temporary_root)
            backups = {
                operation.target: _backup(operation, backup_root, index)
                for index, operation in enumerate(operations)
            }
            for operation in operations:
                _ensure_parent(root, operation.path, created)
                _confined(root, operation.path)
                _check_expected_target(operation)
                backup = backups[operation.target]
                # Record before mutation so an injected replacement that mutates then raises is safe.
                applied.append(backup)
                _apply(operation, backup)
        except BaseException as error:
            original = error.original_error if isinstance(error, TransactionError) else error
            rollback_errors = _rollback(applied, created)
            raise TransactionError(original, rollback_errors) from error
