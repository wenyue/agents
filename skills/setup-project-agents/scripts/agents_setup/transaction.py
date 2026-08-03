from __future__ import annotations

import json
import os
import secrets
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .catalog import ContractError, safe_relative, validate_lock_state
from .models import Change, ChangeKind, LockState, Plan
from .project import ProjectError, confined_target


_LOCK_PATH = PurePosixPath('.agents/lock.json')
_replace = os.replace
_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0)
_FILE_FLAGS = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
_SECURE_DIR_FDS = os.name == 'posix' and bool(getattr(os, 'O_NOFOLLOW', 0))


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
    kind: ChangeKind
    content: bytes | None


@dataclass(frozen=True)
class _Backup:
    operation: _Operation
    snapshot: Path | None
    mode: int | None
    identity: tuple[int, int] | None


@dataclass(frozen=True)
class _Mutation:
    backup: _Backup
    result_identity: tuple[int, int] | None


@dataclass(frozen=True)
class _RootGuard:
    path: Path
    identity: tuple[int, int]


def _path_key(path: PurePosixPath) -> str:
    return path.as_posix()


def _lock_bytes(lock: LockState) -> bytes:
    document = {
        'version': lock.version,
        'source_commit': lock.source_commit,
        'managed_files': [{'path': item.path.as_posix(), 'sha256': item.sha256} for item in lock.managed_files],
        'managed_fields': [
            {'path': item.path.as_posix(), 'key': item.key, 'sha256': item.sha256}
            for item in lock.managed_fields
        ],
    }
    return (json.dumps(document, sort_keys=True, indent=2) + '\n').encode('utf-8')


def _validate_change(change: Change) -> PurePosixPath:
    if not isinstance(change, Change) or not isinstance(change.path, PurePosixPath):
        raise TransactionError(TypeError('plan change must have a relative POSIX path'))
    try:
        path = safe_relative(change.path.as_posix(), 'plan change path')
    except ContractError as error:
        raise TransactionError(error) from error
    if not isinstance(change.kind, ChangeKind):
        raise TransactionError(TypeError(f'unsupported change kind: {change.kind!r}'))
    if change.kind is ChangeKind.DELETE and change.content is not None:
        raise TransactionError(TypeError(f'delete change has content: {_path_key(change.path)}'))
    if change.kind is not ChangeKind.DELETE and not isinstance(change.content, bytes):
        raise TransactionError(TypeError(f'file change content must be bytes: {_path_key(change.path)}'))
    return path


def _operations(plan: Plan) -> tuple[tuple[_Operation, ...], LockState]:
    if not isinstance(plan, Plan):
        raise TransactionError(TypeError('plan must be a Plan'))
    try:
        lock = validate_lock_state(plan.next_lock)
    except ContractError as error:
        raise TransactionError(error) from error
    seen: set[PurePosixPath] = set()
    operations: list[_Operation] = []
    for change in plan.changes:
        path = _validate_change(change)
        if path == _LOCK_PATH:
            raise TransactionError(ValueError('plan cannot change .agents/lock.json directly'))
        if path in seen:
            raise TransactionError(ValueError(f'duplicate plan change: {_path_key(path)}'))
        seen.add(path)
        if change.kind is not ChangeKind.UNCHANGED:
            operations.append(_Operation(path, change.kind, change.content))
    operations.sort(key=lambda operation: _path_key(operation.path))
    return tuple(operations), lock


def _open_root(root: Path) -> int:
    absolute = Path(root).absolute()
    descriptor = os.open(absolute.anchor, _DIRECTORY_FLAGS)
    try:
        for part in absolute.parts[1:]:
            next_descriptor = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _root_guard(root: Path) -> tuple[_RootGuard, int]:
    descriptor = _open_root(root)
    entry = os.fstat(descriptor)
    return _RootGuard(Path(root).absolute(), (entry.st_dev, entry.st_ino)), descriptor


def _assert_root(guard: _RootGuard) -> None:
    try:
        descriptor = _open_root(guard.path)
    except OSError as error:
        raise TransactionError('unsafe root namespace changed during transaction') from error
    try:
        entry = os.fstat(descriptor)
        if (entry.st_dev, entry.st_ino) != guard.identity or not stat.S_ISDIR(entry.st_mode):
            raise TransactionError('unsafe root namespace changed during transaction')
    finally:
        os.close(descriptor)


