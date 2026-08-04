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
from agents_setup.models import Change, ChangeKind, Plan  # noqa: E402
from agents_setup.transaction import TransactionError, apply_plan  # noqa: E402


class SetupTransactionTest(unittest.TestCase):
    @staticmethod
    def plan(*changes: Change) -> Plan:
        return Plan(tuple(changes))

    @staticmethod
    def write(target: Path, relative: str, content: bytes, mode: int | None = None) -> Path:
        path = target.joinpath(*PurePosixPath(relative).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if mode is not None:
            path.chmod(mode)
        return path

    def test_applies_force_convergence_and_preserves_unlisted_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, 'update.txt', b'old\n')
            self.write(target, 'delete.txt', b'delete\n')
            unmanaged = self.write(target, 'notes.txt', b'leave\x00alone')
            apply_plan(
                target,
                self.plan(
                    Change(ChangeKind.CREATE, PurePosixPath('create.txt'), b'new\n'),
                    Change(ChangeKind.UPDATE, PurePosixPath('update.txt'), b'new\n'),
                    Change(ChangeKind.DELETE, PurePosixPath('delete.txt'), None),
                ),
            )
            self.assertEqual((target / 'create.txt').read_bytes(), b'new\n')
            self.assertEqual((target / 'update.txt').read_bytes(), b'new\n')
            self.assertFalse((target / 'delete.txt').exists())
            self.assertEqual(unmanaged.read_bytes(), b'leave\x00alone')

    def test_windows_fallback_keeps_binary_bytes_exact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            content = b'line one\nline two\n\x00'
            with mock.patch.object(transaction, '_SECURE_DIR_FDS', False):
                apply_plan(
                    target,
                    self.plan(Change(ChangeKind.CREATE, PurePosixPath('owned'), content)),
                )
            self.assertEqual((target / 'owned').read_bytes(), content)

    def test_rolls_back_all_changes_when_a_later_replace_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            first = self.write(target, 'a.txt', b'a-old\n')
            second = self.write(target, 'b.txt', b'b-old\n')
            real_replace = transaction._replace
            calls = 0

            def fail_second(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('injected replacement failure')
                return real_replace(*args, **kwargs)

            with mock.patch.object(transaction, '_replace', side_effect=fail_second):
                with self.assertRaisesRegex(TransactionError, 'injected replacement failure'):
                    apply_plan(
                        target,
                        self.plan(
                            Change(ChangeKind.UPDATE, PurePosixPath('a.txt'), b'a-new\n'),
                            Change(ChangeKind.UPDATE, PurePosixPath('b.txt'), b'b-new\n'),
                        ),
                    )
            self.assertEqual(first.read_bytes(), b'a-old\n')
            self.assertEqual(second.read_bytes(), b'b-old\n')

    @unittest.skipIf(os.name == 'nt', 'POSIX mode assertion')
    def test_update_preserves_existing_permissions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = self.write(target, 'owned', b'old', 0o640)
            apply_plan(
                target,
                self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new')),
            )
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_rejects_duplicate_and_nonportable_paths_before_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            duplicate = Change(ChangeKind.CREATE, PurePosixPath('owned'), b'new')
            with self.assertRaisesRegex(TransactionError, 'duplicate plan change'):
                apply_plan(target, self.plan(duplicate, duplicate))
            with self.assertRaisesRegex(TransactionError, 'portable relative path'):
                apply_plan(
                    target,
                    self.plan(Change(ChangeKind.CREATE, PurePosixPath('CON'), b'new')),
                )
            self.assertEqual(list(target.iterdir()), [])

    def test_symlink_target_is_rejected_without_touching_external_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            external = self.write(root, 'external', b'external')
            linked = target / 'owned'
            try:
                linked.symlink_to(external)
            except OSError:
                self.skipTest('symlinks are unavailable')
            with self.assertRaisesRegex(TransactionError, 'symlink|unsafe fallback target'):
                apply_plan(
                    target,
                    self.plan(Change(ChangeKind.UPDATE, PurePosixPath('owned'), b'new')),
                )
            self.assertEqual(external.read_bytes(), b'external')

    def test_unchanged_content_is_verified_but_not_replaced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = self.write(target, 'owned', b'same')
            before = path.stat()
            apply_plan(
                target,
                self.plan(Change(ChangeKind.UNCHANGED, PurePosixPath('owned'), b'same')),
            )
            after = path.stat()
            self.assertEqual((before.st_dev, before.st_ino), (after.st_dev, after.st_ino))


if __name__ == '__main__':
    unittest.main()
