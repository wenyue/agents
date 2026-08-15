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

    def test_ownership_manifest_is_the_last_transaction_mutation(self):
        operations = transaction._operations(self.plan(
            Change(ChangeKind.UPDATE, PurePosixPath('.agents/smartkit.lock.json'), b'next\n'),
            Change(ChangeKind.CREATE, PurePosixPath('z-content.txt'), b'content\n'),
            Change(ChangeKind.DELETE_DIRECTORY, PurePosixPath('retired'), None),
        ))

        self.assertEqual(operations[-1].path, PurePosixPath('.agents/smartkit.lock.json'))

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

    def test_rolls_back_when_structured_field_file_replace_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            ordinary = self.write(target, 'a-file.txt', b'old-file\n')
            structured = self.write(
                target, '.codex/config.toml', b'[mcp_servers.old]\nurl = "old"\n'
            )
            real_replace = transaction._replace

            def fail_structured(source, destination, *args, **kwargs):
                if Path(destination).name == 'config.toml':
                    raise OSError('injected field application failure')
                return real_replace(source, destination, *args, **kwargs)

            with mock.patch.object(transaction, '_replace', side_effect=fail_structured):
                with self.assertRaisesRegex(TransactionError, 'field application failure'):
                    apply_plan(target, self.plan(
                        Change(ChangeKind.UPDATE, PurePosixPath('a-file.txt'), b'new-file\n'),
                        Change(
                            ChangeKind.UPDATE,
                            PurePosixPath('.codex/config.toml'),
                            b'[mcp_servers.next]\nurl = "next"\n',
                        ),
                    ))

            self.assertEqual(ordinary.read_bytes(), b'old-file\n')
            self.assertEqual(structured.read_bytes(), b'[mcp_servers.old]\nurl = "old"\n')

    def test_rolls_back_when_ownership_manifest_replace_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            content = self.write(target, 'a-content.txt', b'old-content\n')
            manifest = self.write(
                target, '.agents/smartkit.lock.json', b'{"old": true}\n'
            )
            real_replace = transaction._replace

            def fail_manifest(source, destination, *args, **kwargs):
                if Path(destination).name == 'smartkit.lock.json':
                    raise OSError('injected manifest application failure')
                return real_replace(source, destination, *args, **kwargs)

            with mock.patch.object(transaction, '_replace', side_effect=fail_manifest):
                with self.assertRaisesRegex(TransactionError, 'manifest application failure'):
                    apply_plan(target, self.plan(
                        Change(ChangeKind.UPDATE, PurePosixPath('a-content.txt'), b'new-content\n'),
                        Change(
                            ChangeKind.UPDATE,
                            PurePosixPath('.agents/smartkit.lock.json'),
                            b'{"old": false}\n',
                        ),
                    ))

            self.assertEqual(content.read_bytes(), b'old-content\n')
            self.assertEqual(
                manifest.read_bytes(), b'{"old": true}\n'
            )

    def test_rolls_back_a_retired_directory_when_parent_removal_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            original = self.write(target, 'retired/nested/owned.txt', b'old\n')
            plan = self.plan(
                Change(ChangeKind.DELETE, PurePosixPath('retired/nested/owned.txt'), None),
                Change(ChangeKind.DELETE_DIRECTORY, PurePosixPath('retired/nested'), None),
                Change(ChangeKind.DELETE_DIRECTORY, PurePosixPath('retired'), None),
            )

            if transaction._SECURE_DIR_FDS:
                real_rmdir = os.rmdir

                def fail_retired(path, *args, **kwargs):
                    if path == 'retired':
                        raise OSError('injected directory removal failure')
                    return real_rmdir(path, *args, **kwargs)

                patch = mock.patch.object(transaction.os, 'rmdir', side_effect=fail_retired)
            else:
                real_rmdir = Path.rmdir

                def fail_retired(path):
                    if path.name == 'retired':
                        raise OSError('injected directory removal failure')
                    return real_rmdir(path)

                patch = mock.patch.object(Path, 'rmdir', new=fail_retired)

            with patch:
                with self.assertRaisesRegex(
                    TransactionError,
                    'injected directory removal failure',
                ):
                    apply_plan(target, plan)

            self.assertEqual(original.read_bytes(), b'old\n')

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
