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
from agents_setup.models import Change, ChangeKind, LockState, ManagedFile, Plan  # noqa: E402
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

            def record_replace(source, destination):
                destinations.append(Path(destination))
                real_replace(source, destination)

            with mock.patch.object(transaction, '_replace', side_effect=record_replace):
                apply_plan(target, plan)

            self.assertEqual(owned.read_bytes(), b'new-a')
            self.assertEqual(stat.S_IMODE(owned.stat().st_mode), 0o640)
            self.assertEqual((target / 'nested/owned-b').read_bytes(), b'new-b')
            self.assertFalse((target / 'removed').exists())
            self.assertEqual(unmanaged.read_bytes(), b'leave me exactly alone\x00')
            self.assertEqual(destinations[-1], target / '.agents/lock.json')
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

            def replace_once_then_fail(source, destination):
                nonlocal calls
                calls += 1
                if calls == 1:
                    real_replace(source, destination)
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

    def test_keeps_the_original_error_when_rollback_also_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, 'owned', b'old')
            plan = self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new'))

            with (
                mock.patch.object(transaction, '_replace', side_effect=OSError('primary boom')),
                mock.patch.object(transaction.os, 'replace', side_effect=OSError('rollback boom')),
            ):
                with self.assertRaisesRegex(TransactionError, 'primary boom') as raised:
                    apply_plan(target, plan)

            self.assertIn('rollback boom', str(raised.exception))
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

            def replace_then_fail_at_lock(source, destination):
                nonlocal calls
                calls += 1
                if calls == 1:
                    real_replace(source, destination)
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

            def record_replace(source, destination):
                destinations.append(Path(destination))
                real_replace(source, destination)

            with mock.patch.object(transaction, '_replace', side_effect=record_replace):
                apply_plan(target, plan)

            self.assertEqual(path.read_bytes(), b'same')
            self.assertEqual(destinations, [target / '.agents/lock.json'])

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
                with self.assertRaisesRegex(TransactionError, 'symlink'):
                    apply_plan(target, plan)

            replace.assert_not_called()
            self.assertFalse((outside / 'rules/a.md').exists())


if __name__ == '__main__':
    unittest.main()
