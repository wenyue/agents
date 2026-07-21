import contextlib
import importlib.util
import io
import inspect
import os
import json
import shutil
import tempfile
import tomllib
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from unittest import mock
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SKILL_ROOT = REPO_ROOT / 'agents' / 'skills' / 'setup-project-agents'
REPO_REFERENCES = REPO_SKILL_ROOT / 'references'
REPO_TEMPLATES = REPO_SKILL_ROOT / 'assets' / 'templates'
TRACK_WORKTREE_TIME_ROOT = REPO_ROOT / 'agents' / 'skills' / 'track-worktree-time'
sys.path.insert(0, str(REPO_SKILL_ROOT / 'scripts'))

import sync_public_agent_assets as sync


def load_track_worktree_time_module():
    script = TRACK_WORKTREE_TIME_ROOT / 'scripts' / 'timing.py'
    spec = importlib.util.spec_from_file_location('track_worktree_time', script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load timing script: {script}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncPublicAgentAssetsTest(unittest.TestCase):
    def test_load_json_returns_object(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'config.json'
            path.write_text('{"source_repo": "https://example.invalid/repo"}\n', encoding='utf-8')

            result = sync.load_json(path)

        self.assertEqual(result, {'source_repo': 'https://example.invalid/repo'})

    def test_load_json_rejects_non_object(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'config.json'
            path.write_text('[]\n', encoding='utf-8')

            with self.assertRaises(sync.SyncError) as error:
                sync.load_json(path)

        self.assertIn('must contain a JSON object', str(error.exception))

    def test_model_request_describes_each_subagent_and_requested_model_fields(self):
        public_config = {
            'agent_prompts': [
                {
                    'name': 'reviewer',
                    'required_intelligence': 'High: compare cross-file behavior and invariants.',
                    'codex': {'sandbox_mode': 'workspace-write'},
                    'cursor': {'readonly': True},
                }
            ]
        }

        self.assertTrue(hasattr(sync, 'build_model_request'))
        request = sync.build_model_request(public_config)

        self.assertEqual(request['schema_version'], 1)
        self.assertRegex(request['catalog_digest'], r'^sha256:[0-9a-f]{64}$')
        self.assertEqual(
            request['agents'],
            {
                'reviewer': {
                    'required_intelligence': (
                        'High: compare cross-file behavior and invariants.'
                    ),
                    'codex': {
                        'model': None,
                        'model_reasoning_effort': None,
                    },
                    'cursor': {'model': None},
                    'github': {'model': None},
                }
            },
        )

    def test_model_request_includes_target_local_subagent(self):
        public_config = {
            'agent_prompts': [
                {
                    'name': 'public-reviewer',
                    'required_intelligence': 'High reasoning depth.',
                }
            ]
        }
        local_config = {
            'agent_prompts': [
                {
                    'name': 'project-reviewer',
                    'description': 'Reviews project-specific API compatibility.',
                }
            ]
        }

        self.assertIn('local_config', inspect.signature(sync.build_model_request).parameters)
        request = sync.build_model_request(public_config, local_config)

        self.assertEqual(
            request['agents']['project-reviewer']['required_intelligence'],
            'Reviews project-specific API compatibility.',
        )
        self.assertEqual(
            set(request['agents']['project-reviewer']),
            {'required_intelligence', 'codex', 'cursor', 'github'},
        )

    def test_model_config_converts_completed_request_to_runtime_overrides(self):
        public_config = {
            'agent_prompts': [
                {
                    'name': 'reviewer',
                    'required_intelligence': 'High reasoning depth.',
                }
            ]
        }
        model_config = sync.build_model_request(public_config)
        model_config['agents']['reviewer']['codex'].update(
            model='codex-model',
            model_reasoning_effort='high',
        )
        model_config['agents']['reviewer']['cursor']['model'] = 'cursor-model'
        model_config['agents']['reviewer']['github']['model'] = 'github-model'

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'models.json'
            path.write_text(json.dumps(model_config), encoding='utf-8')

            self.assertTrue(hasattr(sync, 'load_model_config'))
            result = sync.load_model_config(path, public_config)

        self.assertEqual(
            result,
            {
                'codex_agent_runtime_overrides': {
                    'reviewer': {
                        'model': 'codex-model',
                        'model_reasoning_effort': 'high',
                    }
                },
                'cursor_agent_runtime_overrides': {
                    'reviewer': {'model': 'cursor-model'}
                },
                'github_agent_runtime_overrides': {
                    'reviewer': {'model': 'github-model'}
                },
            },
        )

    def test_model_config_validates_target_local_subagents_from_same_request(self):
        public_config = {'agent_prompts': []}
        local_config = {
            'agent_prompts': [
                {
                    'name': 'project-reviewer',
                    'description': 'Reviews project-specific API compatibility.',
                }
            ]
        }
        model_config = sync.build_model_request(public_config, local_config)
        agent = model_config['agents']['project-reviewer']
        agent['codex'].update(model='codex-model', model_reasoning_effort='high')
        agent['cursor']['model'] = 'cursor-model'
        agent['github']['model'] = 'github-model'

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'models.json'
            path.write_text(json.dumps(model_config), encoding='utf-8')

            self.assertIn('local_config', inspect.signature(sync.load_model_config).parameters)
            result = sync.load_model_config(path, public_config, local_config)

        self.assertIn('project-reviewer', result['codex_agent_runtime_overrides'])

    def test_model_config_rejects_unknown_fields(self):
        public_config = {
            'agent_prompts': [
                {
                    'name': 'reviewer',
                    'required_intelligence': 'High reasoning depth.',
                }
            ]
        }
        model_config = sync.build_model_request(public_config)
        model_config['agents']['reviewer']['codex'] = {
            'model': 'codex-model',
            'model_reasoning_effort': 'high',
            'sandbox_mode': 'danger-full-access',
        }
        model_config['agents']['reviewer']['cursor']['model'] = 'cursor-model'
        model_config['agents']['reviewer']['github']['model'] = 'github-model'

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'models.json'
            path.write_text(json.dumps(model_config), encoding='utf-8')

            with self.assertRaises(sync.SyncError) as error:
                sync.load_model_config(path, public_config)

        self.assertIn('unsupported fields: sandbox_mode', str(error.exception))

    def test_local_asset_discovery_does_not_read_models_from_existing_wrappers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            codex_wrapper = target / '.codex' / 'agents' / 'reviewer.toml'
            codex_wrapper.parent.mkdir(parents=True)
            codex_wrapper.write_text(
                'model = "old-model"\nmodel_reasoning_effort = "low"\n',
                encoding='utf-8',
            )
            public_config = {
                'agent_prompts': [
                    {
                        'name': 'reviewer',
                        'required_intelligence': 'High reasoning depth.',
                    }
                ],
                'platforms': {
                    'agent_wrappers': [
                        {
                            'template': 'agent_wrapper.codex.toml',
                            'path': '.codex/agents/{{agent.name}}.toml',
                        }
                    ]
                },
            }

            result = sync.discover_local_assets(target, public_config)

        self.assertEqual(result['codex_agent_runtime_overrides'], {})

    def test_parser_rejects_local_source_argument(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            sync.build_parser().parse_args(['--source', 'local-agents'])

    def test_parser_declares_two_stage_model_json_arguments(self):
        parser = sync.build_parser()

        self.assertIn('--model-request', parser.format_help())
        self.assertIn('--model-config', parser.format_help())
        self.assertEqual(
            parser.parse_args(['--model-request', 'models.json']).model_request,
            'models.json',
        )
        self.assertEqual(
            parser.parse_args(['--model-config', 'models.json']).model_config,
            'models.json',
        )

    def test_resolve_source_ignores_local_default_and_fetches_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            local_source = root / 'agents'
            (local_source / 'agents' / 'rules').mkdir(parents=True)
            (local_source / 'agents' / 'rules' / '10-base-code.md').write_text('local\n', encoding='utf-8')
            archive = root / 'agents.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('agents-master/agents/rules/10-base-code.md', 'archive\n')
            public_config = {
                'source_archive_url': archive.resolve().as_uri(),
            }

            try:
                result = sync.resolve_source(public_config)
            except sync.SyncError as error:
                self.fail(f'resolve_source should fetch archive: {error}')

            self.assertEqual((result / 'agents' / 'rules' / '10-base-code.md').read_text(), 'archive\n')

    def test_resolve_source_refetches_archive_every_time(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / 'agents.zip'
            public_config = {
                'source_archive_url': archive.resolve().as_uri(),
            }

            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('agents-master/agents/rules/10-base-code.md', 'first\n')
            first = sync.resolve_source(public_config)

            archive.unlink()
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('agents-master/agents/rules/10-base-code.md', 'second\n')
            second = sync.resolve_source(public_config)

        self.assertNotEqual(first, second)
        self.assertEqual((first / 'agents' / 'rules' / '10-base-code.md').read_text(), 'first\n')
        self.assertEqual((second / 'agents' / 'rules' / '10-base-code.md').read_text(), 'second\n')

    def test_archive_fallback_syncs_only_manifest_whitelisted_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            skill_root.mkdir(parents=True)
            archive = root / 'agents.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('agents-master/README.md', 'public readme\n')
                package.writestr('agents-master/agents/rules/10-base-code.md', 'rule\n')
                package.writestr('agents-master/agents/skills/rename/SKILL.md', 'rename skill\n')
                package.writestr('agents-master/agents/skills/unlisted/SKILL.md', 'unlisted skill\n')
                package.writestr('agents-master/agents/agents/sample-agent.md', 'sample agent\n')
            public_config = {
                'source_archive_url': archive.resolve().as_uri(),
                'mirror_delete': True,
                'rules': [{'file': '10-base-code.md'}],
                'skills': [{'name': 'rename'}],
                'agent_prompts': [{'name': 'sample-agent'}],
            }
            source = sync.resolve_source(public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertEqual((target / '.agents' / 'rules' / '10-base-code.md').read_text(), 'rule\n')
            self.assertEqual((target / '.agents' / 'skills' / 'rename' / 'SKILL.md').read_text(), 'rename skill\n')
            self.assertEqual(
                (target / '.agents' / 'agents' / 'sample-agent.md').read_text(),
                'sample agent\n',
            )
            self.assertFalse((target / 'README.md').exists())
            self.assertFalse((target / '.agents' / 'skills' / 'unlisted').exists())

    def test_sync_copies_public_rule_skill_and_agent_prompt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            (source / 'agents' / 'rules').mkdir(parents=True)
            (source / 'agents' / 'skills' / 'rename').mkdir(parents=True)
            (source / 'agents' / 'agents').mkdir(parents=True)
            (target / '.agents' / 'rules').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / 'agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
            (source / 'agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
            (source / 'agents' / 'agents' / 'sample-agent.md').write_text(
                'agent\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'rules': [{'file': '10-base-code.md'}],
                'skills': [{'name': 'rename'}],
                'agent_prompts': [{'name': 'sample-agent'}],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertIn(sync.Change('created', '.agents/rules/10-base-code.md'), changes)
            self.assertEqual((target / '.agents' / 'rules' / '10-base-code.md').read_text(), 'rule\n')
            self.assertEqual((target / '.agents' / 'skills' / 'rename' / 'SKILL.md').read_text(), 'skill\n')
            self.assertEqual(
                (target / '.agents' / 'agents' / 'sample-agent.md').read_text(),
                'agent\n',
            )

    def test_sync_marks_existing_unchanged_public_rule_as_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            (source / 'agents' / 'rules').mkdir(parents=True)
            (target / '.agents' / 'rules').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / 'agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
            (target / '.agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
            public_config = {
                'mirror_delete': True,
                'rules': [{'file': '10-base-code.md'}],
                'skills': [],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertEqual(changes, [sync.Change('unchanged', '.agents/rules/10-base-code.md')])
            self.assertEqual((target / '.agents' / 'rules' / '10-base-code.md').read_text(), 'rule\n')

    def test_sync_deletes_extra_file_inside_public_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            (source / 'agents' / 'skills' / 'rename').mkdir(parents=True)
            (target / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / 'agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
            extra = target / '.agents' / 'skills' / 'rename' / 'extra.md'
            extra.write_text('local\n', encoding='utf-8')
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [{'name': 'rename'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertFalse(extra.exists())

    def test_sync_preserves_extra_file_inside_public_skill_when_mirror_delete_is_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            (source / 'agents' / 'skills' / 'rename').mkdir(parents=True)
            (target / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / 'agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
            extra = target / '.agents' / 'skills' / 'rename' / 'extra.md'
            extra.write_text('local\n', encoding='utf-8')
            public_config = {
                'mirror_delete': False,
                'rules': [],
                'skills': [{'name': 'rename'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertTrue(extra.exists())

    def test_sync_deletes_extra_empty_directory_tree_inside_public_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            (source / 'agents' / 'skills' / 'rename').mkdir(parents=True)
            (target / '.agents' / 'skills' / 'rename' / 'unused' / 'nested').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / 'agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [{'name': 'rename'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertFalse((target / '.agents' / 'skills' / 'rename' / 'unused').exists())

    def test_sync_deletes_skill_declared_retired_by_catalog(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = source / 'agents' / 'skills' / 'setup-project-agents'
            legacy_skill = target / '.agents' / 'skills' / 'old-setup-agent'
            source_skill.mkdir(parents=True)
            legacy_skill.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_skill / 'SKILL.md').write_text('new skill\n', encoding='utf-8')
            (legacy_skill / 'SKILL.md').write_text(
                'project-owned modifications do not block explicit name retirement\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'retired_assets': {
                    'rules': [],
                    'skills': ['old-setup-agent'],
                    'agents': [],
                },
                'rules': [],
                'skills': [{'name': 'setup-project-agents'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertFalse(legacy_skill.exists())
            self.assertEqual(
                (target / '.agents' / 'skills' / 'setup-project-agents' / 'SKILL.md').read_text(),
                'new skill\n',
            )

    def test_sync_deletes_rule_and_wrappers_declared_retired_by_catalog(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            retired_rule = target / '.agents' / 'rules' / '30-old-rule.md'
            cursor_wrapper = target / '.cursor' / 'rules' / '30-old-rule.mdc'
            github_wrapper = target / '.github' / 'instructions' / '30-old-rule.instructions.md'
            retired_rule.parent.mkdir(parents=True)
            cursor_wrapper.parent.mkdir(parents=True)
            github_wrapper.parent.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            retired_rule.write_text('project-modified old rule\n', encoding='utf-8')
            cursor_wrapper.write_text('custom cursor wrapper\n', encoding='utf-8')
            github_wrapper.write_text('custom github wrapper\n', encoding='utf-8')
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            public_config['agent_prompts'] = []
            public_config['entry_files'] = []
            public_config['retired_assets'] = {
                'rules': ['30-old-rule.md'],
                'skills': [],
                'agents': [],
            }
            local_config = sync.discover_local_assets(target, public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            self.assertFalse(retired_rule.exists())
            self.assertFalse(cursor_wrapper.exists())
            self.assertFalse(github_wrapper.exists())
            self.assertEqual(local_config['rules'], [])

    def test_sync_uses_running_skill_when_source_archive_lacks_renamed_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            skill_root.mkdir(parents=True)
            (source / 'agents' / 'skills').mkdir(parents=True)
            (skill_root / 'SKILL.md').write_text('running skill\n', encoding='utf-8')
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [{'name': 'setup-project-agents'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertEqual(
                (target / '.agents' / 'skills' / 'setup-project-agents' / 'SKILL.md').read_text(),
                'running skill\n',
            )

    def test_sync_ignores_generated_files_inside_public_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = source / 'agents' / 'skills' / 'rename'
            target_skill = target / '.agents' / 'skills' / 'rename'
            (source_skill / 'scripts' / '__pycache__').mkdir(parents=True)
            (target_skill / 'scripts' / '__pycache__').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_skill / 'SKILL.md').write_text('skill\n', encoding='utf-8')
            (source_skill / 'scripts' / '__pycache__' / 'source.cpython-310.pyc').write_bytes(b'source')
            target_cache = target_skill / 'scripts' / '__pycache__' / 'target.cpython-310.pyc'
            target_cache.write_bytes(b'target')
            public_config = {
                'mirror_delete': True,
                'ignore': [
                    '__pycache__',
                    '__pycache__/**',
                    '**/__pycache__',
                    '**/__pycache__/**',
                    '*.pyc',
                    '**/*.pyc',
                ],
                'rules': [],
                'skills': [{'name': 'rename'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertEqual(changes, [sync.Change('created', '.agents/skills/rename/SKILL.md')])
            self.assertTrue(target_cache.exists())
            self.assertFalse((target_skill / 'scripts' / '__pycache__' / 'source.cpython-310.pyc').exists())

    def test_sync_generates_rule_wrapper_from_real_platform_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            (source / 'agents' / 'rules').mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source / 'agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = [rule for rule in public_config['rules'] if rule['file'] == '10-base-code.md']
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            local_config = {'rules': [], 'agent_prompts': []}
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            expected = (
                '---\n'
                'description: "[default] Cross-language code goals for ownership, clarity, state, '
                'and boundaries"\n'
                'globs: **/*.{dart,cpp,c,h,hpp,cc,py,js,jsx,ts,tsx,sh}\n'
                'alwaysApply: false\n'
                '---\n\n'
                'Apply @.agents/rules/10-base-code.md\n'
            )
            self.assertEqual(
                (target / '.cursor' / 'rules' / '10-base-code.mdc').read_text(encoding='utf-8'),
                expected,
            )

    def test_sync_deletes_stale_rule_wrapper_when_rule_is_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            (source / 'agents' / 'rules').mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source / 'agents' / 'rules' / '00-global-rule-config.md').write_text('rule\n', encoding='utf-8')
            stale_wrapper = target / '.cursor' / 'rules' / '10-base-code.mdc'
            stale_wrapper.parent.mkdir(parents=True)
            stale_wrapper.write_text(
                '---\nalwaysApply: false\n---\n\nApply @.agents/rules/10-base-code.md\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = [
                rule for rule in public_config['rules'] if rule['file'] == '00-global-rule-config.md'
            ]
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            local_config = {'rules': [], 'agent_prompts': []}
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            self.assertFalse(stale_wrapper.exists())

    def test_sync_defers_agent_wrappers_without_reviewed_models(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text(
                'Apply @.agents/skills/change-set-verification/SKILL.md\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            public_config['agent_prompts'] = [
                agent
                for agent in public_config['agent_prompts']
                if agent['name'] == 'change-set-verifier'
            ]
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            self.assertFalse(
                (target / '.codex' / 'agents' / 'change-set-verifier.toml').exists()
            )
            self.assertFalse(
                (target / '.cursor' / 'agents' / 'change-set-verifier.md').exists()
            )
            self.assertFalse(
                (target / '.github' / 'agents' / 'change-set-verifier.agent.md').exists()
            )

    def test_sync_uses_explicit_codex_runtime_fields_instead_of_target_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text(
                'Apply @.agents/skills/change-set-verification/SKILL.md\n',
                encoding='utf-8',
            )
            existing_wrapper = target / '.codex' / 'agents' / 'change-set-verifier.toml'
            existing_wrapper.parent.mkdir(parents=True)
            existing_wrapper.write_text(
                'name = "stale-name"\n'
                'description = "stale description"\n'
                'model = "project-reviewed-model"\n'
                'model_reasoning_effort = "high"\n'
                'sandbox_mode = "read-only"\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            public_config['platforms']['agent_wrappers'] = [
                wrapper
                for wrapper in public_config['platforms']['agent_wrappers']
                if wrapper['template'] == 'agent_wrapper.codex.toml'
            ]
            local_config = sync.discover_local_assets(target, public_config)
            local_config['codex_agent_runtime_overrides'] = {
                'change-set-verifier': {
                    'model': 'json-selected-model',
                    'model_reasoning_effort': 'medium',
                }
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                local_config,
                require_agent_runtime=True,
            )

            wrapper = tomllib.loads(existing_wrapper.read_text(encoding='utf-8'))
            self.assertEqual(wrapper['name'], 'change-set-verifier')
            self.assertEqual(
                wrapper['description'],
                'Normalizes and verifies a coherent completed change set, then returns semantic '
                'diagnostics to the parent agent.',
            )
            self.assertEqual(wrapper['model'], 'json-selected-model')
            self.assertEqual(wrapper['model_reasoning_effort'], 'medium')
            self.assertEqual(wrapper['sandbox_mode'], 'workspace-write')

    def test_sync_does_not_invent_missing_codex_model_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text('agent\n', encoding='utf-8')
            existing_wrapper = target / '.codex' / 'agents' / 'change-set-verifier.toml'
            existing_wrapper.parent.mkdir(parents=True)
            existing_wrapper.write_text('model = "project-model"\n', encoding='utf-8')
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            public_config['platforms']['agent_wrappers'] = [
                wrapper
                for wrapper in public_config['platforms']['agent_wrappers']
                if wrapper['template'] == 'agent_wrapper.codex.toml'
            ]
            local_config = sync.discover_local_assets(target, public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            self.assertEqual(
                existing_wrapper.read_text(encoding='utf-8'),
                'model = "project-model"\n',
            )
            with self.assertRaises(sync.SyncError) as error:
                sync.sync_public_assets(
                    context,
                    public_config,
                    local_config,
                    require_agent_runtime=True,
                )

            self.assertIn('model_reasoning_effort', str(error.exception))

    def test_strict_sync_rejects_missing_reviewed_agent_models(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text('agent\n', encoding='utf-8')
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            context = sync.SyncContext(target, source, skill_root, False, [])

            with self.assertRaises(sync.SyncError) as error:
                sync.sync_public_assets(
                    context,
                    public_config,
                    {'rules': [], 'agent_prompts': []},
                    require_agent_runtime=True,
                )

            self.assertIn('requires reviewed fields: model', str(error.exception))

    def test_sync_uses_explicit_cursor_model_instead_of_target_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text('agent\n', encoding='utf-8')
            existing_wrapper = target / '.cursor' / 'agents' / 'change-set-verifier.md'
            existing_wrapper.parent.mkdir(parents=True)
            existing_wrapper.write_text(
                '---\nname: stale\ndescription: stale\n'
                'model: project-reviewed-cursor-model\nreadonly: false\n---\nstale body\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            public_config['platforms']['agent_wrappers'] = [
                wrapper
                for wrapper in public_config['platforms']['agent_wrappers']
                if wrapper['template'] == 'agent_wrapper.cursor.md'
            ]
            local_config = sync.discover_local_assets(target, public_config)
            local_config['cursor_agent_runtime_overrides'] = {
                'change-set-verifier': {'model': 'json-selected-cursor-model'}
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                local_config,
                require_agent_runtime=True,
            )

            frontmatter = sync._read_frontmatter(existing_wrapper)
            self.assertEqual(frontmatter['name'], 'change-set-verifier')
            self.assertEqual(frontmatter['model'], 'json-selected-cursor-model')
            self.assertIs(frontmatter['readonly'], False)
            self.assertIn(
                'Apply @.agents/agents/change-set-verifier.md',
                existing_wrapper.read_text(encoding='utf-8'),
            )

    def test_sync_uses_explicit_github_model_instead_of_target_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text('agent\n', encoding='utf-8')
            existing_wrapper = target / '.github' / 'agents' / 'change-set-verifier.agent.md'
            existing_wrapper.parent.mkdir(parents=True)
            existing_wrapper.write_text(
                '---\nname: stale\ndescription: stale\n'
                'model: project-reviewed-github-model\n'
                'disable-model-invocation: true\n---\nstale body\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            public_config['platforms']['agent_wrappers'] = [
                wrapper
                for wrapper in public_config['platforms']['agent_wrappers']
                if wrapper['template'] == 'agent_wrapper.github.agent.md'
            ]
            local_config = sync.discover_local_assets(target, public_config)
            local_config['github_agent_runtime_overrides'] = {
                'change-set-verifier': {'model': 'json-selected-github-model'}
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                local_config,
                require_agent_runtime=True,
            )

            frontmatter = sync._read_frontmatter(existing_wrapper)
            self.assertEqual(frontmatter['name'], 'change-set-verifier')
            self.assertEqual(frontmatter['model'], 'json-selected-github-model')
            self.assertIs(frontmatter['disable-model-invocation'], False)
            self.assertIn(
                'Apply @.agents/agents/change-set-verifier.md',
                existing_wrapper.read_text(encoding='utf-8'),
            )

    def test_strict_sync_accepts_explicit_models_for_every_agent_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text('agent\n', encoding='utf-8')

            codex_wrapper = target / '.codex' / 'agents' / 'change-set-verifier.toml'
            codex_wrapper.parent.mkdir(parents=True)
            codex_wrapper.write_text(
                'model = "project-codex-model"\n'
                'model_reasoning_effort = "high"\n',
                encoding='utf-8',
            )
            cursor_wrapper = target / '.cursor' / 'agents' / 'change-set-verifier.md'
            cursor_wrapper.parent.mkdir(parents=True)
            cursor_wrapper.write_text(
                '---\nmodel: project-cursor-model\nreadonly: false\n---\nstale\n',
                encoding='utf-8',
            )
            github_wrapper = target / '.github' / 'agents' / 'change-set-verifier.agent.md'
            github_wrapper.parent.mkdir(parents=True)
            github_wrapper.write_text(
                '---\nmodel: project-github-model\n---\nstale\n',
                encoding='utf-8',
            )

            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            local_config = sync.discover_local_assets(target, public_config)
            local_config.update(
                {
                    'codex_agent_runtime_overrides': {
                        'change-set-verifier': {
                            'model': 'json-codex-model',
                            'model_reasoning_effort': 'high',
                        }
                    },
                    'cursor_agent_runtime_overrides': {
                        'change-set-verifier': {'model': 'json-cursor-model'}
                    },
                    'github_agent_runtime_overrides': {
                        'change-set-verifier': {'model': 'json-github-model'}
                    },
                }
            )
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                local_config,
                require_agent_runtime=True,
            )

            codex = tomllib.loads(codex_wrapper.read_text(encoding='utf-8'))
            self.assertEqual(codex['model'], 'json-codex-model')
            self.assertEqual(codex['model_reasoning_effort'], 'high')
            self.assertEqual(
                sync._read_frontmatter(cursor_wrapper)['model'],
                'json-cursor-model',
            )
            self.assertEqual(
                sync._read_frontmatter(github_wrapper)['model'],
                'json-github-model',
            )
            self.assertIs(
                sync._read_frontmatter(github_wrapper)['disable-model-invocation'],
                False,
            )

    def test_sync_reconciles_catalog_declared_root_config_for_agent_discovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text('agent\n', encoding='utf-8')
            codex_wrapper = target / '.codex' / 'agents' / 'change-set-verifier.toml'
            codex_wrapper.parent.mkdir(parents=True)
            codex_wrapper.write_text(
                'model = "project-codex-model"\n'
                'model_reasoning_effort = "high"\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            codex_config = tomllib.loads(
                (target / '.codex' / 'config.toml').read_text(encoding='utf-8')
            )
            self.assertIs(codex_config['features']['multi_agent'], True)
            self.assertFalse((target / '.cursor' / 'mcp.json').exists())

    def test_setup_skill_delegates_deterministic_configuration_to_sync_script(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized = ' '.join(content.split())

        self.assertIn(
            'Let the synchronization script maintain deterministic configuration.',
            normalized,
        )
        self.assertIn('sync_public_agent_assets.py', normalized)
        for detail in (
            '.codex/config.toml',
            'features.multi_agent',
            'disable-model-invocation',
            'agent/runSubagent',
            'chat.subagents.allowInvocationsFromSubagents',
        ):
            self.assertNotIn(detail, content)

    def test_setup_skill_names_public_archive_url(self):
        expected = 'https://github.com/wenyue/agents/archive/refs/heads/master.zip'
        skill_paths = (
            REPO_SKILL_ROOT / 'SKILL.md',
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md',
        )

        for skill_path in skill_paths:
            with self.subTest(skill_path=skill_path):
                content = skill_path.read_text(encoding='utf-8')
                self.assertIn(expected, content)

    def test_setup_skill_uses_previous_content_only_as_generation_reference(self):
        english = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        chinese = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md'
        ).read_text(encoding='utf-8')

        self.assertIn(
            'Use current repository evidence; previous content may be used as a reference during '
            'generation, but it is not a source of truth.',
            ' '.join(english.split()),
        )
        self.assertIn(
            '旧内容可在生成过程中作为参考，但不是事实源。',
            ' '.join(chinese.split()),
        )

    def test_setup_skill_configures_every_catalog_declared_platform(self):
        english = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        chinese = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        normalized_english = ' '.join(english.split())
        normalized_chinese = ' '.join(chinese.split())

        self.assertIn('synchronizes every catalog-declared platform', normalized_english)
        self.assertIn('同步公共目录声明的 所有平台', normalized_chinese)
        for forbidden in (
            'installed or explicitly targeted',
            'installed or targeted',
            'Discover installed',
            'or is named in an explicit unresolved blocker',
        ):
            self.assertNotIn(forbidden, normalized_english)
        for forbidden in (
            '已安装或用户明确要求支持',
            '已安装或指定',
            '发现已安装',
            '或已列入明确的未解决阻塞项',
        ):
            self.assertNotIn(forbidden, normalized_chinese)

    def test_setup_skill_uses_two_stage_model_json(self):
        english = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        chinese = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        normalized_english = ' '.join(english.split())
        normalized_chinese = ' '.join(chinese.split())

        for required in (
            '--model-request',
            '`required_intelligence`',
            '`model` for Codex, Cursor, and GitHub',
            '`model_reasoning_effort` for Codex',
            '--model-config',
            'Existing wrappers are not a value source',
        ):
            self.assertIn(required, normalized_english)
        for required in (
            '--model-request',
            '`required_intelligence`',
            '为 Codex、Cursor 和 GitHub 选择 `model`',
            '为 Codex 选择 `model_reasoning_effort`',
            '--model-config',
            '现有 Wrapper 不是取值来源',
        ):
            self.assertIn(required, normalized_chinese)

    def test_setup_skill_keeps_model_json_in_system_temp_directory(self):
        skill_paths = (
            REPO_SKILL_ROOT / 'SKILL.md',
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md',
        )

        for skill_path in skill_paths:
            with self.subTest(skill_path=skill_path):
                content = skill_path.read_text(encoding='utf-8')
                self.assertIn('tempfile.gettempdir()', content)
                self.assertNotIn('.agents/setup-project-agent-models.json', content)

    def test_setup_skill_delegates_generation_and_validation_to_each_blueprint(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized = ' '.join(content.split())

        for generated_rule in (
            '20-project-tools.md',
            '21-project-rules.md',
            '22-project-structure.md',
        ):
            self.assertIn(generated_rule, normalized)
        for generated_skill in (
            'worktree-environment-setup',
            'change-set-verification',
        ):
            self.assertIn(generated_skill, normalized)
        self.assertIn('Each blueprint owns its generation and validation.', normalized)
        self.assertIn(
            'https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/',
            normalized,
        )
        self.assertIn(
            'https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/',
            normalized,
        )
        self.assertNotIn('references/generation-contracts', normalized)

    def test_setup_skill_generates_assets_before_applying_model_config(self):
        english = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        chinese = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md'
        ).read_text(encoding='utf-8')

        self.assertLess(english.index('Open and execute'), english.index('--model-config'))
        self.assertLess(chinese.index('依次打开并执行'), chinese.index('--model-config'))
        self.assertNotIn('Reapply `$MODEL_CONFIG`', english)
        self.assertNotIn('再次应用 `$MODEL_CONFIG`', chinese)

    def test_setup_skill_excludes_public_source_maintenance(self):
        english = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        chinese = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md'
        ).read_text(encoding='utf-8')

        for forbidden in (
            'public source owner',
            'Root configuration declarations and conditions belong',
            'Declare each managed entry file',
            'For public-source edits',
            'test_sync_public_agent_assets.py',
        ):
            self.assertNotIn(forbidden, english)
        for forbidden in (
            '公共源的维护者',
            '根配置的声明和适用条件属于',
            '每个托管入口文件都必须在',
            '修改 `wenyue/agents` 公共源时',
            'test_sync_public_agent_assets.py',
        ):
            self.assertNotIn(forbidden, chinese)

    def test_setup_skill_directory_excludes_repository_tests(self):
        self.assertEqual(list((REPO_SKILL_ROOT / 'scripts').glob('test_*.py')), [])

    def test_setup_skill_excludes_real_model_smoke_tests(self):
        english = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        chinese = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'setup-project-agents' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        normalized_english = ' '.join(english.split())
        normalized_chinese = ' '.join(chinese.split())

        self.assertIn('Do not invoke a real model', normalized_english)
        self.assertNotIn('safe representative invocation', normalized_english)
        self.assertNotIn('smoke checks', normalized_english)
        self.assertIn('不得调用真实模型', normalized_chinese)
        self.assertNotIn('安全的代表性调用方式', normalized_chinese)
        self.assertNotIn('冒烟检查', normalized_chinese)

    def test_repository_local_agents_contains_only_curated_assets(self):
        local_root = REPO_ROOT / '.agents'
        expected_rules = {
            '00-global-rule-config.md',
            '01-global-personality.md',
            '02-global-response-format.md',
            '03-global-reasoning-workflow.md',
            '04-global-skill-config.md',
            '10-base-code.md',
            '20-project-tools.md',
            '21-project-rules.md',
            '22-project-structure.md',
        }
        expected_skills = {
            'change-set-verification',
            'track-worktree-time',
            'worktree-integrate',
            'write-rule',
            'write-skill',
        }

        self.assertEqual(
            {path.name for path in (local_root / 'rules').iterdir()},
            expected_rules,
        )
        self.assertEqual(
            {path.name for path in (local_root / 'skills').iterdir()},
            expected_skills,
        )
        self.assertEqual(
            {path.name for path in (local_root / 'agents').iterdir()},
            {'change-set-verifier.md'},
        )

    def test_public_manifest_declares_generic_root_config_locks(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
        root_configs = public_config['root_configs']
        codex_config = next(
            item for item in root_configs if item['path'] == '.codex/config.toml'
        )

        self.assertEqual(codex_config['format'], 'toml')
        self.assertIn(
            {
                'path': 'features.multi_agent',
                'value': True,
                'when': {'path_glob_exists': '.codex/agents/*.toml'},
            },
            codex_config['locked_values'],
        )

    def test_public_manifest_declares_agents_entry_template(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertEqual(
            public_config.get('entry_files'),
            [
                {
                    'template': 'AGENTS.md',
                    'path': 'AGENTS.md',
                }
            ],
        )

    def _assert_strict_native_config_error(
        self,
        relative_path: str,
        content: str,
        expected_error: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            source = root / 'agents'
            config_path = target / relative_path
            config_path.parent.mkdir(parents=True)
            config_path.write_text(content, encoding='utf-8')
            source.mkdir(parents=True)
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            public_config['platforms'] = {'rule_wrappers': [], 'agent_wrappers': []}
            context = sync.SyncContext(target, source, REPO_SKILL_ROOT, True, [])

            with self.assertRaises(sync.SyncError) as error:
                sync.sync_public_assets(
                    context,
                    public_config,
                    {'rules': [], 'agent_prompts': []},
                )

        self.assertIn(expected_error, str(error.exception))

    def test_strict_sync_rejects_invalid_existing_native_platform_config(self):
        self._assert_strict_native_config_error(
            '.codex/config.toml',
            '[agents\n',
            'Invalid native platform config .codex/config.toml',
        )

    def test_strict_sync_rejects_missing_codex_agent_config_reference(self):
        self._assert_strict_native_config_error(
            '.codex/config.toml',
            '[agents.reviewer]\n'
            'description = "Review changes"\n'
            'config_file = "./agents/reviewer.toml"\n',
            'Codex agent reviewer references missing config file .codex/agents/reviewer.toml',
        )

    def test_strict_sync_rejects_invalid_copilot_mcp_root_structure(self):
        self._assert_strict_native_config_error(
            '.vscode/mcp.json',
            '{"mcpServers": {}}',
            'Native platform config .vscode/mcp.json requires a top-level servers object',
        )

    def test_strict_sync_rejects_invalid_cursor_mcp_root_structure(self):
        self._assert_strict_native_config_error(
            '.cursor/mcp.json',
            '{"servers": {}}',
            'Native platform config .cursor/mcp.json requires a top-level mcpServers object',
        )

    def test_strict_sync_rejects_invalid_copilot_cli_mcp_root_structure(self):
        for relative_path in ('.mcp.json', '.github/mcp.json'):
            with self.subTest(relative_path=relative_path):
                self._assert_strict_native_config_error(
                    relative_path,
                    '{"servers": {}}',
                    f'Native platform config {relative_path} requires a top-level '
                    'mcpServers object',
                )

    def test_sync_locks_required_codex_root_config_value(self):
        cases = (
            None,
            'model = "project-model"\n[features]\nother = true\nmulti_agent = false\n',
            'model = "project-model"\nfeatures.multi_agent = false\n',
            '[features]\nmulti_agent = true\n',
        )
        for config_content in cases:
            with (
                self.subTest(config_content=config_content),
                tempfile.TemporaryDirectory() as temp_dir,
            ):
                root = Path(temp_dir)
                target = root / 'target'
                source = root / 'agents'
                agent_path = target / '.codex' / 'agents' / 'reviewer.toml'
                agent_path.parent.mkdir(parents=True)
                agent_path.write_text('name = "reviewer"\n', encoding='utf-8')
                if config_content is not None:
                    (target / '.codex' / 'config.toml').write_text(
                        config_content,
                        encoding='utf-8',
                    )
                source.mkdir(parents=True)
                public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
                public_config['rules'] = []
                public_config['skills'] = []
                public_config['agent_prompts'] = []
                public_config['platforms'] = {'rule_wrappers': [], 'agent_wrappers': []}
                context = sync.SyncContext(target, source, REPO_SKILL_ROOT, False, [])

                sync.sync_public_assets(
                    context,
                    public_config,
                    {'rules': [], 'agent_prompts': []},
                )

                parsed = tomllib.loads(
                    (target / '.codex' / 'config.toml').read_text(encoding='utf-8')
                )
                self.assertIs(parsed['features']['multi_agent'], True)
                if config_content and 'project-model' in config_content:
                    self.assertEqual(parsed['model'], 'project-model')
                    if 'other' in config_content:
                        self.assertIs(parsed['features']['other'], True)

                second_context = sync.SyncContext(
                    target,
                    source,
                    REPO_SKILL_ROOT,
                    False,
                    [],
                )
                sync.sync_public_assets(
                    second_context,
                    public_config,
                    {'rules': [], 'agent_prompts': []},
                )
                self.assertIn(
                    sync.Change('unchanged', '.codex/config.toml'),
                    second_context.changes,
                )

    def test_sync_locks_generic_json_root_config_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            source = root / 'agents'
            trigger = target / '.tool' / 'agents' / 'reviewer.json'
            trigger.parent.mkdir(parents=True)
            trigger.write_text('{}\n', encoding='utf-8')
            config_path = target / '.tool' / 'config.json'
            config_path.write_text(
                '{"feature": {"enabled": false}, "keep": {"value": 7}}\n',
                encoding='utf-8',
            )
            source.mkdir(parents=True)
            public_config = {
                'rules': [],
                'skills': [],
                'agent_prompts': [],
                'platforms': {'rule_wrappers': [], 'agent_wrappers': []},
                'root_configs': [
                    {
                        'path': '.tool/config.json',
                        'format': 'json',
                        'locked_values': [
                            {
                                'path': 'feature.enabled',
                                'value': True,
                                'when': {
                                    'path_glob_exists': '.tool/agents/*.json',
                                },
                            }
                        ],
                    }
                ],
            }
            context = sync.SyncContext(target, source, REPO_SKILL_ROOT, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            parsed = json.loads(config_path.read_text(encoding='utf-8'))
            self.assertIs(parsed['feature']['enabled'], True)
            self.assertEqual(parsed['keep'], {'value': 7})

    def test_check_reports_locked_root_config_drift_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            source = root / 'agents'
            agent_path = target / '.codex' / 'agents' / 'reviewer.toml'
            agent_path.parent.mkdir(parents=True)
            agent_path.write_text('name = "reviewer"\n', encoding='utf-8')
            config_path = target / '.codex' / 'config.toml'
            config_path.write_text('[features]\nmulti_agent = false\n', encoding='utf-8')
            source.mkdir(parents=True)
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            public_config['platforms'] = {'rule_wrappers': [], 'agent_wrappers': []}
            context = sync.SyncContext(target, source, REPO_SKILL_ROOT, True, [])

            sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            self.assertIn(
                sync.Change('updated', '.codex/config.toml'),
                context.changes,
            )
            self.assertIn('multi_agent = false', config_path.read_text(encoding='utf-8'))

    def test_sync_preserves_custom_platform_only_agent_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            stale_wrapper = target / '.github' / 'agents' / 'obsolete-agent.agent.md'
            stale_wrapper.parent.mkdir(parents=True)
            stale_wrapper.write_text('# Custom platform-only agent\n', encoding='utf-8')
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            local_config = {'rules': [], 'agent_prompts': []}
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            self.assertTrue(stale_wrapper.exists())

    def test_sync_deletes_stale_generated_agent_wrapper_when_agent_is_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            stale_wrapper = target / '.github' / 'agents' / 'obsolete-agent.agent.md'
            stale_wrapper.parent.mkdir(parents=True)
            stale_wrapper.write_text(
                '---\nname: obsolete-agent\ndescription: Obsolete\n---\n\n'
                'Apply @.agents/agents/obsolete-agent.md\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            local_config = {'rules': [], 'agent_prompts': []}
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            self.assertFalse(stale_wrapper.exists())

    def test_sync_deletes_agent_and_wrappers_declared_retired_by_catalog(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / 'agents' / 'agents'
            target_agents = target / '.agents' / 'agents'
            source_agents.mkdir(parents=True)
            target_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'current-verifier.md').write_text(
                'current verifier\n',
                encoding='utf-8',
            )
            (target_agents / 'old-verifier.md').write_text(
                'project-owned modifications do not block explicit name retirement\n',
                encoding='utf-8',
            )
            current_wrapper = target / '.codex' / 'agents' / 'current-verifier.toml'
            current_wrapper.parent.mkdir(parents=True)
            current_wrapper.write_text(
                'model = "project-reviewed-model"\n'
                'model_reasoning_effort = "medium"\n',
                encoding='utf-8',
            )
            old_wrapper = target / '.codex' / 'agents' / 'old-verifier.toml'
            old_wrapper.write_text(
                'custom = "content does not block explicit retirement"\n',
                encoding='utf-8',
            )
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = []
            public_config['skills'] = []
            public_config['skill_blueprints'] = []
            public_config['retired_assets'] = {
                'rules': [],
                'skills': [],
                'agents': ['old-verifier'],
            }
            public_config['agent_prompts'] = [
                {
                    'name': 'current-verifier',
                    'description': 'Current verifier',
                    'codex': {
                        'sandbox_mode': 'workspace-write',
                    },
                }
            ]
            context = sync.SyncContext(target, source, skill_root, False, [])
            local_config = sync.discover_local_assets(target, public_config)

            changes = sync.sync_public_assets(
                context,
                public_config,
                local_config,
            )

            self.assertFalse((target_agents / 'old-verifier.md').exists())
            self.assertFalse(old_wrapper.exists())
            self.assertEqual(
                (target_agents / 'current-verifier.md').read_text(encoding='utf-8'),
                'current verifier\n',
            )
            self.assertTrue(
                current_wrapper.is_file()
            )
            self.assertIn(sync.Change('deleted', '.agents/agents/old-verifier.md'), changes)
            self.assertIn(sync.Change('deleted', '.codex/agents/old-verifier.toml'), changes)

    def test_sync_generates_configured_agents_entry_from_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            templates.mkdir(parents=True)
            (templates / 'project_agents.md').write_text(
                '# Project Agent Entry\n\n{{global_rule_rows}}\n{{base_rule_rows}}\n{{project_rule_rows}}\n',
                encoding='utf-8',
            )
            source_rules = source / 'agents' / 'rules'
            source_rules.mkdir(parents=True)
            (source_rules / '00-global-rule-config.md').write_text('rule\n', encoding='utf-8')
            (source_rules / '20-project-tools.md').write_text('rule\n', encoding='utf-8')
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = [
                rule
                for rule in public_config['rules']
                if rule['file'] == '00-global-rule-config.md'
            ]
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            public_config['entry_files'] = [
                {
                    'template': 'project_agents.md',
                    'path': 'config/AGENTS.md',
                }
            ]
            public_config['platforms'] = {'rule_wrappers': [], 'agent_wrappers': []}
            local_config = {
                'rules': [
                    {
                        'file': '20-project-tools.md',
                        'read_when': 'Project tooling, MCP, runtime, or verification',
                        'strength': 'Mandatory',
                        'section': 'project',
                    },
                ],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            entry_path = target / 'config' / 'AGENTS.md'
            self.assertTrue(entry_path.is_file())
            entry = entry_path.read_text(encoding='utf-8')
            self.assertIn(
                '| Starting any repository task | `.agents/rules/00-global-rule-config.md` |'
                ' `Mandatory` |',
                entry,
            )
            self.assertIn(
                '| Project tooling, MCP, runtime, or verification |'
                ' `.agents/rules/20-project-tools.md` | `Mandatory` |',
                entry,
            )

    def test_sync_rejects_entry_file_paths_outside_owned_roots(self):
        cases = (
            (
                'template',
                '../AGENTS.md',
                r'entry_files\[0\]\.template must stay inside assets/templates',
            ),
            (
                'path',
                '../AGENTS.md',
                r'entry_files\[0\]\.path must stay inside the target repository',
            ),
        )
        for field, value, expected_error in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = root / 'agents'
                target = root / 'target'
                skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
                templates = skill_root / 'assets' / 'templates'
                templates.mkdir(parents=True)
                (templates / 'AGENTS.md').write_text('entry\n', encoding='utf-8')
                entry_file = {
                    'template': 'AGENTS.md',
                    'path': 'AGENTS.md',
                }
                entry_file[field] = value
                public_config = {
                    'rules': [],
                    'skills': [],
                    'agent_prompts': [],
                    'entry_files': [entry_file],
                    'root_configs': [],
                    'platforms': {'rule_wrappers': [], 'agent_wrappers': []},
                }
                context = sync.SyncContext(target, source, skill_root, False, [])

                with self.assertRaisesRegex(sync.SyncError, expected_error):
                    sync.sync_public_assets(
                        context,
                        public_config,
                        {'rules': [], 'agent_prompts': []},
                    )

    def test_sync_does_not_create_missing_rule_blueprint_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_blueprints = source / 'agents' / 'blueprints' / 'rules'
            source_blueprints.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_blueprints / '20-project-tools.md').write_text(
                'project tools blueprint\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            target_rule = target / '.agents' / 'rules' / '20-project-tools.md'
            self.assertFalse(target_rule.exists())
            self.assertNotIn(sync.Change('created', '.agents/rules/20-project-tools.md'), changes)

    def test_sync_deletes_generated_skill_declared_retired_by_catalog(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = (
                source / 'agents' / 'blueprints' / 'skills' / 'worktree-environment-setup'
            )
            legacy_skill = target / '.agents' / 'skills' / 'project-development-workflow'
            source_skill.mkdir(parents=True)
            legacy_skill.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_skill / 'SKILL.md').write_text(
                '---\n'
                'name: worktree-environment-setup\n'
                'description: Generator contract\n'
                '---\n',
                encoding='utf-8',
            )
            (legacy_skill / 'SKILL.md').write_text(
                '---\n'
                'name: project-development-workflow\n'
                'description: Legacy\n'
                '---\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'retired_assets': {
                    'rules': [],
                    'skills': ['project-development-workflow'],
                    'agents': [],
                },
                'rules': [],
                'skills': [],
                'skill_blueprints': [{'name': 'worktree-environment-setup'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertFalse(legacy_skill.exists())
            self.assertFalse(
                (target / '.agents' / 'skills' / 'worktree-environment-setup').exists()
            )
            self.assertIn(
                sync.Change('deleted', '.agents/skills/project-development-workflow/SKILL.md'),
                changes,
            )

    def test_sync_deletes_another_generated_skill_declared_retired_by_catalog(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = (
                source / 'agents' / 'blueprints' / 'skills' / 'change-set-verification'
            )
            legacy_skill = target / '.agents' / 'skills' / 'project-verification'
            source_skill.mkdir(parents=True)
            legacy_skill.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_skill / 'SKILL.md').write_text(
                '---\nname: change-set-verification\ndescription: Generator contract\n---\n',
                encoding='utf-8',
            )
            (legacy_skill / 'SKILL.md').write_text(
                '---\nname: project-verification\ndescription: Legacy generator\n---\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'retired_assets': {
                    'rules': [],
                    'skills': ['project-verification'],
                    'agents': [],
                },
                'rules': [],
                'skills': [],
                'skill_blueprints': [{'name': 'change-set-verification'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            self.assertFalse(legacy_skill.exists())
            self.assertFalse(
                (target / '.agents' / 'skills' / 'change-set-verification').exists()
            )

            self.assertIn(
                sync.Change('deleted', '.agents/skills/project-verification/SKILL.md'),
                changes,
            )

    def test_sync_does_not_copy_project_blueprints_into_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_rule = source / 'agents' / 'blueprints' / 'rules' / '20-project-tools.md'
            source_skill = (
                source / 'agents' / 'blueprints' / 'skills' / 'change-set-verification'
            )
            source_setup_skill = source / 'agents' / 'skills' / 'setup-project-agents'
            source_rule.parent.mkdir(parents=True)
            source_skill.mkdir(parents=True)
            source_setup_skill.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            source_rule.write_text('project rule contract\n', encoding='utf-8')
            (source_skill / 'SKILL.md').write_text(
                'project skill contract\n',
                encoding='utf-8',
            )
            (source_setup_skill / 'SKILL.md').write_text(
                'setup contract\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [{'name': 'setup-project-agents'}],
                'rule_blueprints': [{'file': '20-project-tools.md'}],
                'skill_blueprints': [{'name': 'change-set-verification'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            contracts = skill_root / 'references' / 'generation-contracts'
            self.assertFalse(contracts.exists())
            self.assertFalse(
                (target / '.agents' / 'skills' / 'change-set-verification').exists()
            )

    def test_check_reports_missing_project_generation_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            source = root / 'source'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            target.mkdir()
            skill_root.mkdir(parents=True)
            public_config = {
                'rules': [],
                'skills': [],
                'rule_blueprints': [{'file': '20-project-tools.md'}],
                'skill_blueprints': [{'name': 'change-set-verification'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, True, [])

            changes = sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            self.assertIn(
                sync.Change('missing', '.agents/rules/20-project-tools.md'),
                changes,
            )
            self.assertIn(
                sync.Change(
                    'missing',
                    '.agents/skills/change-set-verification/SKILL.md',
                ),
                changes,
            )

    def test_retired_project_development_workflow_is_absent(self):
        self.assertFalse(
            (REPO_ROOT / 'agents' / 'skills' / 'project-development-workflow').exists()
        )

    def test_public_config_lists_skill_blueprints(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        blueprint_names = {
            blueprint['name'] for blueprint in public_config['skill_blueprints']
        }

        self.assertIn('worktree-environment-setup', blueprint_names)
        self.assertIn('change-set-verification', blueprint_names)

    def test_public_blueprints_use_a_separate_catalog_namespace(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertNotIn('project_rule_generators', public_config)
        self.assertNotIn('project_skill_generators', public_config)
        self.assertIn('rule_blueprints', public_config)
        self.assertIn('skill_blueprints', public_config)

        for filename in (
            '20-project-tools.md',
            '21-project-rules.md',
            '22-project-structure.md',
        ):
            for catalog in ('agents', 'agents-zh'):
                self.assertTrue(
                    (REPO_ROOT / catalog / 'blueprints' / 'rules' / filename).is_file()
                )
            self.assertFalse((REPO_ROOT / 'agents' / 'rules' / filename).exists())
            self.assertFalse((REPO_ROOT / 'agents-zh' / 'rules' / filename).exists())

        for name in ('worktree-environment-setup', 'change-set-verification'):
            for catalog in ('agents', 'agents-zh'):
                self.assertTrue(
                    (
                        REPO_ROOT
                        / catalog
                        / 'blueprints'
                        / 'skills'
                        / name
                        / 'SKILL.md'
                    ).is_file()
                )
            self.assertFalse((REPO_ROOT / 'agents' / 'skills' / name).exists())
            self.assertFalse((REPO_ROOT / 'agents-zh' / 'skills' / name).exists())

    def test_public_config_owns_rule_blueprint_routing(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn('rule_blueprints', public_config)
        self.assertEqual(
            public_config['rule_blueprints'],
            [
                {
                    'file': '20-project-tools.md',
                    'read_when': 'Project tooling, MCP, runtime, or verification',
                    'strength': 'Mandatory',
                    'section': 'project',
                    'cursor': {'alwaysApply': True},
                    'github': {'applyTo': '**'},
                },
                {
                    'file': '21-project-rules.md',
                    'read_when': (
                        'Project APIs, generated files, lint, or domain conventions'
                    ),
                    'strength': 'Default',
                    'section': 'project',
                    'cursor': {'alwaysApply': True},
                    'github': {'applyTo': '**'},
                },
                {
                    'file': '22-project-structure.md',
                    'read_when': (
                        'Making structure, module, or dependency-boundary decisions'
                    ),
                    'strength': 'Advisory',
                    'section': 'project',
                    'cursor': {'alwaysApply': True},
                    'github': {'applyTo': '**'},
                },
            ],
        )

    def test_public_config_exposes_only_change_set_verifier(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertEqual(
            public_config['agent_prompts'],
            [
                {
                    'name': 'change-set-verifier',
                    'description': (
                        'Normalizes and verifies a coherent completed change set, then returns '
                        'semantic diagnostics to the parent agent.'
                    ),
                    'required_intelligence': (
                        'Medium: follow the explicit verification contract, run the required '
                        'checks, preserve unrelated work, and return diagnostics without making '
                        "semantic fixes. Select each platform's current balanced general-purpose "
                        'model tier—the tier between the flagship/deepest model and the fastest/'
                        'lightweight model—and use medium reasoning effort where supported. '
                        'Prefer capability, latency, and cost balance; escalate to a flagship '
                        'model only when repository evidence shows that the verification task '
                        'requires deeper judgment.'
                    ),
                    'codex': {
                        'sandbox_mode': 'workspace-write',
                    },
                    'cursor': {
                        'readonly': False,
                    },
                }
            ],
        )

    def test_public_config_cannot_own_target_agent_models(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
        public_config['agent_prompts'][0]['codex']['model'] = 'hardcoded-model'

        with self.assertRaises(sync.SyncError) as error:
            sync._validate_public_agent_model_ownership(public_config)

        self.assertIn(
            'must not define target-owned codex fields: model',
            str(error.exception),
        )

    def test_agent_runtime_model_fields_reject_empty_values(self):
        for platform, field in (
            ('codex', 'model'),
            ('codex', 'model_reasoning_effort'),
            ('cursor', 'model'),
            ('github', 'model'),
        ):
            with self.subTest(platform=platform, field=field):
                with self.assertRaises(sync.SyncError) as error:
                    sync._agent_data(
                        {
                            'name': 'sample-agent',
                            platform: {field: '   '},
                        }
                    )

                self.assertIn('must be a non-empty string', str(error.exception))

    def test_public_config_is_the_only_source_of_retired_asset_names(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
        script = (REPO_SKILL_ROOT / 'scripts' / 'sync_public_agent_assets.py').read_text(
            encoding='utf-8'
        )

        self.assertEqual(
            public_config['retired_assets'],
            {
                'rules': [
                    '03-global-engineering-workflow.md',
                    '03-global-skill-config.md',
                ],
                'skills': [
                    'update-project-rules',
                    'project-development-workflow',
                    'project-verification',
                ],
                'agents': ['rename', 'verifier'],
            },
        )
        for retired_name in (
            '03-global-engineering-workflow.md',
            '03-global-skill-config.md',
            'update-project-rules',
            'project-development-workflow',
            'project-verification',
            'rename',
            'verifier',
        ):
            self.assertNotIn(retired_name, script)

    def test_retired_assets_reject_unsafe_names_and_active_overlap(self):
        with self.assertRaisesRegex(sync.SyncError, 'Unsafe retired asset name'):
            sync._retired_assets(
                {
                    'retired_assets': {
                        'rules': [],
                        'skills': ['../outside'],
                        'agents': [],
                    }
                }
            )
        with self.assertRaisesRegex(sync.SyncError, 'Unsafe retired asset name'):
            sync._retired_assets(
                {
                    'retired_assets': {
                        'rules': [],
                        'skills': ['..'],
                        'agents': [],
                    }
                }
            )
        with self.assertRaisesRegex(sync.SyncError, 'active and retired'):
            sync._retired_assets(
                {
                    'retired_assets': {
                        'rules': [],
                        'skills': [],
                        'agents': ['same-agent'],
                    },
                    'agent_prompts': [{'name': 'same-agent'}],
                }
            )
        with self.assertRaisesRegex(sync.SyncError, 'active and retired'):
            sync._retired_assets(
                {
                    'retired_assets': {
                        'rules': ['20-project-tools.md'],
                        'skills': [],
                        'agents': [],
                    },
                    'rule_blueprints': [{'file': '20-project-tools.md'}],
                }
            )

    def test_public_config_lists_worktree_integrate_skill(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn({'name': 'worktree-integrate'}, public_config['skills'])

    def test_public_config_lists_track_worktree_time_skill(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn({'name': 'track-worktree-time'}, public_config['skills'])

    def test_global_rules_separate_personality_workflow_and_skill_configuration(self):
        source_root = REPO_ROOT / 'agents' / 'rules'
        mirror_root = REPO_ROOT / 'agents-zh' / 'rules'
        personality = (source_root / '01-global-personality.md').read_text(encoding='utf-8')
        workflow = (source_root / '03-global-reasoning-workflow.md').read_text(
            encoding='utf-8'
        )
        skill_config = (source_root / '04-global-skill-config.md').read_text(
            encoding='utf-8'
        )
        mirror_personality = (mirror_root / '01-global-personality.md').read_text(
            encoding='utf-8'
        )
        mirror_workflow = (mirror_root / '03-global-reasoning-workflow.md').read_text(
            encoding='utf-8'
        )
        mirror_skill_config = (mirror_root / '04-global-skill-config.md').read_text(
            encoding='utf-8'
        )

        self.assertTrue(personality.startswith('# Agent Personality\n'))
        self.assertIn('## Reasoning', personality)
        self.assertNotIn('## Act', personality)
        self.assertTrue(workflow.startswith('# Reasoning Workflow\n'))
        self.assertIn('## Decide', workflow)
        self.assertIn('## Act', workflow)
        self.assertIn('## Verify', workflow)
        self.assertIn('The original request does not count as confirmation.', workflow)
        self.assertIn(
            'For advisory or informational questions, search the web before answering and ground '
            'the response in current sources.',
            ' '.join(workflow.split()),
        )
        self.assertTrue(skill_config.startswith('# Workflow Configuration\n'))
        self.assertTrue(mirror_personality.startswith('# Agent 人格\n'))
        self.assertIn('## 推理方式', mirror_personality)
        self.assertTrue(mirror_workflow.startswith('# 思考流程\n'))
        self.assertIn('## 判断', mirror_workflow)
        self.assertIn('## 行动', mirror_workflow)
        self.assertIn('## 验证', mirror_workflow)
        self.assertIn('原始请求不构成确认。', mirror_workflow)
        self.assertIn(
            '对于咨询或信息类问题，回答前先搜索网上资料，并以当前来源作为依据。',
            mirror_workflow,
        )
        self.assertTrue(mirror_skill_config.startswith('# 工作流配置\n'))

    def test_response_format_uses_one_language_rule_for_all_user_facing_text(self):
        source = (REPO_ROOT / 'agents' / 'rules' / '02-global-response-format.md').read_text(
            encoding='utf-8'
        )
        mirror = (
            REPO_ROOT / 'agents-zh' / 'rules' / '02-global-response-format.md'
        ).read_text(encoding='utf-8')

        self.assertIn(
            'Use Simplified Chinese for all user-facing text unless the user explicitly requests '
            'another language.',
            ' '.join(source.split()),
        )
        for obsolete in (
            'restates the request in English',
            'English restatement',
            'English goal text',
            'Update the menu owner scope behavior.',
            'Verification limit',
        ):
            with self.subTest(language='english', obsolete=obsolete):
                self.assertNotIn(obsolete, source)
        self.assertIn(
            '除非用户明确要求其他语言，所有面向用户的文字都使用简体中文。',
            mirror,
        )
        for obsolete in (
            '用英语复述',
            '英语复述',
            '英语目标说明',
            'Update the menu owner scope behavior.',
            'Verification limit',
        ):
            with self.subTest(language='chinese', obsolete=obsolete):
                self.assertNotIn(obsolete, mirror)

        self.assertIn(
            'For implementation work, list the main changed files and summarize the change in one '
            'or two sentences.',
            ' '.join(source.split()),
        )
        self.assertNotIn('verification performed', source)
        self.assertNotIn('If verification was skipped', source)
        self.assertIn(
            '实现类工作只列出主要修改文件，并用一两句话概括修改内容。',
            mirror,
        )
        self.assertNotIn('执行的验证', mirror)
        self.assertNotIn('跳过或无法执行验证', mirror)
        for choice_label in ('A.', 'B.', 'C.', 'D.'):
            with self.subTest(choice_label=choice_label):
                self.assertIn(choice_label, source)
                self.assertIn(choice_label, mirror)

    def test_global_worktree_rule_requires_complete_timing_report(self):
        source = (REPO_ROOT / 'agents' / 'rules' / '04-global-skill-config.md').read_text(
            encoding='utf-8'
        )
        mirror = (
            REPO_ROOT / 'agents-zh' / 'rules' / '04-global-skill-config.md'
        ).read_text(encoding='utf-8')
        normalized_source = ' '.join(source.split())
        normalized_mirror = ' '.join(mirror.split())

        self.assertIn(
            'Use `track-worktree-time` for every task that creates or reuses a linked Git '
            'worktree for code changes.',
            normalized_source,
        )
        self.assertIn('one cumulative ledger across repeated phases', normalized_source)
        self.assertIn('reconciled timing report in the final handoff', normalized_source)
        self.assertIn('代码修改', normalized_mirror)
        self.assertIn('完整计时报告', normalized_mirror)

    def test_track_worktree_time_skill_defines_complete_phase_contract(self):
        source = (TRACK_WORKTREE_TIME_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        mirror = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'track-worktree-time' / 'SKILL.md'
        ).read_text(encoding='utf-8')

        for phase in (
            'environment',
            'code-generation',
            'review',
            'verification',
            'testing',
            'integration',
            'waiting',
            'other',
        ):
            self.assertIn(f'`{phase}`', source)
        self.assertIn('wall-clock', source)
        self.assertIn('not applicable', source)
        self.assertIn('scripts/timing.py', source)
        self.assertIn('完整任务耗时', mirror)

    def test_public_config_lists_write_skill(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn({'name': 'write-skill'}, public_config['skills'])

    def test_public_config_lists_write_rule(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn({'name': 'write-rule'}, public_config['skills'])

    def test_write_skill_organizes_subsections_by_responsibility(self):
        english_sections = {
            'Classify': (),
            'Evidence': (
                'Task and Failure Evidence',
                'Owned-Surface Evidence',
                'Portability and Generation Evidence',
            ),
            'Author': (),
            'Skill Contract': (
                'Core Document',
                'Resources',
                'Review, Acceptance, and Handoff',
                'Scripted Workflows',
            ),
            'Validate': ('Content Review', 'Execution', 'Distribution'),
            'Result': (),
        }
        mirror_sections = {
            '分类': (),
            '证据': ('任务和失败预期', '负责范围的证据', '跨环境与生成证据'),
            '编写': (),
            'Skill 契约': ('正文', '资源', '审查、验收与交接', '脚本入口'),
            '验证': ('成品检查', '实际执行', '分发检查'),
            '结果': (),
        }

        def section_body(content, heading):
            lines = content.splitlines()
            start = lines.index(f'## {heading}') + 1
            end = next(
                (index for index in range(start, len(lines)) if lines[index].startswith('## ')),
                len(lines),
            )
            return '\n'.join(lines[start:end])

        for path in (
            REPO_ROOT / 'agents' / 'skills' / 'write-skill' / 'SKILL.md',
            REPO_ROOT / '.agents' / 'skills' / 'write-skill' / 'SKILL.md',
        ):
            content = path.read_text(encoding='utf-8')
            for section, expected_subsections in english_sections.items():
                with self.subTest(path=path.relative_to(REPO_ROOT), section=section):
                    body = section_body(content, section)
                    actual_subsections = tuple(
                        line.removeprefix('### ')
                        for line in body.splitlines()
                        if line.startswith('### ')
                    )
                    self.assertEqual(expected_subsections, actual_subsections)
            self.assertIn('| Condition | Class |', content)
            for type_heading in (
                'Project-Local Skills',
                'Shared Skills',
                'Shared Skill-Generation Contracts',
            ):
                self.assertNotIn(f'### {type_heading}', content)

        mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / 'write-skill' / 'SKILL.md'
        mirror = mirror_path.read_text(encoding='utf-8')
        for section, expected_subsections in mirror_sections.items():
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT), section=section):
                body = section_body(mirror, section)
                actual_subsections = tuple(
                    line.removeprefix('### ')
                    for line in body.splitlines()
                    if line.startswith('### ')
                )
                self.assertEqual(expected_subsections, actual_subsections)
        self.assertIn('| 判断依据 | 类型 |', mirror)
        for type_heading in ('项目本地 Skill', '共享 Skill', '共享 Skill 生成契约'):
            self.assertNotIn(f'### {type_heading}', mirror)

    def test_write_rule_organizes_subsections_by_responsibility(self):
        english_sections = {
            'Classify': (),
            'Evidence': (
                'Policy Evidence',
                'Repository Evidence',
                'Distribution and Generation Evidence',
            ),
            'Author': (),
            'Rule Contract': ('Required Header', 'Policy Body', 'Generation Contracts'),
            'Validate': ('Policy Review', 'Context Validation', 'Discovery Surfaces'),
            'Result': (),
        }
        mirror_sections = {
            '分类': (),
            '证据': ('规则依据', '仓库事实', '分发与生成依据'),
            '编写': (),
            '规则契约': ('基本格式', '规则正文', '生成契约'),
            '验证': ('成品检查', '适用环境检查', '加载入口检查'),
            '结果': (),
        }

        def section_body(content, heading):
            lines = content.splitlines()
            start = lines.index(f'## {heading}') + 1
            end = next(
                (index for index in range(start, len(lines)) if lines[index].startswith('## ')),
                len(lines),
            )
            return '\n'.join(lines[start:end])

        for path in (
            REPO_ROOT / 'agents' / 'skills' / 'write-rule' / 'SKILL.md',
            REPO_ROOT / '.agents' / 'skills' / 'write-rule' / 'SKILL.md',
        ):
            content = path.read_text(encoding='utf-8')
            for section, expected_subsections in english_sections.items():
                with self.subTest(path=path.relative_to(REPO_ROOT), section=section):
                    body = section_body(content, section)
                    actual_subsections = tuple(
                        line.removeprefix('### ')
                        for line in body.splitlines()
                        if line.startswith('### ')
                    )
                    self.assertEqual(expected_subsections, actual_subsections)
            self.assertIn('| Condition | Class |', content)
            for type_heading in (
                'Project-Local Rules',
                'Shared Rules',
                'Shared Rule-Generation Contracts',
            ):
                self.assertNotIn(f'### {type_heading}', content)

        mirror = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'write-rule' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        for section, expected_subsections in mirror_sections.items():
            with self.subTest(path='agents-zh/skills/write-rule/SKILL.md', section=section):
                body = section_body(mirror, section)
                actual_subsections = tuple(
                    line.removeprefix('### ')
                    for line in body.splitlines()
                    if line.startswith('### ')
                )
                self.assertEqual(expected_subsections, actual_subsections)
        self.assertIn('| 判断依据 | 类型 |', mirror)
        for type_heading in ('项目本地规则', '共享规则', '共享规则生成契约'):
            self.assertNotIn(f'### {type_heading}', mirror)

    def test_write_authoring_skills_do_not_force_result_type_subsections(self):
        cases = {
            'write-skill': {
                'english_heading': 'Result',
                'mirror_heading': '结果',
            },
            'write-rule': {
                'english_heading': 'Result',
                'mirror_heading': '结果',
            },
        }

        def subsection_headings(content, heading):
            lines = content.splitlines()
            start = lines.index(f'## {heading}') + 1
            end = next(
                (index for index in range(start, len(lines)) if lines[index].startswith('## ')),
                len(lines),
            )
            return tuple(
                line.removeprefix('### ')
                for line in lines[start:end]
                if line.startswith('### ')
            )

        for skill_name, contract in cases.items():
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = path.read_text(encoding='utf-8')
                    self.assertEqual(
                        (),
                        subsection_headings(content, contract['english_heading']),
                    )

            mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
            mirror = mirror_path.read_text(encoding='utf-8')
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT)):
                self.assertEqual(
                    (),
                    subsection_headings(mirror, contract['mirror_heading']),
                )

    def test_write_authoring_skills_do_not_duplicate_type_rules_in_summary_tables(self):
        for skill_name in ('write-skill', 'write-rule'):
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = path.read_text(encoding='utf-8')
                    for duplicate_table_header in (
                        '| Class | Owns | Specificity |',
                        '| Contract shape | Required content | Additional constraint |',
                        '| 类型 | 负责什么 | 需要具体到什么程度 |',
                        '| 契约形式 | 必须包含 | 额外要求 |',
                    ):
                        self.assertNotIn(duplicate_table_header, content)

    def test_write_authoring_skills_keep_shared_classification_guard_concise(self):
        cases = {
            'write-rule': {
                'english': (
                    'Use distribution, ownership, and the requested output to select one class '
                    'before authoring.',
                    'Removing local details does not make a rule shared. Classify it as shared '
                    'only when the policy itself remains stable across repositories; otherwise '
                    'keep it project-local.',
                ),
                'mirror': (
                    '动笔前，先根据规则的分发方式、职责归属和用户要的产物判断类型。',
                    '删掉本地细节，并不会自动变成共享规则。只有规则本身在不同仓库中都能保持稳定，'
                    '才把它归为共享规则；否则继续作为项目本地规则。',
                ),
            },
            'write-skill': {
                'english': (
                    'Use distribution, ownership, and the requested output to select one class '
                    'before authoring.',
                    'Removing local details does not make a skill shared. Classify it as shared '
                    'only when the workflow itself remains stable across repositories and '
                    'target-specific facts can be discovered at runtime; otherwise keep it '
                    'project-local.',
                ),
                'mirror': (
                    '动笔前，先根据 Skill 的分发方式、职责归属和用户要的产物判断类型。',
                    '删掉本地细节，并不会自动变成共享 Skill。只有工作流本身在不同仓库中都能保持稳定，'
                    '而且能在运行时发现目标项目的具体事实，才把它归为共享 Skill；否则继续作为项目本地 '
                    'Skill。',
                ),
            },
        }

        for skill_name, expected in cases.items():
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = ' '.join(path.read_text(encoding='utf-8').split())
                    for sentence in expected['english']:
                        self.assertIn(sentence, content)
                    self.assertNotIn('Catalogs, manifests, installation scope', content)

            mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT)):
                mirror = ''.join(mirror_path.read_text(encoding='utf-8').split())
                for sentence in expected['mirror']:
                    self.assertIn(''.join(sentence.split()), mirror)
                self.assertNotIn('资产目录、清单、安装范围', mirror)

    def test_write_authoring_skills_name_type_specific_boundaries_directly(self):
        cases = {
            'write-rule': {
                'english': 'Use the selected rule class to set its content boundary:',
                'mirror': '根据规则类型确定内容边界：',
            },
            'write-skill': {
                'english': (
                    'Use the selected skill class to set its execution and content boundaries:'
                ),
                'mirror': '根据 Skill 类型确定执行方式和内容边界：',
            },
        }

        for skill_name, expected in cases.items():
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = ' '.join(path.read_text(encoding='utf-8').split())
                    self.assertIn(expected['english'], content)
                    self.assertNotIn(
                        'Apply class-specific requirements inside the step that owns them',
                        content,
                    )

            mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT)):
                mirror = ''.join(mirror_path.read_text(encoding='utf-8').split())
                self.assertIn(''.join(expected['mirror'].split()), mirror)
                self.assertNotIn('类型特有的要求要放进真正负责它的步骤', mirror)

    def test_write_authoring_skills_require_clear_unambiguous_faithful_language(self):
        cases = {
            'write-rule': {
                'english_required': (
                    'Every requirement must have one clear interpretation.',
                    'subject, scope, conditions, strength, and expected behavior',
                    'explicit wherever they affect meaning',
                ),
                'mirror_required': (
                    '每项要求都只能有一种明确解读',
                    '约束对象、适用范围、条件、强度和预期行为',
                    '只要会影响含义',
                ),
            },
            'write-skill': {
                'english_required': (
                    'Every instruction must have one clear interpretation.',
                    'actor, trigger, conditions, action, stop or completion conditions, and expected result',
                    'explicit wherever they affect execution',
                ),
                'mirror_required': (
                    '每条指令都只能有一种明确解读',
                    '执行者、触发条件、适用条件、动作、停止或完成条件和预期结果',
                    '只要会影响执行',
                ),
            },
        }
        english_common = (
            'Do not broaden, narrow, weaken, strengthen, or otherwise reinterpret',
            'without new evidence or explicit user approval',
            'Check the final candidate for ambiguity or semantic drift',
            'If either condition fails, reject the candidate',
        )
        mirror_common = (
            '不得扩大、缩小、弱化、强化或改写原意',
            '除非有新证据或用户明确同意',
            '检查最终成稿是否存在歧义或语义偏移',
            '任一条件不满足都不能通过',
        )
        english_ambiguous = (
            'supported direction',
            'natural owner',
            'resulting contract shape',
            'against this standard',
        )
        mirror_ambiguous = ('仍有依据的方向', '最合适的责任方', '契约形式', '上述标准')

        for skill_name, expected in cases.items():
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = ' '.join(path.read_text(encoding='utf-8').split())
                    for required in (*expected['english_required'], *english_common):
                        self.assertIn(required, content)
                    for ambiguous in english_ambiguous:
                        self.assertNotIn(ambiguous, content)
                    if skill_name == 'write-skill':
                        self.assertNotIn('Direct skills', content)

            mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT)):
                mirror = ''.join(mirror_path.read_text(encoding='utf-8').split())
                for required in (*expected['mirror_required'], *mirror_common):
                    self.assertIn(''.join(required.split()), mirror)
                for ambiguous in mirror_ambiguous:
                    self.assertNotIn(''.join(ambiguous.split()), mirror)
                if skill_name == 'write-skill':
                    self.assertNotIn('直接使用的Skill', mirror)

    def test_write_authoring_skills_do_not_edit_each_others_artifacts(self):
        cases = {
            'write-rule': {
                'contract_heading': '## Rule Contract',
                'english_author_required': (
                    'Put each requirement in the rule responsible for it.',
                    'If the requested rule does not own a requirement, do not add it there.',
                    'Modify the owning rule only if it is already within the user\'s requested '
                    'scope; otherwise get explicit user approval first.',
                    'Modify only rules and the wrappers, indexes, manifests, mirrors, and contract '
                    'tests required to load or distribute them.',
                    'Report any other required change as out of scope.',
                ),
                'english_validation_required':
                    'Confirm changes are limited to rules and their owned surfaces.',
                'english_forbidden': (
                    'rule or skill responsible for it',
                    'Put each instruction in the rule responsible for it.',
                    'Do not edit anything outside rules and their owned surfaces',
                ),
                'mirror_contract_heading': '## 规则契约',
                'mirror_author_required': (
                    '每项要求都写进负责它的 Rule',
                    '用户点名的 Rule 不负责某项要求时，不要写进去',
                    '只有负责该要求的 Rule 已经在用户请求范围内时，才能直接修改；否则先取得用户明确同意',
                    '只修改 Rule，以及让这些 Rule 正确加载或分发所必需的平台适配文件、索引、清单、语言镜像和契约测试',
                    '其他类型的改动都超出范围，必须报告',
                ),
                'mirror_validation_required': '确认改动只限于 Rule 及其管理的文件和入口',
                'mirror_forbidden': (
                    '负责它的 Rule 或 Skill',
                    '每项要求都放进负责它的 Rule',
                    'Rule 及其管理的文件和入口',
                ),
            },
            'write-skill': {
                'contract_heading': '## Skill Contract',
                'english_author_required': (
                    'Put each requirement in the skill section or skill-owned resource responsible for it.',
                    'If the requested skill does not own a requirement, do not add it there.',
                    'Modify the owning skill only if it is already within the user\'s requested '
                    'scope; otherwise get explicit user approval first.',
                    'Modify only skills and the skill-owned resources, wrappers, indexes, manifests, '
                    'mirrors, and contract tests required to execute or distribute them.',
                    'Report any other required change as out of scope.',
                ),
                'english_validation_required':
                    'Confirm changes are limited to skills and their owned surfaces.',
                'english_forbidden': (
                    'rule, skill section, or resource responsible for it',
                    'Put each instruction in the skill section or owned resource responsible for it.',
                    'Do not edit anything outside skills and their owned surfaces',
                    'Project policy must remain in rules.',
                    'A skill may reference a rule, but must not edit or copy the rule\'s content.',
                ),
                'mirror_contract_heading': '## Skill 契约',
                'mirror_author_required': (
                    '每项要求都写进负责它的 Skill 章节或 Skill 自有资源',
                    '用户点名的 Skill 不负责某项要求时，不要写进去',
                    '只有负责该要求的 Skill 已经在用户请求范围内时，才能直接修改；否则先取得用户明确同意',
                    '只修改 Skill，以及执行或分发这些 Skill 所必需的自有资源、平台适配文件、索引、清单、语言镜像和契约测试',
                    '其他类型的改动都超出范围，必须报告',
                ),
                'mirror_validation_required': '确认改动只限于 Skill 及其管理的文件和入口',
                'mirror_forbidden': (
                    '负责它的 Rule、Skill 章节或资源',
                    '每项要求都放进负责它的 Skill 章节或自有资源',
                    'Skill 及其管理的文件和入口',
                    '项目政策必须留在 Rule 中',
                    'Skill 可以引用 Rule，但不得修改或复制 Rule 的内容',
                ),
            },
        }

        for skill_name, expected in cases.items():
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = path.read_text(encoding='utf-8')
                    authoring = content.split('## Author', 1)[1].split(
                        expected['contract_heading'], 1
                    )[0]
                    validation = content.split('## Validate', 1)[1].split('## Result', 1)[0]
                    normalized = ' '.join(authoring.split())
                    for required in expected['english_author_required']:
                        self.assertIn(required, normalized)
                    self.assertIn(
                        expected['english_validation_required'],
                        ' '.join(validation.split()),
                    )
                    for forbidden in expected['english_forbidden']:
                        self.assertNotIn(forbidden, normalized)

            mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT)):
                mirror = mirror_path.read_text(encoding='utf-8')
                mirror_authoring = mirror.split('## 编写', 1)[1].split(
                    expected['mirror_contract_heading'], 1
                )[0]
                mirror_validation = mirror.split('## 验证', 1)[1].split('## 结果', 1)[0]
                normalized_mirror = ''.join(mirror_authoring.split())
                for required in expected['mirror_author_required']:
                    self.assertIn(''.join(required.split()), normalized_mirror)
                self.assertIn(
                    ''.join(expected['mirror_validation_required'].split()),
                    ''.join(mirror_validation.split()),
                )
                for forbidden in expected['mirror_forbidden']:
                    self.assertNotIn(''.join(forbidden.split()), normalized_mirror)

    def test_write_authoring_skills_align_shared_language(self):
        cases = {
            'write-rule': {
                'english_specific': (
                    'Organize the result as the rule you would author today, placing each '
                    'requirement where it belongs instead of appending a note or preserving old '
                    'order for a smaller diff.',
                    'Put each requirement in the rule responsible for it. '
                    'If the requested rule does not own a requirement, do not add it there. '
                    'Modify the owning rule only if it is already within the user\'s requested '
                    'scope; otherwise get explicit user approval first.',
                    'Run the current validators, contract tests, and diff-integrity checks for every '
                    'required discovery surface. Confirm applicable wrappers, indexes, manifests, '
                    'mirrors, and other distribution surfaces remain aligned.',
                    'Do not report success while evidence is unresolved, claims are unsupported, '
                    'required discovery surfaces are stale or unreachable, or required checks fail '
                    'or remain unreported.',
                    'Report the artifact class, owning artifact or repository, final document '
                    'structure, preserved decisions, removed or moved content, updated discovery '
                    'and distribution surfaces and language mirrors, and exact validation outcomes.',
                ),
                'mirror_specific': (
                    '假设今天从零开始写这条规则，按最合理的顺序组织它；每项要求都放到应在的位置，'
                    '不要为了缩小 diff 而在末尾补一句，也不要机械保留旧顺序。',
                    '每项要求都写进负责它的 Rule。用户点名的 Rule 不负责某项要求时，不要写进去。'
                    '只有负责该要求的 Rule 已经在用户请求范围内时，才能直接修改；否则先取得用户明确同意。',
                    '对每个必需的发现入口运行当前项目规定的验证器、契约测试和 diff 完整性检查。'
                    '确认适用的平台适配文件、索引、清单、语言镜像和其他分发入口仍然一致。',
                    '只要证据还有疑点、说法没有事实支持、必需的发现入口已经过时或无法访问，'
                    '或者必需检查失败或没有报告，就不能声称工作成功。',
                    '交付时说明：产物属于哪一类、由哪个产物或仓库负责、最终文档结构、保留了哪些决定、'
                    '删除或迁移了哪些内容、更新了哪些发现入口、分发入口和语言镜像，以及各项验证的具体结果。',
                ),
            },
            'write-skill': {
                'english_specific': (
                    'Organize the result as the skill you would author today, placing each '
                    'requirement where it belongs instead of appending a note or preserving old '
                    'order for a smaller diff.',
                    'Put each requirement in the skill section or skill-owned resource responsible '
                    'for it. If the requested skill does not own a requirement, do not add it there. '
                    'Modify the owning skill only if it is already within the user\'s requested '
                    'scope; otherwise get explicit user approval first.',
                    'Run the current validators, contract tests, and diff-integrity checks for every '
                    'owned resource and required discovery surface. Confirm applicable wrappers, '
                    'indexes, manifests, mirrors, and other distribution surfaces remain aligned.',
                    'Do not report success while evidence is unresolved, behavior is unsupported, '
                    'owned resources or required discovery surfaces are stale or unreachable, or '
                    'required checks fail or remain unreported.',
                    'Report the artifact class, owning artifact or repository, final document '
                    'structure and gates, preserved decisions, removed or moved content and '
                    'resources, updated discovery and distribution surfaces and language mirrors, '
                    'and exact validation outcomes.',
                ),
                'mirror_specific': (
                    '假设今天从零开始写这个 Skill，按最合理的顺序组织它；每项要求都放到应在的位置，'
                    '不要为了缩小 diff 而在末尾补一句，也不要机械保留旧顺序。',
                    '每项要求都写进负责它的 Skill 章节或 Skill 自有资源。用户点名的 Skill 不负责某项要求时，'
                    '不要写进去。只有负责该要求的 Skill 已经在用户请求范围内时，才能直接修改；'
                    '否则先取得用户明确同意。',
                    '对每项自有资源和每个必需的发现入口运行当前项目规定的验证器、契约测试和 diff 完整性检查。'
                    '确认适用的平台适配文件、索引、清单、语言镜像和其他分发入口仍然一致。',
                    '只要证据还有疑点、行为没有事实支持、自有资源或必需的发现入口已经过时或无法访问，'
                    '或者必需检查失败或没有报告，就不能声称工作成功。',
                    '交付时说明：产物属于哪一类、由哪个产物或仓库负责、最终文档结构和关口、保留了哪些决定、'
                    '删除或迁移了哪些内容与资源、更新了哪些发现入口、分发入口和语言镜像，以及各项验证的具体结果。',
                ),
            },
        }
        english_shared = (
            'Give the implementing agent freedom when several approaches are valid; prescribe '
            'ordered steps when sequence affects correctness or safety.',
            'Refer to another rule or skill by the canonical name declared or recognized by the '
            'target system, never by its filesystem path.',
        )
        mirror_shared = (
            '如果有多种做法都合理，就给执行 Agent 留出选择空间；如果顺序会影响正确性或安全性，'
            '就明确规定步骤。',
            '提到其他 Rule 或 Skill 时，使用目标系统声明或认可的正式名称，不要写它在文件系统里的路径。',
        )

        for skill_name, expected in cases.items():
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = ' '.join(path.read_text(encoding='utf-8').split())
                    for specific in expected['english_specific']:
                        self.assertIn(specific, content)
                    for shared in english_shared:
                        self.assertIn(shared, content)

            mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT)):
                mirror = ''.join(mirror_path.read_text(encoding='utf-8').split())
                for specific in expected['mirror_specific']:
                    self.assertIn(''.join(specific.split()), mirror)
                for shared in mirror_shared:
                    self.assertIn(''.join(shared.split()), mirror)

    def test_write_authoring_skills_require_unified_contract_format(self):
        cases = {
            'write-rule': {
                'english_required': 'Start every rule with:',
                'english_forbidden': (
                    "When the target uses this repository's format",
                    "Use the target system's supported title",
                ),
                'mirror_required': '每条规则都必须这样开头：',
                'mirror_forbidden': ('如果目标项目采用本仓库的规则格式', '采用目标系统支持的格式'),
            },
            'write-skill': {
                'english_required': (
                    'Frontmatter contains only `name` and `description`; the name is'
                ),
                'english_forbidden': ("Under this repository's convention",),
                'mirror_required': 'frontmatter 只能包含 `name` 和 `description`。',
                'mirror_forbidden': ('按本仓库约定',),
            },
        }

        for skill_name, expected in cases.items():
            for path in (
                REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md',
                REPO_ROOT / '.agents' / 'skills' / skill_name / 'SKILL.md',
            ):
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = ' '.join(path.read_text(encoding='utf-8').split())
                    self.assertIn(expected['english_required'], content)
                    for forbidden in expected['english_forbidden']:
                        self.assertNotIn(forbidden, content)

            mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
            with self.subTest(path=mirror_path.relative_to(REPO_ROOT)):
                mirror = ' '.join(mirror_path.read_text(encoding='utf-8').split())
                self.assertIn(expected['mirror_required'], mirror)
                for forbidden in expected['mirror_forbidden']:
                    self.assertNotIn(forbidden, mirror)

    def test_write_skill_keeps_common_resource_rules_in_resources_topic(self):
        english_common_rules = (
            'Keep core decisions in `SKILL.md`.',
            'Do not add README, changelog, installation, or quick-reference files',
            'Keep one source of truth for each instruction',
        )
        for path in (
            REPO_ROOT / 'agents' / 'skills' / 'write-skill' / 'SKILL.md',
            REPO_ROOT / '.agents' / 'skills' / 'write-skill' / 'SKILL.md',
        ):
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                content = path.read_text(encoding='utf-8')
                contract = content.split('## Skill Contract', 1)[1].split('## Validate', 1)[0]
                resources = contract.split('### Resources', 1)[1].split(
                    '### Review, Acceptance, and Handoff', 1
                )[0]
                for common_rule in english_common_rules:
                    self.assertIn(common_rule, ' '.join(resources.split()))

        mirror = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'write-skill' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        mirror_contract = mirror.split('## Skill 契约', 1)[1].split('## 验证', 1)[0]
        mirror_resources = mirror_contract.split('### 资源', 1)[1].split(
            '### 审查、验收与交接', 1
        )[0]
        mirror_resources = ' '.join(mirror_resources.split())
        for common_rule in (
            '关键决定留在 `SKILL.md`。',
            '不要添加 README、变更日志、安装说明或速查文件',
            '每项要求只保留一个',
            '权威来源',
        ):
            self.assertIn(common_rule, mirror_resources)

    def test_write_skill_keeps_shared_orchestrator_contract_complete(self):
        for path in (
            REPO_ROOT / 'agents' / 'skills' / 'write-skill' / 'SKILL.md',
            REPO_ROOT / '.agents' / 'skills' / 'write-skill' / 'SKILL.md',
        ):
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                content = path.read_text(encoding='utf-8')
                contract = content.split('## Skill Contract', 1)[1].split('## Validate', 1)[0]
                core_document = contract.split('### Core Document', 1)[1].split(
                    '### Resources', 1
                )[0]
                for required_part in (
                    'Ownership',
                    'Managed Assets',
                    'Reconciliation Workflow',
                    'Review Gate',
                    'Acceptance Gate',
                    'Validation',
                    'Output',
                ):
                    self.assertIn(required_part, core_document)

        mirror = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'write-skill' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        mirror_contract = mirror.split('## Skill 契约', 1)[1].split('## 验证', 1)[0]
        mirror_document = mirror_contract.split('### 正文', 1)[1].split('### 资源', 1)[0]
        for required_part in (
            'Ownership',
            'Managed Assets',
            'Reconciliation Workflow',
            'Review Gate',
            'Acceptance Gate',
            'Validation',
            'Output',
        ):
            self.assertIn(required_part, mirror_document)

    def test_write_authoring_skills_reference_rules_and_skills_by_name(self):
        expected_source = (
            'Refer to another rule or skill by the canonical name declared or recognized by the '
            'target system, never by its filesystem path.'
        )
        expected_mirror = (
            '提到其他 Rule 或 Skill 时，使用目标系统声明或认可的正式名称，'
            '不要写它在文件系统里的路径。'
        )

        for skill_name in ('write-rule', 'write-skill'):
            with self.subTest(skill=skill_name):
                source = (
                    REPO_ROOT / 'agents' / 'skills' / skill_name / 'SKILL.md'
                ).read_text(encoding='utf-8')
                mirror = (
                    REPO_ROOT / 'agents-zh' / 'skills' / skill_name / 'SKILL.md'
                ).read_text(encoding='utf-8')

                self.assertEqual(' '.join(source.split()).count(expected_source), 1)
                self.assertEqual(' '.join(mirror.split()).count(expected_mirror), 1)

    def test_shared_skill_generation_contract_requires_acceptance(self):
        for path in (
            REPO_ROOT / 'agents' / 'skills' / 'write-skill' / 'SKILL.md',
            REPO_ROOT / '.agents' / 'skills' / 'write-skill' / 'SKILL.md',
        ):
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                content = path.read_text(encoding='utf-8')
                skill_contract = content.split('## Skill Contract', 1)[1].split('## Validate', 1)[0]
                generation_contract = skill_contract.split(
                    '### Review, Acceptance, and Handoff', 1
                )[1].split('### Scripted Workflows', 1)[0]
                required_gates = ('Review Gate', 'Acceptance Gate', 'Handoff')
                for required_gate in required_gates:
                    self.assertIn(required_gate, generation_contract)
                self.assertEqual(
                    [generation_contract.index(gate) for gate in required_gates],
                    sorted(generation_contract.index(gate) for gate in required_gates),
                )
                for handoff_contract in (
                    'Hand off only after review and acceptance pass',
                    'accepted candidate',
                    'review decision',
                    'acceptance evidence',
                    'unresolved or not-run items',
                    'stop and report',
                ):
                    self.assertIn(handoff_contract, generation_contract)
                normalized = ' '.join(content.split())
                for acceptance_contract in (
                    'review the complete candidate',
                    'exercising its workflow',
                    'representative target context',
                ):
                    self.assertIn(acceptance_contract, normalized)

        mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / 'write-skill' / 'SKILL.md'
        mirror = mirror_path.read_text(encoding='utf-8')
        mirror_skill_contract = mirror.split('## Skill 契约', 1)[1].split('## 验证', 1)[0]
        mirror_generation_contract = mirror_skill_contract.split(
            '### 审查、验收与交接', 1
        )[1].split('### 脚本入口', 1)[0]
        required_gates = ('Review Gate', 'Acceptance Gate', 'Handoff')
        for required_gate in required_gates:
            self.assertIn(required_gate, mirror_generation_contract)
        self.assertEqual(
            [mirror_generation_contract.index(gate) for gate in required_gates],
            sorted(mirror_generation_contract.index(gate) for gate in required_gates),
        )
        self.assertIn('验收', mirror_generation_contract)
        for handoff_contract in (
            '审查和验收都通过后才能交接',
            '通过验收的候选 Skill',
            '审查结论',
            '验收证据',
            '未运行',
            '未解决的事项',
            '停止交接并报告',
        ):
            self.assertIn(handoff_contract, mirror_generation_contract)
        normalized_mirror = ' '.join(mirror.split())
        for acceptance_contract in (
            '审查完整候选 Skill',
            '有代表性的目标项目环境',
            '实际执行它的工作流',
            '完成验收',
        ):
            self.assertIn(acceptance_contract, normalized_mirror)

    def test_write_skill_selects_script_runtime_by_artifact_ownership(self):
        for path in (
            REPO_ROOT / 'agents' / 'skills' / 'write-skill' / 'SKILL.md',
            REPO_ROOT / '.agents' / 'skills' / 'write-skill' / 'SKILL.md',
        ):
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                content = path.read_text(encoding='utf-8')
                skill_contract = content.split('## Skill Contract', 1)[1].split(
                    '## Validate', 1
                )[0]
                scripted_workflows = skill_contract.split('### Scripted Workflows', 1)[1]
                validation = content.split('## Validate', 1)[1].split('## Result', 1)[0]
                execution = validation.split('### Execution', 1)[1].split(
                    '### Distribution', 1
                )[0]
                scripted_workflows = ' '.join(scripted_workflows.split())
                execution = ' '.join(execution.split())
                for provision_contract in (
                    "For a project-local skill, choose either scripts that match the project's "
                    'established language and runtime',
                    'Python in a Python project',
                    'Dart in a Dart project',
                    'or paired `.sh` and `.ps1` entry points',
                    'For any shared skill, including a shared skill-generation contract',
                    'paired `.sh` and `.ps1` entry points',
                    'same supported outcome',
                    'evidence-backed platform differences',
                    'A target-owned project-local skill produced by a generation contract',
                    'its scripts do not become shared merely because its generator is shared',
                ):
                    self.assertIn(provision_contract, scripted_workflows)
                for validation_contract in (
                    'For the project-matched option',
                    "using the project's established language and runtime",
                    'For the paired-entry option',
                    "validate only the current platform's entry point",
                    '`.ps1` on Windows',
                    '`.sh` on all other platforms',
                    'Do not require validation of the other entry point on the current host',
                    "Validate the generated skill's scripts according to that skill's own class",
                ):
                    self.assertIn(validation_contract, execution)
                for forbidden in (
                    'When a shared skill-generation contract produces executable scripts',
                    'Review both files',
                    'For the paired non-native entry point',
                ):
                    self.assertNotIn(forbidden, f'{scripted_workflows} {execution}')
                self.assertNotIn('validate only the current platform', scripted_workflows)
                self.assertNotIn(
                    'may choose project-matched scripts or paired `.sh` and `.ps1` entry points',
                    execution,
                )

        mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / 'write-skill' / 'SKILL.md'
        mirror = mirror_path.read_text(encoding='utf-8')
        mirror_contract = mirror.split('## Skill 契约', 1)[1].split('## 验证', 1)[0]
        mirror_scripted_workflows = mirror_contract.split('### 脚本入口', 1)[1]
        mirror_validation = mirror.split('## 验证', 1)[1].split('## 结果', 1)[0]
        mirror_execution = mirror_validation.split('### 实际执行', 1)[1].split(
            '### 分发检查', 1
        )[0]
        mirror_scripted_workflows = ''.join(mirror_scripted_workflows.split())
        mirror_execution = ''.join(mirror_execution.split())
        for provision_contract in (
            '项目本地 Skill 可以选择与项目已有语言和运行时匹配的脚本',
            'Python 项目使用 Python',
            'Dart 项目使用 Dart',
            '也可以同时提供 `.sh` 和 `.ps1` 入口',
            '任何共享 Skill，包括共享 Skill 生成契约',
            '同时提供 `.sh` 和 `.ps1` 入口',
            '同一项受支持的结果',
            '有证据依据的平台差异',
            '生成契约产出的项目本地 Skill',
            '不会因为生成器是共享的而自动变成共享脚本',
        ):
            self.assertIn(''.join(provision_contract.split()), mirror_scripted_workflows)
        for validation_contract in (
            '选择项目匹配方案时',
            '使用项目已有的语言和运行时',
            '选择成对入口时',
            '只验证当前平台对应的入口',
            'Windows 运行 `.ps1`',
            '其他平台运行 `.sh`',
            '不要求在当前宿主验证另一个入口',
            '生成出来的 Skill 按自身类型验证脚本',
        ):
            self.assertIn(''.join(validation_contract.split()), mirror_execution)
        for forbidden in (
            '当共享 Skill 生成契约会生成可执行脚本时',
            '两个文件都要审查',
            '成对脚本中的非原生入口',
        ):
            self.assertNotIn(
                ''.join(forbidden.split()),
                f'{mirror_scripted_workflows}{mirror_execution}',
            )
        self.assertNotIn('只验证当前平台对应的入口', mirror_scripted_workflows)
        self.assertNotIn(
            ''.join('可以选择与项目匹配的脚本，也可以选择 `.sh` 和 `.ps1` 成对入口'.split()),
            mirror_execution,
        )

    def test_write_rule_does_not_claim_file_or_resource_ownership(self):
        source_exception = (
            'Use paths only for owned files or resources whose location is part of the current '
            'contract.'
        )
        mirror_exception = (
            '只有文件或资源本身归当前契约管理，而且位置就是契约的一部分时，才使用路径。'
        )
        public_write_rule = (
            REPO_ROOT / 'agents' / 'skills' / 'write-rule' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        local_write_rule = (
            REPO_ROOT / '.agents' / 'skills' / 'write-rule' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        mirror_write_rule = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'write-rule' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        public_write_skill = (
            REPO_ROOT / 'agents' / 'skills' / 'write-skill' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        mirror_write_skill = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'write-skill' / 'SKILL.md'
        ).read_text(encoding='utf-8')

        self.assertNotIn(source_exception, ' '.join(public_write_rule.split()))
        self.assertNotIn(source_exception, ' '.join(local_write_rule.split()))
        self.assertNotIn(mirror_exception, ' '.join(mirror_write_rule.split()))
        self.assertIn(source_exception, ' '.join(public_write_skill.split()))
        self.assertIn(mirror_exception, ' '.join(mirror_write_skill.split()))

    def test_rule_and_skill_responsibility_references_use_canonical_names(self):
        cases = {
            REPO_ROOT / 'agents' / 'blueprints' / 'rules' / '20-project-tools.md': {
                'expected': (
                    '`Project Rules`',
                    '`Project Structure`',
                    '`worktree-environment-setup`',
                    '`change-set-verification`',
                ),
                'forbidden': (
                    '`21-project-rules.md`',
                    '`22-project-structure.md`',
                    '`.agents/skills/worktree-environment-setup/`',
                    '`.agents/skills/change-set-verification/`',
                ),
            },
            REPO_ROOT / 'agents' / 'blueprints' / 'rules' / '21-project-rules.md': {
                'expected': ('`Project Tools`', '`Project Structure`'),
                'forbidden': ('`20-project-tools.md`', '`22-project-structure.md`'),
            },
            REPO_ROOT / 'agents' / 'blueprints' / 'rules' / '22-project-structure.md': {
                'expected': ('`Project Tools`', '`Project Rules`'),
                'forbidden': ('`20-project-tools.md`', '`21-project-rules.md`'),
            },
            REPO_ROOT
            / 'agents'
            / 'blueprints'
            / 'skills'
            / 'worktree-environment-setup'
            / 'SKILL.md': {
                'expected': ('`Project Tools`',),
                'forbidden': ('`.agents/rules/20-project-tools.md`',),
            },
            REPO_ROOT / 'agents-zh' / 'blueprints' / 'rules' / '20-project-tools.md': {
                'expected': (
                    '`Project Rules`',
                    '`Project Structure`',
                    '`worktree-environment-setup`',
                    '`change-set-verification`',
                ),
                'forbidden': (
                    '`21-project-rules.md`',
                    '`22-project-structure.md`',
                    '`.agents/skills/worktree-environment-setup/`',
                    '`.agents/skills/change-set-verification/`',
                ),
            },
            REPO_ROOT / 'agents-zh' / 'blueprints' / 'rules' / '21-project-rules.md': {
                'expected': ('`Project Tools`', '`Project Structure`'),
                'forbidden': ('`20-project-tools.md`', '`22-project-structure.md`'),
            },
            REPO_ROOT / 'agents-zh' / 'blueprints' / 'rules' / '22-project-structure.md': {
                'expected': ('`Project Tools`', '`Project Rules`'),
                'forbidden': ('`20-project-tools.md`', '`21-project-rules.md`'),
            },
            REPO_ROOT
            / 'agents-zh'
            / 'blueprints'
            / 'skills'
            / 'worktree-environment-setup'
            / 'SKILL.md': {
                'expected': ('`Project Tools`',),
                'forbidden': ('`.agents/rules/20-project-tools.md`',),
            },
            REPO_ROOT / '.agents' / 'rules' / '20-project-tools.md': {
                'expected': (
                    '`Project Rules`',
                    '`Project Structure`',
                    '`change-set-verification`',
                ),
                'forbidden': (
                    '`21-project-rules.md`',
                    '`22-project-structure.md`',
                    '`.agents/skills/change-set-verification/SKILL.md`',
                ),
            },
            REPO_ROOT / '.agents' / 'rules' / '21-project-rules.md': {
                'expected': ('`Project Tools`', '`Project Structure`'),
                'forbidden': ('`20-project-tools.md`', '`22-project-structure.md`'),
            },
            REPO_ROOT / '.agents' / 'rules' / '22-project-structure.md': {
                'expected': ('`Project Tools`', '`Project Rules`'),
                'forbidden': ('`20-project-tools.md`', '`21-project-rules.md`'),
            },
        }

        for path, contract in cases.items():
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                content = path.read_text(encoding='utf-8')
                for canonical_name in contract['expected']:
                    self.assertIn(canonical_name, content)
                for filesystem_reference in contract['forbidden']:
                    self.assertNotIn(filesystem_reference, content)

    def test_public_blueprints_keep_required_contract_shapes_and_gates(self):
        rule_contracts = {
            REPO_ROOT / 'agents': (
                '## Generation Contract',
                '## Evidence',
                '## Content',
                '## Boundaries',
            ),
            REPO_ROOT / 'agents-zh': (
                '## 生成契约',
                '## 证据',
                '## 内容',
                '## 边界',
            ),
        }
        for root, required_sections in rule_contracts.items():
            for filename in (
                '20-project-tools.md',
                '21-project-rules.md',
                '22-project-structure.md',
            ):
                path = root / 'blueprints' / 'rules' / filename
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = path.read_text(encoding='utf-8')
                    positions = [content.index(section) for section in required_sections]
                    self.assertEqual(positions, sorted(positions))

        skill_contracts = {
            REPO_ROOT / 'agents': (
                (
                    '## Evidence',
                    '## Authoring Workflow',
                    '## Generated Skill Contract',
                    '## Review Gate',
                    '## Acceptance Gate',
                    '## Handoff',
                ),
                '## Review and Handoff',
            ),
            REPO_ROOT / 'agents-zh': (
                (
                    '## 证据',
                    '## 编写流程',
                    '## 生成 Skill 契约',
                    '## 审查关口',
                    '## 验收关口',
                    '## 交接',
                ),
                '## 审查与交付',
            ),
        }
        for root, (required_sections, obsolete_combined_gate) in skill_contracts.items():
            for skill_name in ('worktree-environment-setup', 'change-set-verification'):
                path = root / 'blueprints' / 'skills' / skill_name / 'SKILL.md'
                with self.subTest(path=path.relative_to(REPO_ROOT)):
                    content = path.read_text(encoding='utf-8')
                    positions = [content.index(section) for section in required_sections]
                    self.assertEqual(positions, sorted(positions))
                    self.assertNotIn(obsolete_combined_gate, content)

        worktree_source = (
            REPO_ROOT
            / 'agents'
            / 'blueprints'
            / 'skills'
            / 'worktree-environment-setup'
            / 'SKILL.md'
        ).read_text(encoding='utf-8')
        self.assertIn(
            "choose either the target project's established language and runtime or paired",
            ' '.join(worktree_source.split()),
        )
        worktree_mirror = (
            REPO_ROOT
            / 'agents-zh'
            / 'blueprints'
            / 'skills'
            / 'worktree-environment-setup'
            / 'SKILL.md'
        ).read_text(encoding='utf-8')
        self.assertIn(
            '可以选用目标项目已有的语言和运行时，也可以同时生成',
            ' '.join(worktree_mirror.split()),
        )

    def test_write_rule_skill_allows_project_local_boundaries_when_needed(self):
        source = (
            REPO_ROOT / 'agents' / 'skills' / 'write-rule' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        mirror = (
            REPO_ROOT / 'agents-zh' / 'skills' / 'write-rule' / 'SKILL.md'
        ).read_text(encoding='utf-8')
        source_contract = source.split('## Rule Contract', 1)[1].split('## Validate', 1)[0]
        policy_body = source_contract.split('### Policy Body', 1)[1].split(
            '### Generation Contracts', 1
        )[0]
        mirror_contract = mirror.split('## 规则契约', 1)[1].split('## 验证', 1)[0]
        mirror_policy_body = mirror_contract.split('### 规则正文', 1)[1].split(
            '### 生成契约', 1
        )[0]
        policy_body = ' '.join(policy_body.split())
        mirror_policy_body = ' '.join(mirror_policy_body.split())
        self.assertIn(
            'Boundaries or Exceptions when needed',
            policy_body,
        )
        self.assertIn(
            'Boundaries 或 Exceptions',
            mirror_policy_body,
        )
        self.assertNotIn('mutually independent', source)
        self.assertNotIn('no `Boundaries` section', source)
        self.assertNotIn('相互独立', mirror)
        self.assertNotIn('不设 `Boundaries`', mirror)

    def test_public_config_uses_archive_without_local_source_or_cache(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn('source_repo', public_config)
        self.assertNotIn('source_default', public_config)
        self.assertNotIn('source_cache_dir', public_config)

    def test_sync_preserves_target_specific_worktree_environment_setup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = (
                source / 'agents' / 'blueprints' / 'skills' / 'worktree-environment-setup'
            )
            target_skill = target / '.agents' / 'skills' / 'worktree-environment-setup'
            source_skill.mkdir(parents=True)
            target_skill.mkdir(parents=True)
            target_scripts = target_skill / 'scripts'
            target_scripts.mkdir()
            skill_root.mkdir(parents=True)
            (source_skill / 'SKILL.md').write_text(
                '---\nname: worktree-environment-setup\ndescription: Generator contract\n---\n',
                encoding='utf-8',
            )
            existing = (
                '---\n'
                'name: worktree-environment-setup\n'
                'description: Target environment setup\n'
                '---\n\n'
                'Target-specific environment setup.\n'
            )
            (target_skill / 'SKILL.md').write_text(existing, encoding='utf-8')
            setup_script = '#!/usr/bin/env bash\nset -euo pipefail\n'
            (target_scripts / 'setup.sh').write_text(setup_script, encoding='utf-8')
            setup_ps1 = (
                '[CmdletBinding()]\n'
                'param()\n'
                "Set-StrictMode -Version Latest\n"
                "$ErrorActionPreference = 'Stop'\n"
            )
            (target_scripts / 'setup.ps1').write_text(setup_ps1, encoding='utf-8')
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [],
                'skill_blueprints': [{'name': 'worktree-environment-setup'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertEqual((target_skill / 'SKILL.md').read_text(encoding='utf-8'), existing)
            self.assertEqual(
                (target_scripts / 'setup.sh').read_text(encoding='utf-8'),
                setup_script,
            )
            self.assertEqual(
                (target_scripts / 'setup.ps1').read_text(encoding='utf-8'),
                setup_ps1,
            )
            self.assertNotIn(
                sync.Change('updated', '.agents/skills/worktree-environment-setup/SKILL.md'),
                changes,
            )

    def test_sync_preserves_target_specific_change_set_verification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = (
                source / 'agents' / 'blueprints' / 'skills' / 'change-set-verification'
            )
            target_skill = target / '.agents' / 'skills' / 'change-set-verification'
            source_skill.mkdir(parents=True)
            target_references = target_skill / 'references'
            target_references.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_skill / 'SKILL.md').write_text(
                '---\nname: change-set-verification\ndescription: Generator contract\n---\n',
                encoding='utf-8',
            )
            existing = (
                '---\n'
                'name: change-set-verification\n'
                'description: Target verification\n'
                '---\n\n'
                'Target-specific verification.\n'
            )
            (target_skill / 'SKILL.md').write_text(existing, encoding='utf-8')
            matrix = '# Verification Matrix\n'
            (target_references / 'verification-matrix.md').write_text(
                matrix,
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [],
                'skill_blueprints': [
                    {'name': 'worktree-environment-setup'},
                    {'name': 'change-set-verification'},
                ],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            self.assertEqual((target_skill / 'SKILL.md').read_text(encoding='utf-8'), existing)
            self.assertEqual(
                (target_references / 'verification-matrix.md').read_text(encoding='utf-8'),
                matrix,
            )
            self.assertNotIn(
                sync.Change('updated', '.agents/skills/change-set-verification/SKILL.md'),
                changes,
            )

    def test_sync_does_not_copy_change_set_verification_blueprint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = (
                source / 'agents' / 'blueprints' / 'skills' / 'change-set-verification'
            )
            source_skill.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_skill / 'SKILL.md').write_text(
                '---\nname: change-set-verification\ndescription: Generator contract\n---\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [],
                'skill_blueprints': [{'name': 'change-set-verification'}],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, False, [])

            changes = sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            target_skill = target / '.agents' / 'skills' / 'change-set-verification'
            self.assertFalse(target_skill.exists())
            self.assertNotIn(
                sync.Change('created', '.agents/skills/change-set-verification/SKILL.md'),
                changes,
            )

    def test_discover_local_agent_description_from_referenced_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            agents_root = target / '.agents' / 'agents'
            skill_root = target / '.agents' / 'skills' / 'dart-verify'
            agents_root.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (agents_root / 'dart-verify.md').write_text(
                'Apply @.agents/skills/dart-verify/SKILL.md\n',
                encoding='utf-8',
            )
            (skill_root / 'SKILL.md').write_text(
                '---\n'
                'name: dart-verify\n'
                'description: Dart and Flutter verification specialist.\n'
                '---\n',
                encoding='utf-8',
            )

            result = sync.discover_local_assets(target, {'rules': [], 'agent_prompts': []})

        self.assertEqual(
            result['agent_prompts'],
            [
                {
                    'name': 'dart-verify',
                    'description': 'Dart and Flutter verification specialist.',
                }
            ],
        )

    def test_discover_local_agent_description_falls_back_when_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            agents_root = target / '.agents' / 'agents'
            agents_root.mkdir(parents=True)
            (agents_root / 'project-agent.md').write_text('Apply @.agents/skills/missing/SKILL.md\n', encoding='utf-8')

            result = sync.discover_local_assets(target, {'rules': [], 'agent_prompts': []})

        self.assertEqual(
            result['agent_prompts'],
            [{'name': 'project-agent', 'description': 'Project-local agent: project-agent'}],
        )

    def test_empty_cursor_globs_are_normalized_before_wrapper_rendering(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            rules_root = target / '.agents' / 'rules'
            cursor_root = target / '.cursor' / 'rules'
            (source / 'agents' / 'rules').mkdir(parents=True)
            templates.mkdir(parents=True)
            rules_root.mkdir(parents=True)
            cursor_root.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (rules_root / '20-project-tools.md').write_text('Strength: Mandatory\n', encoding='utf-8')
            (cursor_root / '20-project-tools.mdc').write_text(
                '---\n'
                'description: "[mandatory] Project tools"\n'
                'globs: \n'
                'alwaysApply: true\n'
                '---\n\n'
                'Apply @.agents/rules/20-project-tools.md\n',
                encoding='utf-8',
            )
            public_config = {
                'mirror_delete': True,
                'rules': [],
                'skills': [],
                'agent_prompts': [],
                'platforms': {
                    'rule_wrappers': [
                        {
                            'template': 'rule_wrapper.cursor.mdc',
                            'path': '.cursor/rules/{{rule.name}}.mdc',
                        },
                    ],
                    'agent_wrappers': [],
                },
            }
            local_config = sync.discover_local_assets(target, public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            self.assertIn(
                'globs: ""',
                (cursor_root / '20-project-tools.mdc').read_text(encoding='utf-8'),
            )

    def test_render_template_replaces_nested_variables(self):
        result = sync.render_template(
            'Apply @{{rule.path}}\n',
            {'rule': {'path': '.agents/rules/10-base-code.md'}},
            'sample',
        )

        self.assertEqual(result, 'Apply @.agents/rules/10-base-code.md\n')

    def test_rule_data_builds_cursor_description_from_static_routing(self):
        result = sync._rule_data(
            {
                'file': '20-project-tools.md',
                'read_when': 'Project tooling, MCP, runtime, or verification',
                'strength': 'Mandatory',
                'cursor': {'alwaysApply': True},
            }
        )

        self.assertEqual(
            result['rule']['cursor_description'],
            '[mandatory] Project tooling, MCP, runtime, or verification',
        )

    def test_render_template_rejects_missing_variable(self):
        with self.assertRaises(sync.SyncError) as error:
            sync.render_template('Apply @{{rule.path}}\n', {'rule': {}}, 'sample')

        self.assertIn('sample', str(error.exception))
        self.assertIn('rule.path', str(error.exception))

    def test_check_mode_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            (source / 'agents' / 'rules').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / 'agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
            public_config = {
                'mirror_delete': True,
                'rules': [{'file': '10-base-code.md'}],
                'skills': [],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, True, [])

            changes = sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertEqual(changes, [sync.Change('created', '.agents/rules/10-base-code.md')])
            self.assertFalse((target / '.agents' / 'rules' / '10-base-code.md').exists())

    def test_check_mode_reports_retirement_without_deleting(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            retired_skill = target / '.agents' / 'skills' / 'old-skill'
            retired_skill.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            skill_file = retired_skill / 'SKILL.md'
            skill_file.write_text('old skill\n', encoding='utf-8')
            public_config = {
                'mirror_delete': True,
                'retired_assets': {
                    'rules': [],
                    'skills': ['old-skill'],
                    'agents': [],
                },
                'rules': [],
                'skills': [],
                'agent_prompts': [],
            }
            context = sync.SyncContext(target, source, skill_root, True, [])

            changes = sync.sync_public_assets(
                context,
                public_config,
                {'rules': [], 'agent_prompts': []},
            )

            self.assertTrue(skill_file.is_file())
            self.assertIn(sync.Change('deleted', '.agents/skills/old-skill/SKILL.md'), changes)

    def test_main_check_returns_one_when_changes_are_needed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            source.mkdir()
            shutil.copytree(REPO_ROOT / 'agents', source / 'agents')
            target.mkdir()
            previous_cwd = Path.cwd()
            stdout = io.StringIO()
            public_config = {
                'mirror_delete': True,
                'rules': [{'file': '00-global-rule-config.md'}],
                'skills': [],
                'agent_prompts': [],
            }
            try:
                os.chdir(target)
                with mock.patch.object(
                    sync,
                    'load_json',
                    return_value=public_config,
                ), mock.patch.object(
                    sync,
                    'load_model_config',
                    return_value={
                        'codex_agent_runtime_overrides': {},
                        'cursor_agent_runtime_overrides': {},
                        'github_agent_runtime_overrides': {},
                    },
                ), mock.patch.object(
                    sync,
                    'resolve_source',
                    return_value=source,
                ), contextlib.redirect_stdout(stdout):
                    exit_code = sync.main(
                        ['--check', '--model-config', str(root / 'models.json')]
                    )
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(exit_code, 1)

    def test_main_first_stage_writes_model_request_after_deterministic_sync(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            request_path = root / 'models.json'
            public_config = {
                'rules': [],
                'skills': [],
                'agent_prompts': [
                    {
                        'name': 'reviewer',
                        'required_intelligence': 'High reasoning depth.',
                    }
                ],
            }
            previous_cwd = Path.cwd()
            try:
                os.chdir(target)
                with mock.patch.object(
                    sync,
                    'load_json',
                    return_value=public_config,
                ), mock.patch.object(
                    sync,
                    'resolve_source',
                    return_value=root / 'source',
                ), mock.patch.object(
                    sync,
                    'sync_public_assets',
                    return_value=[],
                ) as sync_assets:
                    exit_code = sync.main(['--model-request', str(request_path)])
            finally:
                os.chdir(previous_cwd)

            self.assertEqual(exit_code, 0)
            self.assertTrue(request_path.is_file())
            self.assertEqual(
                json.loads(request_path.read_text(encoding='utf-8')),
                sync.build_model_request(public_config),
            )
            supplied_local_config = sync_assets.call_args.args[2]
            self.assertEqual(supplied_local_config['codex_agent_runtime_overrides'], {})
            self.assertEqual(supplied_local_config['cursor_agent_runtime_overrides'], {})
            self.assertEqual(supplied_local_config['github_agent_runtime_overrides'], {})

    def test_main_uses_downloaded_manifest_instead_of_installed_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'source'
            target = root / 'target'
            source_rule = source / 'agents' / 'rules' / 'new-rule.md'
            source_skill = source / 'agents' / 'skills' / 'setup-project-agents'
            source_rule.parent.mkdir(parents=True)
            source_skill.mkdir(parents=True)
            target.mkdir()
            source_rule.write_text('new rule\n', encoding='utf-8')
            request_path = root / 'models.json'
            installed_config = {
                'source_repo': 'https://example.invalid/agents',
                'rules': [{'file': 'removed-rule.md'}],
                'skills': [],
                'agent_prompts': [],
            }
            downloaded_config = {
                'rules': [{'file': 'new-rule.md'}],
                'skills': [],
                'agent_prompts': [],
            }
            installed_manifest = REPO_REFERENCES / 'public_assets.json'
            downloaded_manifest = source_skill / 'references' / 'public_assets.json'

            def load_manifest(path):
                if Path(path) == installed_manifest:
                    return installed_config
                if Path(path) == downloaded_manifest:
                    return downloaded_config
                self.fail(f'Unexpected manifest path: {path}')

            previous_cwd = Path.cwd()
            stdout = io.StringIO()
            try:
                os.chdir(target)
                with mock.patch.object(
                    sync,
                    'load_json',
                    side_effect=load_manifest,
                ), mock.patch.object(
                    sync,
                    'resolve_source',
                    return_value=source,
                ), contextlib.redirect_stdout(stdout):
                    exit_code = sync.main(['--model-request', str(request_path)])
            finally:
                os.chdir(previous_cwd)

            self.assertEqual(exit_code, 0, stdout.getvalue())
            self.assertEqual(
                (target / '.agents' / 'rules' / 'new-rule.md').read_text(
                    encoding='utf-8'
                ),
                'new rule\n',
            )
            self.assertFalse((target / '.agents' / 'rules' / 'removed-rule.md').exists())
            self.assertEqual(
                json.loads(request_path.read_text(encoding='utf-8')),
                sync.build_model_request(downloaded_config),
            )

    def test_main_check_requires_completed_model_config(self):
        stderr = io.StringIO()
        with mock.patch.object(
            sync,
            'load_json',
            return_value={'rules': [], 'skills': [], 'agent_prompts': []},
        ), mock.patch.object(
            sync,
            'resolve_source',
            return_value=Path('/tmp/source'),
        ), mock.patch.object(
            sync,
            'sync_public_assets',
            return_value=[],
        ), contextlib.redirect_stderr(stderr):
            exit_code = sync.main(['--check'])

        self.assertEqual(exit_code, 2)
        self.assertIn('--check requires --model-config', stderr.getvalue())

    def test_main_requires_an_explicit_model_json_stage(self):
        stderr = io.StringIO()
        with mock.patch.object(
            sync,
            'load_json',
            return_value={'rules': [], 'skills': [], 'agent_prompts': []},
        ), mock.patch.object(
            sync,
            'resolve_source',
            return_value=Path('/tmp/source'),
        ), mock.patch.object(
            sync,
            'sync_public_assets',
            return_value=[],
        ), contextlib.redirect_stderr(stderr):
            exit_code = sync.main([])

        self.assertEqual(exit_code, 2)
        self.assertIn('requires --model-request or --model-config', stderr.getvalue())

    def test_main_second_stage_supplies_model_config_to_strict_sync(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            public_config = {
                'rules': [],
                'skills': [],
                'agent_prompts': [
                    {
                        'name': 'reviewer',
                        'required_intelligence': 'High reasoning depth.',
                    }
                ],
            }
            model_config = sync.build_model_request(public_config)
            model_config['agents']['reviewer']['codex'].update(
                model='codex-model',
                model_reasoning_effort='high',
            )
            model_config['agents']['reviewer']['cursor']['model'] = 'cursor-model'
            model_config['agents']['reviewer']['github']['model'] = 'github-model'
            model_path = root / 'models.json'
            model_path.write_text(json.dumps(model_config), encoding='utf-8')
            previous_cwd = Path.cwd()
            try:
                os.chdir(target)
                with mock.patch.object(
                    sync,
                    'load_json',
                    side_effect=lambda path: (
                        model_config if Path(path) == model_path else public_config
                    ),
                ), mock.patch.object(
                    sync,
                    'resolve_source',
                    return_value=root / 'source',
                ), mock.patch.object(
                    sync,
                    'sync_public_assets',
                    return_value=[],
                ) as sync_assets:
                    exit_code = sync.main(['--model-config', str(model_path)])
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(exit_code, 0)
        supplied_local_config = sync_assets.call_args.args[2]
        self.assertIn('reviewer', supplied_local_config['codex_agent_runtime_overrides'])
        self.assertEqual(
            supplied_local_config['codex_agent_runtime_overrides']['reviewer'],
            {'model': 'codex-model', 'model_reasoning_effort': 'high'},
        )
        self.assertEqual(
            supplied_local_config['cursor_agent_runtime_overrides']['reviewer'],
            {'model': 'cursor-model'},
        )
        self.assertEqual(
            supplied_local_config['github_agent_runtime_overrides']['reviewer'],
            {'model': 'github-model'},
        )
        self.assertTrue(sync_assets.call_args.kwargs['require_agent_runtime'])

    def test_main_model_protocol_includes_discovered_target_subagents(self):
        public_config = {'rules': [], 'skills': [], 'agent_prompts': []}
        local_config = {
            'rules': [],
            'agent_prompts': [
                {
                    'name': 'project-reviewer',
                    'description': 'Reviews project-specific API compatibility.',
                }
            ],
            'codex_agent_runtime_overrides': {},
            'cursor_agent_runtime_overrides': {},
            'github_agent_runtime_overrides': {},
        }
        model_config = sync.build_model_request(public_config, local_config)
        agent = model_config['agents']['project-reviewer']
        agent['codex'].update(model='codex-model', model_reasoning_effort='high')
        agent['cursor']['model'] = 'cursor-model'
        agent['github']['model'] = 'github-model'
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / 'models.json'
            model_path.write_text(json.dumps(model_config), encoding='utf-8')
            with mock.patch.object(
                sync,
                'load_json',
                side_effect=lambda path: (
                    model_config if Path(path) == model_path else public_config
                ),
            ), mock.patch.object(
                sync,
                'discover_local_assets',
                return_value=local_config,
            ), mock.patch.object(
                sync,
                'resolve_source',
                return_value=Path(temp_dir) / 'source',
            ), mock.patch.object(
                sync,
                'sync_public_assets',
                return_value=[],
            ) as sync_assets:
                exit_code = sync.main(['--model-config', str(model_path)])

        self.assertEqual(exit_code, 0)
        self.assertIn(
            'project-reviewer',
            sync_assets.call_args.args[2]['codex_agent_runtime_overrides'],
        )

    def test_main_check_returns_zero_for_unchanged_only_changes(self):
        stdout = io.StringIO()
        public_config = {
            'mirror_delete': True,
            'rules': [],
            'skills': [],
            'agent_prompts': [],
        }
        local_config = {'rules': [], 'agent_prompts': []}
        with mock.patch.object(
            sync,
            'sync_public_assets',
            return_value=[sync.Change('unchanged', '.agents/rules/10-base-code.md')],
        ), mock.patch.object(
            sync,
            'load_json',
            return_value=public_config,
        ), mock.patch.object(
            sync,
            'load_model_config',
            return_value={
                'codex_agent_runtime_overrides': {},
                'cursor_agent_runtime_overrides': {},
                'github_agent_runtime_overrides': {},
            },
        ), mock.patch.object(
            sync,
            'discover_local_assets',
            return_value=local_config,
        ), mock.patch.object(
            sync,
            'resolve_source',
            return_value=Path('/tmp/agents'),
        ), mock.patch.object(
            sync.Path,
            'cwd',
            return_value=Path('/tmp/target'),
        ), contextlib.redirect_stdout(stdout):
            exit_code = sync.main(['--check', '--model-config', '/tmp/models.json'])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().strip(), 'unchanged .agents/rules/10-base-code.md')

    def test_main_check_returns_one_for_missing_generated_output(self):
        stdout = io.StringIO()
        public_config = {
            'mirror_delete': True,
            'rules': [],
            'skills': [],
            'agent_prompts': [],
        }
        local_config = {'rules': [], 'agent_prompts': []}
        with mock.patch.object(
            sync,
            'sync_public_assets',
            return_value=[sync.Change('missing', '.agents/rules/20-project-tools.md')],
        ), mock.patch.object(
            sync,
            'load_json',
            return_value=public_config,
        ), mock.patch.object(
            sync,
            'load_model_config',
            return_value={
                'codex_agent_runtime_overrides': {},
                'cursor_agent_runtime_overrides': {},
                'github_agent_runtime_overrides': {},
            },
        ), mock.patch.object(
            sync,
            'discover_local_assets',
            return_value=local_config,
        ), mock.patch.object(
            sync,
            'resolve_source',
            return_value=Path('/tmp/agents'),
        ), mock.patch.object(
            sync.Path,
            'cwd',
            return_value=Path('/tmp/target'),
        ), contextlib.redirect_stdout(stdout):
            exit_code = sync.main(['--check', '--model-config', '/tmp/models.json'])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            stdout.getvalue().strip(),
            'missing .agents/rules/20-project-tools.md',
        )

    def test_discover_local_assets_preserves_project_specific_rules_and_agents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            rules_root = target / '.agents' / 'rules'
            agents_root = target / '.agents' / 'agents'
            rules_root.mkdir(parents=True)
            agents_root.mkdir(parents=True)
            (rules_root / '00-global-rule-config.md').write_text('Strength: Mandatory\n', encoding='utf-8')
            (rules_root / '30-module-common.md').write_text('Strength: Advisory\n', encoding='utf-8')
            (agents_root / 'project-agent.md').write_text(
                '---\nname: project-agent\ndescription: Project reviewer\nmodel: sonnet\n---\n',
                encoding='utf-8',
            )
            public_config = {
                'rules': [{'file': '00-global-rule-config.md'}],
                'agent_prompts': [],
            }

            result = sync.discover_local_assets(target, public_config)

        self.assertEqual(
            result['rules'],
            [
                {
                    'file': '30-module-common.md',
                    'read_when': 'Project-local rule applies',
                    'strength': 'Advisory',
                    'section': 'project',
                    'cursor': {
                        'description': '[project] 30-module-common',
                        'globs': '""',
                        'alwaysApply': True,
                    },
                    'github': {'applyTo': '**'},
                }
            ],
        )
        self.assertEqual(
            result['agent_prompts'],
            [{'name': 'project-agent', 'description': 'Project reviewer'}],
        )

    def test_discover_local_assets_preserves_existing_rule_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            rules_root = target / '.agents' / 'rules'
            cursor_root = target / '.cursor' / 'rules'
            github_root = target / '.github' / 'instructions'
            entry_root = target / 'config'
            rules_root.mkdir(parents=True)
            cursor_root.mkdir(parents=True)
            github_root.mkdir(parents=True)
            entry_root.mkdir(parents=True)
            (entry_root / 'AGENTS.md').write_text(
                '| Read when | Rule | Strength |\n'
                '| --- | --- | --- |\n'
                '| Working with module common widgets | `.agents/rules/30-module-common.md` |'
                ' `Advisory` |\n',
                encoding='utf-8',
            )
            (rules_root / '30-module-common.md').write_text('Strength: Default\n', encoding='utf-8')
            (cursor_root / '30-module-common.mdc').write_text(
                '---\n'
                'description: "[module] common widgets"\n'
                'globs: "common/**"\n'
                'alwaysApply: false\n'
                '---\n\n'
                'Apply @.agents/rules/30-module-common.md\n',
                encoding='utf-8',
            )
            (github_root / '30-module-common.instructions.md').write_text(
                '---\napplyTo: "common/**"\n---\n\nApply @.agents/rules/30-module-common.md\n',
                encoding='utf-8',
            )
            public_config = {
                'rules': [],
                'agent_prompts': [],
                'entry_files': [
                    {
                        'template': 'AGENTS.md',
                        'path': 'config/AGENTS.md',
                    }
                ],
            }

            result = sync.discover_local_assets(target, public_config)

        self.assertEqual(
            result['rules'],
            [
                {
                    'file': '30-module-common.md',
                    'read_when': 'Working with module common widgets',
                    'strength': 'Advisory',
                    'section': 'project',
                    'cursor': {
                        'description': '[module] common widgets',
                        'globs': 'common/**',
                        'alwaysApply': False,
                    },
                    'github': {'applyTo': 'common/**'},
                }
            ],
        )

    def test_discover_local_assets_uses_catalog_routing_for_generated_project_rule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            rules_root = target / '.agents' / 'rules'
            rules_root.mkdir(parents=True)
            (rules_root / '20-project-tools.md').write_text(
                'Strength: Default\n',
                encoding='utf-8',
            )
            expected = {
                'file': '20-project-tools.md',
                'read_when': 'Project tooling, MCP, runtime, or verification',
                'strength': 'Mandatory',
                'section': 'project',
                'cursor': {'alwaysApply': True},
                'github': {'applyTo': '**'},
            }
            public_config = {
                'rules': [],
                'rule_blueprints': [expected],
                'agent_prompts': [],
            }

            result = sync.discover_local_assets(target, public_config)

        self.assertEqual(result['rules'], [expected])


class TrackWorktreeTimeTest(unittest.TestCase):
    def setUp(self):
        self.timing = load_track_worktree_time_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name)
        self.started_at = datetime(2026, 7, 16, 2, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp_dir.cleanup()

    def at(self, seconds):
        return self.started_at + timedelta(seconds=seconds)

    def test_repeated_phases_accumulate_and_reconcile_with_total(self):
        state = self.timing.start_task(
            task='timed change',
            repository='D:/repo',
            phase='environment',
            state_dir=self.state_dir,
            now=self.at(0),
        )
        task_id = state['task_id']
        self.timing.transition_task(
            task_id, 'code-generation', self.state_dir, now=self.at(10)
        )
        self.timing.transition_task(task_id, 'review', self.state_dir, now=self.at(30))
        self.timing.transition_task(
            task_id, 'code-generation', self.state_dir, now=self.at(40)
        )
        self.timing.transition_task(task_id, 'testing', self.state_dir, now=self.at(60))

        completed = self.timing.finish_task(task_id, self.state_dir, now=self.at(70))
        report = self.timing.build_report(completed)

        self.assertEqual(report['phases']['environment'], 10_000_000)
        self.assertEqual(report['phases']['code-generation'], 40_000_000)
        self.assertEqual(report['phases']['review'], 10_000_000)
        self.assertEqual(report['phases']['testing'], 10_000_000)
        self.assertEqual(report['total'], 70_000_000)
        self.assertEqual(
            sum(value for value in report['phases'].values() if value is not None),
            report['total'],
        )

    def test_pause_resume_and_unused_phases_are_reported(self):
        state = self.timing.start_task(
            task='paused change',
            repository='D:/repo',
            phase='environment',
            state_dir=self.state_dir,
            now=self.at(0),
        )
        task_id = state['task_id']
        self.timing.pause_task(task_id, self.state_dir, now=self.at(5))
        self.timing.resume_task(
            task_id, 'code-generation', self.state_dir, now=self.at(15)
        )

        completed = self.timing.finish_task(task_id, self.state_dir, now=self.at(25))
        report = self.timing.build_report(completed)
        markdown = self.timing.render_markdown(report)

        self.assertEqual(report['phases']['waiting'], 10_000_000)
        self.assertIsNone(report['phases']['integration'])
        self.assertIn('| integration | not applicable |', markdown)
        self.assertIn('| total | 00:00:25.000 |', markdown)

    def test_state_uses_system_temp_by_default_and_isolates_tasks(self):
        self.assertEqual(
            self.timing.default_state_dir(),
            Path(tempfile.gettempdir()) / 'codex-worktree-time',
        )
        first = self.timing.start_task(
            task='first',
            repository='D:/repo',
            phase='environment',
            state_dir=self.state_dir,
            now=self.at(0),
        )
        second = self.timing.start_task(
            task='second',
            repository='D:/repo',
            phase='environment',
            state_dir=self.state_dir,
            now=self.at(0),
        )

        self.assertNotEqual(first['task_id'], second['task_id'])
        self.assertTrue((self.state_dir / f"{first['task_id']}.json").is_file())
        self.assertTrue((self.state_dir / f"{second['task_id']}.json").is_file())


if __name__ == '__main__':
    unittest.main()