def _open_parent(root_fd: int, path: PurePosixPath, *, create: bool, created: list[PurePosixPath]) -> int:
    descriptor = os.dup(root_fd)
    try:
        for index, part in enumerate(path.parts[:-1], start=1):
            try:
                next_descriptor = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, 0o777, dir_fd=descriptor)
                created.append(PurePosixPath(*path.parts[:index]))
                next_descriptor = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except OSError as error:
                raise TransactionError(f'unsafe parent path: {part}') from error
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _stat_at(parent_fd: int, name: str) -> os.stat_result | None:
    try:
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(entry.st_mode):
        raise TransactionError(f'unsafe symlink at transaction target: {name}')
    if not stat.S_ISREG(entry.st_mode):
        raise TransactionError(f'target path is not a regular file: {name}')
    return entry


def _read_at(parent_fd: int, name: str) -> tuple[bytes, int] | None:
    entry = _stat_at(parent_fd, name)
    if entry is None:
        return None
    descriptor = os.open(name, _FILE_FLAGS, dir_fd=parent_fd)
    try:
        current = os.fstat(descriptor)
        if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != (entry.st_dev, entry.st_ino):
            raise TransactionError(f'unsafe target changed while reading: {name}')
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 65536):
            chunks.append(chunk)
        return b''.join(chunks), stat.S_IMODE(current.st_mode), (current.st_dev, current.st_ino)
    finally:
        os.close(descriptor)


def _write_sibling(
    root_fd: int,
    path: PurePosixPath,
    content: bytes,
    mode: int | None,
    created: list[PurePosixPath],
    guard: _RootGuard | None = None,
) -> tuple[str, int]:
    """Create a closed same-directory temporary file through a freshly opened safe parent fd."""
    if guard is not None:
        _assert_root(guard)
    parent_fd = _open_parent(root_fd, path, create=True, created=created)
    temporary = f'.{path.name}.agents-setup-{secrets.token_hex(12)}.tmp'
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    if guard is not None:
        _assert_root(guard)
    descriptor = os.open(temporary, flags, 0o666, dir_fd=parent_fd)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
    except BaseException:
        os.close(descriptor)
        os.unlink(temporary, dir_fd=parent_fd)
        os.close(parent_fd)
        raise
    else:
        os.close(descriptor)
    if mode is not None:
        if guard is not None:
            _assert_root(guard)
        os.chmod(temporary, mode, dir_fd=parent_fd, follow_symlinks=False)
    return temporary, parent_fd


def _same_parent(root_fd: int, path: PurePosixPath, parent_fd: int) -> None:
    fresh_fd = _open_parent(root_fd, path, create=False, created=[])
    try:
        fresh = os.fstat(fresh_fd)
        held = os.fstat(parent_fd)
        if (fresh.st_dev, fresh.st_ino) != (held.st_dev, held.st_ino):
            raise TransactionError(f'unsafe parent changed during transaction: {_path_key(path)}')
    finally:
        os.close(fresh_fd)


def _expected(root_fd: int, operation: _Operation, *, lock: bool = False) -> None:
    try:
        parent_fd = _open_parent(root_fd, operation.path, create=False, created=[])
    except FileNotFoundError:
        if operation.kind is ChangeKind.CREATE or lock:
            return
        raise TransactionError(f'target disappeared after planning: {_path_key(operation.path)}')
    try:
        entry = _stat_at(parent_fd, operation.path.name)
    finally:
        os.close(parent_fd)
    if lock:
        return
    if operation.kind is ChangeKind.CREATE and entry is not None:
        raise TransactionError(f'create target appeared after planning: {_path_key(operation.path)}')
    if operation.kind in {ChangeKind.UPDATE, ChangeKind.DELETE} and entry is None:
        raise TransactionError(f'target disappeared after planning: {_path_key(operation.path)}')


def _backup(root_fd: int, operation: _Operation, backup_root: Path, index: int) -> _Backup:
    try:
        parent_fd = _open_parent(root_fd, operation.path, create=False, created=[])
    except FileNotFoundError:
        return _Backup(operation, None, None, None)
    try:
        current = _read_at(parent_fd, operation.path.name)
    finally:
        os.close(parent_fd)
    if current is None:
        return _Backup(operation, None, None, None)
    content, mode, identity = current
    snapshot = backup_root / f'{index:04d}'
    snapshot.write_bytes(content)
    return _Backup(operation, snapshot, mode, identity)


