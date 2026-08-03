import json
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup.planner import (  # noqa: E402
    PlanningError,
    build_plan,
    sha256_bytes,
)
from agents_setup.catalog import load_lock  # noqa: E402
from agents_setup.models import (  # noqa: E402
    Change,
    ChangeKind,
    DesiredField,
    DesiredFile,
    LockState,
    ManagedField,
)


class SetupPlannerTest(unittest.TestCase):
    def desired_file(self, content: bytes = b'new\n') -> DesiredFile:
        return DesiredFile(PurePosixPath('.agents/rules/a.md'), content)

    def write_target(self, target: Path, relative: PurePosixPath, content: bytes) -> None:
        path = target.joinpath(*relative.parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def test_creates_absent_file_rejects_collision_and_updates_owned_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            desired_files = (self.desired_file(),)

            plan = build_plan(target, desired_files, (), LockState.empty())
            self.assertEqual(plan.changes[0].kind, ChangeKind.CREATE)
            self.assertFalse((target / '.agents/rules/a.md').exists())

            self.write_target(target, desired_files[0].path, b'user\n')
            with self.assertRaisesRegex(PlanningError, 'unmanaged collision'):
                build_plan(target, desired_files, (), LockState.empty())

            owned = LockState.from_files(
                {desired_files[0].path.as_posix(): sha256_bytes(b'old\n')}
            )
            self.write_target(target, desired_files[0].path, b'old\n')
            plan = build_plan(target, desired_files, (), owned)
            self.assertEqual(plan.changes[0].kind, ChangeKind.UPDATE)

    def test_deletes_removed_lock_owned_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = PurePosixPath('.agents/rules/a.md')
            self.write_target(target, path, b'old\n')
            lock = LockState.from_files({path.as_posix(): sha256_bytes(b'old\n')})

            plan = build_plan(target, (), (), lock)

            self.assertEqual(
                plan.changes,
                (Change(ChangeKind.DELETE, path, None),),
            )
            self.assertEqual(plan.next_lock, LockState.empty())

    def test_marks_matching_desired_file_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            desired_file = self.desired_file()
            self.write_target(target, desired_file.path, desired_file.content)
            lock = LockState.from_files(
                {desired_file.path.as_posix(): sha256_bytes(desired_file.content)}
            )

            plan = build_plan(target, (desired_file,), (), lock)

            self.assertEqual(
                plan.changes,
                (Change(ChangeKind.UNCHANGED, desired_file.path, desired_file.content),),
            )

    def test_rejects_modified_lock_owned_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            desired_file = self.desired_file()
            self.write_target(target, desired_file.path, b'user changed\n')
            lock = LockState.from_files(
                {desired_file.path.as_posix(): sha256_bytes(b'old\n')}
            )

            with self.assertRaisesRegex(PlanningError, 'managed content changed'):
                build_plan(target, (desired_file,), (), lock)

    def test_rejects_symlinked_target_root_and_components(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            real_target = container / 'real-target'
            real_target.mkdir()
            linked_target = container / 'linked-target'
            linked_target.symlink_to(real_target, target_is_directory=True)
            desired_file = self.desired_file()

            with self.assertRaisesRegex(PlanningError, 'symlink'):
                build_plan(linked_target, (desired_file,), (), LockState.empty())

            target = container / 'target'
            target.mkdir()
            linked_agents = container / 'linked-agents'
            linked_agents.mkdir()
            (target / '.agents').symlink_to(linked_agents, target_is_directory=True)
            with self.assertRaisesRegex(PlanningError, 'symlink'):
                build_plan(target, (desired_file,), (), LockState.empty())

    def test_sorts_paths_and_builds_next_lock_from_desired_content_and_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            desired_a = DesiredFile(PurePosixPath('.agents/rules/a.md'), b'a\n')
            desired_b = DesiredFile(PurePosixPath('.agents/rules/b.md'), b'b\n')
            removed = PurePosixPath('.agents/rules/removed.md')
            self.write_target(target, removed, b'old\n')
            lock = LockState.from_files({removed.as_posix(): sha256_bytes(b'old\n')})
            desired_field = DesiredField(
                desired_a.path, 'catalog.version', '1.0.0', 'json'
            )

            plan = build_plan(
                target,
                (desired_b, desired_a),
                (desired_field,),
                lock,
                source_commit='a' * 40,
            )

            self.assertEqual(
                tuple(change.path.as_posix() for change in plan.changes),
                (
                    '.agents/rules/a.md',
                    '.agents/rules/b.md',
                    '.agents/rules/removed.md',
                ),
            )
            self.assertEqual(plan.next_lock.source_commit, 'a' * 40)
            self.assertEqual(
                tuple(item.path.as_posix() for item in plan.next_lock.managed_files),
                ('.agents/rules/a.md', '.agents/rules/b.md'),
            )
            self.assertEqual(
                plan.next_lock.managed_fields[0].sha256,
                sha256_bytes(b'"1.0.0"'),
            )

    def test_field_ownership_requires_rendered_file_and_shares_its_conflict_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = PurePosixPath('.agents/config.json')
            desired_file = DesiredFile(path, b'{"feature": true}\n')
            desired_field = DesiredField(path, 'feature', True, 'json')

            with self.assertRaisesRegex(PlanningError, 'rendered desired file'):
                build_plan(target, (), (desired_field,), LockState.empty())

            self.write_target(target, path, b'{"feature": false}\n')
            field_lock = LockState(
                1,
                None,
                (),
                (ManagedField(path, 'feature', sha256_bytes(b'false')),),
            )
            plan = build_plan(target, (desired_file,), (desired_field,), field_lock)

            self.assertEqual(plan.changes[0].kind, ChangeKind.UPDATE)

    def test_rejects_deleting_a_field_only_path_without_rendered_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = PurePosixPath('.agents/config.json')
            content = b'{"project_owned": true, "feature": false}\n'
            self.write_target(target, path, content)
            lock = LockState(
                1,
                None,
                (),
                (ManagedField(path, 'feature', sha256_bytes(b'false')),),
            )

            with self.assertRaisesRegex(PlanningError, 'field-only'):
                build_plan(target, (), (), lock)

    def test_rejects_invalid_source_commit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(PlanningError, 'source_commit'):
                build_plan(
                    Path(temp_dir),
                    (self.desired_file(),),
                    (),
                    LockState.empty(),
                    source_commit='not-a-commit',
                )

    def test_dotted_field_key_round_trips_through_lock_parser(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            desired_file = DesiredFile(
                PurePosixPath('.agents/config.json'), b'{"catalog": {}}\n'
            )
            plan = build_plan(
                target,
                (desired_file,),
                (DesiredField(desired_file.path, 'catalog.version', '1.0.0', 'json'),),
                LockState.empty(),
            )
            lock_path = target / 'lock.json'
            lock_path.write_text(
                json.dumps(
                    {
                        'version': plan.next_lock.version,
                        'source_commit': plan.next_lock.source_commit,
                        'managed_files': [
                            {'path': item.path.as_posix(), 'sha256': item.sha256}
                            for item in plan.next_lock.managed_files
                        ],
                        'managed_fields': [
                            {
                                'path': item.path.as_posix(),
                                'key': item.key,
                                'sha256': item.sha256,
                            }
                            for item in plan.next_lock.managed_fields
                        ],
                    }
                ),
                encoding='utf-8',
            )

            self.assertEqual(load_lock(lock_path), plan.next_lock)

    def test_rejects_unsafe_dotted_field_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            desired_file = DesiredFile(
                PurePosixPath('.agents/config.json'), b'{"catalog": {}}\n'
            )

            with self.assertRaisesRegex(PlanningError, 'field key'):
                build_plan(
                    Path(temp_dir),
                    (desired_file,),
                    (DesiredField(desired_file.path, 'catalog..version', '1.0.0', 'json'),),
                    LockState.empty(),
                )

    def test_rejects_drift_in_managed_field_but_allows_unmanaged_field_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = PurePosixPath('.codex/config.toml')
            original = b'[features]\nhooks = true\n\n[user]\nvalue = "a"\n'
            desired_content = b'[features]\nhooks = true\n\n[user]\nvalue = "b"\n'
            desired = DesiredFile(path, desired_content)
            field = DesiredField(path, 'features.hooks', True, 'toml')
            lock = LockState(
                1,
                None,
                (),
                (ManagedField(path, 'features.hooks', sha256_bytes(b'true')),),
            )

            self.write_target(target, path, original.replace(b'true', b'false'))
            with self.assertRaisesRegex(PlanningError, 'managed field changed'):
                build_plan(target, (desired,), (field,), lock)

            self.write_target(target, path, original.replace(b'"a"', b'"b"'))
            plan = build_plan(target, (desired,), (field,), lock)
            self.assertEqual(plan.changes[0].kind, ChangeKind.UNCHANGED)

    def test_new_field_can_claim_matching_or_missing_value_but_rejects_conflict(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            path = PurePosixPath('.agents/config.json')
            desired = DesiredFile(path, b'{"user": true, "version": 1}\n')
            field = DesiredField(path, 'version', 1, 'json')

            self.write_target(target, path, b'{"user": true}\n')
            missing = build_plan(target, (desired,), (field,), LockState.empty())
            self.assertEqual(missing.changes[0].kind, ChangeKind.UPDATE)

            self.write_target(target, path, b'{"user": true, "version": 1}\n')
            matching = build_plan(target, (desired,), (field,), LockState.empty())
            self.assertEqual(matching.changes[0].kind, ChangeKind.UNCHANGED)

            self.write_target(target, path, b'{"user": true, "version": 2}\n')
            with self.assertRaisesRegex(PlanningError, 'unmanaged field collision'):
                build_plan(target, (desired,), (field,), LockState.empty())


if __name__ == '__main__':
    unittest.main()
