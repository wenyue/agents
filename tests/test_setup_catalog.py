import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup.catalog import (  # noqa: E402
    ContractError,
    load_catalog,
    load_lock,
    load_project_config,
    parse_asset,
    safe_relative,
)
from agents_setup.models import Platform  # noqa: E402


class SetupCatalogTest(unittest.TestCase):
    def test_catalog_excludes_setup_control_plane(self):
        catalog = load_catalog(REPO_ROOT)

        targets = {
            asset.target.as_posix()
            for asset in catalog.assets
            if asset.target is not None
        }

        self.assertNotIn('.agents/skills/setup-project-agents', targets)
        self.assertIn('.agents/skills/manage-agent-tools', targets)

    def test_project_config_defaults_to_all_hosts_and_hooks_off(self):
        config = load_project_config(None, catalog=load_catalog(REPO_ROOT))

        self.assertEqual(config.platforms, tuple(Platform))
        self.assertFalse(config.hooks_enabled)
        self.assertIn('00-global-rule-config', config.selected_rules)
        self.assertIn('manage-agent-tools', config.selected_skills)
        self.assertNotIn('setup-project-agents', config.selected_skills)
        self.assertEqual(config.selected_agents, ('change-set-verifier',))

    def test_catalog_rejects_escape_and_absolute_targets(self):
        for target in ('../escape', '/tmp/escape', 'C:/escape'):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ContractError, 'relative path'):
                    parse_asset(
                        {
                            'id': 'bad',
                            'kind': 'file',
                            'source': 'README.md',
                            'target': target,
                        }
                    )

    def test_asset_parser_rejects_unknown_fields_and_control_plane_target(self):
        with self.assertRaisesRegex(ContractError, 'unknown asset fields'):
            parse_asset(
                {
                    'id': 'bad',
                    'kind': 'file',
                    'source': 'README.md',
                    'target': 'README.md',
                    'extra': True,
                }
            )

    def test_asset_metadata_is_strictly_typed_and_available_to_renderers(self):
        parsed = parse_asset(
            {
                'id': 'rule',
                'kind': 'rule',
                'source': 'rules/rule.md',
                'target': '.agents/rules/rule.md',
                'metadata': {
                    'section': 'global',
                    'read_when': 'Always',
                    'strength': 'Mandatory',
                    'cursor': {
                        'description': 'A rule',
                        'globs': '**',
                        'alwaysApply': True,
                    },
                    'github': {'applyTo': '**'},
                },
            }
        )
        self.assertEqual(parsed.metadata['section'], 'global')
        self.assertEqual(parsed.metadata['cursor']['alwaysApply'], True)

        for metadata, message in (
            ([], 'metadata must be an object'),
            ({'unknown': True}, 'unknown rule metadata fields'),
            ({
                'section': 'global', 'read_when': 'Always', 'strength': 'Mandatory',
                'cursor': {'description': 'A rule', 'alwaysApply': 'yes'},
                'github': {'applyTo': '**'},
            }, 'alwaysApply must be a boolean'),
        ):
            with self.subTest(metadata=metadata):
                with self.assertRaisesRegex(ContractError, message):
                    parse_asset(
                        {
                            'id': 'rule',
                            'kind': 'rule',
                            'source': 'rules/rule.md',
                            'target': '.agents/rules/rule.md',
                            'metadata': metadata,
                        }
                    )

    def test_rule_agent_and_project_rule_blueprint_metadata_are_complete(self):
        rule_metadata = {
            'section': 'global',
            'read_when': 'Always',
            'strength': 'Mandatory',
            'cursor': {'description': 'A rule', 'alwaysApply': True},
            'github': {'applyTo': '**'},
        }
        rule = {
            'id': 'rule',
            'kind': 'rule',
            'source': 'rules/rule.md',
            'target': '.agents/rules/rule.md',
            'metadata': rule_metadata,
        }
        for field in ('section', 'read_when', 'strength', 'cursor', 'github'):
            with self.subTest(rule_field=field):
                candidate = dict(rule)
                candidate['metadata'] = dict(rule_metadata)
                del candidate['metadata'][field]
                with self.assertRaises(ContractError):
                    parse_asset(candidate)
        for parent, field in (('cursor', 'description'), ('cursor', 'alwaysApply'), ('github', 'applyTo')):
            with self.subTest(parent=parent, field=field):
                candidate = dict(rule)
                candidate['metadata'] = {**rule_metadata, parent: dict(rule_metadata[parent])}
                del candidate['metadata'][parent][field]
                with self.assertRaises(ContractError):
                    parse_asset(candidate)
        for key, value in (('section', 'unknown'), ('strength', 'Required')):
            with self.subTest(key=key):
                candidate = dict(rule)
                candidate['metadata'] = {**rule_metadata, key: value}
                with self.assertRaises(ContractError):
                    parse_asset(candidate)

        agent_metadata = {
            'description': 'An agent',
            'codex': {'sandbox_mode': 'workspace-write'},
            'cursor': {'readonly': False},
        }
        agent = {
            'id': 'agent', 'kind': 'agent', 'source': 'agents/agent.md',
            'target': '.agents/agents/agent.md', 'metadata': agent_metadata,
        }
        for field in ('description', 'codex', 'cursor'):
            with self.subTest(agent_field=field):
                candidate = dict(agent)
                candidate['metadata'] = dict(agent_metadata)
                del candidate['metadata'][field]
                with self.assertRaises(ContractError):
                    parse_asset(candidate)
        for parent, field in (('codex', 'sandbox_mode'), ('cursor', 'readonly')):
            with self.subTest(parent=parent, field=field):
                candidate = dict(agent)
                candidate['metadata'] = {**agent_metadata, parent: dict(agent_metadata[parent])}
                del candidate['metadata'][parent][field]
                with self.assertRaises(ContractError):
                    parse_asset(candidate)

        blueprint = {
            'id': 'project-rule', 'kind': 'blueprint', 'source': 'blueprints/rule.md',
            'target': '.agents/rules/project.md', 'mode': 'generate',
            'metadata': {
                'section': 'project', 'read_when': 'Project work', 'strength': 'Default',
                'cursor': {'alwaysApply': True}, 'github': {'applyTo': '**'},
            },
        }
        self.assertEqual(parse_asset(blueprint).metadata['section'], 'project')
        blueprint['metadata']['section'] = 'base'
        with self.assertRaises(ContractError):
            parse_asset(blueprint)
        with self.assertRaises(ContractError):
            parse_asset({
                'id': 'skill-blueprint', 'kind': 'blueprint', 'source': 'blueprints/skill.md',
                'target': '.agents/skills/skill/SKILL.md', 'mode': 'generate',
                'metadata': {'section': 'project'},
            })

        with self.assertRaisesRegex(ContractError, 'control-plane'):
            parse_asset(
                {
                    'id': 'setup-project-agents',
                    'kind': 'skill',
                    'source': 'skills/setup-project-agents',
                    'target': '.agents/skills/setup-project-agents',
                    'control_plane': True,
                }
            )

    def test_catalog_and_config_reject_unknown_top_level_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / 'VERSION').write_text('0.1.0\n', encoding='utf-8')
            (root / 'catalog').mkdir()
            (root / 'catalog' / 'project-assets.json').write_text(
                json.dumps(
                    {
                        'plugin': {
                            'id': 'agents',
                            'version': '0.1.0',
                            'repository': 'https://github.com/wenyue/agents.git',
                            'ref': 'main',
                        },
                        'assets': [],
                        'unexpected': True,
                    }
                ),
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ContractError, 'unknown catalog fields'):
                load_catalog(root)

            catalog = load_catalog(REPO_ROOT)
            config_path = root / 'config.json'
            config_path.write_text(
                json.dumps({'version': 1, 'unknown': True}), encoding='utf-8'
            )
            with self.assertRaisesRegex(ContractError, 'unknown project config fields'):
                load_project_config(config_path, catalog=catalog)

    def test_catalog_uses_semver_2_for_version_and_plugin_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / 'catalog').mkdir()
            catalog_path = root / 'catalog' / 'project-assets.json'

            for version in (
                '1.0.0',
                '1.0.0-alpha.1',
                '1.0.0-rc.1+build.7',
            ):
                with self.subTest(valid=version):
                    (root / 'VERSION').write_text(f'{version}\n', encoding='utf-8')
                    catalog_path.write_text(
                        json.dumps(
                            {
                                'plugin': {
                                    'id': 'agents',
                                    'version': version,
                                    'repository': 'https://example.invalid/agents.git',
                                    'ref': 'main',
                                },
                                'assets': [],
                            }
                        ),
                        encoding='utf-8',
                    )
                    self.assertEqual(load_catalog(root).plugin_version, version)

            for version in (
                '01.0.0',
                '1.01.0',
                '1.0.01',
                '1.0.0-alpha..1',
                '1١.0.0',
                '1.0.0-1١',
            ):
                with self.subTest(invalid=version):
                    (root / 'VERSION').write_text(f'{version}\n', encoding='utf-8')
                    catalog_path.write_text(
                        json.dumps(
                            {
                                'plugin': {
                                    'id': 'agents',
                                    'version': version,
                                    'repository': 'https://example.invalid/agents.git',
                                    'ref': 'main',
                                },
                                'assets': [],
                            }
                        ),
                        encoding='utf-8',
                    )
                    with self.assertRaisesRegex(ContractError, 'semantic version'):
                        load_catalog(root)

    def test_safe_relative_rejects_windows_unsafe_segments_and_keeps_wrappers(self):
        for value in (
            'rules/bad\x00name.md',
            'rules/bad\nname.md',
            'rules/bad:name.md',
            'rules/bad?.md',
            'rules/bad*.md',
            'rules/bad".md',
            'rules/bad<name>.md',
            'rules/bad|name.md',
            'rules/trailing .md ',
            'rules/trailing..',
            'rules/CON.md',
            'rules/prn.txt',
            'rules/AUX',
            'rules/NUL.data',
            'rules/COM1.json',
            'rules/lpt9.cfg',
            'rules/COM¹.txt',
            'rules/COM²',
            'rules/COM³.cfg',
            'rules/LPT¹.txt',
            'rules/lpt²',
            'rules/LPT³.md',
        ):
            with self.subTest(value=value):
                with self.assertRaises(ContractError):
                    safe_relative(value, 'path')

        self.assertEqual(
            safe_relative('.codex/agents/{agent-name}.toml', 'path').as_posix(),
            '.codex/agents/{agent-name}.toml',
        )
        self.assertEqual(
            safe_relative('.cursor/rules/{rule-name}.mdc', 'path').as_posix(),
            '.cursor/rules/{rule-name}.mdc',
        )

    def test_lock_validates_commit_and_owned_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'lock.json'
            path.write_text(
                json.dumps(
                    {
                        'version': 1,
                        'managed_files': [],
                        'managed_fields': [],
                    }
                ),
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ContractError, 'requires source_commit'):
                load_lock(path)

            path.write_text(
                json.dumps(
                    {
                        'version': 1,
                        'source_commit': 'not-a-commit',
                        'managed_files': [],
                        'managed_fields': [],
                    }
                ),
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ContractError, '40-character hexadecimal'):
                load_lock(path)

            path.write_text(
                json.dumps(
                    {
                        'version': 1,
                        'source_commit': 'a' * 40,
                        'managed_files': [
                            {'path': '../escape', 'sha256': 'b' * 64}
                        ],
                        'managed_fields': [],
                    }
                ),
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ContractError, 'relative path'):
                load_lock(path)


if __name__ == '__main__':
    unittest.main()
