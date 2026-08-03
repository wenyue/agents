from __future__ import annotations

import json
import os
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
from agents_setup import source as source_module  # noqa: E402
import bootstrap  # noqa: E402
import setup_project_agents  # noqa: E402


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
    manifests = {
        '.codex-plugin/plugin.json': {
            'name': 'agents', 'version': version, 'skills': './skills/',
        },
        '.cursor-plugin/plugin.json': {
            'name': 'agents', 'version': version, 'skills': './skills/',
            'rules': './rules/', 'agents': './agents/',
        },
        'plugin.json': {
            'name': 'agents', 'version': version, 'skills': './skills/',
            'agents': './agents/',
        },
    }
    for relative, document in manifests.items():
        (root / relative).write_text(json.dumps(document), encoding='utf-8')
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

    def test_validate_source_accepts_the_actual_plugin_root(self):
        self.assertEqual(validate_source(REPO_ROOT), REPO_ROOT)

    def test_validate_source_requires_exact_platform_manifest_roots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cases = (
                ('.codex-plugin/plugin.json', {'rules': './rules/'}),
                ('.cursor-plugin/plugin.json', {'rules': '../rules/'}),
                ('plugin.json', {'agents': '../agents/'}),
                ('plugin.json', {'agents': None}),
            )
            for index, (relative, updates) in enumerate(cases):
                with self.subTest(relative=relative, updates=updates):
                    source = Path(temp_dir) / f'source-{index}'
                    write_valid_source(source)
                    path = source / relative
                    document = json.loads(path.read_text(encoding='utf-8'))
                    document.update(updates)
                    path.write_text(json.dumps(document), encoding='utf-8')
                    with self.assertRaises(InvalidFetchedSource):
                        validate_source(source)

    def test_fetch_main_cleans_only_its_new_checkout_after_fetch_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / 'session'
            workspace.mkdir()
            sentinel = workspace / 'request.json'
            sentinel.write_text('{}\n', encoding='utf-8')
            with self.assertRaises(SourceUnavailable):
                fetch_main((Path(temp_dir) / 'missing-origin.git').as_uri(), work_root=workspace)

            self.assertTrue(workspace.is_dir())
            self.assertEqual(sentinel.read_text(encoding='utf-8'), '{}\n')
            self.assertFalse((workspace / 'source').exists())
            origin, _ = self.make_origin(Path(temp_dir))
            self.assertEqual(
                fetch_main(origin.as_uri(), work_root=workspace).root,
                workspace / 'source',
            )

    def test_fetch_main_rejects_a_missing_session_below_a_symlinked_ancestor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            outside = temporary / 'outside'
            outside.mkdir()
            ancestor = temporary / 'ancestor'
            ancestor.symlink_to(outside, target_is_directory=True)

            with self.assertRaises(InvalidFetchedSource):
                fetch_main('file:///origin.git', work_root=ancestor / 'session')

            self.assertFalse((outside / 'session').exists())

    def test_git_commands_receive_a_sanitized_environment(self):
        with mock.patch.dict(
            os.environ,
            {'GIT_DIR': '/attacker/git', 'GIT_WORK_TREE': '/attacker/tree', 'GIT_INDEX_FILE': '/attacker/index'},
            clear=False,
        ), mock.patch.object(
            source_module.subprocess,
            'run',
            return_value=subprocess.CompletedProcess(('git', 'version'), 0),
        ) as run:
            source_module._run_git(('git', 'version'), failure=SourceUnavailable)

        environment = run.call_args.kwargs['env']
        self.assertNotIn('GIT_DIR', environment)
        self.assertNotIn('GIT_WORK_TREE', environment)
        self.assertNotIn('GIT_INDEX_FILE', environment)
        self.assertEqual(environment['GIT_TERMINAL_PROMPT'], '0')
        self.assertEqual(environment['GIT_CONFIG_NOSYSTEM'], '1')
        self.assertEqual(environment['GIT_CONFIG_GLOBAL'], os.devnull)

    def test_cleanup_error_preserves_the_original_source_unavailable_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(
                source_module,
                '_safe_remove_staging',
                side_effect=OSError('cleanup failed'),
            ):
                with self.assertRaises(SourceUnavailable):
                    fetch_main(
                        (Path(temp_dir) / 'missing-origin.git').as_uri(),
                        work_root=Path(temp_dir) / 'session',
                    )

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX directory descriptors')
    def test_cleanup_does_not_delete_a_replacement_after_identity_check(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / 'session'
            workspace.mkdir()
            workspace_state = source_module._open_safe_workspace(workspace)
            try:
                staging = source_module._create_staging(workspace_state)
                try:
                    source = workspace / 'source'
                    source.mkdir()
                    (source / 'sentinel').write_text('keep\n', encoding='utf-8')
                    source_module._safe_remove_staging(workspace_state, staging)
                finally:
                    staging.close()
            finally:
                workspace_state.close()

            self.assertEqual((workspace / 'source' / 'sentinel').read_text(encoding='utf-8'), 'keep\n')
            self.assertTrue(workspace.is_dir())

    def test_fetch_main_never_overwrites_a_preexisting_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, _ = self.make_origin(temporary)
            workspace = temporary / 'session'
            source = workspace / 'source'
            source.mkdir(parents=True)
            marker = source / 'keep'
            marker.write_text('preserve\n', encoding='utf-8')
            with self.assertRaises(InvalidFetchedSource):
                fetch_main(origin.as_uri(), work_root=workspace)
            self.assertEqual(marker.read_text(encoding='utf-8'), 'preserve\n')

    def test_fetch_main_no_replace_publish_leaves_a_source_symlink_target_untouched(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, _ = self.make_origin(temporary)
            workspace = temporary / 'session'
            workspace.mkdir()
            outside = temporary / 'outside'
            outside.mkdir()
            marker = outside / 'keep'
            marker.write_text('preserve\n', encoding='utf-8')
            (workspace / 'source').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(InvalidFetchedSource):
                fetch_main(origin.as_uri(), work_root=workspace)
            self.assertEqual(marker.read_text(encoding='utf-8'), 'preserve\n')

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX staging protocol')
    def test_git_uses_the_held_staging_fd_path_and_passes_that_fd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / 'session'
            commands = [
                subprocess.CompletedProcess(('git', 'init'), 0),
                subprocess.CompletedProcess(('git', 'remote'), 1),
            ]
            with mock.patch.object(source_module.subprocess, 'run', side_effect=commands) as run:
                with self.assertRaises(SourceUnavailable):
                    fetch_main('file:///origin.git', work_root=workspace)

            argv = run.call_args_list[0].args[0]
            self.assertRegex(argv[-1], r'^/proc/self/fd/[0-9]+$')
            self.assertEqual(run.call_args_list[0].kwargs['pass_fds'], (int(argv[-1].rsplit('/', 1)[1]),))
            self.assertFalse((workspace / 'source').exists())

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX staging protocol')
    def test_workspace_namespace_replacement_never_redirects_git_into_an_external_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            workspace = temporary / 'session'
            external = temporary / 'external'
            external.mkdir()
            moved = temporary / 'moved-session'

            def replace_namespace() -> None:
                workspace.rename(moved)
                workspace.symlink_to(external, target_is_directory=True)

            with mock.patch.object(source_module, '_before_first_git', replace_namespace):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main('file:///origin.git', work_root=workspace)

            self.assertFalse(any(external.iterdir()))

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX staging protocol')
    def test_publish_undoes_source_when_the_post_publish_namespace_guard_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, _ = self.make_origin(temporary)
            workspace = temporary / 'session'
            external = temporary / 'external'
            external.mkdir()
            moved = temporary / 'moved-session'

            def replace_namespace_after_rename() -> None:
                workspace.rename(moved)
                workspace.symlink_to(external, target_is_directory=True)

            with mock.patch.object(
                source_module,
                '_after_publish_rename',
                replace_namespace_after_rename,
            ):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main(origin.as_uri(), work_root=workspace)

            self.assertFalse((workspace / 'source').exists())
            self.assertFalse((moved / 'source').exists())
            self.assertFalse(any(external.iterdir()))

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX staging protocol')
    def test_publish_reverts_to_the_third_party_staging_inode_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, _ = self.make_origin(temporary)
            workspace = temporary / 'session'
            staging_name: list[str] = []

            def replace_staging(workspace_state, name: str) -> None:
                staging_name.append(name)
                os.rename(name, f'{name}-original', src_dir_fd=workspace_state.fd, dst_dir_fd=workspace_state.fd)
                os.mkdir(name, dir_fd=workspace_state.fd)
                sentinel = workspace / name / 'sentinel'
                sentinel.write_text('keep\n', encoding='utf-8')

            with mock.patch.object(source_module, '_before_publish_rename', replace_staging):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main(origin.as_uri(), work_root=workspace)

            self.assertFalse((workspace / 'source').exists())
            self.assertEqual((workspace / staging_name[0] / 'sentinel').read_text(encoding='utf-8'), 'keep\n')

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX staging protocol')
    def test_publish_undoes_an_rename_wrapper_exception_after_the_syscall(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, _ = self.make_origin(temporary)
            workspace = temporary / 'session'
            rename = source_module._rename_noreplace

            def rename_then_raise(fd: int, old: str, new: str, *, on_success=None) -> None:
                rename(fd, old, new, on_success=on_success)
                raise RuntimeError('rename wrapper failed after syscall')

            with mock.patch.object(source_module, '_rename_noreplace', rename_then_raise):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main(origin.as_uri(), work_root=workspace)

            self.assertFalse((workspace / 'source').exists())

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX staging protocol')
    def test_failed_publish_never_moves_an_independent_concurrent_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, _ = self.make_origin(temporary)
            workspace = temporary / 'session'
            staging_name: list[str] = []

            def replace_staging_and_create_source(workspace_state, name: str) -> None:
                staging_name.append(name)
                os.rename(
                    name,
                    f'{name}-moved',
                    src_dir_fd=workspace_state.fd,
                    dst_dir_fd=workspace_state.fd,
                )
                os.mkdir('source', dir_fd=workspace_state.fd)
                (workspace / 'source' / 'sentinel').write_text('independent\n', encoding='utf-8')

            with mock.patch.object(
                source_module,
                '_before_publish_rename',
                replace_staging_and_create_source,
            ):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main(origin.as_uri(), work_root=workspace)

            self.assertEqual(
                (workspace / 'source' / 'sentinel').read_text(encoding='utf-8'),
                'independent\n',
            )
            self.assertFalse((workspace / staging_name[0]).exists())

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX staging protocol')
    def test_post_publish_source_replacement_is_not_undone_over_the_sentinel(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            origin, _ = self.make_origin(temporary)
            workspace = temporary / 'session'
            moved = temporary / 'published-source-moved'

            def replace_published_source() -> None:
                (workspace / 'source').rename(moved)
                (workspace / 'source').mkdir()
                (workspace / 'source' / 'sentinel').write_text('independent\n', encoding='utf-8')

            with mock.patch.object(source_module, '_after_publish_rename', replace_published_source):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main(origin.as_uri(), work_root=workspace)

            self.assertEqual(
                (workspace / 'source' / 'sentinel').read_text(encoding='utf-8'),
                'independent\n',
            )
            self.assertTrue(moved.is_dir())

    def test_unavailable_secure_staging_primitives_do_not_mutate_or_run_git(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / 'session'
            with (
                mock.patch.object(source_module, '_secure_fetch_supported', return_value=False),
                mock.patch.object(source_module.os, 'mkdir') as mkdir,
                mock.patch.object(source_module.subprocess, 'run') as run,
            ):
                with self.assertRaises(SourceUnavailable):
                    fetch_main('file:///origin.git', work_root=workspace)
            mkdir.assert_not_called()
            run.assert_not_called()

    def test_fetch_main_classifies_post_fetch_git_failures_as_invalid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / 'session'
            checkout_failure = [
                subprocess.CompletedProcess(('git', 'init'), 0),
                subprocess.CompletedProcess(('git', 'remote'), 0),
                subprocess.CompletedProcess(('git', 'fetch'), 0),
                subprocess.CompletedProcess(('git', 'checkout'), 1),
            ]
            with mock.patch('agents_setup.source.subprocess.run', side_effect=checkout_failure):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main('file:///origin.git', work_root=workspace)
            self.assertFalse((workspace / 'source').exists())

            rev_parse_failure = [
                subprocess.CompletedProcess(('git', 'init'), 0),
                subprocess.CompletedProcess(('git', 'remote'), 0),
                subprocess.CompletedProcess(('git', 'fetch'), 0),
                subprocess.CompletedProcess(('git', 'checkout'), 0),
                subprocess.CompletedProcess(('git', 'rev-parse'), 1),
            ]
            with mock.patch('agents_setup.source.subprocess.run', side_effect=rev_parse_failure):
                with self.assertRaises(InvalidFetchedSource):
                    fetch_main('file:///origin.git', work_root=workspace)
            self.assertFalse((workspace / 'source').exists())

    def test_fetch_main_rejects_unsafe_repository_argv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for repository in ('-c', 'https://example.invalid/\x00repo', 'https://example.invalid/\nrepo'):
                with self.subTest(repository=repository):
                    with self.assertRaises(InvalidFetchedSource):
                        fetch_main(repository, work_root=Path(temp_dir) / repository.replace('/', '_').replace('\x00', 'nul').replace('\n', 'nl'))

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
                    return_value=subprocess.CompletedProcess(('child',), 23),
                ) as run,
            ):
                result = bootstrap.main(forwarded, installed_root=temporary / 'installed')

            self.assertEqual(result, 23)
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

    def test_bootstrap_uses_the_real_installed_plugin_root_for_offline_handoff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            session = temporary / 'session'
            with (
                mock.patch.object(
                    bootstrap,
                    'fetch_main',
                    side_effect=SourceUnavailable('network unavailable'),
                ),
                mock.patch.object(
                    bootstrap.subprocess,
                    'run',
                    return_value=subprocess.CompletedProcess(('child',), 23),
                ) as run,
            ):
                result = bootstrap.main(['prepare', '--session', str(session)])

            self.assertEqual(result, 23)
            self.assertEqual(
                run.call_args.args[0][1],
                str(REPO_ROOT / 'skills/setup-project-agents/scripts/setup_project_agents.py'),
            )

    def test_bootstrap_rejects_non_prepare_and_reserved_user_arguments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            for argv in (
                ['apply', '--session', str(temporary / 'session')],
                ['prepare', '--session', str(temporary / 'session'), '--source-root', 'forged'],
                ['prepare', '--session', str(temporary / 'session'), '--source-commit=forged'],
                ['prepare', '--session', str(temporary / 'session'), '--no-bootstrap'],
                ['prepare', '--session', str(temporary / 'session'), '--no-bootstrap=forged'],
            ):
                with self.subTest(argv=argv):
                    with mock.patch.object(bootstrap.subprocess, 'run') as run:
                        self.assertEqual(bootstrap.main(argv, installed_root=temporary / 'installed'), 2)
                    run.assert_not_called()

    def test_entrypoint_normalizes_the_offline_commit_only_at_cli_boundary(self):
        self.assertIsNone(setup_project_agents.normalize_source_commit('offline'))
        self.assertEqual(setup_project_agents.normalize_source_commit('a' * 40), 'a' * 40)
        with self.assertRaises(ValueError):
            setup_project_agents.normalize_source_commit('main')

    def test_entrypoint_validates_the_pinned_protocol_without_claiming_orchestration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = setup_project_agents.main(
                [
                    'prepare', '--target', temp_dir, '--session', temp_dir,
                    '--source-root', str(REPO_ROOT), '--source-commit', 'offline', '--no-bootstrap',
                ]
            )
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
