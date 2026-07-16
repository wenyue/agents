import contextlib
import io
import os
import json
import shutil
import tempfile
import tomllib
import unittest
import zipfile
from unittest import mock
from pathlib import Path

import sync_public_agent_assets as sync


REPO_SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = REPO_SKILL_ROOT.parents[2]
REPO_REFERENCES = REPO_SKILL_ROOT / 'references'
REPO_TEMPLATES = REPO_SKILL_ROOT / 'assets' / 'templates'


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
            (local_source / '.agents' / 'rules').mkdir(parents=True)
            (local_source / '.agents' / 'rules' / '10-base-code.md').write_text('local\n', encoding='utf-8')
            archive = root / 'agents.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('agents-master/.agents/rules/10-base-code.md', 'archive\n')
            public_config = {
                'source_archive_url': archive.resolve().as_uri(),
            }

            try:
                result = sync.resolve_source(public_config)
            except sync.SyncError as error:
                self.fail(f'resolve_source should fetch archive: {error}')

            self.assertEqual((result / '.agents' / 'rules' / '10-base-code.md').read_text(), 'archive\n')

    def test_resolve_source_refetches_archive_every_time(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / 'agents.zip'
            public_config = {
                'source_archive_url': archive.resolve().as_uri(),
            }

            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('agents-master/.agents/rules/10-base-code.md', 'first\n')
            first = sync.resolve_source(public_config)

            archive.unlink()
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('agents-master/.agents/rules/10-base-code.md', 'second\n')
            second = sync.resolve_source(public_config)

        self.assertNotEqual(first, second)
        self.assertEqual((first / '.agents' / 'rules' / '10-base-code.md').read_text(), 'first\n')
        self.assertEqual((second / '.agents' / 'rules' / '10-base-code.md').read_text(), 'second\n')

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
                package.writestr('agents-master/.agents/rules/10-base-code.md', 'rule\n')
                package.writestr('agents-master/.agents/skills/rename/SKILL.md', 'rename skill\n')
                package.writestr('agents-master/.agents/skills/unlisted/SKILL.md', 'unlisted skill\n')
                package.writestr('agents-master/.agents/agents/sample-agent.md', 'sample agent\n')
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
            (source / '.agents' / 'rules').mkdir(parents=True)
            (source / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            (source / '.agents' / 'agents').mkdir(parents=True)
            (target / '.agents' / 'rules').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / '.agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
            (source / '.agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
            (source / '.agents' / 'agents' / 'sample-agent.md').write_text(
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
            (source / '.agents' / 'rules').mkdir(parents=True)
            (target / '.agents' / 'rules').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / '.agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
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
            (source / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            (target / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / '.agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
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
            (source / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            (target / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / '.agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
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
            (source / '.agents' / 'skills' / 'rename').mkdir(parents=True)
            (target / '.agents' / 'skills' / 'rename' / 'unused' / 'nested').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / '.agents' / 'skills' / 'rename' / 'SKILL.md').write_text('skill\n', encoding='utf-8')
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
            source_skill = source / '.agents' / 'skills' / 'setup-project-agents'
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
            (source / '.agents' / 'skills').mkdir(parents=True)
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
            source_skill = source / '.agents' / 'skills' / 'rename'
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
            (source / '.agents' / 'rules').mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source / '.agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
            public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
            public_config['rules'] = [rule for rule in public_config['rules'] if rule['file'] == '10-base-code.md']
            public_config['skills'] = []
            public_config['agent_prompts'] = []
            local_config = {'rules': [], 'agent_prompts': []}
            context = sync.SyncContext(target, source, skill_root, False, [])

            sync.sync_public_assets(context, public_config, local_config)

            expected = (
                '---\n'
                'description: "[default] Cross-language code taste for ownership, extraction, state, and flow"\n'
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
            (source / '.agents' / 'rules').mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source / '.agents' / 'rules' / '00-global-rule-config.md').write_text('rule\n', encoding='utf-8')
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
            source_agents = source / '.agents' / 'agents'
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
            source_agents = source / '.agents' / 'agents'
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
            source_agents = source / '.agents' / 'agents'
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
            source_agents = source / '.agents' / 'agents'
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
            source_agents = source / '.agents' / 'agents'
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

    def test_sync_preserves_reviewed_github_model_from_target_wrapper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / '.agents' / 'agents'
            source_agents.mkdir(parents=True)
            templates.mkdir(parents=True)
            for template in REPO_TEMPLATES.glob('*'):
                shutil.copy2(template, templates / template.name)
            (source_agents / 'change-set-verifier.md').write_text('agent\n', encoding='utf-8')
            existing_wrapper = target / '.github' / 'agents' / 'change-set-verifier.agent.md'
            existing_wrapper.parent.mkdir(parents=True)
            existing_wrapper.write_text(
                '---\nname: stale\ndescription: stale\n'
                'model: project-reviewed-github-model\n---\nstale body\n',
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
            source_agents = source / '.agents' / 'agents'
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

    def test_sync_does_not_create_platform_root_config_for_agent_discovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            source_agents = source / '.agents' / 'agents'
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

            sync.sync_public_assets(context, public_config, {'rules': [], 'agent_prompts': []})

            self.assertFalse((target / '.codex' / 'config.toml').exists())
            self.assertFalse((target / '.cursor' / 'mcp.json').exists())

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
            source_agents = source / '.agents' / 'agents'
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

    def test_sync_generates_agents_entry_from_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            templates = skill_root / 'assets' / 'templates'
            templates.mkdir(parents=True)
            (templates / 'AGENTS.md').write_text(
                '# Project Agent Entry\n\n{{global_rule_rows}}\n{{base_rule_rows}}\n{{project_rule_rows}}\n',
                encoding='utf-8',
            )
            source_rules = source / '.agents' / 'rules'
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

            entry = (target / 'AGENTS.md').read_text(encoding='utf-8')
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

    def test_sync_does_not_create_missing_project_rule_placeholder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_rules = source / '.agents' / 'rules'
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
            source_skill = source / '.agents' / 'skills' / 'worktree-environment-setup'
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
            source_skill = source / '.agents' / 'skills' / 'change-set-verification'
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

    def test_project_rules_use_generator_contract_style(self):
        for filename in [
            '20-project-tools.md',
            '21-project-rules.md',
            '22-project-structure.md',
        ]:
            with self.subTest(filename=filename):
                content = (REPO_ROOT / '.agents' / 'rules' / filename).read_text(encoding='utf-8')

                self.assertIn('\nStrength: `', content)
                self.assertIn('\nScope: ', content)
                self.assertIn('## Generation Contract', content)
                self.assertIn('## Evidence', content)
                self.assertIn('## Content', content)
                self.assertIn('## Boundaries', content)
                self.assertNotIn('## Placeholder', content)
                self.assertNotIn('Write the generated rule in English', content)
                self.assertNotIn('Generate a complete candidate', content)

    def test_worktree_environment_setup_is_generator_contract(self):
        workflow = (
            REPO_ROOT
            / '.agents'
            / 'skills'
            / 'worktree-environment-setup'
            / 'SKILL.md'
        )
        content = workflow.read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertTrue(
            content.startswith(
                '---\n'
                'name: worktree-environment-setup\n'
                'description: Use when creating or revising a target repository'
            )
        )
        self.assertIn('## Authoring Workflow', content)
        self.assertIn('## Generated Skill Contract', content)
        self.assertIn('## Failure Recovery', content)
        self.assertIn('## Review and Handoff', content)
        self.assertIn('.agents/rules/20-project-tools.md', content)
        self.assertIn('minimum repeatable preparation', normalized_content)
        self.assertIn('already-created linked worktree', content)
        self.assertIn('generated-file ownership', normalized_content)
        self.assertIn('scripts/setup.sh', content)
        self.assertIn('scripts/setup.ps1', content)
        self.assertIn('same core environment result', normalized_content)
        self.assertIn('`change-set-verification`', content)
        self.assertIn('verification trigger timing', normalized_content)
        self.assertIn('scope selection', content)
        self.assertIn(
            'Require the generated `SKILL.md` to include its own `## Failure Recovery`',
            normalized_content,
        )
        self.assertIn('analyze the cause', content)
        self.assertIn('propose a concrete script or environment change', normalized_content)
        self.assertIn('stop immediately', normalized_content)
        self.assertNotIn('## Review Gate', content)
        self.assertNotIn('## Acceptance', content)
        self.assertNotIn('[CmdletBinding()]', content)
        self.assertNotIn('$LASTEXITCODE', content)
        self.assertNotIn('merge-back', content)
        self.assertNotIn('create or enter an isolated', content)
        self.assertNotIn('\nStrength:', content)
        self.assertNotIn('\nScope:', content)
        self.assertFalse((REPO_ROOT / '.agents' / 'skills' / 'project-development-workflow').exists())

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
        self.assertFalse((REPO_ROOT / '.agents' / 'agents' / 'rename.md').exists())
        self.assertFalse((REPO_ROOT / '.agents' / 'agents' / 'verifier.md').exists())
        self.assertTrue(
            (REPO_ROOT / '.agents' / 'agents' / 'change-set-verifier.md').is_file()
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
                'rules': [],
                'skills': [
                    'update-project-rules',
                    'project-development-workflow',
                    'project-verification',
                ],
                'agents': ['rename', 'verifier'],
            },
        )
        for retired_name in (
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

    def test_change_set_verification_is_generator_contract(self):
        workflow = (
            REPO_ROOT
            / '.agents'
            / 'skills'
            / 'change-set-verification'
            / 'SKILL.md'
        )
        content = workflow.read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertTrue(
            content.startswith(
                '---\n'
                'name: change-set-verification\n'
                'description: Use when creating or revising a target repository'
            )
        )
        self.assertIn('## Authoring Workflow', content)
        self.assertIn('## Generated Skill Contract', content)
        self.assertIn('### Normalization and Repair', content)
        self.assertIn('### Verification and Results', content)
        self.assertIn('## Optional Resources', content)
        self.assertIn('## Review and Handoff', content)
        self.assertIn('coherent completed change set', content)
        self.assertIn('minimum sufficient', content)
        self.assertIn('once per completed checkpoint', content)
        self.assertIn('Start with the minimum sufficient scope', content)
        self.assertIn('project-approved automatic fixer', content)
        self.assertIn(
            'regardless of whether the current change introduced',
            normalized_content,
        )
        self.assertIn('Do not widen scope only to discover or repair older violations', normalized_content)
        self.assertIn('remaining semantic diagnostics to the parent implementation agent', content)
        self.assertIn('directly owned tests', content)
        self.assertIn('full baseline suite', normalized_content)
        for status in ['passed', 'failed', 'inconclusive', 'not applicable']:
            self.assertIn(f'`{status}`', content)
        self.assertIn('`semantic_fix_required`', content)
        self.assertIn('A generated skill with scripts', normalized_content)
        self.assertIn('include `## Failure Recovery`', normalized_content)
        self.assertIn('stop on script failure', normalized_content)
        self.assertIn('analyze the cause', normalized_content)
        self.assertIn('propose a candidate change', normalized_content)
        self.assertNotIn('## Acceptance', content)
        self.assertNotIn('\nStrength:', content)

    def test_project_tools_contract_records_tool_facts_not_verification_workflow(self):
        content = (REPO_ROOT / '.agents' / 'rules' / '20-project-tools.md').read_text(
            encoding='utf-8'
        )
        normalized_content = ' '.join(content.split())

        self.assertIn('tool facts, capabilities, and invocation constraints', normalized_content)
        self.assertIn('supported scope selection', normalized_content)
        self.assertIn('mutation behavior', normalized_content)
        self.assertIn('safe-fix capability', normalized_content)
        self.assertIn('relative cost', normalized_content)
        self.assertIn('`.agents/skills/change-set-verification/`', normalized_content)
        self.assertIn('verification trigger timing', normalized_content)
        self.assertIn('deduplication', normalized_content)
        self.assertIn('risk-based broadening', normalized_content)

    def test_write_skill_owns_portability_without_global_rule_duplication(self):
        rule = (REPO_ROOT / '.agents' / 'rules' / '00-global-rule-config.md').read_text(
            encoding='utf-8'
        )
        skill = (REPO_ROOT / '.agents' / 'skills' / 'write-skill' / 'SKILL.md').read_text(
            encoding='utf-8'
        )
        normalized_skill = ' '.join(skill.split())

        self.assertNotIn('## Skill Authoring Ownership', rule)
        self.assertNotIn('skill classification, complete-rewrite behavior', rule)
        self.assertNotIn('## Skill Portability', rule)
        self.assertIn('## Path and Ownership Rules', skill)
        self.assertIn('Never hardcode an absolute filesystem path', normalized_skill)
        self.assertIn('repository-root-relative paths', normalized_skill)
        self.assertIn('semantic project targets and runtime discovery', normalized_skill)

    def test_setup_project_agents_requires_subagent_local_generation(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')

        self.assertIn('subagent', content)
        self.assertIn('generator contracts', content)
        self.assertIn('.agents/rules/20-project-tools.md', content)
        self.assertIn('.agents/rules/21-project-rules.md', content)
        self.assertIn('.agents/rules/22-project-structure.md', content)
        self.assertIn('.agents/skills/worktree-environment-setup/', content)
        self.assertIn('.agents/skills/change-set-verification/', content)
        self.assertIn('blocker', content)

    def test_setup_project_agents_requires_english_for_generated_project_assets(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')

        self.assertIn(
            'Write every generated or refreshed project-owned rule and skill in English.',
            content,
        )

    def test_setup_project_agents_owns_only_shared_generation_requirements(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertIn('## Shared Generation Requirements', content)
        self.assertIn('conform to `.agents/rules/00-global-rule-config.md`', normalized_content)
        for required_rule_field in ('title', '`Strength:`', '`Scope:`', 'numbering'):
            self.assertIn(required_rule_field, normalized_content)
        self.assertIn('frontmatter containing only `name` and `description`', normalized_content)
        self.assertIn('Follow the target generator contracts', normalized_content)
        self.assertNotIn('## Failure Recovery', content)
        self.assertNotIn('minimum preparation', content)
        self.assertNotIn('Normalization And Mechanical Repair', content)

    def test_setup_project_agents_uses_full_reconciliation_for_setup_and_update(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertIn('same complete reconciliation', content)
        self.assertIn('one idempotent workflow', normalized_content)
        self.assertIn('as complete candidates', content)
        self.assertIn('only as omission checklists', normalized_content)
        self.assertIn('revalidate every retained', content)
        self.assertIn('real temporary linked worktree', content)
        self.assertIn('byte equality', content)
        self.assertIn('created or materially changed', content)
        self.assertIn('byte-equivalent candidates', content)

    def test_setup_project_agents_reviews_and_accepts_generated_rules(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertGreaterEqual(content.count('### Generated Rules'), 2)
        self.assertIn('correct title, `Strength:`, `Scope:`, number', normalized_content)
        self.assertIn('placeholder language', content)
        self.assertIn('static and integration checks', normalized_content)
        self.assertIn('`AGENTS.md`', content)
        self.assertIn('wrappers remain thin', normalized_content)
        self.assertIn('single source of truth', normalized_content)
        self.assertIn(
            'rules, environment setup, then change-set verification',
            normalized_content,
        )

    def test_setup_project_agents_reviews_environment_skill_before_acceptance(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertIn('## Review', content)
        self.assertIn('## Acceptance', content)
        review_index = content.index('## Review')
        acceptance_index = content.index('## Acceptance')

        self.assertLess(review_index, acceptance_index)
        self.assertIn('both host entry points', normalized_content)
        self.assertIn('Review complete candidate files', content)
        self.assertIn('Do not start acceptance while any review finding', content)
        self.assertIn('Run only after candidate review passes', content)
        self.assertIn('native shell tooling', normalized_content)
        self.assertIn('Bash on Linux and macOS', normalized_content)
        self.assertIn('PowerShell on Windows', normalized_content)
        self.assertIn(
            "Do not parse or invoke the other platform's setup script",
            normalized_content,
        )
        self.assertNotIn('parse both setup scripts', content)
        self.assertIn('real temporary linked worktree', content)
        self.assertIn('Inspect both repository and worktree state', content)
        self.assertNotIn('## Environment Skill Evidence', content)
        self.assertNotIn('## Environment Skill Script Selection', content)
        self.assertNotIn('[CmdletBinding()]', content)
        self.assertNotIn('$LASTEXITCODE', content)

    def test_setup_project_agents_reviews_and_accepts_change_set_verification(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertIn('one subagent', content)
        self.assertIn('verification matrix', content)
        self.assertIn('unconditional whole-project checks', content)
        self.assertIn('unrelated dirty files', content)
        self.assertIn('approved automatic fixer', content)
        self.assertIn('semantic diagnostics return to the parent', normalized_content)
        self.assertIn(
            'Accept the environment skill before the verification skill',
            normalized_content,
        )
        self.assertIn('expensive full suite only for acceptance', normalized_content)

    def test_setup_project_agents_reviews_agent_runtime_on_every_run(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertIn('## Agent Runtime Review', content)
        self.assertIn('every setup or update', content)
        self.assertIn('Do not store model or reasoning-effort choices', content)
        self.assertIn('during every setup or update', normalized_content)
        for field in ('model', 'model_reasoning_effort', 'sandbox_mode'):
            self.assertIn(f'`{field}`', content)
        self.assertIn('Cursor and GitHub Copilot wrappers', normalized_content)
        self.assertIn('Retain them only after confirming', normalized_content)
        self.assertIn('explicit supported model', normalized_content)
        self.assertIn('Require non-empty', normalized_content)
        self.assertIn('final-gate blocker', normalized_content)
        self.assertIn('representative smoke invocation', content)
        self.assertIn('final public sync must preserve', normalized_content)
        self.assertIn('## Platform Configuration Review', content)
        self.assertIn(
            'Do not create `.codex/config.toml` only to register agents',
            normalized_content,
        )

    def test_script_failure_recovery_is_not_owned_by_setup_project_agents(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())

        self.assertNotIn('## Failure Recovery', content)
        self.assertNotIn('If a generated script fails', normalized_content)

    def test_worktree_integrate_is_public_skill(self):
        skill_path = REPO_ROOT / '.agents' / 'skills' / 'worktree-integrate' / 'SKILL.md'
        content = skill_path.read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
        rule = (REPO_ROOT / '.agents' / 'rules' / '03-global-skill-config.md').read_text(
            encoding='utf-8'
        )

        self.assertIn({'name': 'worktree-integrate'}, public_config['skills'])
        self.assertTrue(
            content.startswith(
                '---\n'
                'name: worktree-integrate\n'
                'description: Use when verified implementation in a named linked Git worktree'
            )
        )
        self.assertIn('## Review Mode', content)
        self.assertIn('## Commit Mode', content)
        self.assertIn('HEAD and index unchanged', content)
        self.assertIn('three-way merge', content)
        self.assertIn('downgrade to review mode', content)
        self.assertIn('task branch, worktree, and external backup', normalized_content)
        self.assertIn('confirmed task-owned work', normalized_content)
        self.assertIn('Git common directory', normalized_content)
        self.assertIn('rebase the task commit again', normalized_content)
        self.assertIn('keep the returned working-tree result', normalized_content)
        self.assertIn('creation ownership', normalized_content)
        self.assertIn('platform-created worktrees', normalized_content)
        self.assertIn('git merge --ff-only', content)
        self.assertIn('superpowers:finishing-a-development-branch', content)
        self.assertIn('superpowers:using-git-worktrees', rule)
        self.assertIn('worktree-environment-setup', rule)
        self.assertIn('worktree-integrate', rule)
        self.assertIn('superpowers:finishing-a-development-branch', rule)
        self.assertNotIn('Assume `master`', rule)
        self.assertNotIn('project-development-workflow', rule)

    def test_write_skill_is_public_and_requires_global_rewrite(self):
        skill_path = REPO_ROOT / '.agents' / 'skills' / 'write-skill' / 'SKILL.md'
        mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / 'write-skill' / 'SKILL.md'
        content = skill_path.read_text(encoding='utf-8')
        mirror = mirror_path.read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn({'name': 'write-skill'}, public_config['skills'])
        self.assertTrue(
            content.startswith(
                '---\n'
                'name: write-skill\n'
                'description: Use when creating, rewriting, or materially updating any agent skill,'
            )
        )
        self.assertIn('## Whole-Skill Rewrite Invariant', content)
        self.assertIn('## Classify Before Authoring', content)
        self.assertIn('## Required Format and Contract Shape', content)
        self.assertIn('## Anti-Degradation Gate', content)
        self.assertIn('## Validation and Handoff', content)
        self.assertIn('Project-local skill', content)
        self.assertIn('Shared skill-generation contract', content)
        self.assertIn('Shared skill', content)
        self.assertNotIn('Shared generator contract', content)
        self.assertNotIn('Shared direct-execution contract', content)
        self.assertIn('共享 Skill 生成契约', mirror)
        self.assertIn('共享 Skill', mirror)
        self.assertNotIn('共享生成器契约', mirror)
        self.assertNotIn('共享直接执行契约', mirror)
        self.assertIn('evidence and an omission checklist', normalized_content)
        self.assertIn('complete candidate', normalized_content)
        self.assertIn('never optimize the skill for the smallest textual patch', normalized_content)
        self.assertIn('Do not append a new exception, note, addendum', normalized_content)
        self.assertIn('Rewrite the governing sections', normalized_content)
        self.assertIn('Do not turn a target-specific skill into a shared skill', normalized_content)
        self.assertIn('Never hardcode an absolute filesystem path', normalized_content)
        self.assertIn('target facts come from evidence rather than the generator', normalized_content)
        self.assertIn('Would this be the skill written today if no previous version existed?', content)
        self.assertIn('frontmatter containing only `name` and `description`', normalized_content)
        self.assertNotIn('[TODO', content)
        self.assertFalse((skill_path.parent / 'README.md').exists())
        self.assertFalse((skill_path.parent / 'CHANGELOG.md').exists())

    def test_write_rule_is_public_and_rewrites_complete_rule(self):
        skill_path = REPO_ROOT / '.agents' / 'skills' / 'write-rule' / 'SKILL.md'
        mirror_path = REPO_ROOT / 'agents-zh' / 'skills' / 'write-rule' / 'SKILL.md'
        content = skill_path.read_text(encoding='utf-8')
        mirror = mirror_path.read_text(encoding='utf-8')
        normalized_content = ' '.join(content.split())
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn({'name': 'write-rule'}, public_config['skills'])
        self.assertTrue(
            content.startswith(
                '---\n'
                'name: write-rule\n'
                'description: Use when creating, rewriting, or materially updating '
                'any repository rule,'
            )
        )
        for heading in (
            '## Whole-Rule Rewrite Invariant',
            '## Classify Before Authoring',
            '## Evidence',
            '## Path and Ownership Rules',
            '## Required Format and Contract Shape',
            '## Workflow',
            '## Content and Boundaries',
            '## Anti-Degradation Gate',
            '## Validation and Handoff',
            '## Result',
        ):
            self.assertIn(heading, content)
        self.assertIn('Project-local rule', content)
        self.assertIn('Shared rule', content)
        self.assertIn('Shared rule-generation contract', content)
        self.assertIn(
            'Generation Contract; Evidence; Content; Boundaries', normalized_content
        )
        self.assertIn(
            'existing rule and its discovery surfaces as evidence and an omission checklist',
            normalized_content,
        )
        self.assertIn('The diff is only a delivery mechanism', normalized_content)
        self.assertIn('Never hardcode an absolute filesystem path', normalized_content)
        self.assertIn('target facts come from evidence rather than the generator', normalized_content)
        self.assertIn(
            'Do not turn a target-specific rule into a shared rule', normalized_content
        )
        self.assertIn(
            'When intent is clear, implement the policy in its natural owner and report the '
            'named-destination conflict',
            normalized_content,
        )
        self.assertIn(
            'Would this be the rule written today if no previous version existed?',
            normalized_content,
        )
        self.assertIn('name: write-rule', mirror)
        self.assertEqual(content.count('\n## '), mirror.count('\n## '))

    def test_setup_project_agents_uses_public_archive_without_local_source_or_cache(self):
        content = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')

        self.assertIn('Always fetch the configured public GitHub archive', content)
        self.assertNotIn('`--source', content)
        self.assertIn('source_repo', public_config)
        self.assertNotIn('source_default', public_config)
        self.assertNotIn('source_cache_dir', public_config)

    def test_sync_preserves_target_specific_worktree_environment_setup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'agents'
            target = root / 'target'
            skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
            source_skill = source / '.agents' / 'skills' / 'worktree-environment-setup'
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
            source_skill = source / '.agents' / 'skills' / 'change-set-verification'
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
            source_skill = source / '.agents' / 'skills' / 'change-set-verification'
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
            (source / '.agents' / 'rules').mkdir(parents=True)
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

    def test_entry_docs_route_project_asset_details_to_placeholders(self):
        readme = (REPO_ROOT / 'README.md').read_text(encoding='utf-8')
        if 'Shared agent configuration for projects that use `.agents/` rules' not in readme:
            self.skipTest('target repositories replace public placeholders with local project facts')
        update_skill = (REPO_SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        project_rule = (REPO_ROOT / '.agents' / 'rules' / '20-project-tools.md').read_text(encoding='utf-8')
        project_skill = (
            REPO_ROOT
            / '.agents'
            / 'skills'
            / 'worktree-environment-setup'
            / 'SKILL.md'
        ).read_text(encoding='utf-8')

        self.assertNotIn('Local Project Rule Authoring Guide', readme)
        self.assertNotIn('Local Project Skill Authoring Guide', readme)
        self.assertNotIn('## Local Project Assets', update_skill)
        self.assertNotIn('## Local Project Skills', update_skill)
        self.assertIn('## Generation Contract', project_rule)
        self.assertIn('## Generation Contract', project_skill)

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
            (source / '.agents' / 'rules').mkdir(parents=True)
            skill_root.mkdir(parents=True)
            (source / '.agents' / 'rules' / '10-base-code.md').write_text('rule\n', encoding='utf-8')
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
            shutil.copytree(REPO_ROOT / '.agents', source / '.agents')
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
            rules_root.mkdir(parents=True)
            cursor_root.mkdir(parents=True)
            github_root.mkdir(parents=True)
            (target / 'AGENTS.md').write_text(
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
            public_config = {'rules': [], 'agent_prompts': []}

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


if __name__ == '__main__':
    unittest.main()
