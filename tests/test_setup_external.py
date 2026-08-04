import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup import external  # noqa: E402
from agents_setup.external import ExternalSkillError, snapshot_external_skills  # noqa: E402
from agents_setup.models import ExternalSkillSpec  # noqa: E402


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
        git(work, 'add', '.')
        git(work, 'commit', '--quiet', '-m', 'initial')
        subprocess.run(
            ('git', 'clone', '--quiet', '--bare', str(work), str(origin)),
            check=True,
        )
        git(work, 'remote', 'add', 'origin', str(origin))
        return work, origin

    @staticmethod
    def spec() -> ExternalSkillSpec:
        return ExternalSkillSpec(
            'external-check',
            'example/repository',
            'main',
            PurePosixPath('plugins/example/skills/external-check'),
        )

    def test_each_session_fetches_and_snapshots_the_current_ref(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work, origin = self.make_repository(root)
            with mock.patch.object(external, '_repository_url', return_value=origin.as_uri()):
                first_session = root / 'first'
                first_session.mkdir()
                first = snapshot_external_skills((self.spec(),), session=first_session)
                assert first is not None
                self.assertIn('# External', (first / 'external-check/SKILL.md').read_text())
                self.assertFalse((first_session / 'external-checkouts').exists())

                skill = work / 'plugins/example/skills/external-check/SKILL.md'
                skill.write_text(skill.read_text() + '\nUpdated.\n', encoding='utf-8')
                git(work, 'add', '.')
                git(work, 'commit', '--quiet', '-m', 'update')
                git(work, 'push', '--quiet', 'origin', 'main')

                second_session = root / 'second'
                second_session.mkdir()
                second = snapshot_external_skills((self.spec(),), session=second_session)
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
            with mock.patch.object(external, '_repository_url', return_value=origin.as_uri()):
                with self.assertRaisesRegex(ExternalSkillError, 'name does not match'):
                    snapshot_external_skills((self.spec(),), session=session)
                self.assertFalse((session / 'external-checkouts').exists())


if __name__ == '__main__':
    unittest.main()
