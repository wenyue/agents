from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path, PurePosixPath
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'
sys.path.insert(0, str(SCRIPTS_ROOT))

import setup_project_agents  # noqa: E402


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
                '--platform', 'cursor', '--hooks', 'enabled', *extra, *self.source_args(),
            ]
        )

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
            self.assertTrue(request['hooks_enabled'])
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

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX session ownership checks')
    def test_create_session_uses_a_private_current_user_temporary_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Path(temp_dir) / 'session'
            session.mkdir(mode=0o755)
            with mock.patch.object(setup_project_agents.tempfile, 'mkdtemp', return_value=str(session)):
                created = setup_project_agents.create_session()

            status = created.stat()
            self.assertEqual(created, session)
            self.assertEqual(status.st_uid, os.geteuid())
            self.assertEqual(stat.S_IMODE(status.st_mode), 0o700)

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
            lock = json.loads((target / '.agents/lock.json').read_text(encoding='utf-8'))
            self.assertEqual(lock['source_commit'], self.source_commit)

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
            self.assertEqual(setup_project_agents.main(check_args), 1)
            self.assertEqual(self.snapshot_tree(target), before)

    def test_apply_rejects_tampered_selections_or_model_requests_without_writing(self):
        tamper = (
            ('selected_rules', ['unknown-rule']),
            ('selected_skills', ['manage-agent-tools', 'manage-agent-tools']),
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

    def test_apply_and_check_emit_one_structured_result_without_running_refresh(self):
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
            self.assertEqual(apply_result['changed_paths'], sorted(apply_result['changed_paths']))
            self.assertIn('.agents/rules/00-global-rule-config.md', apply_result['changed_paths'])
            self.assertIn('cursor', apply_result['capabilities'])
            self.assertEqual(apply_result['refresh_actions'][0]['platform'], 'cursor')
            self.assertEqual(apply_result['refresh_actions'][0]['command'], ['cursor', '--version'])

            check_output = StringIO()
            with redirect_stdout(check_output):
                self.assertEqual(setup_project_agents.main(check_args), 0)
            check_result = json.loads(check_output.getvalue())
            self.assertEqual(check_result['phase'], 'check')
            self.assertEqual(check_result['changed_paths'], [])

    def test_copilot_model_key_is_validated_and_rendered_into_its_agent_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            prepare_args = [
                'prepare', '--target', str(target), '--session', str(session),
                '--platform', 'codex', '--platform', 'cursor', '--platform', 'copilot',
                '--hooks', 'disabled', *self.source_args(),
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


if __name__ == '__main__':
    unittest.main()
