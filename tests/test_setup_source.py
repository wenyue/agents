from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'
sys.path.insert(0, str(SCRIPTS_ROOT))

from agents_setup.source import (  # noqa: E402
    InvalidFetchedSource,
    SourceSnapshot,
    SourceUnavailable,
    fetch_main,
    validate_source,
)
import bootstrap  # noqa: E402


CANONICAL_REPOSITORY = 'https://github.com/wenyue/agents.git'


def run_git(directory: Path, *args: str) -> str:
    completed = subprocess.run(
        ('git', '-C', str(directory), *args),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout


def write_valid_source(root: Path, *, version: str = '0.1.0') -> None:
    (root / '.codex-plugin').mkdir(parents=True)
    (root / '.cursor-plugin').mkdir()
    (root / 'catalog').mkdir()
    entrypoint = root / 'skills' / 'setup-project-agents' / 'scripts' / 'setup_project_agents.py'
    entrypoint.parent.mkdir(parents=True)
    entrypoint.write_text('raise SystemExit(0)\n', encoding='utf-8')
    (root / 'VERSION').write_text(f'{version}\n', encoding='utf-8')
    for relative in ('.codex-plugin/plugin.json', '.cursor-plugin/plugin.json', 'plugin.json'):
        (root / relative).write_text(
            json.dumps({'name': 'agents', 'version': version, 'skills': './skills/'}),
            encoding='utf-8',
        )
    (root / 'catalog' / 'project-assets.json').write_text(
        json.dumps(
            {
                'plugin': {
                    'id': 'agents',
                    'version': version,
                    'repository': CANONICAL_REPOSITORY,
                    'ref': 'main',
                },
                'assets': [
                    {
                        'id': 'setup-project-agents',
                        'kind': 'skill',
                        'source': 'skills/setup-project-agents',
                        'control_plane': True,
                    }
                ],
            }
        ),
        encoding='utf-8',
    )


class SetupSourceTest(unittest.TestCase):
    def make_origin(self, root: Path) -> tuple[Path, Path]:
        origin = root / 'origin.git'
        origin_work = root / 'origin-work'
        subprocess.run(('git', 'init', '--bare', '--quiet', str(origin)), check=True)
        subprocess.run(('git', 'init', '--quiet', str(origin_work)), check=True)
        run_git(origin_work, 'checkout', '--quiet', '-b', 'main')
        run_git(origin_work, 'config', 'user.email', 'test@example.com')
        run_git(origin_work, 'config', 'user.name', 'Test User')
        write_valid_source(origin_work)
        run_git(origin_work, 'add', '.')
        run_git(origin_work, 'commit', '--quiet', '-m', 'initial main')
        run_git(origin_work, 'remote', 'add', 'origin', origin.as_uri())
        run_git(origin_work, 'push', '--quiet', 'origin', 'main')
        return origin, origin_work

    def test_fetch_main_pins_a_valid_main_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, origin_work = self.make_origin(temporary)

            snapshot = fetch_main(origin.as_uri(), work_root=temporary / 'session')

            self.assertEqual(snapshot.commit, run_git(origin_work, 'rev-parse', 'main').strip())
            self.assertEqual(snapshot.root.joinpath('VERSION').read_text().strip(), '0.1.0')
            self.assertFalse(snapshot.root.joinpath('.git').is_symlink())
            self.assertEqual(snapshot.root, temporary / 'session' / 'source')

    def test_fetch_main_uses_the_new_main_commit_for_a_new_session(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, origin_work = self.make_origin(temporary)
            first = fetch_main(origin.as_uri(), work_root=temporary / 'first')
            (origin_work / 'new-main.txt').write_text('new main\n', encoding='utf-8')
            run_git(origin_work, 'add', 'new-main.txt')
            run_git(origin_work, 'commit', '--quiet', '-m', 'advance main')
            run_git(origin_work, 'push', '--quiet', 'origin', 'main')

            second = fetch_main(origin.as_uri(), work_root=temporary / 'second')

            self.assertNotEqual(first.commit, second.commit)
            self.assertEqual(second.commit, run_git(origin_work, 'rev-parse', 'main').strip())
            self.assertEqual(second.root.joinpath('new-main.txt').read_text(), 'new main\n')

    def test_fetched_invalid_catalog_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, origin_work = self.make_origin(temporary)
            catalog_path = origin_work / 'catalog' / 'project-assets.json'
            catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
            catalog['plugin']['ref'] = 'release'
            catalog_path.write_text(json.dumps(catalog), encoding='utf-8')
            run_git(origin_work, 'add', 'catalog/project-assets.json')
            run_git(origin_work, 'commit', '--quiet', '-m', 'invalid catalog')
            run_git(origin_work, 'push', '--quiet', 'origin', 'main')

            with self.assertRaises(InvalidFetchedSource):
                fetch_main(origin.as_uri(), work_root=temporary / 'session')

    def test_validate_source_rejects_symlinked_root_git_and_entrypoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            source = temporary / 'source'
            write_valid_source(source)
            alias = temporary / 'alias'
            alias.symlink_to(source, target_is_directory=True)
            with self.assertRaises(InvalidFetchedSource):
                validate_source(alias)

            source.joinpath('.git').symlink_to(temporary / 'outside', target_is_directory=True)
            with self.assertRaises(InvalidFetchedSource):
                validate_source(source)

            source.joinpath('.git').unlink()
            entrypoint = source / 'skills' / 'setup-project-agents' / 'scripts' / 'setup_project_agents.py'
            entrypoint.unlink()
            entrypoint.symlink_to(temporary / 'outside.py')
            with self.assertRaises(InvalidFetchedSource):
                validate_source(source)

    def test_bootstrap_falls_back_only_when_fetch_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            installed = temporary / 'installed'
            write_valid_source(installed)
            session = temporary / 'session'
            completed = subprocess.CompletedProcess(('child',), 23)
            with (
                mock.patch.object(
                    bootstrap,
                    'fetch_main',
                    side_effect=SourceUnavailable('network unavailable'),
                ),
                mock.patch.object(bootstrap.subprocess, 'run', return_value=completed) as run,
            ):
                result = bootstrap.main(
                    ['prepare', '--session', str(session), '--target', str(temporary / 'target')],
                    installed_root=installed,
                )

            self.assertEqual(result, 23)
            self.assertEqual(
                run.call_args.args[0][-3:],
                ['--source-commit', 'offline', '--no-bootstrap'],
            )

    def test_bootstrap_never_falls_back_after_an_invalid_fetch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            installed = temporary / 'installed'
            write_valid_source(installed)
            with (
                mock.patch.object(
                    bootstrap,
                    'fetch_main',
                    side_effect=InvalidFetchedSource('bad fetched source'),
                ),
                mock.patch.object(bootstrap.subprocess, 'run') as run,
            ):
                result = bootstrap.main(
                    ['prepare', '--session', str(temporary / 'session')],
                    installed_root=installed,
                )

            self.assertEqual(result, 1)
            run.assert_not_called()

    def test_bootstrap_forwards_exact_pinned_child_arguments_and_keeps_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            source = temporary / 'session' / 'source'
            write_valid_source(source)
            snapshot = SourceSnapshot(source, 'a' * 40)
            forwarded = ['prepare', '--session', str(temporary / 'session'), '--target', str(temporary / 'target')]
            with (
                mock.patch.object(bootstrap, 'fetch_main', return_value=snapshot) as fetch,
                mock.patch.object(
                    bootstrap.subprocess,
                    'run',
                    return_value=subprocess.CompletedProcess(('child',), 0),
                ) as run,
            ):
                result = bootstrap.main(forwarded, installed_root=temporary / 'installed')

            self.assertEqual(result, 0)
            fetch.assert_called_once_with(CANONICAL_REPOSITORY, work_root=temporary / 'session')
            self.assertEqual(
                run.call_args.args[0],
                [
                    sys.executable,
                    str(source / 'skills/setup-project-agents/scripts/setup_project_agents.py'),
                    *forwarded,
                    '--source-root', str(source),
                    '--source-commit', 'a' * 40,
                    '--no-bootstrap',
                ],
            )
            self.assertTrue(source.is_dir())

    def test_bootstrap_rejects_non_prepare_and_reserved_user_arguments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            for argv in (
                ['apply', '--session', str(temporary / 'session')],
                ['prepare', '--session', str(temporary / 'session'), '--source-root', 'forged'],
                ['prepare', '--session', str(temporary / 'session'), '--source-commit=forged'],
                ['prepare', '--session', str(temporary / 'session'), '--no-bootstrap'],
            ):
                with self.subTest(argv=argv):
                    with mock.patch.object(bootstrap.subprocess, 'run') as run:
                        self.assertEqual(bootstrap.main(argv, installed_root=temporary / 'installed'), 2)
                    run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
