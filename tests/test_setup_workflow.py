from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path, PurePosixPath
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'
sys.path.insert(0, str(SCRIPTS_ROOT))

import bootstrap  # noqa: E402
import workflow  # noqa: E402


POWERSHELL = shutil.which('pwsh') or shutil.which('powershell')


def run_git(directory: Path, *args: str) -> None:
    subprocess.run(
        ('git', '-C', str(directory), *args),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class SetupWorkflowTest(unittest.TestCase):
    def test_powershell_wrapper_keeps_minimum_version_exit_reachable(self):
        wrapper = (
            SCRIPTS_ROOT / 'setup_project_agents.ps1'
        ).read_text(encoding='utf-8')

        self.assertIn(
            "[Console]::Error.WriteLine('Python 3.10 or newer is required.')",
            wrapper,
        )
        self.assertIn("exit 2", wrapper)

    @unittest.skipUnless(
        os.name == 'posix' and shutil.which('dirname') and shutil.which('tr'),
        'requires POSIX shell tools',
    )
    def test_shell_wrapper_reports_minimum_when_uv_cannot_find_python(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            executable_root = Path(temp_dir)
            for name in ('dirname', 'tr'):
                executable = shutil.which(name)
                self.assertIsNotNone(executable)
                (executable_root / name).symlink_to(executable)
            for name in ('python3', 'python', 'uv'):
                incompatible_command = executable_root / name
                incompatible_command.write_text(
                    '#!/bin/sh\nexit 1\n', encoding='utf-8'
                )
                incompatible_command.chmod(0o755)
            environment = dict(os.environ)
            environment['PATH'] = str(executable_root)

            completed = subprocess.run(
                (
                    '/bin/sh',
                    str(SCRIPTS_ROOT / 'setup_project_agents.sh'),
                    '--help',
                ),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn(
                'ERROR: Python 3.10 or newer is required.', completed.stderr
            )

    @unittest.skipUnless(POWERSHELL, 'requires PowerShell')
    def test_powershell_wrapper_reports_minimum_when_uv_cannot_find_python(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            executable_root = Path(temp_dir)
            for name in ('python3', 'python', 'uv'):
                if os.name == 'nt':
                    incompatible_command = executable_root / f'{name}.cmd'
                    incompatible_command.write_text(
                        '@exit /b 1\r\n', encoding='utf-8'
                    )
                else:
                    incompatible_command = executable_root / name
                    incompatible_command.write_text(
                        '#!/bin/sh\nexit 1\n', encoding='utf-8'
                    )
                    incompatible_command.chmod(0o755)
            environment = dict(os.environ)
            environment['PATH'] = str(executable_root)

            completed = subprocess.run(
                (
                    str(POWERSHELL),
                    '-NoProfile',
                    '-File',
                    str(SCRIPTS_ROOT / 'setup_project_agents.ps1'),
                    '--help',
                ),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn(
                'Python 3.10 or newer is required.',
                completed.stdout + completed.stderr,
            )

    @unittest.skipUnless(
        os.name == 'posix'
        and shutil.which('python3.10')
        and shutil.which('dirname')
        and shutil.which('tr'),
        'requires Python 3.10 and POSIX shell tools',
    )
    def test_shell_wrapper_runs_workflow_with_python_310(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            executable_root = Path(temp_dir)
            for name in ('python3', 'dirname', 'tr'):
                executable = shutil.which('python3.10' if name == 'python3' else name)
                self.assertIsNotNone(executable)
                (executable_root / name).symlink_to(executable)
            for name in ('python', 'uv'):
                incompatible_command = executable_root / name
                incompatible_command.write_text(
                    '#!/bin/sh\nexit 1\n', encoding='utf-8'
                )
                incompatible_command.chmod(0o755)
            environment = dict(os.environ)
            environment['PATH'] = str(executable_root)

            completed = subprocess.run(
                (
                    '/bin/sh',
                    str(SCRIPTS_ROOT / 'setup_project_agents.sh'),
                    '--help',
                ),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('usage:', completed.stdout)

    @unittest.skipUnless(os.name == 'posix', 'requires a POSIX shell')
    def test_shell_wrapper_selects_a_compatible_versioned_python(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            executable_root = Path(temp_dir)
            for name in ('python3', 'python', 'uv'):
                incompatible_command = executable_root / name
                incompatible_command.write_text(
                    '#!/bin/sh\nexit 1\n', encoding='utf-8'
                )
                incompatible_command.chmod(0o755)
            compatible_python = executable_root / (
                f'python{sys.version_info.major}.{sys.version_info.minor}'
            )
            compatible_python.symlink_to(sys.executable)
            environment = dict(os.environ)
            environment['PATH'] = (
                f'{executable_root}{os.pathsep}{environment.get("PATH", "")}'
            )

            completed = subprocess.run(
                (
                    'sh',
                    str(SCRIPTS_ROOT / 'setup_project_agents.sh'),
                    '--help',
                ),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('usage:', completed.stdout)

    @staticmethod
    def make_origin(root: Path) -> Path:
        origin = root / 'origin.git'
        work = root / 'origin-work'
        shutil.copytree(
            REPO_ROOT,
            work,
            ignore=shutil.ignore_patterns('.git', '.superpowers', '__pycache__', '*.pyc'),
        )
        subprocess.run(('git', 'init', '--bare', '--quiet', str(origin)), check=True)
        subprocess.run(('git', '-C', str(work), 'init', '--quiet'), check=True)
        run_git(work, 'checkout', '--quiet', '-b', 'main')
        run_git(work, 'config', 'user.email', 'test@example.invalid')
        run_git(work, 'config', 'user.name', 'Setup Test')
        run_git(work, 'add', '.')
        run_git(work, 'commit', '--quiet', '-m', 'workflow source')
        run_git(work, 'remote', 'add', 'origin', origin.as_uri())
        run_git(work, 'push', '--quiet', 'origin', 'main')
        return origin

    @staticmethod
    def write_generated_outputs(session: Path) -> None:
        for relative in (
            '.agents/rules/20-project-tools.md',
            '.agents/rules/21-project-rules.md',
            '.agents/rules/22-project-structure.md',
            '.agents/skills/change-set-verification/SKILL.md',
            '.agents/skills/worktree-environment-setup/SKILL.md',
        ):
            path = session / 'generated' / PurePosixPath(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'# generated {path.name}\n', encoding='utf-8')

    @staticmethod
    def fill_models(session: Path) -> None:
        models = json.loads((session / 'models.json').read_text(encoding='utf-8'))
        for platform in models['agents']['change-set-verifier'].values():
            if not platform['model']:
                platform['model'] = 'test-model'
        (session / 'models.json').write_text(
            json.dumps(models) + '\n', encoding='utf-8'
        )

    def test_start_rejects_removed_platform_option(self):
        with redirect_stderr(StringIO()):
            result = workflow.main([
                'start', '--target', str(REPO_ROOT), '--platform', 'cursor'
            ])

        self.assertEqual(result, 2)

    def test_start_and_finish_own_session_apply_check_summary_and_cleanup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            origin = self.make_origin(root)
            target = root / 'target'
            target.mkdir()
            local_rule = target / '.agents/rules/40-local-testing.md'
            local_rule.parent.mkdir(parents=True)
            local_rule.write_text(
                '# Local Testing\n\nStrength: `Default`\n\n'
                'Scope: Local repository tests.\n',
                encoding='utf-8',
            )
            local_skill = target / '.agents/skills/local-check/SKILL.md'
            local_skill.parent.mkdir(parents=True)
            local_skill.write_text(
                '---\nname: local-check\ndescription: Use for local checks.\n---\n',
                encoding='utf-8',
            )
            local_rule_content = local_rule.read_bytes()
            local_skill_content = local_skill.read_bytes()
            generated_resource = (
                target
                / '.agents/skills/change-set-verification/references/verification-matrix.md'
            )
            generated_resource.parent.mkdir(parents=True)
            generated_resource.write_text('# local matrix\n', encoding='utf-8')
            generated_resource_content = generated_resource.read_bytes()
            start_output = StringIO()

            with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', origin.as_uri()):
                with redirect_stdout(start_output):
                    self.assertEqual(
                        workflow.main(['start', '--target', str(target)]),
                        0,
                    )

            start = json.loads(start_output.getvalue())
            session = Path(start['session'])
            self.assertEqual(start['phase'], 'start')
            self.assertEqual(start['models'], str(session / 'models.json'))
            self.assertEqual(start['generated'], str(session / 'generated'))
            self.assertTrue((session / workflow._SESSION_MARKER).is_file())
            models = json.loads((session / 'models.json').read_text(encoding='utf-8'))
            self.assertEqual(
                models['agents']['change-set-verifier']['cursor']['model'], ''
            )

            self.fill_models(session)
            self.write_generated_outputs(session)
            finish_output = StringIO()
            with redirect_stdout(finish_output):
                self.assertEqual(
                    workflow.main(['finish', '--session', str(session)]), 0
                )

            finish = json.loads(finish_output.getvalue())
            self.assertEqual(finish['phase'], 'finish')
            self.assertEqual(finish['check'], 'clean')
            self.assertEqual(finish['external_skills'], ['debug-mode'])
            self.assertEqual(
                finish['preserved_paths'],
                [
                    '.agents/rules/40-local-testing.md',
                    '.agents/skills/change-set-verification/references/verification-matrix.md',
                    '.agents/skills/local-check/SKILL.md',
                ],
            )
            self.assertIn(
                '.agents/rules/00-global-rule-config.md', finish['changed_paths']
            )
            self.assertFalse(session.exists())
            self.assertTrue((target / 'AGENTS.md').is_file())
            self.assertEqual(local_rule.read_bytes(), local_rule_content)
            self.assertEqual(local_skill.read_bytes(), local_skill_content)
            self.assertEqual(
                generated_resource.read_bytes(), generated_resource_content
            )

    def test_start_prefills_existing_platform_models_and_optional_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            origin = self.make_origin(root)
            target = root / 'target'
            codex = target / '.codex/agents/change-set-verifier.toml'
            cursor = target / '.cursor/agents/change-set-verifier.md'
            copilot = target / '.github/agents/change-set-verifier.agent.md'
            for path in (codex, cursor, copilot):
                path.parent.mkdir(parents=True, exist_ok=True)
            codex.write_text(
                'model = "gpt-5.6-terra"\n'
                'model_reasoning_effort = "medium"\n'
                'sandbox_mode = "workspace-write"\n',
                encoding='utf-8',
            )
            cursor.write_text(
                '---\nmodel: cursor-existing\nreadonly: true\n---\n',
                encoding='utf-8',
            )
            copilot.write_text(
                '---\nmodel: copilot-existing\n---\n',
                encoding='utf-8',
            )
            output = StringIO()

            with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', origin.as_uri()):
                with redirect_stdout(output):
                    self.assertEqual(
                        workflow.main(['start', '--target', str(target)]),
                        0,
                    )

            session = Path(json.loads(output.getvalue())['session'])
            models = json.loads((session / 'models.json').read_text(encoding='utf-8'))
            self.assertEqual(models, {'agents': {'change-set-verifier': {
                'codex': {
                    'model': 'gpt-5.6-terra',
                    'model_reasoning_effort': 'medium',
                    'sandbox_mode': 'workspace-write',
                },
                'cursor': {'model': 'cursor-existing', 'readonly': True},
                'github': {'model': 'copilot-existing'},
            }}})
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    workflow.main(['cancel', '--session', str(session)]),
                    0,
                )
            self.assertFalse(session.exists())

    def test_finish_failure_reports_error_cleans_session_and_does_not_write_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            origin = self.make_origin(root)
            target = root / 'target'
            target.mkdir()
            output = StringIO()
            with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', origin.as_uri()):
                with redirect_stdout(output):
                    self.assertEqual(
                        workflow.main(['start', '--target', str(target)]),
                        0,
                    )
            session = Path(json.loads(output.getvalue())['session'])
            self.fill_models(session)
            before = tuple(target.rglob('*'))
            error = StringIO()

            with redirect_stderr(error):
                self.assertEqual(
                    workflow.main(['finish', '--session', str(session)]), 2
                )

            self.assertIn('generated outputs must contain exactly', error.getvalue())
            self.assertFalse(session.exists())
            self.assertEqual(tuple(target.rglob('*')), before)

    def test_finish_rejects_unowned_directory_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            unowned = Path(temp_dir)
            marker = unowned / 'keep.txt'
            marker.write_text('keep\n', encoding='utf-8')
            with redirect_stderr(StringIO()):
                self.assertEqual(
                    workflow.main(['finish', '--session', str(unowned)]), 2
                )
            self.assertEqual(marker.read_text(encoding='utf-8'), 'keep\n')

    def test_finish_rejects_request_target_tampering_and_cleans_session(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            origin = self.make_origin(root)
            target = root / 'target'
            other = root / 'other'
            target.mkdir()
            other.mkdir()
            output = StringIO()
            with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', origin.as_uri()):
                with redirect_stdout(output):
                    self.assertEqual(
                        workflow.main(['start', '--target', str(target)]),
                        0,
                    )
            session = Path(json.loads(output.getvalue())['session'])
            request_path = session / 'request.json'
            request = json.loads(request_path.read_text(encoding='utf-8'))
            request['target'] = str(other)
            request_path.write_text(json.dumps(request), encoding='utf-8')
            error = StringIO()

            with redirect_stderr(error):
                self.assertEqual(
                    workflow.main(['finish', '--session', str(session)]), 2
                )

            self.assertIn('session request changed after start', error.getvalue())
            self.assertFalse(session.exists())
            self.assertEqual(tuple(target.rglob('*')), ())
            self.assertEqual(tuple(other.rglob('*')), ())

    def test_start_failure_cleans_the_owned_session(self):
        session = workflow._create_session()
        target = Path(tempfile.mkdtemp(prefix='setup-workflow-target-'))
        try:
            with (
                mock.patch.object(workflow, '_create_session', return_value=session),
                mock.patch.object(bootstrap, 'main', return_value=1),
            ):
                self.assertEqual(
                    workflow.main(['start', '--target', str(target)]), 1
                )
            self.assertFalse(session.exists())
        finally:
            shutil.rmtree(target, ignore_errors=True)

    def test_cleanup_handles_readonly_git_style_files(self):
        session = workflow._create_session()
        packed = session / 'source/.git/objects/pack/example.idx'
        packed.parent.mkdir(parents=True)
        packed.write_bytes(b'index')
        packed.chmod(stat.S_IREAD)

        workflow._remove_session(session)

        self.assertFalse(session.exists())

    def test_cancel_cleans_an_owned_unfinished_session(self):
        session = workflow._create_session()
        output = StringIO()

        with redirect_stdout(output):
            self.assertEqual(
                workflow.main(['cancel', '--session', str(session)]), 0
            )

        self.assertEqual(json.loads(output.getvalue())['phase'], 'cancel')
        self.assertFalse(session.exists())

    def test_offline_start_and_finish_use_the_installed_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            output = StringIO()
            warning = StringIO()
            missing = (root / 'missing.git').as_uri()

            with (
                mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', missing),
                redirect_stdout(output),
                redirect_stderr(warning),
            ):
                self.assertEqual(
                    workflow.main(['start', '--target', str(target)]),
                    0,
                )
            start = json.loads(output.getvalue())
            session = Path(start['session'])
            self.assertIsNone(start['source_commit'])
            self.assertEqual(Path(start['source_root']), REPO_ROOT)
            self.assertIn('using installed plugin source', warning.getvalue())
            self.fill_models(session)
            self.write_generated_outputs(session)

            with redirect_stdout(StringIO()):
                self.assertEqual(
                    workflow.main(['finish', '--session', str(session)]), 0
                )

            self.assertFalse(session.exists())
            self.assertTrue((target / 'AGENTS.md').is_file())


if __name__ == '__main__':
    unittest.main()
