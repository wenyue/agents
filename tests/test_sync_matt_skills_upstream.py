import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'sync_matt_skills_upstream.py'


def load_module():
    spec = importlib.util.spec_from_file_location('sync_matt_skills_upstream', SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError('cannot load sync_matt_skills_upstream')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_skill(root: Path, source: str, name: str, *, marker: str = 'current') -> None:
    skill_root = root / source
    (skill_root / 'agents').mkdir(parents=True)
    (skill_root / 'SKILL.md').write_text(
        f'---\nname: {name}\ndescription: Test skill\n---\n\n# {name}\n\n{marker}\n',
        encoding='utf-8',
    )
    (skill_root / 'agents' / 'openai.yaml').write_text(
        f'name: {name}\n', encoding='utf-8'
    )


def write_upstream(
    root: Path,
    *,
    version: str = '1.2.4',
    skills: tuple[tuple[str, str], ...] = (
        ('skills/engineering/ask-matt', 'ask-matt'),
        ('skills/engineering/tdd', 'tdd'),
    ),
) -> None:
    manifest = {
        'name': 'mattpocock-skills',
        'version': version,
        'license': 'MIT',
        'skills': [f'./{source}' for source, _ in skills],
    }
    manifest_path = root / '.claude-plugin' / 'plugin.json'
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    (root / 'LICENSE').write_text('MIT fixture\n', encoding='utf-8')
    for source, name in skills:
        write_skill(root, source, name)


class MattSkillsUpstreamSyncTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_release_must_be_a_stable_semver(self):
        invalid = (
            {'tag_name': 'v1.2.4', 'draft': True, 'prerelease': False},
            {'tag_name': 'v1.2.4', 'draft': False, 'prerelease': True},
            {'tag_name': 'latest', 'draft': False, 'prerelease': False},
            {'tag_name': 'v1.2.4-beta.1', 'draft': False, 'prerelease': False},
        )
        for release in invalid:
            with self.subTest(release=release):
                with self.assertRaises(self.module.SyncError):
                    self.module.validate_release(release)

        self.assertEqual(
            self.module.validate_release(
                {'tag_name': 'v1.2.4', 'draft': False, 'prerelease': False}
            ),
            'v1.2.4',
        )

    def test_upstream_manifest_and_skill_trees_are_strictly_validated(self):
        cases = (
            ('wrong-name', {'name': 'other'}, self.module.SyncError),
            ('wrong-version', {'version': '9.9.9'}, self.module.SyncError),
            ('wrong-license', {'license': 'Apache-2.0'}, self.module.SyncError),
            ('path-escape', {'skills': ['../outside']}, self.module.SyncError),
            (
                'duplicate-target',
                {
                    'skills': [
                        './skills/engineering/ask-matt',
                        './skills/productivity/ask-matt',
                    ]
                },
                self.module.SyncError,
            ),
            (
                'reserved-target',
                {'skills': ['./skills/engineering/setup-project-agents']},
                self.module.SyncError,
            ),
        )
        for label, overrides, error_type in cases:
            with self.subTest(case=label):
                checkout = self.root / label
                write_upstream(checkout)
                manifest_path = checkout / '.claude-plugin' / 'plugin.json'
                manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                manifest.update(overrides)
                manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                with self.assertRaises(error_type):
                    self.module.load_upstream(
                        checkout,
                        tag='v1.2.4',
                        commit='a' * 40,
                    )

    def test_upstream_rejects_missing_or_mismatched_skill_metadata(self):
        checkout = self.root / 'missing'
        write_upstream(checkout)
        (checkout / 'skills/engineering/ask-matt/SKILL.md').unlink()
        with self.assertRaises(self.module.SyncError):
            self.module.load_upstream(checkout, tag='v1.2.4', commit='a' * 40)

        checkout = self.root / 'mismatch'
        write_upstream(checkout)
        (checkout / 'skills/engineering/ask-matt/SKILL.md').write_text(
            '---\nname: wrong\ndescription: Wrong\n---\n', encoding='utf-8'
        )
        with self.assertRaises(self.module.SyncError):
            self.module.load_upstream(checkout, tag='v1.2.4', commit='a' * 40)

    def test_upstream_rejects_links(self):
        checkout = self.root / 'links'
        write_upstream(checkout)
        link = checkout / 'skills/engineering/ask-matt/link.md'
        try:
            link.symlink_to(checkout / 'LICENSE')
        except OSError as error:
            self.skipTest(f'symlinks unavailable: {error}')
        with self.assertRaises(self.module.SyncError):
            self.module.load_upstream(checkout, tag='v1.2.4', commit='a' * 40)

    def test_check_reports_release_and_local_content_drift_without_writes(self):
        checkout = self.root / 'upstream'
        project = self.root / 'project'
        write_upstream(checkout)
        (project / 'skills/setup-project-agents').mkdir(parents=True)
        upstream = self.module.load_upstream(
            checkout, tag='v1.2.4', commit='a' * 40
        )

        before = tuple(sorted(path.relative_to(project) for path in project.rglob('*')))
        report = self.module.check_repository(project, upstream)
        after = tuple(sorted(path.relative_to(project) for path in project.rglob('*')))

        self.assertEqual(before, after)
        self.assertFalse(report.clean)
        self.assertIn('vendor/mattpocock-skills.lock.json', report.drift_paths)

        self.module.update_repository(project, upstream)
        self.assertTrue(self.module.check_repository(project, upstream).clean)

        skill = project / 'skills/ask-matt/SKILL.md'
        skill.write_text(skill.read_text(encoding='utf-8') + '\ndrift\n', encoding='utf-8')
        report = self.module.check_repository(project, upstream)
        self.assertFalse(report.clean)
        self.assertIn('skills/ask-matt/SKILL.md', report.drift_paths)

    def test_update_replaces_only_lock_owned_skills_and_preserves_other_content(self):
        first_checkout = self.root / 'upstream-first'
        second_checkout = self.root / 'upstream-second'
        project = self.root / 'project'
        write_upstream(first_checkout)
        write_upstream(
            second_checkout,
            version='1.2.5',
            skills=(('skills/engineering/tdd', 'tdd'),),
        )
        write_skill(project, 'skills/setup-project-agents', 'setup-project-agents')
        write_skill(project, 'skills/team-owned', 'team-owned')

        first = self.module.load_upstream(
            first_checkout, tag='v1.2.4', commit='a' * 40
        )
        second = self.module.load_upstream(
            second_checkout, tag='v1.2.5', commit='b' * 40
        )
        self.module.update_repository(project, first)
        preserved = (project / 'skills/team-owned/SKILL.md').read_bytes()
        control_plane = (project / 'skills/setup-project-agents/SKILL.md').read_bytes()

        result = self.module.update_repository(project, second)

        self.assertFalse((project / 'skills/ask-matt').exists())
        self.assertTrue((project / 'skills/tdd').is_dir())
        self.assertEqual((project / 'skills/team-owned/SKILL.md').read_bytes(), preserved)
        self.assertEqual(
            (project / 'skills/setup-project-agents/SKILL.md').read_bytes(),
            control_plane,
        )
        lock = json.loads(
            (project / 'vendor/mattpocock-skills.lock.json').read_text(encoding='utf-8')
        )
        self.assertEqual(lock['tag'], 'v1.2.5')
        self.assertEqual(lock['commit'], 'b' * 40)
        self.assertEqual({item['name'] for item in lock['skills']}, {'tdd'})
        self.assertIn('skills/ask-matt', result.removed_paths)

    def test_failed_replacement_restores_vendor_lock_license_and_skills(self):
        first_checkout = self.root / 'upstream-first'
        second_checkout = self.root / 'upstream-second'
        project = self.root / 'project'
        write_upstream(first_checkout)
        write_upstream(second_checkout, version='1.2.5')
        first = self.module.load_upstream(
            first_checkout, tag='v1.2.4', commit='a' * 40
        )
        second = self.module.load_upstream(
            second_checkout, tag='v1.2.5', commit='b' * 40
        )
        self.module.update_repository(project, first)
        before = {
            path.relative_to(project).as_posix(): path.read_bytes()
            for path in project.rglob('*')
            if path.is_file()
        }
        calls = 0

        def fail_after_first_change(staged: Path | None, target: Path) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected replacement failure')
            self.module.replace_path(staged, target)

        with self.assertRaises(self.module.SyncError):
            self.module.update_repository(project, second, replace=fail_after_first_change)

        after = {
            path.relative_to(project).as_posix(): path.read_bytes()
            for path in project.rglob('*')
            if path.is_file()
        }
        self.assertEqual(after, before)
        self.assertFalse(any(project.parent.glob('.matt-skills-sync-*')))


if __name__ == '__main__':
    unittest.main()
