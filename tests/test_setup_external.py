import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup import external  # noqa: E402
from agents_setup.external import ExternalSkillError, snapshot_external_skills  # noqa: E402
from agents_setup.external_contract import (  # noqa: E402
    ExternalContractError,
    license_matches,
)
from agents_setup.models import (  # noqa: E402
    ExternalSkillSpec,
    ExternalSourceSpec,
)


def git(directory: Path, *args: str) -> None:
    subprocess.run(
        ('git', '-C', str(directory), *args),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class SetupExternalSkillTest(unittest.TestCase):
    def make_repository(self, root: Path) -> tuple[Path, Path]:
        work = root / 'work'
        origin = root / 'origin.git'
        work.mkdir()
        git(work, 'init', '--quiet', '-b', 'main')
        git(work, 'config', 'user.email', 'test@example.invalid')
        git(work, 'config', 'user.name', 'Setup Test')
        skill = work / 'plugins/example/skills/external-check'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(
            '---\nname: external-check\ndescription: Use for external checks.\n---\n\n# External\n',
            encoding='utf-8',
        )
        (work / 'LICENSE').write_text(
            'MIT License\n\nPermission is hereby granted, free of charge.\n',
            encoding='utf-8',
        )
        git(work, 'add', '.')
        git(work, 'commit', '--quiet', '-m', 'initial')
        subprocess.run(
            ('git', 'clone', '--quiet', '--bare', str(work), str(origin)),
            check=True,
        )
        git(work, 'remote', 'add', 'origin', str(origin))
        return work, origin

    @staticmethod
    def spec(repository: str) -> ExternalSourceSpec:
        return ExternalSourceSpec(
            'example/repository',
            repository,
            'main',
            (ExternalSkillSpec(
                'example/external-check',
                'external-check',
                PurePosixPath('plugins/example/skills/external-check'),
            ),),
        )

    def test_each_session_fetches_and_snapshots_the_current_ref(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work, origin = self.make_repository(root)
            first_session = root / 'first'
            first_session.mkdir()
            first = snapshot_external_skills((self.spec(origin.as_uri()),), session=first_session)
            assert first is not None
            self.assertIn('# External', (first / 'external-check/SKILL.md').read_text())
            self.assertFalse((first_session / 'external-checkouts').exists())
            lock = json.loads((first / 'sources.json').read_text())
            self.assertEqual(lock['sources'][0]['resolved_ref'], 'main')
            self.assertEqual(lock['sources'][0]['ref_kind'], 'branch')
            license_item = lock['sources'][0]['license']
            self.assertEqual(license_item['spdx'], 'MIT')
            self.assertEqual(license_item['path'], 'LICENSE')
            self.assertRegex(license_item['sha256'], r'^[0-9a-f]{64}$')

            skill = work / 'plugins/example/skills/external-check/SKILL.md'
            skill.write_text(skill.read_text() + '\nUpdated.\n', encoding='utf-8')
            git(work, 'add', '.')
            git(work, 'commit', '--quiet', '-m', 'update')
            git(work, 'push', '--quiet', 'origin', 'main')

            second_session = root / 'second'
            second_session.mkdir()
            second = snapshot_external_skills((self.spec(origin.as_uri()),), session=second_session)
            assert second is not None
            self.assertIn('Updated.', (second / 'external-check/SKILL.md').read_text())
            self.assertFalse((second_session / 'external-checkouts').exists())

    def test_rejects_a_skill_whose_frontmatter_name_does_not_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work, origin = self.make_repository(root)
            skill = work / 'plugins/example/skills/external-check/SKILL.md'
            skill.write_text(skill.read_text().replace('external-check', 'wrong-name'))
            git(work, 'add', '.')
            git(work, 'commit', '--quiet', '-m', 'wrong name')
            git(work, 'push', '--quiet', 'origin', 'main')
            session = root / 'session'
            session.mkdir()
            with self.assertRaisesRegex(ExternalSkillError, 'name does not match'):
                snapshot_external_skills((self.spec(origin.as_uri()),), session=session)
            self.assertFalse((session / 'external-checkouts').exists())

    def test_recognizes_standard_spdx_license_text(self):
        self.assertTrue(license_matches(
            'Apache-2.0',
            b'Apache License\nVersion 2.0, January 2004\n',
        ))
        self.assertFalse(license_matches('Apache-2.0', b'not a license'))
        with self.assertRaisesRegex(ExternalContractError, 'unsupported SPDX'):
            license_matches('GPL-3.0-only', b'GPL-3.0-only')

    def test_discovers_a_supported_copying_file_without_project_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / 'COPYING').write_text(
                'Apache License\nVersion 2.0, January 2004\n',
                encoding='utf-8',
            )
            discovered = external.discover_license(root, 'external source license')
            self.assertEqual(discovered.spdx, 'Apache-2.0')
            self.assertEqual(discovered.path, PurePosixPath('COPYING'))

    def test_rejects_a_source_without_a_recognized_root_license(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work, origin = self.make_repository(root)
            (work / 'LICENSE').write_text('A private license.\n', encoding='utf-8')
            git(work, 'add', '.')
            git(work, 'commit', '--quiet', '-m', 'unrecognized license')
            git(work, 'push', '--quiet', 'origin', 'main')
            session = root / 'session'
            session.mkdir()
            with self.assertRaisesRegex(ExternalSkillError, 'not found or recognized'):
                snapshot_external_skills((self.spec(origin.as_uri()),), session=session)
            self.assertFalse((session / 'external-checkouts').exists())

    def test_rejects_conflicting_recognized_root_licenses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work, origin = self.make_repository(root)
            (work / 'COPYING').write_text(
                'Apache License\nVersion 2.0, January 2004\n',
                encoding='utf-8',
            )
            git(work, 'add', '.')
            git(work, 'commit', '--quiet', '-m', 'ambiguous licenses')
            git(work, 'push', '--quiet', 'origin', 'main')
            session = root / 'session'
            session.mkdir()

            with self.assertRaisesRegex(ExternalSkillError, 'license.*ambiguous'):
                snapshot_external_skills((self.spec(origin.as_uri()),), session=session)

            self.assertFalse((session / 'external-checkouts').exists())

    def test_rejects_a_symlinked_selected_path_ancestor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work, origin = self.make_repository(root)
            (work / 'plugins/linked').symlink_to('example', target_is_directory=True)
            git(work, 'add', '.')
            git(work, 'commit', '--quiet', '-m', 'linked path')
            git(work, 'push', '--quiet', 'origin', 'main')
            spec = ExternalSourceSpec(
                'example/repository', origin.as_uri(), 'main',
                (ExternalSkillSpec(
                    'example/external-check', 'external-check',
                    PurePosixPath('plugins/linked/skills/external-check'),
                ),),
            )
            session = root / 'session'
            session.mkdir()
            with self.assertRaisesRegex(ExternalSkillError, 'contains a symlink'):
                snapshot_external_skills((spec,), session=session)

    def test_rejects_a_tag_that_moved_since_the_existing_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work, origin = self.make_repository(root)
            git(work, 'tag', 'v1')
            git(work, 'push', '--quiet', 'origin', 'refs/tags/v1')
            tagged = ExternalSourceSpec(
                'example/repository', origin.as_uri(), 'v1',
                (ExternalSkillSpec(
                    'example/external-check', 'external-check',
                    PurePosixPath('plugins/example/skills/external-check'),
                ),),
            )
            first_session = root / 'first'
            first_session.mkdir()
            first = snapshot_external_skills((tagged,), session=first_session)
            assert first is not None
            source_metadata = json.loads((first / 'sources.json').read_text())
            for source in source_metadata['sources']:
                for skill_item in source['skills']:
                    skill_item.pop('files')
            existing_manifest = first_session / 'smartkit.lock.json'
            existing_manifest.write_text(json.dumps({
                'version': 1,
                'sources': source_metadata['sources'],
                'assets': [{
                    'kind': 'tree',
                    'role': 'skill',
                    'path': '.agents/skills/external-check',
                    'digest': 'b' * 64,
                    'source': 'example/repository',
                    'source_path': 'plugins/example/skills/external-check',
                }],
                'seeded': [],
            }), encoding='utf-8')

            skill = work / 'plugins/example/skills/external-check/SKILL.md'
            skill.write_text(skill.read_text() + '\nMoved tag.\n', encoding='utf-8')
            git(work, 'add', '.')
            git(work, 'commit', '--quiet', '-m', 'move tag')
            git(work, 'tag', '--force', 'v1')
            git(work, 'push', '--quiet', '--force', 'origin', 'refs/tags/v1')

            second_session = root / 'second'
            second_session.mkdir()
            with self.assertRaisesRegex(ExternalSkillError, 'tag moved'):
                snapshot_external_skills(
                    (tagged,),
                    session=second_session,
                    existing_manifest=existing_manifest,
                )


if __name__ == '__main__':
    unittest.main()
