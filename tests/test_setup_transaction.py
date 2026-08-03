import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup import transaction  # noqa: E402
from agents_setup.models import (  # noqa: E402
    Change,
    ChangeKind,
    LockState,
    ManagedField,
    ManagedFile,
    Plan,
)
from agents_setup.transaction import TransactionError, apply_plan  # noqa: E402


class SetupTransactionTest(unittest.TestCase):
    @staticmethod
    def plan(*changes: Change, lock: LockState | None = None) -> Plan:
        return Plan(tuple(changes), lock or LockState.empty())

    @staticmethod
    def write(target: Path, relative: str, content: bytes, mode: int | None = None) -> Path:
        path = target.joinpath(*PurePosixPath(relative).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if mode is not None:
            path.chmod(mode)
        return path

    def test_applies_changes_preserves_unmanaged_bytes_and_commits_lock_last(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            owned = self.write(target, 'owned-a', b'old-a', 0o640)
            self.write(target, 'removed', b'remove-me')
            unmanaged = self.write(target, 'notes.txt', b'leave me exactly alone\x00')
            next_lock = LockState(
                1,
                'a' * 40,
                (ManagedFile(PurePosixPath('owned-a'), 'b' * 64),),
                (),
            )
            plan = self.plan(
                Change(ChangeKind.DELETE, PurePosixPath('removed'), None),
                Change(ChangeKind.CREATE, PurePosixPath('nested/owned-b'), b'new-b'),
                Change(ChangeKind.UPDATE, PurePosixPath('owned-a'), b'new-a'),
                lock=next_lock,
            )
            real_replace = os.replace
            destinations: list[Path] = []

            def record_replace(source, destination, **kwargs):
                destinations.append(Path(destination))
                real_replace(source, destination, **kwargs)

            with mock.patch.object(transaction, '_replace', side_effect=record_replace):
                apply_plan(target, plan)

            self.assertEqual(owned.read_bytes(), b'new-a')
            self.assertEqual(stat.S_IMODE(owned.stat().st_mode), 0o640)
            self.assertEqual((target / 'nested/owned-b').read_bytes(), b'new-b')
            self.assertFalse((target / 'removed').exists())
            self.assertEqual(unmanaged.read_bytes(), b'leave me exactly alone\x00')
            self.assertEqual(destinations[-1], Path('lock.json'))
            self.assertEqual(
                json.loads((target / '.agents/lock.json').read_text(encoding='utf-8')),
                {
                    'managed_fields': [],
                    'managed_files': [{'path': 'owned-a', 'sha256': 'b' * 64}],
                    'source_commit': 'a' * 40,
                    'version': 1,
                },
            )

    def test_rolls_back_all_applied_changes_when_replacement_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, 'owned-a', b'old-a')
            self.write(target, 'owned-b', b'old-b')
            plan = self.plan(
                Change(ChangeKind.UPDATE, PurePosixPath('owned-a'), b'new-a'),
                Change(ChangeKind.UPDATE, PurePosixPath('owned-b'), b'new-b'),
            )

            with mock.patch.object(transaction, '_replace', side_effect=[None, OSError('boom')]):
                with self.assertRaisesRegex(TransactionError, 'boom'):
                    apply_plan(target, plan)

            self.assertEqual((target / 'owned-a').read_bytes(), b'old-a')
            self.assertEqual((target / 'owned-b').read_bytes(), b'old-b')
            self.assertFalse((target / '.agents/lock.json').exists())

    def test_rolls_back_an_actual_replacement_and_keeps_original_permissions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            owned = self.write(target, 'owned-a', b'old-a', 0o640)
            self.write(target, 'owned-b', b'old-b')
            plan = self.plan(
                Change(ChangeKind.UPDATE, PurePosixPath('owned-a'), b'new-a'),
                Change(ChangeKind.UPDATE, PurePosixPath('owned-b'), b'new-b'),
            )
            real_replace = os.replace
            calls = 0

            def replace_once_then_fail(source, destination, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    real_replace(source, destination, **kwargs)
                    return None
                raise OSError('boom after replacement')

            with mock.patch.object(transaction, '_replace', side_effect=replace_once_then_fail):
                with self.assertRaisesRegex(TransactionError, 'boom after replacement'):
                    apply_plan(target, plan)

            self.assertEqual(owned.read_bytes(), b'old-a')
            self.assertEqual(stat.S_IMODE(owned.stat().st_mode), 0o640)
            self.assertEqual((target / 'owned-b').read_bytes(), b'old-b')

    def test_restores_a_deleted_file_when_a_later_change_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            deleted = self.write(target, 'owned-a', b'restore me', 0o640)
            self.write(target, 'owned-b', b'old-b')
            plan = self.plan(
                Change(ChangeKind.DELETE, PurePosixPath('owned-a'), None),
                Change(ChangeKind.UPDATE, PurePosixPath('owned-b'), b'new-b'),
            )

            with mock.patch.object(transaction, '_replace', side_effect=OSError('boom after delete')):
                with self.assertRaisesRegex(TransactionError, 'boom after delete'):
                    apply_plan(target, plan)

            self.assertEqual(deleted.read_bytes(), b'restore me')
            self.assertEqual(stat.S_IMODE(deleted.stat().st_mode), 0o640)

    def test_keeps_the_original_error_when_replacement_never_mutated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, 'owned', b'old')
            plan = self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new'))

            with mock.patch.object(transaction, '_replace', side_effect=OSError('primary boom')):
                with self.assertRaisesRegex(TransactionError, 'primary boom') as raised:
                    apply_plan(target, plan)

            self.assertEqual(str(raised.exception.original_error), 'primary boom')

    def test_rejects_duplicate_changes_before_any_replacement(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            plan = self.plan(
                Change(ChangeKind.CREATE, PurePosixPath('owned'), b'first'),
                Change(ChangeKind.CREATE, PurePosixPath('owned'), b'second'),
            )

            with mock.patch.object(transaction, '_replace') as replace:
                with self.assertRaisesRegex(TransactionError, 'duplicate'):
                    apply_plan(target, plan)

            replace.assert_not_called()
            self.assertFalse((target / 'owned').exists())

    def test_restores_existing_lock_and_new_parent_directories_after_a_late_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            old_lock = self.write(target, '.agents/lock.json', b'{"old": true}\n', 0o600)
            original_lock_mode = stat.S_IMODE(old_lock.stat().st_mode)
            plan = self.plan(
                Change(ChangeKind.CREATE, PurePosixPath('new/child/file'), b'created'),
                lock=LockState.empty(),
            )
            real_replace = os.replace
            calls = 0

            def replace_then_fail_at_lock(source, destination, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    real_replace(source, destination, **kwargs)
                    return None
                raise OSError('lock write failed')

            with mock.patch.object(transaction, '_replace', side_effect=replace_then_fail_at_lock):
                with self.assertRaisesRegex(TransactionError, 'lock write failed'):
                    apply_plan(target, plan)

            self.assertFalse((target / 'new').exists())
            self.assertEqual(old_lock.read_bytes(), b'{"old": true}\n')
            self.assertEqual(stat.S_IMODE(old_lock.stat().st_mode), original_lock_mode)

    def test_unchanged_change_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = self.write(target, 'owned', b'same')
            plan = self.plan(Change(ChangeKind.UNCHANGED, PurePosixPath('owned'), b'same'))
            real_replace = os.replace
            destinations: list[Path] = []

            def record_replace(source, destination, **kwargs):
                destinations.append(Path(destination))
                real_replace(source, destination, **kwargs)

            with mock.patch.object(transaction, '_replace', side_effect=record_replace):
                apply_plan(target, plan)

            self.assertEqual(path.read_bytes(), b'same')
            self.assertEqual(destinations, [Path('lock.json')])

    def test_symlink_introduced_after_planning_aborts_before_first_replacement(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target = container / 'target'
            target.mkdir()
            outside = container / 'outside'
            outside.mkdir()
            plan = self.plan(
                Change(ChangeKind.CREATE, PurePosixPath('.agents/rules/a.md'), b'new'),
            )
            (target / '.agents').symlink_to(outside, target_is_directory=True)

            with mock.patch.object(transaction, '_replace') as replace:
                with self.assertRaisesRegex(TransactionError, 'symlink|unsafe'):
                    apply_plan(target, plan)

            replace.assert_not_called()
            self.assertFalse((outside / 'rules/a.md').exists())

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX openat semantics')
    def test_parent_replacement_before_sibling_write_never_writes_outside_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target = container / 'target'
            managed = target / 'managed'
            external = container / 'external'
            managed.mkdir(parents=True)
            external.mkdir()
            self.write(target, 'managed/owned', b'old')
            plan = self.plan(Change(ChangeKind.UPDATE, PurePosixPath('managed/owned'), b'new'))
            original_write = transaction._write_sibling
            attacked = False

            def swap_parent_then_write(*args, **kwargs):
                nonlocal attacked
                if not attacked:
                    attacked = True
                    managed.rename(container / 'moved-managed')
                    managed.symlink_to(external, target_is_directory=True)
                return original_write(*args, **kwargs)

            with mock.patch.object(transaction, '_write_sibling', side_effect=swap_parent_then_write), \
                 mock.patch.object(transaction, '_replace') as replace:
                with self.assertRaisesRegex(TransactionError, 'symlink|unsafe'):
                    apply_plan(target, plan)

            replace.assert_not_called()
            self.assertEqual(list(external.iterdir()), [])
            self.assertFalse((target / '.agents/lock.json').exists())

    def test_revalidates_unchanged_content_before_committing_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, 'changed', b'old')
            unchanged = self.write(target, 'unchanged', b'same')
            plan = self.plan(
                Change(ChangeKind.UPDATE, PurePosixPath('changed'), b'new'),
                Change(ChangeKind.UNCHANGED, PurePosixPath('unchanged'), b'same'),
            )
            real_replace = os.replace
            calls = 0

            def replace_then_tamper(source, destination, **kwargs):
                nonlocal calls
                calls += 1
                real_replace(source, destination, **kwargs)
                if calls == 1:
                    unchanged.write_bytes(b'tampered')

            with mock.patch.object(transaction, '_replace', side_effect=replace_then_tamper):
                with self.assertRaisesRegex(TransactionError, 'unchanged|content'):
                    apply_plan(target, plan)

            self.assertEqual((target / 'changed').read_bytes(), b'old')
            self.assertEqual(unchanged.read_bytes(), b'tampered')
            self.assertFalse((target / '.agents/lock.json').exists())

    def test_rejects_invalid_next_locks_before_any_replacement(self):
        invalid_locks = (
            LockState(2, None, (), ()),
            LockState(1, 'not-a-commit', (), ()),
            LockState(1, None, (ManagedFile(PurePosixPath('../escape'), 'a' * 64),), ()),
            LockState(1, None, (ManagedFile(PurePosixPath('owned'), 'short'),), ()),
            LockState(
                1,
                None,
                (
                    ManagedFile(PurePosixPath('owned'), 'a' * 64),
                    ManagedFile(PurePosixPath('owned'), 'b' * 64),
                ),
                (),
            ),
            LockState(
                1,
                None,
                (),
                (ManagedField(PurePosixPath('owned'), 'bad..key', 'a' * 64),),
            ),
            LockState(
                1,
                None,
                (),
                (
                    ManagedField(PurePosixPath('owned'), 'key', 'a' * 64),
                    ManagedField(PurePosixPath('owned'), 'key', 'b' * 64),
                ),
            ),
        )
        for lock in invalid_locks:
            with self.subTest(lock=lock), tempfile.TemporaryDirectory() as temp_dir:
                target = Path(temp_dir)
                plan = self.plan(Change(ChangeKind.CREATE, PurePosixPath('owned'), b'new'), lock=lock)

                with mock.patch.object(transaction, '_replace') as replace:
                    with self.assertRaises(TransactionError):
                        apply_plan(target, plan)

                replace.assert_not_called()
                self.assertFalse((target / 'owned').exists())
                self.assertFalse((target / '.agents/lock.json').exists())

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX modes')
    def test_create_uses_the_process_umask_instead_of_a_private_tempfile_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            old_umask = os.umask(0o027)
            try:
                apply_plan(
                    target,
                    self.plan(Change(ChangeKind.CREATE, PurePosixPath('owned'), b'new')),
                )
            finally:
                os.umask(old_umask)

            self.assertEqual(stat.S_IMODE((target / 'owned').stat().st_mode), 0o640)

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX openat semantics')
    def test_unchanged_symlink_after_an_update_blocks_lock_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target = container / 'target'
            external = container / 'external'
            target.mkdir()
            external.write_bytes(b'same')
            self.write(target, 'changed', b'old')
            unchanged = self.write(target, 'unchanged', b'same')
            plan = self.plan(
                Change(ChangeKind.UPDATE, PurePosixPath('changed'), b'new'),
                Change(ChangeKind.UNCHANGED, PurePosixPath('unchanged'), b'same'),
            )
            real_replace = os.replace
            calls = 0

            def replace_then_swap_unchanged(source, destination, **kwargs):
                nonlocal calls
                calls += 1
                real_replace(source, destination, **kwargs)
                if calls == 1:
                    unchanged.unlink()
                    unchanged.symlink_to(external)

            with mock.patch.object(transaction, '_replace', side_effect=replace_then_swap_unchanged):
                with self.assertRaisesRegex(TransactionError, 'symlink|unsafe'):
                    apply_plan(target, plan)

            self.assertEqual((target / 'changed').read_bytes(), b'old')
            self.assertEqual(external.read_bytes(), b'same')
            self.assertFalse((target / '.agents/lock.json').exists())

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX openat semantics')
    def test_root_replacement_after_temp_creation_aborts_without_writing_detached_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target = container / 'target'
            moved = container / 'moved'
            external = container / 'external'
            target.mkdir()
            external.mkdir()
            self.write(target, 'owned', b'old')
            original_write = transaction._write_sibling

            def write_then_swap_root(*args, **kwargs):
                result = original_write(*args, **kwargs)
                target.rename(moved)
                target.symlink_to(external, target_is_directory=True)
                return result

            with mock.patch.object(transaction, '_write_sibling', side_effect=write_then_swap_root), \
                 mock.patch.object(transaction, '_replace') as replace:
                with self.assertRaisesRegex(TransactionError, 'root|namespace|unsafe'):
                    apply_plan(target, self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new')))

            replace.assert_not_called()
            self.assertEqual(list(external.iterdir()), [])
            self.assertEqual((moved / 'owned').read_bytes(), b'old')
            self.assertFalse((moved / '.agents/lock.json').exists())

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX openat semantics')
    def test_final_entry_swap_after_temp_creation_aborts_before_replace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target = container / 'target'
            external = container / 'external'
            target.mkdir()
            external.write_bytes(b'external')
            owned = self.write(target, 'owned', b'old')
            original_write = transaction._write_sibling

            def write_then_swap_entry(*args, **kwargs):
                result = original_write(*args, **kwargs)
                owned.unlink()
                owned.symlink_to(external)
                return result

            with mock.patch.object(transaction, '_write_sibling', side_effect=write_then_swap_entry), \
                 mock.patch.object(transaction, '_replace') as replace:
                with self.assertRaisesRegex(TransactionError, 'target|unsafe'):
                    apply_plan(target, self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new')))

            replace.assert_not_called()
            self.assertEqual(external.read_bytes(), b'external')
            self.assertFalse((target / '.agents/lock.json').exists())

    def test_rejects_nonportable_plan_paths_before_any_mutation(self):
        for path in (r'..\outside\pwn', r'a\b', 'C:/outside', '.', 'NUL'):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp_dir:
                target = Path(temp_dir)
                plan = self.plan(Change(ChangeKind.CREATE, PurePosixPath(path), b'new'))
                with mock.patch.object(transaction, '_replace') as replace:
                    with self.assertRaises(TransactionError):
                        apply_plan(target, plan)
                replace.assert_not_called()

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX openat semantics')
    def test_final_regular_swap_after_temp_preserves_attacker_file_during_rollback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            owned = self.write(target, 'owned', b'old')
            attacker = target / 'attacker'
            attacker.write_bytes(b'attacker')
            attacker_identity = (attacker.stat().st_dev, attacker.stat().st_ino)
            original_write = transaction._write_sibling

            def write_then_swap_entry(*args, **kwargs):
                result = original_write(*args, **kwargs)
                owned.unlink()
                attacker.rename(owned)
                return result

            with mock.patch.object(transaction, '_write_sibling', side_effect=write_then_swap_entry), \
                 mock.patch.object(transaction, '_replace') as replace, \
                 mock.patch.object(transaction.os, 'replace', wraps=os.replace) as rollback_replace:
                with self.assertRaises(TransactionError):
                    apply_plan(target, self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new')))

            replace.assert_not_called()
            rollback_replace.assert_not_called()
            self.assertEqual(owned.read_bytes(), b'attacker')
            self.assertEqual((owned.stat().st_dev, owned.stat().st_ino), attacker_identity)

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX openat semantics')
    def test_root_swap_during_second_replace_restores_first_mutation_via_held_fd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target = container / 'target'
            moved = container / 'moved'
            external = container / 'external'
            target.mkdir()
            external.mkdir()
            self.write(target, 'a', b'old-a')
            self.write(target, 'b', b'old-b')
            real_replace = os.replace
            calls = 0

            def replace_then_swap_root(source, destination, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return real_replace(source, destination, **kwargs)
                target.rename(moved)
                target.symlink_to(external, target_is_directory=True)
                raise OSError('second replace failed')

            with mock.patch.object(transaction, '_replace', side_effect=replace_then_swap_root):
                with self.assertRaisesRegex(TransactionError, 'second replace failed') as raised:
                    apply_plan(
                        target,
                        self.plan(
                            Change(ChangeKind.UPDATE, PurePosixPath('a'), b'new-a'),
                            Change(ChangeKind.UPDATE, PurePosixPath('b'), b'new-b'),
                        ),
                    )

            self.assertEqual((moved / 'a').read_bytes(), b'old-a')
            self.assertEqual((moved / 'b').read_bytes(), b'old-b')
            self.assertEqual(list(external.iterdir()), [])
            self.assertFalse((moved / '.agents/lock.json').exists())
            self.assertIn('namespace', str(raised.exception))

    def test_fallback_rejects_attacker_regular_inode_before_replace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            owned = self.write(target, 'owned', b'old')
            attacker = target / 'attacker'
            attacker.write_bytes(b'attacker')
            real_token = transaction.secrets.token_hex
            swapped = False

            def swap_after_backup(*args, **kwargs):
                nonlocal swapped
                if not swapped:
                    swapped = True
                    owned.unlink()
                    attacker.rename(owned)
                return real_token(*args, **kwargs)

            with mock.patch.object(transaction, '_SECURE_DIR_FDS', False), \
                 mock.patch.object(transaction.secrets, 'token_hex', side_effect=swap_after_backup), \
                 mock.patch.object(transaction, '_replace') as replace:
                with self.assertRaises(TransactionError):
                    apply_plan(target, self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new')))

            replace.assert_not_called()
            self.assertEqual(owned.read_bytes(), b'old')

    def test_fallback_root_swap_does_not_rollback_into_new_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target, moved = container / 'target', container / 'moved'
            target.mkdir()
            real_replace, calls = os.replace, 0

            def replace_then_swap(source, destination, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return real_replace(source, destination, **kwargs)
                target.rename(moved)
                target.mkdir()
                (target / 'new').mkdir()
                raise OSError('swap')

            with mock.patch.object(transaction, '_SECURE_DIR_FDS', False), \
                 mock.patch.object(transaction, '_replace', side_effect=replace_then_swap):
                with self.assertRaisesRegex(TransactionError, 'unsupported') as raised:
                    apply_plan(target, self.plan(
                        Change(ChangeKind.CREATE, PurePosixPath('new/a'), b'a'),
                        Change(ChangeKind.CREATE, PurePosixPath('new/b'), b'b'),
                    ))
            self.assertFalse((target / 'new').exists())
            self.assertIn('unsupported', str(raised.exception))

    def test_fallback_cleanup_stops_when_root_swaps_after_create_result_removal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            target, moved = container / 'target', container / 'moved'
            target.mkdir()
            real_unlink = Path.unlink
            swapped = False
            real_replace = os.replace
            calls = 0

            def unlink_then_swap(path, *args, **kwargs):
                nonlocal swapped
                result = real_unlink(path, *args, **kwargs)
                if not swapped and path.name == 'a':
                    swapped = True
                    target.rename(moved)
                    target.mkdir()
                    (target / 'new').mkdir()
                return result

            def replace_once_then_fail(source, destination, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return real_replace(source, destination, **kwargs)
                raise OSError('fail')

            with mock.patch.object(transaction, '_SECURE_DIR_FDS', False), \
                 mock.patch.object(transaction, '_replace', side_effect=replace_once_then_fail), \
                 mock.patch.object(Path, 'unlink', new=unlink_then_swap):
                with self.assertRaisesRegex(TransactionError, 'unsupported'):
                    apply_plan(target, self.plan(
                        Change(ChangeKind.CREATE, PurePosixPath('new/a'), b'a'),
                        Change(ChangeKind.CREATE, PurePosixPath('new/b'), b'b'),
                    ))
            self.assertFalse((target / 'new').exists())


if __name__ == '__main__':
    unittest.main()
