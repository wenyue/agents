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
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'
sys.path.insert(0, str(SCRIPTS_ROOT))

import setup_project_agents  # noqa: E402
import bootstrap  # noqa: E402
from agents_setup import transaction  # noqa: E402


CANONICAL_REPOSITORY = 'https://github.com/wenyue/agents.git'


def run_git(directory: Path, *args: str) -> str:
    completed = subprocess.run(
        ('git', '-C', str(directory), *args),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


class SetupCliTest(unittest.TestCase):
    source_commit = 'a' * 40

    def source_args(self) -> list[str]:
        return [
            '--source-root', str(REPO_ROOT),
            '--source-commit', self.source_commit,
            '--no-bootstrap',
        ]

    def private_session(self, root: Path) -> Path:
        session = Path(tempfile.mkdtemp(dir=root))
        session.chmod(0o700)
        return session

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
    def snapshot_tree(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob('*'))
            if path.is_file()
        }

    @staticmethod
    def write_models(session: Path, *, model: str = 'cursor-default') -> Path:
        path = session / 'models.json'
        path.write_text(
            json.dumps(
                {
                    'agents': {
                        'change-set-verifier': {
                            'cursor': {'model': model},
                        }
                    }
                }
            ) + '\n',
            encoding='utf-8',
        )
        return path

    def prepare(self, target: Path, session: Path, *extra: str) -> int:
        return setup_project_agents.main(
            [
                'prepare', '--target', str(target), '--session', str(session),
                '--platform', 'cursor', *extra, *self.source_args(),
            ]
        )

    def test_prepare_rejects_removed_hooks_option(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)

            with redirect_stderr(StringIO()):
                result = self.prepare(target, session, '--hooks', 'enabled')

            self.assertEqual(result, 2)
            self.assertEqual(self.snapshot_tree(target), {})

    def test_prepare_records_pinned_choices_and_five_generation_requests_without_target_writes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)

            self.assertEqual(self.prepare(target, session), 0)

            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            self.assertEqual(request['version'], 1)
            self.assertEqual(request['target'], str(target.absolute()))
            self.assertEqual(request['source_root'], str(REPO_ROOT.absolute()))
            self.assertEqual(request['source_commit'], self.source_commit)
            self.assertEqual(request['platforms'], ['cursor'])
            self.assertEqual(request['external_skills'], [])
            self.assertNotIn('hooks_enabled', request)
            self.assertEqual(
                request['model_requests'],
                [
                    {
                        'agent': 'change-set-verifier',
                        'platform': 'cursor',
                        'model_key': 'cursor',
                        'required_fields': ['model'],
                    }
                ],
            )
            self.assertEqual(len(request['generation_requests']), 5)
            self.assertEqual(
                {item['target'] for item in request['generation_requests']},
                {
                    '.agents/rules/20-project-tools.md',
                    '.agents/rules/21-project-rules.md',
                    '.agents/rules/22-project-structure.md',
                    '.agents/skills/change-set-verification/SKILL.md',
                    '.agents/skills/worktree-environment-setup/SKILL.md',
                },
            )
            self.assertTrue((session / 'generated/.agents/rules').is_dir())
            self.assertTrue((session / 'generated/.agents/skills').is_dir())
            self.assertEqual(self.snapshot_tree(target), {})

    def test_apply_rejects_cross_target_replay_and_models_outside_its_session(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            other_target = root / 'other-target'
            target.mkdir()
            other_target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            models = self.write_models(session)
            outside_models = root / 'models.json'
            outside_models.write_text('{"agents": {}}\n', encoding='utf-8')

            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(other_target), '--session', str(session), '--models', str(models), *self.source_args()]
                ),
                2,
            )
            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), '--models', str(outside_models), *self.source_args()]
                ),
                2,
            )
            self.assertEqual(self.snapshot_tree(target), {})
            self.assertEqual(self.snapshot_tree(other_target), {})

    def test_apply_requires_all_generated_outputs_then_writes_a_complete_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            models = self.write_models(session)

            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
                ),
                2,
            )
            self.assertEqual(self.snapshot_tree(target), {})

            self.write_generated_outputs(session)
            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
                ),
                0,
            )
            self.assertTrue((target / '.agents/rules/00-global-rule-config.md').is_file())
            self.assertTrue((target / '.agents/rules/20-project-tools.md').is_file())
            self.assertTrue((target / '.agents/skills/change-set-verification/SKILL.md').is_file())
            self.assertFalse((target / '.agents/lock.json').exists())

    def test_external_skill_is_snapshotted_and_force_replaces_its_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            config = target / '.agents/config.json'
            config.parent.mkdir(parents=True)
            config.write_text(
                json.dumps(
                    {
                        'version': 1,
                        'skills': {
                            'external': [
                                {
                                    'name': 'external-check',
                                    'repository': 'example/repository',
                                    'ref': 'main',
                                    'path': 'skills/external-check',
                                }
                            ]
                        },
                    }
                ),
                encoding='utf-8',
            )
            installed = target / '.agents/skills/external-check'
            installed.mkdir(parents=True)
            (installed / 'stale.txt').write_text('stale\n', encoding='utf-8')
            (installed / 'SKILL.md').write_text('locally changed\n', encoding='utf-8')
            session = self.private_session(root)

            def snapshot(specs, *, session):
                self.assertEqual([item.name for item in specs], ['external-check'])
                destination = session / 'external-skills/external-check'
                destination.mkdir(parents=True)
                (destination / 'SKILL.md').write_text(
                    '---\nname: external-check\ndescription: Use for checks.\n---\n',
                    encoding='utf-8',
                )
                return destination.parent

            with mock.patch.object(
                setup_project_agents,
                'snapshot_external_skills',
                side_effect=snapshot,
            ):
                self.assertEqual(self.prepare(target, session), 0)
            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            self.assertEqual(request['external_skills'][0]['name'], 'external-check')
            self.write_generated_outputs(session)
            models = self.write_models(session)
            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
                ),
                0,
            )
            self.assertFalse((installed / 'stale.txt').exists())
            self.assertIn('name: external-check', (installed / 'SKILL.md').read_text())

    def test_check_shares_apply_planning_and_never_writes_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            models = self.write_models(session)
            apply_args = ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
            check_args = ['check', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
            self.assertEqual(setup_project_agents.main(apply_args), 0)

            self.assertEqual(setup_project_agents.main(check_args), 0)
            (target / '.agents/rules/00-global-rule-config.md').write_text('drift\n', encoding='utf-8')
            before = self.snapshot_tree(target)
            drift_output = StringIO()
            with redirect_stdout(drift_output):
                self.assertEqual(setup_project_agents.main(check_args), 1)
            drift = json.loads(drift_output.getvalue())
            self.assertEqual(
                drift['drift'],
                {
                    'kind': 'desired_state_diff',
                    'message': 'desired state differs from the target project',
                    'paths': ['.agents/rules/00-global-rule-config.md'],
                },
            )
            self.assertEqual(drift['changed_paths'], ['.agents/rules/00-global-rule-config.md'])
            self.assertEqual(self.snapshot_tree(target), before)

    def test_check_reports_managed_field_drift_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            models = self.write_models(session)
            apply_args = ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
            check_args = ['check', *apply_args[1:]]
            with redirect_stdout(StringIO()):
                self.assertEqual(setup_project_agents.main(apply_args), 0)
            cursor_config = target / '.cursor/cli.json'
            document = json.loads(cursor_config.read_text(encoding='utf-8'))
            document['permissions']['allow'] = []
            cursor_config.write_text(json.dumps(document), encoding='utf-8')
            before = self.snapshot_tree(target)

            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(setup_project_agents.main(check_args), 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result['drift']['kind'], 'desired_state_diff')
            self.assertEqual(result['drift']['paths'], ['.cursor/cli.json'])
            self.assertEqual(result['changed_paths'], ['.cursor/cli.json'])
            self.assertEqual(self.snapshot_tree(target), before)

    def test_existing_managed_path_is_reported_then_force_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            models = self.write_models(session)
            collision = target / '.agents/rules/00-global-rule-config.md'
            collision.parent.mkdir(parents=True)
            collision.write_text('user-owned\n', encoding='utf-8')
            before = self.snapshot_tree(target)

            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    setup_project_agents.main(
                        ['check', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
                    ),
                    1,
                )
            result = json.loads(output.getvalue())
            self.assertEqual(result['drift']['kind'], 'desired_state_diff')
            self.assertIn('.agents/rules/00-global-rule-config.md', result['drift']['paths'])
            self.assertIn('.agents/rules/00-global-rule-config.md', result['changed_paths'])
            self.assertEqual(self.snapshot_tree(target), before)
            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
                ),
                0,
            )
            self.assertEqual(
                collision.read_bytes(),
                (REPO_ROOT / 'setup-assets/rules/00-global-rule-config.md').read_bytes(),
            )

    def test_apply_rejects_tampered_selections_or_model_requests_without_writing(self):
        tamper = (
            ('selected_rules', ['unknown-rule']),
            ('selected_skills', ['refactor-code', 'refactor-code']),
            ('selected_agents', ['unknown-agent']),
            ('model_requests', []),
        )
        for key, value in tamper:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                target = root / 'target'
                target.mkdir()
                session = self.private_session(root)
                self.assertEqual(self.prepare(target, session), 0)
                self.write_generated_outputs(session)
                models = self.write_models(session)
                request_path = session / 'request.json'
                request = json.loads(request_path.read_text(encoding='utf-8'))
                request[key] = value
                request_path.write_text(json.dumps(request), encoding='utf-8')

                self.assertEqual(
                    setup_project_agents.main(
                        ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
                    ),
                    2,
                )
                self.assertEqual(self.snapshot_tree(target), {})

    def test_apply_rejects_missing_or_empty_required_models_without_writing(self):
        for document in (
            {'agents': {}},
            {'agents': {'change-set-verifier': {'cursor': {'model': ''}}}},
        ):
            with self.subTest(document=document), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                target = root / 'target'
                target.mkdir()
                session = self.private_session(root)
                self.assertEqual(self.prepare(target, session), 0)
                self.write_generated_outputs(session)
                models = session / 'models.json'
                models.write_text(json.dumps(document), encoding='utf-8')

                self.assertEqual(
                    setup_project_agents.main(
                        ['apply', '--target', str(target), '--session', str(session), '--models', str(models), *self.source_args()]
                    ),
                    2,
                )
                self.assertEqual(self.snapshot_tree(target), {})

    def test_apply_and_check_emit_one_project_scoped_structured_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            models = self.write_models(session)
            apply_args = [
                'apply', '--target', str(target), '--session', str(session),
                '--models', str(models), *self.source_args(),
            ]
            check_args = ['check', *apply_args[1:]]

            apply_output = StringIO()
            with redirect_stdout(apply_output):
                self.assertEqual(setup_project_agents.main(apply_args), 0)
            apply_result = json.loads(apply_output.getvalue())
            self.assertEqual(apply_result['version'], 1)
            self.assertEqual(apply_result['phase'], 'apply')
            self.assertEqual(apply_result['source_commit'], self.source_commit)
            self.assertIsNone(apply_result['drift'])
            self.assertEqual(apply_result['changed_paths'], sorted(apply_result['changed_paths']))
            self.assertIn('.agents/rules/00-global-rule-config.md', apply_result['changed_paths'])
            self.assertEqual(apply_result['platforms'], ['cursor'])
            self.assertEqual(apply_result['external_skills'], [])
            self.assertEqual(apply_result['preserved_paths'], [])
            self.assertEqual(
                set(apply_result),
                {
                    'version', 'phase', 'source_commit', 'changed_paths', 'platforms',
                    'external_skills', 'preserved_paths', 'drift',
                },
            )

            check_output = StringIO()
            with redirect_stdout(check_output):
                self.assertEqual(setup_project_agents.main(check_args), 0)
            check_result = json.loads(check_output.getvalue())
            self.assertEqual(check_result['phase'], 'check')
            self.assertEqual(check_result['changed_paths'], [])
            self.assertIsNone(check_result['drift'])

    def test_copilot_model_key_is_validated_and_rendered_into_its_agent_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            prepare_args = [
                'prepare', '--target', str(target), '--session', str(session),
                '--platform', 'codex', '--platform', 'cursor', '--platform', 'copilot',
                *self.source_args(),
            ]
            self.assertEqual(setup_project_agents.main(prepare_args), 0)
            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            copilot_request = next(
                item for item in request['model_requests'] if item['platform'] == 'copilot'
            )
            self.assertEqual(copilot_request['model_key'], 'github')
            self.write_generated_outputs(session)
            models = session / 'models.json'
            models.write_text(
                json.dumps(
                    {
                        'agents': {
                            'change-set-verifier': {
                                'codex': {'model': 'codex-model'},
                                'cursor': {'model': 'cursor-model'},
                                'github': {'model': 'copilot-model'},
                            }
                        }
                    }
                ),
                encoding='utf-8',
            )

            with redirect_stdout(StringIO()):
                self.assertEqual(
                    setup_project_agents.main(
                        [
                            'apply', '--target', str(target), '--session', str(session),
                            '--models', str(models), *self.source_args(),
                        ]
                    ),
                    0,
                )
            wrapper = (target / '.github/agents/change-set-verifier.agent.md').read_text(
                encoding='utf-8'
            )
            self.assertIn('model: copilot-model\n', wrapper)
            self.assertNotIn('model: \n', wrapper)

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX session ownership checks')
    def test_rejects_nonprivate_session_before_target_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = root / 'session'
            session.mkdir(mode=0o755)
            session.chmod(0o755)

            self.assertEqual(self.prepare(target, session), 2)
            self.assertEqual(stat.S_IMODE(session.stat().st_mode), 0o755)
            self.assertEqual(self.snapshot_tree(target), {})