def _final_matches(parent_fd: int, operation: _Operation, backup: _Backup) -> None:
    current = _stat_at(parent_fd, operation.path.name)
    if backup.identity is None:
        if current is not None:
            raise TransactionError(f'unsafe final target appeared: {_path_key(operation.path)}')
    elif current is None or (current.st_dev, current.st_ino) != backup.identity:
        raise TransactionError(f'unsafe final target changed: {_path_key(operation.path)}')


def _apply(root_fd: int, guard: _RootGuard, operation: _Operation, backup: _Backup, created: list[PurePosixPath], applied: list[_Mutation]) -> None:
    if operation.kind is ChangeKind.DELETE:
        parent_fd = _open_parent(root_fd, operation.path, create=False, created=created)
        try:
            _assert_root(guard)
            _final_matches(parent_fd, operation, backup)
            applied.append(_Mutation(backup, None))
            os.unlink(operation.path.name, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
        return
    assert operation.content is not None
    temporary, parent_fd = _write_sibling(
        root_fd, operation.path, operation.content, backup.mode, created, guard
    )
    try:
        _assert_root(guard)
        _same_parent(root_fd, operation.path, parent_fd)
        _final_matches(parent_fd, operation, backup)
        temp_entry = os.stat(temporary, dir_fd=parent_fd, follow_symlinks=False)
        applied.append(_Mutation(backup, (temp_entry.st_dev, temp_entry.st_ino)))
        _replace(temporary, operation.path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    finally:
        try:
            os.unlink(temporary, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.close(parent_fd)


def _verify_desired(root_fd: int, changes: tuple[Change, ...]) -> None:
    for change in changes:
        try:
            parent_fd = _open_parent(root_fd, change.path, create=False, created=[])
        except FileNotFoundError:
            if change.kind is ChangeKind.DELETE:
                continue
            raise TransactionError(f'content changed before lock commit: {_path_key(change.path)}')
        try:
            current = _read_at(parent_fd, change.path.name)
        except FileNotFoundError:
            current = None
        finally:
            os.close(parent_fd)
        if change.kind is ChangeKind.DELETE:
            if current is not None:
                raise TransactionError(f'delete result changed: {_path_key(change.path)}')
        elif current is None or current[0] != change.content:
            raise TransactionError(f'content changed before lock commit: {_path_key(change.path)}')


def _restore(root_fd: int, mutation: _Mutation, created: list[PurePosixPath]) -> None:
    backup = mutation.backup
    try:
        parent_fd = _open_parent(root_fd, backup.operation.path, create=backup.snapshot is not None, created=created)
    except FileNotFoundError:
        return
    try:
        current = _stat_at(parent_fd, backup.operation.path.name)
        current_identity = None if current is None else (current.st_dev, current.st_ino)
        if current_identity == backup.identity:
            return
        if current_identity != mutation.result_identity:
            raise TransactionError(f'third-party target retained during rollback: {_path_key(backup.operation.path)}')
        if backup.snapshot is None:
            if current is not None:
                os.unlink(backup.operation.path.name, dir_fd=parent_fd)
            return
    finally:
        os.close(parent_fd)
    assert backup.snapshot is not None
    content = backup.snapshot.read_bytes()
    temporary, parent_fd = _write_sibling(root_fd, backup.operation.path, content, backup.mode, created)
    try:
        _same_parent(root_fd, backup.operation.path, parent_fd)
        os.replace(temporary, backup.operation.path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    finally:
        try:
            os.unlink(temporary, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.close(parent_fd)


def _cleanup_created(root_fd: int, created: list[PurePosixPath]) -> list[BaseException]:
    errors: list[BaseException] = []
    for path in reversed(created):
        try:
            parent_fd = _open_parent(root_fd, path, create=False, created=[])
            try:
                os.rmdir(path.name, dir_fd=parent_fd)
            finally:
                os.close(parent_fd)
        except BaseException as error:
            errors.append(error)
    return errors


def _rollback(root_fd: int, guard: _RootGuard, applied: list[_Mutation], created: list[PurePosixPath]) -> tuple[BaseException, ...]:
    errors: list[BaseException] = []
    try:
        _assert_root(guard)
    except BaseException as error:
        errors.append(error)
    for mutation in reversed(applied):
        try:
            _restore(root_fd, mutation, created)
        except BaseException as error:
            errors.append(error)
    errors.extend(_cleanup_created(root_fd, created))
    return tuple(errors)


def _apply_secure(target_root: Path, plan: Plan) -> None:
    operations, lock = _operations(plan)
    guard, root_fd = _root_guard(target_root)
    applied: list[_Mutation] = []
    created: list[PurePosixPath] = []
    try:
        for change in plan.changes:
            _expected(root_fd, _Operation(_validate_change(change), change.kind, change.content))
        lock_operation = _Operation(_LOCK_PATH, ChangeKind.UPDATE, _lock_bytes(lock))
        _expected(root_fd, lock_operation, lock=True)
        with tempfile.TemporaryDirectory(prefix='agents-setup-transaction-') as temporary_root:
            try:
                all_operations = (*operations, lock_operation)
                backups = {
                    operation.path: _backup(root_fd, operation, Path(temporary_root), index)
                    for index, operation in enumerate(all_operations)
                }
                for operation in operations:
                    _expected(root_fd, operation)
                    _apply(root_fd, guard, operation, backups[operation.path], created, applied)
                _verify_desired(root_fd, plan.changes)
                _expected(root_fd, lock_operation, lock=True)
                _apply(root_fd, guard, lock_operation, backups[lock_operation.path], created, applied)
            except BaseException as error:
                original = error.original_error if isinstance(error, TransactionError) else error
                raise TransactionError(original, _rollback(root_fd, guard, applied, created)) from error
    finally:
        os.close(root_fd)


def _apply_fallback(target_root: Path, plan: Plan) -> None:
    """Functional fallback with repeated confinement; it cannot provide POSIX openat guarantees."""
    operations, lock = _operations(plan)
    root = Path(target_root)
    root_entry = root.lstat()
    root_identity = (root_entry.st_dev, root_entry.st_ino)
    applied: list[_Mutation] = []
    created: list[Path] = []

    def target(path: PurePosixPath) -> Path:
        try:
            return confined_target(root, path)
        except ProjectError as error:
            raise TransactionError(error) from error

    def guard() -> None:
        item = root.lstat()
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode) or (item.st_dev, item.st_ino) != root_identity:
            raise TransactionError('unsafe fallback root namespace changed')

    def entry(path: Path) -> os.stat_result | None:
        try:
            item = path.lstat()
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise TransactionError(f'unsafe fallback target: {path}')
        return item

    def ensure_parent(path: Path) -> None:
        guard()
        parent = path.parent
        missing: list[Path] = []
        current = parent
        while not current.exists():
            missing.append(current)
            current = current.parent
        if current.is_symlink() or not current.is_dir():
            raise TransactionError(f'unsafe fallback parent: {current}')
        for directory in reversed(missing):
            guard()
            directory.mkdir()
            created.append(directory)
            if directory.is_symlink() or not directory.is_dir():
                raise TransactionError(f'unsafe fallback parent: {directory}')

    def sibling(path: Path, content: bytes, mode: int | None) -> Path:
        ensure_parent(path)
        temporary = path.parent / f'.{path.name}.agents-setup-{secrets.token_hex(12)}.tmp'
        guard()
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
        try:
            view = memoryview(content)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
        finally:
            os.close(descriptor)
        if mode is not None:
            guard()
            temporary.chmod(mode)
        return temporary

    def expected(operation: _Operation, *, is_lock: bool = False) -> None:
        current = entry(target(operation.path))
        if is_lock:
            return
        if operation.kind is ChangeKind.CREATE and current is not None:
            raise TransactionError(f'create target appeared after planning: {_path_key(operation.path)}')
        if operation.kind in {ChangeKind.UPDATE, ChangeKind.DELETE} and current is None:
            raise TransactionError(f'target disappeared after planning: {_path_key(operation.path)}')
        if operation.kind is ChangeKind.UNCHANGED:
            assert operation.content is not None
            if current is None or target(operation.path).read_bytes() != operation.content:
                raise TransactionError(f'content changed before lock commit: {_path_key(operation.path)}')

    try:
        for change in plan.changes:
            expected(_Operation(change.path, change.kind, change.content))
        lock_operation = _Operation(_LOCK_PATH, ChangeKind.UPDATE, _lock_bytes(lock))
        expected(lock_operation, is_lock=True)
        with tempfile.TemporaryDirectory(prefix='agents-setup-transaction-') as temporary_root:
            snapshots = Path(temporary_root)
            all_operations = (*operations, lock_operation)
            backups: dict[PurePosixPath, _Backup] = {}
            for index, operation in enumerate(all_operations):
                path = target(operation.path)
                item = entry(path)
                if item is None:
                    backups[operation.path] = _Backup(operation, None, None, None)
                else:
                    snapshot = snapshots / f'{index:04d}'
                    snapshot.write_bytes(path.read_bytes())
                    backups[operation.path] = _Backup(operation, snapshot, stat.S_IMODE(item.st_mode), (item.st_dev, item.st_ino))
            for operation in (*operations, lock_operation):
                if operation.path == _LOCK_PATH:
                    for change in plan.changes:
                        change_path = target(change.path)
                        current = entry(change_path)
                        if change.kind is ChangeKind.DELETE:
                            if current is not None:
                                raise TransactionError(f'delete result changed: {_path_key(change.path)}')
                        elif current is None or change_path.read_bytes() != change.content:
                            raise TransactionError(f'content changed before lock commit: {_path_key(change.path)}')
                expected(operation, is_lock=operation.path == _LOCK_PATH)
                backup = backups[operation.path]
                path = target(operation.path)
                guard()
                current = entry(path)
                identity = None if current is None else (current.st_dev, current.st_ino)
                if identity != backup.identity:
                    raise TransactionError(f'unsafe fallback final target changed: {_path_key(operation.path)}')
                if operation.kind is ChangeKind.DELETE:
                    applied.append(_Mutation(backup, None))
                    path.unlink()
                    continue
                assert operation.content is not None
                temporary = sibling(path, operation.content, backup.mode)
                try:
                    current = entry(target(operation.path))
                    identity = None if current is None else (current.st_dev, current.st_ino)
                    if identity != backup.identity:
                        raise TransactionError(f'unsafe fallback final target changed: {_path_key(operation.path)}')
                    current_parent = target(operation.path).parent.stat()
                    temporary_parent = temporary.parent.stat()
                    if (current_parent.st_dev, current_parent.st_ino) != (temporary_parent.st_dev, temporary_parent.st_ino):
                        raise TransactionError(f'unsafe fallback parent changed: {_path_key(operation.path)}')
                    temp_entry = temporary.stat()
                    applied.append(_Mutation(backup, (temp_entry.st_dev, temp_entry.st_ino)))
                    guard()
                    _replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)
    except BaseException as error:
        rollback_errors: list[BaseException] = []
        try:
            guard()
        except BaseException as rollback_error:
            rollback_errors.append(rollback_error)
            original = error.original_error if isinstance(error, TransactionError) else error
            raise TransactionError(original, tuple(rollback_errors)) from error
        for mutation in reversed(applied):
            try:
                guard()
                backup = mutation.backup
                operation = backup.operation
                guard()
                path = target(operation.path)
                guard()
                current = entry(path)
                identity = None if current is None else (current.st_dev, current.st_ino)
                if identity == backup.identity:
                    continue
                if identity != mutation.result_identity:
                    raise TransactionError(f'third-party fallback target retained: {_path_key(operation.path)}')
                if backup.snapshot is None:
                    if current is not None:
                        guard()
                        path.unlink()
                else:
                    guard()
                    temporary = sibling(path, backup.snapshot.read_bytes(), backup.mode)
                    try:
                        guard()
                        os.replace(temporary, path)
                    finally:
                        temporary.unlink(missing_ok=True)
            except BaseException as rollback_error:
                rollback_errors.append(rollback_error)
        for directory in reversed(created):
            try:
                guard()
                if not directory.is_symlink():
                    guard()
                    directory.rmdir()
            except BaseException as rollback_error:
                rollback_errors.append(rollback_error)
                if 'fallback root namespace changed' in str(rollback_error):
                    break
        original = error.original_error if isinstance(error, TransactionError) else error
        raise TransactionError(original, tuple(rollback_errors)) from error


def apply_plan(target_root: Path, plan: Plan) -> None:
    """Apply a validated plan, using descriptor-relative no-follow operations where available."""
    if _SECURE_DIR_FDS:
        try:
            _apply_secure(Path(target_root), plan)
        except BaseException as error:
            if isinstance(error, TransactionError):
                raise
            raise TransactionError(error) from error
        return
    _apply_fallback(Path(target_root), plan)
