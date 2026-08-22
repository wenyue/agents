from __future__ import annotations

import json
import hashlib
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

try:
    import tomllib
except ModuleNotFoundError:
    from _vendor import tomli as tomllib

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
        request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
        for relative in (item['target'] for item in request['generation_requests']):
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
    def snapshot_external_skills(specs, *, session: Path, existing_manifest=None):
        if not specs:
            return None
        root = session / 'external-skills'
        for source in specs:
            for spec in source.skills:
                skill = root / spec.name / 'SKILL.md'
                skill.parent.mkdir(parents=True)
                skill.write_text(
                    f'---\nname: {spec.name}\ndescription: Use for tests.\n---\n',
                    encoding='utf-8',
                )
        (root / 'sources.json').write_text(
            json.dumps({'sources': [
                {
                    'id': source.id, 'url': source.url,
                    'requested_ref': source.ref, 'resolved_ref': source.ref or 'main',
                    'ref_kind': 'branch', 'commit': 'a' * 40,
                    'license': {'spdx': 'MIT', 'path': 'LICENSE', 'sha256': 'b' * 64},
                    'skills': [
                        {
                            'id': spec.id,
                            'path': spec.path.as_posix(),
                            'files': {
                                'SKILL.md': hashlib.sha256(
                                    (root / spec.name / 'SKILL.md').read_bytes()
                                ).hexdigest(),
                            },
                        }
                        for spec in source.skills
                    ],
                }
                for source in specs
            ]}) + '\n', encoding='utf-8'
        )
        return root

    def prepare(self, target: Path, session: Path, *extra: str, snapshot=None) -> int:
        with mock.patch.object(
            setup_project_agents,
            'snapshot_external_skills',
            side_effect=snapshot or self.snapshot_external_skills,
        ):
            return setup_project_agents.main(
                [
                    'prepare', '--target', str(target), '--session', str(session),
                    *extra, *self.source_args(),
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

    def test_prepare_rejects_removed_platform_option(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)

            with redirect_stderr(StringIO()):
                result = self.prepare(target, session, '--platform', 'cursor')

            self.assertEqual(result, 2)
            self.assertEqual(self.snapshot_tree(target), {})

    def test_prepare_records_fixed_harnesses_and_five_generation_requests_without_target_writes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)

            self.assertEqual(self.prepare(target, session), 0)

            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            self.assertIsNone(request['external_snapshot_sha256'])
            self.assertEqual(request['target'], str(target.absolute()))
            self.assertEqual(request['source_root'], str(REPO_ROOT.absolute()))
            self.assertEqual(request['source_commit'], self.source_commit)
            self.assertEqual(request['harnesses'], ['codex', 'cursor', 'copilot'])
            self.assertEqual(
                request['external_sources'],
                [],
            )
            self.assertEqual(request['mcp_servers'], [])
            self.assertEqual(request['project_agents'], [])
            self.assertNotIn('hooks_enabled', request)
            self.assertNotIn('selected_agents', request)
            self.assertNotIn('model_requests', request)
            self.assertEqual(len(request['generation_requests']), 5)
            self.assertEqual(
                {item['target'] for item in request['generation_requests']},
                {
                    '.agents/rules/00-project-tools.md',
                    '.agents/rules/01-project-contracts.md',
                    '.agents/rules/02-project-structure.md',
                    '.agents/skills/change-set-verification/SKILL.md',
                    '.agents/skills/worktree-environment-setup/SKILL.md',
                },
            )
            self.assertTrue((session / 'generated/.agents/rules').is_dir())
            self.assertTrue((session / 'generated/.agents/skills').is_dir())
            self.assertEqual(self.snapshot_tree(target), {})

    def test_http_project_mcp_round_trips_through_prepare_apply_and_check(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            config = target / '.agents/config.json'
            config.parent.mkdir()
            config.write_text(json.dumps({
                'mcp': [{
                    'id': 'sentry',
                    'url': 'https://mcp.sentry.dev/mcp',
                    'overrides': [{
                        'when': {'harnesses': ['cursor']},
                        'set': {'url': 'https://cursor.sentry.dev/mcp'},
                    }],
                    'readiness': {
                        'harnesses': ['codex'],
                        'operatingSystems': ['linux'],
                        'checks': [],
                    },
                }],
            }), encoding='utf-8')
            session = self.private_session(root)

            self.assertEqual(self.prepare(target, session), 0)
            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            self.assertEqual(request['mcp_servers'], [{
                'id': 'sentry',
                'harnesses': ['codex', 'cursor', 'copilot'],
                'url': 'https://mcp.sentry.dev/mcp',
                'overrides': [{
                    'when': {'harnesses': ['cursor']},
                    'set': {'url': 'https://cursor.sentry.dev/mcp'},
                }],
                'readiness': {
                    'harnesses': ['codex'],
                    'operatingSystems': ['linux'],
                    'checks': [],
                },
            }])
            self.write_generated_outputs(session)
            invocation = [
                '--target', str(target), '--session', str(session),
                *self.source_args(),
            ]
            self.assertEqual(setup_project_agents.main(['apply', *invocation]), 0)
            self.assertEqual(
                tomllib.loads((target / '.codex/config.toml').read_text())[
                    'mcp_servers'
                ]['sentry'],
                {'url': 'https://mcp.sentry.dev/mcp'},
            )
            self.assertEqual(
                json.loads((target / '.cursor/mcp.json').read_text())[
                    'mcpServers'
                ]['sentry'],
                {'type': 'http', 'url': 'https://cursor.sentry.dev/mcp'},
            )
            self.assertEqual(
                json.loads((target / '.vscode/mcp.json').read_text())[
                    'servers'
                ]['sentry'],
                {'type': 'http', 'url': 'https://mcp.sentry.dev/mcp'},
            )
            lock = json.loads(
                (target / '.agents/smartkit.lock.json').read_text()
            )
            keys = {
                asset['key'] for asset in lock['assets'] if asset['role'] == 'mcp'
            }
            self.assertTrue(any(key.startswith('mcp_servers.sentry.') for key in keys))
            self.assertTrue(any(key.startswith('mcpServers.sentry.') for key in keys))
            self.assertTrue(any(key.startswith('servers.sentry.') for key in keys))
            self.assertEqual(setup_project_agents.main(['check', *invocation]), 0)

    def test_apply_rejects_cross_target_replay(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            other_target = root / 'other-target'
            target.mkdir()
            other_target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)

            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(other_target), '--session', str(session), *self.source_args()]
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

            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), *self.source_args()]
                ),
                2,
            )
            self.assertEqual(self.snapshot_tree(target), {})

            self.write_generated_outputs(session)
            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), *self.source_args()]
                ),
                0,
            )
            self.assertTrue((target / '.agents/rules/00-project-tools.md').is_file())
            self.assertTrue((target / '.agents/rules/00-project-tools.md').is_file())
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
                        'skills': [{
                            'source': 'example/repository',
                            'ref': 'main',
                            'include': ['skills/external-check'],
                        }],
                    }
                ),
                encoding='utf-8',
            )
            installed = target / '.agents/skills/external-check'
            session = self.private_session(root)

            def snapshot(specs, *, session, existing_manifest=None):
                self.assertEqual(
                    [item.name for source in specs for item in source.skills],
                    ['external-check'],
                )
                destination = session / 'external-skills'
                for name in ('external-check',):
                    skill = destination / name / 'SKILL.md'
                    skill.parent.mkdir(parents=True)
                    skill.write_text(
                        f'---\nname: {name}\ndescription: Use for checks.\n---\n',
                        encoding='utf-8',
                    )
                (destination / 'sources.json').write_text(
                    json.dumps({'sources': [{
                        'id': 'example/repository',
                        'url': 'https://github.com/example/repository',
                        'requested_ref': 'main', 'resolved_ref': 'main',
                        'ref_kind': 'branch', 'commit': 'a' * 40,
                        'license': {'spdx': 'MIT', 'path': 'LICENSE', 'sha256': 'b' * 64},
                        'skills': [{
                            'id': 'example/external-check',
                            'path': 'skills/external-check',
                            'files': {
                                'SKILL.md': hashlib.sha256(
                                    (destination / 'external-check/SKILL.md').read_bytes()
                                ).hexdigest(),
                            },
                        }],
                    }]}) + '\n', encoding='utf-8'
                )
                return destination

            self.assertEqual(self.prepare(target, session, snapshot=snapshot), 0)
            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            self.assertRegex(request['external_snapshot_sha256'], r'^[0-9a-f]{64}$')
            self.assertEqual(
                [item['source'] for item in request['external_sources']],
                ['example/repository'],
            )
            self.write_generated_outputs(session)
            self.assertEqual(
                setup_project_agents.main(
                    ['apply', '--target', str(target), '--session', str(session), *self.source_args()]
                ),
                0,
            )
            self.assertIn('name: external-check', (installed / 'SKILL.md').read_text())

    def test_apply_rejects_external_snapshot_metadata_changed_after_prepare(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            config = target / '.agents/config.json'
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({
                'skills': [{
                    'source': 'example/repository',
                    'include': ['skills/external-check'],
                }],
            }), encoding='utf-8')
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            metadata = session / 'external-skills/sources.json'
            document = json.loads(metadata.read_text(encoding='utf-8'))
            document['sources'][0]['secret'] = 'must-not-enter-manifest'
            metadata.write_text(json.dumps(document), encoding='utf-8')

            with redirect_stderr(StringIO()):
                result = setup_project_agents.main([
                    'apply', '--target', str(target), '--session', str(session),
                    *self.source_args(),
                ])

            self.assertEqual(result, 2)
            self.assertEqual(self.snapshot_tree(target), {
                '.agents/config.json': config.read_bytes(),
            })

    def test_prepare_reports_external_license_failure_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            config = target / '.agents/config.json'
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({
                'skills': [{
                    'source': 'example/repository',
                    'include': ['skills/external-check'],
                }],
            }), encoding='utf-8')
            session = self.private_session(root)

            def reject(*args, **kwargs):
                raise setup_project_agents.ExternalSkillError(
                    'external source license example/repository is ambiguous'
                )

            with redirect_stderr(StringIO()):
                result = self.prepare(target, session, snapshot=reject)

            self.assertEqual(result, 2)
            self.assertEqual(self.snapshot_tree(target), {
                '.agents/config.json': config.read_bytes(),
            })

    def test_check_rejects_modified_managed_file_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            apply_args = ['apply', '--target', str(target), '--session', str(session), *self.source_args()]
            check_args = ['check', '--target', str(target), '--session', str(session), *self.source_args()]
            self.assertEqual(setup_project_agents.main(apply_args), 0)

            self.assertEqual(setup_project_agents.main(check_args), 0)
            (target / '.agents/rules/00-project-tools.md').write_text('drift\n', encoding='utf-8')
            before = self.snapshot_tree(target)
            with redirect_stderr(StringIO()):
                self.assertEqual(setup_project_agents.main(check_args), 2)
            self.assertEqual(self.snapshot_tree(target), before)

    def test_check_rejects_modified_managed_field_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            apply_args = ['apply', '--target', str(target), '--session', str(session), *self.source_args()]
            check_args = ['check', *apply_args[1:]]
            with redirect_stdout(StringIO()):
                self.assertEqual(setup_project_agents.main(apply_args), 0)
            cursor_config = target / '.cursor/cli.json'
            document = json.loads(cursor_config.read_text(encoding='utf-8'))
            document['permissions']['allow'] = []
            cursor_config.write_text(json.dumps(document), encoding='utf-8')
            before = self.snapshot_tree(target)

            with redirect_stderr(StringIO()):
                self.assertEqual(setup_project_agents.main(check_args), 2)
            self.assertEqual(self.snapshot_tree(target), before)

    def test_first_adoption_rejects_conflicting_managed_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            self.assertEqual(self.prepare(target, session), 0)
            self.write_generated_outputs(session)
            collision = target / '.agents/rules/00-project-tools.md'
            collision.parent.mkdir(parents=True)
            collision.write_text('user-owned\n', encoding='utf-8')
            before = self.snapshot_tree(target)

            with redirect_stderr(StringIO()):
                self.assertEqual(
                    setup_project_agents.main(
                        ['check', '--target', str(target), '--session', str(session), *self.source_args()]
                    ),
                    2,
                )
            self.assertEqual(self.snapshot_tree(target), before)

    def test_apply_rejects_tampered_selections_without_writing(self):
        tamper = (
            ('selected_rules', ['unknown-rule']),
            ('selected_skills', ['refactor-code', 'refactor-code']),
        )
        for key, value in tamper:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                target = root / 'target'
                target.mkdir()
                session = self.private_session(root)
                self.assertEqual(self.prepare(target, session), 0)
                self.write_generated_outputs(session)
                request_path = session / 'request.json'
                request = json.loads(request_path.read_text(encoding='utf-8'))
                request[key] = value
                request_path.write_text(json.dumps(request), encoding='utf-8')

                self.assertEqual(
                    setup_project_agents.main(
                        ['apply', '--target', str(target), '--session', str(session), *self.source_args()]
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
            apply_args = [
                'apply', '--target', str(target), '--session', str(session),
                *self.source_args(),
            ]
            check_args = ['check', *apply_args[1:]]

            apply_output = StringIO()
            with redirect_stdout(apply_output):
                self.assertEqual(setup_project_agents.main(apply_args), 0)
            apply_result = json.loads(apply_output.getvalue())
            self.assertEqual(apply_result['phase'], 'apply')
            self.assertEqual(apply_result['source_commit'], self.source_commit)
            self.assertIsNone(apply_result['drift'])
            self.assertEqual(apply_result['changed_paths'], sorted(apply_result['changed_paths']))
            self.assertIn('.agents/rules/00-project-tools.md', apply_result['changed_paths'])
            self.assertEqual(
                apply_result['harnesses'], ['codex', 'cursor', 'copilot']
            )
            self.assertEqual(apply_result['external_skills'], [])
            self.assertEqual(apply_result['preserved_paths'], [])
            self.assertEqual(
                set(apply_result),
                {
                    'phase', 'source_commit', 'changed_paths', 'harnesses',
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

    def test_apply_installs_only_codex_plugin_agent_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            session = self.private_session(root)
            prepare_args = [
                'prepare', '--target', str(target), '--session', str(session),
                *self.source_args(),
            ]
            self.assertEqual(setup_project_agents.main(prepare_args), 0)
            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            self.assertNotIn('model_requests', request)
            self.assertNotIn('selected_agents', request)
            self.write_generated_outputs(session)

            with redirect_stdout(StringIO()):
                self.assertEqual(
                    setup_project_agents.main(
                        [
                            'apply', '--target', str(target), '--session', str(session),
                            *self.source_args(),
                        ]
                    ),
                    0,
                )
            codex = target / '.codex/agents/change-set-verifier.toml'
            self.assertEqual(
                codex.read_bytes(),
                (REPO_ROOT / 'agents/codex/change-set-verifier.toml').read_bytes(),
            )
            for relative in (
                '.cursor/agents/change-set-verifier.md',
                '.github/agents/change-set-verifier.agent.md',
            ):
                self.assertFalse((target / relative).exists())
            ownership = json.loads(
                (target / '.agents/smartkit.lock.json').read_text(encoding='utf-8')
            )
            verifier = next(
                item for item in ownership['assets']
                if item['path'] == '.codex/agents/change-set-verifier.toml'
            )
            self.assertEqual(verifier['role'], 'agent')

    def test_project_agent_round_trips_through_prepare_apply_and_check(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            source = target / '.agents/agents/l10n.md'
            source.parent.mkdir(parents=True)
            source.write_text('# L10n\n\nUse project localization policy.\n', encoding='utf-8')
            config = target / '.agents/config.json'
            config.write_text(json.dumps({
                'agents': [{
                    'id': 'l10n',
                    'source': '.agents/agents/l10n.md',
                    'description': 'Project-local agent: l10n',
                    'harnesses': {
                        'codex': {
                            'model': 'gpt-5.6-terra',
                            'model_reasoning_effort': 'medium',
                            'sandbox_mode': 'workspace-write',
                        },
                        'cursor': {'model': 'gpt-5.6-terra', 'readonly': False},
                        'copilot': {
                            'model': 'gpt-5.6-terra',
                            'disable_model_invocation': False,
                        },
                    },
                }],
            }), encoding='utf-8')
            session = self.private_session(root)
            invocation = [
                '--target', str(target), '--session', str(session), *self.source_args(),
            ]

            self.assertEqual(setup_project_agents.main(['prepare', *invocation]), 0)
            request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
            self.assertEqual(request['project_agents'][0]['id'], 'l10n')
            self.write_generated_outputs(session)
            with redirect_stdout(StringIO()):
                self.assertEqual(setup_project_agents.main(['apply', *invocation]), 0)
                self.assertEqual(setup_project_agents.main(['check', *invocation]), 0)

            self.assertTrue((target / '.codex/agents/l10n.toml').is_file())
            self.assertTrue((target / '.cursor/agents/l10n.md').is_file())
            self.assertTrue((target / '.github/agents/l10n.agent.md').is_file())
            self.assertTrue(source.is_file())

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
        run_git(work, 'checkout', '--quiet', '-b', 'master')
        run_git(work, 'config', 'user.email', 'test@example.com')
        run_git(work, 'config', 'user.name', 'Setup Test')
        run_git(work, 'add', '.')
        run_git(work, 'commit', '--quiet', '-m', 'initial master')
        run_git(work, 'remote', 'add', 'origin', origin.as_uri())
        run_git(work, 'push', '--quiet', 'origin', 'master')
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
        request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
        for relative in (item['target'] for item in request['generation_requests']):
            path = session / 'generated' / PurePosixPath(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'# generated {path.name}\n', encoding='utf-8')

    def bootstrap_prepare(self, origin: Path, target: Path, session: Path) -> None:
        with mock.patch.object(bootstrap, 'CANONICAL_REPOSITORY', origin.as_uri()):
            self.assertEqual(
                bootstrap.main([
                    'prepare', '--target', str(target), '--session', str(session),
                ]),
                0,
            )

    def apply_pinned(self, target: Path, session: Path) -> tuple[int, dict[str, object] | None]:
        request = json.loads((session / 'request.json').read_text(encoding='utf-8'))
        source_root = Path(request['source_root'])
        completed = subprocess.run(
            (
                sys.executable,
                str(source_root / 'skills/setup-project-agents/scripts/setup_project_agents.py'),
                'apply', '--target', str(target), '--session', str(session),
                '--source-root', str(source_root),
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
        return setup_project_agents.main([
            'apply', '--target', str(target), '--session', str(session),
            '--source-root', request['source_root'],
            '--source-commit', request['source_commit'] or 'offline', '--no-bootstrap',
        ])

    def test_remote_master_upgrade_is_idempotent_and_keeps_setup_control_plane_out_of_snapshot(self):
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
            self.assertFalse((target / '.github/copilot/settings.json').exists())
            self.assertFalse((target / '.agents/skills/setup-project-agents').exists())
            (target / 'unmanaged.txt').write_text('keep\n', encoding='utf-8')
            before_upgrade = self.snapshot_tree(target)

            rule = work / 'setup-assets/templates/harness-config/cursor.cli.json'
            rule_document = json.loads(rule.read_text(encoding='utf-8'))
            rule_document['permissions']['allow'].append('Shell(git status)')
            rule.write_text(json.dumps(rule_document) + '\n', encoding='utf-8')
            run_git(work, 'add', 'setup-assets/templates/harness-config/cursor.cli.json')
            run_git(work, 'commit', '--quiet', '-m', 'update managed rule')
            run_git(work, 'push', '--quiet', 'origin', 'master')

            second_session = self.private_session(root, 'second-session')
            self.bootstrap_prepare(origin, target, second_session)
            self.write_generated_outputs(second_session)
            second_result, second_output = self.apply_pinned(target, second_session)
            self.assertEqual(second_result, 0)
            assert second_output is not None
            self.assertIn('.cursor/cli.json', second_output['changed_paths'])
            self.assertEqual((target / 'unmanaged.txt').read_bytes(), before_upgrade['unmanaged.txt'])
            after_upgrade = self.snapshot_tree(target)
            changed = {
                path for path in set(before_upgrade) | set(after_upgrade)
                if before_upgrade.get(path) != after_upgrade.get(path)
            }
            self.assertEqual(
                changed,
                {
                    '.cursor/cli.json',
                    '.agents/smartkit.lock.json',
                },
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
            document['plugin']['ref'] = 'not-master'
            invalid_catalog.write_text(json.dumps(document), encoding='utf-8')
            run_git(work, 'add', 'setup-assets/catalog/assets.json')
            run_git(work, 'commit', '--quiet', '-m', 'invalid fetched source')
            run_git(work, 'push', '--quiet', 'origin', 'master')
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
            self.assertIn('WARNING: canonical master is unavailable', stderr.getvalue())

            source = root / 'source'
            shutil.copytree(REPO_ROOT, source, ignore=shutil.ignore_patterns('.git', '.superpowers', '__pycache__', '*.pyc'))
            baseline_session = self.private_session(root, 'baseline-session')
            self.assertEqual(setup_project_agents.main([
                'prepare', '--target', str(target), '--session', str(baseline_session),
                '--source-root', str(source),
                '--source-commit', 'a' * 40, '--no-bootstrap',
            ]), 0)
            self.write_generated_outputs(baseline_session)
            self.assertEqual(self.apply_pinned(target, baseline_session)[0], 0)
            original = self.snapshot_tree(target)
            collision_target = root / 'collision-target'
            collision_target.mkdir()
            collision = collision_target / '.agents/rules/00-project-tools.md'
            collision.parent.mkdir(parents=True)
            collision.write_text('user collision\n', encoding='utf-8')
            collision_content = collision.read_bytes()
            collision_session = self.private_session(root, 'collision-session')
            self.assertEqual(setup_project_agents.main([
                'prepare', '--target', str(collision_target), '--session', str(collision_session),
                '--source-root', str(source),
                '--source-commit', 'a' * 40, '--no-bootstrap',
            ]), 0)
            self.write_generated_outputs(collision_session)
            self.assertEqual(self.apply_pinned(collision_target, collision_session)[0], 2)
            self.assertEqual(
                collision.read_bytes(),
                collision_content,
            )

            source_rule = source / 'setup-assets/templates/harness-config/codex.config.toml'
            source_rule.write_text(
                source_rule.read_text(encoding='utf-8') + '\n# changed once\n',
                encoding='utf-8',
            )
            second_source_rule = source / 'setup-assets/templates/harness-config/cursor.cli.json'
            second_document = json.loads(
                second_source_rule.read_text(encoding='utf-8')
            )
            second_document['permissions']['deny'].append('Shell(git clean)')
            second_source_rule.write_text(
                json.dumps(second_document) + '\n',
                encoding='utf-8',
            )
            rollback_session = self.private_session(root, 'rollback-session')
            self.assertEqual(setup_project_agents.main([
                'prepare', '--target', str(target), '--session', str(rollback_session),
                '--source-root', str(source),
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