class SetupEndToEndTest(unittest.TestCase):
    """The public setup path, without depending on retired synchronizer fixtures."""

    def make_origin(self, root: Path) -> tuple[Path, Path]:
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
        run_git(work, 'config', 'user.email', 'test@example.com')
        run_git(work, 'config', 'user.name', 'Setup Test')
        run_git(work, 'add', '.')
        run_git(work, 'commit', '--quiet', '-m', 'initial main')
        run_git(work, 'remote', 'add', 'origin', origin.as_uri())
        run_git(work, 'push', '--quiet', 'origin', 'main')
        return origin, work

    @staticmethod
    def private_session(root: Path, name: str) -> Path:
        session = root / name
        session.mkdir(mode=0o700)
        session.chmod(0o700)
        return session

    @staticmethod
    def snapshot_tree(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob('*'))
            if path.is_file()
        }

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
    def write_models(session: Path) -> Path:
        path = session / 'models.json'
        path.write_text(
            json.dumps({'agents': {'change-set-verifier': {
                'codex': {'model': 'codex-test'},
                'cursor': {'model': 'cursor-test'},
                'github': {'model': 'copilot-test'},
            }}}),
            encoding='utf-8',
        )
        return path

    def bootstrap_prepare(self, origin: Path, target: Path, session: Path) -> None:
        with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', origin.as_uri()):
            self.assertEqual(
                bootstrap.main([
                    'prepare', '--target', str(target), '--session', str(session),
                    '--platform', 'codex', '--platform', 'cursor', '--platform', 'copilot',
                ]),
                0,
            )

    def apply_pinned(self, target: Path, session: Path) -> tuple[int, dict[str, object] | None]:
        request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
        models = self.write_models(session)
        source_root = Path(request['source_root'])
        completed = subprocess.run(
            (
                sys.executable,
                str(source_root / 'skills/setup-project-agents/scripts/setup_project_agents.py'),
                'apply', '--target', str(target), '--session', str(session),
                '--models', str(models), '--source-root', str(source_root),
                '--source-commit', request['source_commit'] or 'offline', '--no-bootstrap',
            ),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.returncode, json.loads(completed.stdout) if completed.stdout else None

    def apply_with_injected_transaction_failure(self, target: Path, session: Path) -> int:
        """Only the fault injection stays in-process; ordinary E2E applies use the pinned CLI."""
        request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
        models = self.write_models(session)
        return setup_project_agents.main([
            'apply', '--target', str(target), '--session', str(session),
            '--models', str(models), '--source-root', request['source_root'],
            '--source-commit', request['source_commit'] or 'offline', '--no-bootstrap',
        ])

    def test_remote_main_upgrade_is_idempotent_and_keeps_setup_control_plane_out_of_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            origin, work = self.make_origin(root)
            target = root / 'target'
            target.mkdir()

            first_session = self.private_session(root, 'first-session')
            self.bootstrap_prepare(origin, target, first_session)
            self.write_generated_outputs(first_session)
            first_result, _ = self.apply_pinned(target, first_session)
            self.assertEqual(first_result, 0)
            self.assertFalse((target / '.agents/lock.json').exists())
            self.assertFalse((target / '.codex/hooks.json').exists())
            self.assertFalse((target / '.cursor/hooks.json').exists())
            self.assertFalse((target / '.github/hooks/project-agent-tool-check.json').exists())
            self.assertNotIn(
                'hooks', tomllib.loads((target / '.codex/config.toml').read_text()).get('features', {})
            )
            self.assertNotIn(
                'disableAllHooks',
                json.loads((target / '.github/copilot/settings.json').read_text()),
            )
            self.assertFalse((target / '.agents/skills/setup-project-agents').exists())
            (target / 'unmanaged.txt').write_text('keep\n', encoding='utf-8')
            before_upgrade = self.snapshot_tree(target)

            rule = work / 'setup-assets/rules/00-global-rule-config.md'
            rule.write_text(rule.read_text(encoding='utf-8') + '\nRemote main update.\n', encoding='utf-8')
            run_git(work, 'add', 'setup-assets/rules/00-global-rule-config.md')
            run_git(work, 'commit', '--quiet', '-m', 'update managed rule')
            run_git(work, 'push', '--quiet', 'origin', 'main')

            second_session = self.private_session(root, 'second-session')
            self.bootstrap_prepare(origin, target, second_session)
            self.write_generated_outputs(second_session)
            second_result, second_output = self.apply_pinned(target, second_session)
            self.assertEqual(second_result, 0)
            assert second_output is not None
            self.assertIn('.agents/rules/00-global-rule-config.md', second_output['changed_paths'])
            self.assertEqual((target / 'unmanaged.txt').read_bytes(), before_upgrade['unmanaged.txt'])
            after_upgrade = self.snapshot_tree(target)
            changed = {
                path for path in set(before_upgrade) | set(after_upgrade)
                if before_upgrade.get(path) != after_upgrade.get(path)
            }
            self.assertEqual(
                changed,
                {'.agents/rules/00-global-rule-config.md'},
            )

            third_session = self.private_session(root, 'third-session')
            self.bootstrap_prepare(origin, target, third_session)
            self.write_generated_outputs(third_session)
            third_result, third_output = self.apply_pinned(target, third_session)
            self.assertEqual(third_result, 0)
            assert third_output is not None
            self.assertEqual(third_output['changed_paths'], [])

    def test_failure_paths_fall_back_fail_closed_and_restore_the_original_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            origin, work = self.make_origin(root)
            target = root / 'target'
            target.mkdir()

            invalid_catalog = work / 'setup-assets/catalog/assets.json'
            document = json.loads(invalid_catalog.read_text(encoding='utf-8'))
            document['plugin']['ref'] = 'not-main'
            invalid_catalog.write_text(json.dumps(document), encoding='utf-8')
            run_git(work, 'add', 'setup-assets/catalog/assets.json')
            run_git(work, 'commit', '--quiet', '-m', 'invalid fetched source')
            run_git(work, 'push', '--quiet', 'origin', 'main')
            before_invalid = self.snapshot_tree(target)
            invalid_session = self.private_session(root, 'invalid-session')
            with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', origin.as_uri()):
                self.assertEqual(
                    bootstrap.main(['prepare', '--target', str(target), '--session', str(invalid_session)]),
                    1,
                )
            self.assertEqual(self.snapshot_tree(target), before_invalid)

            offline_target = root / 'offline-target'
            offline_target.mkdir()
            offline_session = self.private_session(root, 'offline-session')
            stderr = StringIO()
            with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', (root / 'missing.git').as_uri()), redirect_stderr(stderr):
                self.assertEqual(
                    bootstrap.main([
                        'prepare', '--target', str(offline_target), '--session', str(offline_session),
                    ]),
                    0,
                )
            self.assertIn('WARNING: canonical main is unavailable', stderr.getvalue())

            source = root / 'source'
            shutil.copytree(REPO_ROOT, source, ignore=shutil.ignore_patterns('.git', '.superpowers', '__pycache__', '*.pyc'))
            baseline_session = self.private_session(root, 'baseline-session')
            self.assertEqual(setup_project_agents.main([
                'prepare', '--target', str(target), '--session', str(baseline_session),
                '--platform', 'cursor', '--source-root', str(source),
                '--source-commit', 'a' * 40, '--no-bootstrap',
            ]), 0)
            self.write_generated_outputs(baseline_session)
            self.assertEqual(self.apply_pinned(target, baseline_session)[0], 0)
            original = self.snapshot_tree(target)
            collision_target = root / 'collision-target'
            collision_target.mkdir()
            collision = collision_target / '.agents/rules/00-global-rule-config.md'
            collision.parent.mkdir(parents=True)
            collision.write_text('user collision\n', encoding='utf-8')
            collision_session = self.private_session(root, 'collision-session')
            self.assertEqual(setup_project_agents.main([
                'prepare', '--target', str(collision_target), '--session', str(collision_session),
                '--platform', 'cursor', '--source-root', str(source),
                '--source-commit', 'a' * 40, '--no-bootstrap',
            ]), 0)
            self.write_generated_outputs(collision_session)
            self.assertEqual(self.apply_pinned(collision_target, collision_session)[0], 0)
            self.assertEqual(
                collision.read_bytes(),
                (source / 'setup-assets/rules/00-global-rule-config.md').read_bytes(),
            )

            source_rule = source / 'setup-assets/rules/00-global-rule-config.md'
            source_rule.write_text(source_rule.read_text(encoding='utf-8') + '\nchanged once\n', encoding='utf-8')
            second_source_rule = source / 'setup-assets/rules/01-global-personality.md'
            second_source_rule.write_text(
                second_source_rule.read_text(encoding='utf-8') + '\nchanged twice\n',
                encoding='utf-8',
            )
            rollback_session = self.private_session(root, 'rollback-session')
            self.assertEqual(setup_project_agents.main([
                'prepare', '--target', str(target), '--session', str(rollback_session),
                '--platform', 'cursor', '--source-root', str(source),
                '--source-commit', 'b' * 40, '--no-bootstrap',
            ]), 0)
            self.write_generated_outputs(rollback_session)
            before_rollback = self.snapshot_tree(target)
            real_replace = transaction._replace
            calls = 0

            def replace_then_fail(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('injected replacement failure')
                return real_replace(*args, **kwargs)

            with mock.patch.object(transaction, '_replace', side_effect=replace_then_fail):
                self.assertEqual(self.apply_with_injected_transaction_failure(target, rollback_session), 2)
            self.assertEqual(self.snapshot_tree(target), before_rollback)


if __name__ == '__main__':
    unittest.main()
