import contextlib
import importlib.util
import io
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

    def test_parser_rejects_local_source_argument(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            sync.build_parser().parse_args(['--source', 'local-agents'])

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
            public_config['project_skill_generators'] = []
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
            public_config['project_skill_generators'] = []
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

    def test_sync_preserves_reviewed_codex_runtime_fields_from_target_wrapper(self):
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
            public_config['project_skill_generators'] = []
            public_config['platforms']['agent_wrappers'] = [
                wrapper
                for wrapper in public_config['platforms']['agent_wrappers']
                if wrapper['template'] == 'agent_wrapper.codex.toml'
            ]
            local_config = sync.discover_local_assets(target, public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            wrapper = tomllib.loads(existing_wrapper.read_text(encoding='utf-8'))
            self.assertEqual(wrapper['name'], 'change-set-verifier')
            self.assertEqual(
                wrapper['description'],
                'Normalizes and verifies a coherent completed change set, then returns semantic '
                'diagnostics to the parent agent.',
            )
            self.assertEqual(wrapper['model'], 'project-reviewed-model')
            self.assertEqual(wrapper['model_reasoning_effort'], 'high')
            self.assertEqual(wrapper['sandbox_mode'], 'read-only')

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
            public_config['project_skill_generators'] = []
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
            public_config['project_skill_generators'] = []
            context = sync.SyncContext(target, source, skill_root, False, [])

            with self.assertRaises(sync.SyncError) as error:
                sync.sync_public_assets(
                    context,
                    public_config,
                    {'rules': [], 'agent_prompts': []},
                    require_agent_runtime=True,
                )

            self.assertIn('requires reviewed fields: model', str(error.exception))

    def test_sync_preserves_reviewed_cursor_runtime_fields_from_target_wrapper(self):
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
            public_config['project_skill_generators'] = []
            local_config = sync.discover_local_assets(target, public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            frontmatter = sync._read_frontmatter(existing_wrapper)
            self.assertEqual(frontmatter['name'], 'change-set-verifier')
            self.assertEqual(frontmatter['model'], 'project-reviewed-cursor-model')
            self.assertIs(frontmatter['readonly'], False)
            self.assertIn(
                'Apply @.agents/agents/change-set-verifier.md',
                existing_wrapper.read_text(encoding='utf-8'),
            )

    def test_sync_preserves_reviewed_github_model_and_enables_model_invocation(self):
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
            public_config['project_skill_generators'] = []
            local_config = sync.discover_local_assets(target, public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            frontmatter = sync._read_frontmatter(existing_wrapper)
            self.assertEqual(frontmatter['name'], 'change-set-verifier')
            self.assertEqual(frontmatter['model'], 'project-reviewed-github-model')
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
            public_config['project_skill_generators'] = []
            local_config = sync.discover_local_assets(target, public_config)
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(
                context,
                public_config,
                local_config,
                require_agent_runtime=True,
            )

            codex = tomllib.loads(codex_wrapper.read_text(encoding='utf-8'))
            self.assertEqual(codex['model'], 'project-codex-model')
            self.assertEqual(codex['model_reasoning_effort'], 'high')
            self.assertEqual(
                sync._read_frontmatter(cursor_wrapper)['model'],
                'project-cursor-model',
            )
            self.assertEqual(
                sync._read_frontmatter(github_wrapper)['model'],
                'project-github-model',
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
            public_config['project_skill_generators'] = []
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            codex_config = tomllib.loads(
                (target / '.codex' / 'config.toml').read_text(encoding='utf-8')
            )
            self.assertIs(codex_config['features']['multi_agent'], True)
            self.assertFalse((target / '.cursor' / 'mcp.json').exists())

    def test_setup_skill_delegates_root_configuration_to_sync_script(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized = ' '.join(content.split())

        self.assertIn(
            'Let the synchronization command manage deterministic root configuration and entry files',
            normalized,
        )
        self.assertIn('Review its reported changes', normalized)
        self.assertIn('instead of reconstructing or editing managed values manually', normalized)
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
            'Generate project-owned configuration from current target evidence. Previous content '
            'may be used as reference during generation, but it is not a source of truth.',
            ' '.join(english.split()),
        )
        self.assertIn(
            '根据目标仓库的当前证据生成项目自有配置。生成过程中可以参考旧内容，'
            '但旧内容不是事实源。',
            ' '.join(chinese.split()),
        )

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
            '03-global-engineering-workflow.md',
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
            public_config['project_skill_generators'] = []
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

    def test_sync_does_not_create_missing_project_rule_placeholder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_rules = source / 'agents' / 'rules'
            source_rules.mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source_rules / '20-project-tools.md').write_text('project tools placeholder\n', encoding='utf-8')
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
            source_skill = source / 'agents' / 'skills' / 'worktree-environment-setup'
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
                'project_skill_generators': [{'name': 'worktree-environment-setup'}],
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
            source_skill = source / 'agents' / 'skills' / 'change-set-verification'
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
                'project_skill_generators': [{'name': 'change-set-verification'}],
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

    def test_retired_project_development_workflow_is_absent(self):
        self.assertFalse(
            (REPO_ROOT / 'agents' / 'skills' / 'project-development-workflow').exists()
        )

    def test_public_config_lists_change_set_verification_generator(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        generator_names = {
            generator['name'] for generator in public_config['project_skill_generators']
        }

        self.assertIn('worktree-environment-setup', generator_names)
        self.assertIn('change-set-verification', generator_names)

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
                'rules': ['03-global-skill-config.md'],
                'skills': [
                    'update-project-rules',
                    'project-development-workflow',
                    'project-verification',
                ],
                'agents': ['rename', 'verifier'],
            },
        )
        for retired_name in (
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
        workflow = (source_root / '03-global-engineering-workflow.md').read_text(
            encoding='utf-8'
        )
        skill_config = (source_root / '04-global-skill-config.md').read_text(
            encoding='utf-8'
        )
        mirror_personality = (mirror_root / '01-global-personality.md').read_text(
            encoding='utf-8'
        )
        mirror_workflow = (mirror_root / '03-global-engineering-workflow.md').read_text(
            encoding='utf-8'
        )
        mirror_skill_config = (mirror_root / '04-global-skill-config.md').read_text(
            encoding='utf-8'
        )

        self.assertTrue(personality.startswith('# Agent Personality\n'))
        self.assertIn('## Reasoning', personality)
        self.assertNotIn('## Change', personality)
        self.assertTrue(workflow.startswith('# Engineering Workflow\n'))
        self.assertIn('## Change', workflow)
        self.assertIn('## Verify', workflow)
        self.assertIn(
            'For advisory or informational questions, search the web before answering and ground '
            'the response in current sources.',
            ' '.join(workflow.split()),
        )
        self.assertTrue(skill_config.startswith('# Workflow Configuration\n'))
        self.assertTrue(mirror_personality.startswith('# Agent 人格\n'))
        self.assertIn('## 推理方式', mirror_personality)
        self.assertTrue(mirror_workflow.startswith('# 工程工作流\n'))
        self.assertIn('## 修改', mirror_workflow)
        self.assertIn('## 验证', mirror_workflow)
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
            source_skill = source / 'agents' / 'skills' / 'worktree-environment-setup'
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
                'project_skill_generators': [{'name': 'worktree-environment-setup'}],
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
            source_skill = source / 'agents' / 'skills' / 'change-set-verification'
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
                'project_skill_generators': [
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

    def test_sync_does_not_copy_change_set_verification_generator_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = source / 'agents' / 'skills' / 'change-set-verification'
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
                'project_skill_generators': [{'name': 'change-set-verification'}],
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
                    'model': 'sonnet',
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
            [{'name': 'project-agent', 'description': 'Project-local agent: project-agent', 'model': 'sonnet'}],
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
                    'resolve_source',
                    return_value=source,
                ), contextlib.redirect_stdout(stdout):
                    exit_code = sync.main(['--check'])
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(exit_code, 1)

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
            exit_code = sync.main(['--check'])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().strip(), 'unchanged .agents/rules/10-base-code.md')

    def test_main_check_returns_one_for_drift_changes(self):
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
            return_value=[sync.Change('created', '.agents/rules/10-base-code.md')],
        ), mock.patch.object(
            sync,
            'load_json',
            return_value=public_config,
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
            exit_code = sync.main(['--check'])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue().strip(), 'created .agents/rules/10-base-code.md')

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
            [{'name': 'project-agent', 'description': 'Project reviewer', 'model': 'sonnet'}],
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
