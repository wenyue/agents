import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup.models import ChangeKind, DesiredField, DesiredFile  # noqa: E402
from agents_setup.planner import PlanningError, build_plan  # noqa: E402


class SetupPlannerTest(unittest.TestCase):
    @staticmethod
    def write(target: Path, relative: str, content: bytes) -> Path:
        path = target.joinpath(*PurePosixPath(relative).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_force_convergence_creates_updates_and_keeps_matching_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, 'update.md', b'user edit\n')
            self.write(target, 'same.md', b'same\n')
            plan = build_plan(
                target,
                (
                    DesiredFile(PurePosixPath('create.md'), b'new\n'),
                    DesiredFile(PurePosixPath('update.md'), b'canonical\n'),
                    DesiredFile(PurePosixPath('same.md'), b'same\n'),
                ),
            )
            self.assertEqual(
                [(item.path.as_posix(), item.kind) for item in plan.changes],
                [
                    ('create.md', ChangeKind.CREATE),
                    ('same.md', ChangeKind.UNCHANGED),
                    ('update.md', ChangeKind.UPDATE),
                ],
            )

    def test_explicit_retired_path_is_deleted_without_a_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, '.agents/lock.json', b'old\n')
            plan = build_plan(
                target,
                (),
                delete_paths=(PurePosixPath('.agents/lock.json'),),
            )
            self.assertEqual(plan.changes[0].kind, ChangeKind.DELETE)

    def test_replace_root_removes_stale_files_and_preserves_other_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.write(target, '.agents/skills/shared/stale.md', b'stale\n')
            self.write(target, '.agents/skills/local/SKILL.md', b'local\n')
            desired = DesiredFile(
                PurePosixPath('.agents/skills/shared/SKILL.md'), b'canonical\n'
            )
            plan = build_plan(
                target,
                (desired,),
                replace_roots=(PurePosixPath('.agents/skills/shared'),),
            )
            self.assertEqual(
                [(item.path.as_posix(), item.kind) for item in plan.changes],
                [
                    ('.agents/skills/shared/SKILL.md', ChangeKind.CREATE),
                    ('.agents/skills/shared/stale.md', ChangeKind.DELETE),
                ],
            )

    def test_desired_fields_require_a_rendered_file_and_safe_unique_keys(self):
        path = PurePosixPath('.codex/config.toml')
        field = DesiredField(path, 'agents.worker.model', 'gpt', 'toml')
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            with self.assertRaisesRegex(PlanningError, 'requires a rendered desired file'):
                build_plan(target, (), (field,))
            desired = DesiredFile(path, b'[agents.worker]\nmodel = "gpt"\n')
            with self.assertRaisesRegex(PlanningError, 'duplicate desired field'):
                build_plan(target, (desired,), (field, field))

    def test_rejects_overlapping_desired_and_retired_paths(self):
        path = PurePosixPath('owned.md')
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(PlanningError, 'overlap'):
                build_plan(
                    Path(temp_dir),
                    (DesiredFile(path, b'new\n'),),
                    delete_paths=(path,),
                )

    def test_rejects_symlinked_target_components_and_managed_roots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root / 'outside'
            outside.mkdir()
            linked = root / 'linked'
            try:
                linked.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest('symlinks are unavailable')
            with self.assertRaisesRegex(PlanningError, 'symlink'):
                build_plan(
                    linked,
                    (DesiredFile(PurePosixPath('owned.md'), b'new\n'),),
                )


if __name__ == '__main__':
    unittest.main()
