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
    load_project_config,
    parse_asset,
    safe_relative,
)


class SetupCatalogTest(unittest.TestCase):
    def test_catalog_parses_only_safe_unique_structured_retired_fields(self):
        def load_with(retired_fields):
            root = Path(self.temp_dir)
            (root / 'setup-assets/catalog').mkdir(parents=True, exist_ok=True)
            (root / 'VERSION').write_text('1.0.0\n', encoding='utf-8')
            (root / 'setup-assets/catalog/assets.json').write_text(
                json.dumps({
                    'plugin': {
                        'id': 'smartkit',
                        'version': '1.0.0',
                        'repository': 'https://example.invalid/agents.git',
                        'ref': 'master',
                    },
                    'assets': [],
                    'retired_fields': retired_fields,
                }),
                encoding='utf-8',
            )
            return load_catalog(root)

        with tempfile.TemporaryDirectory() as self.temp_dir:
            catalog = load_with([{
                'path': '.github/copilot/settings.json',
                'key': 'enabledPlugins.superpowers@superpowers-marketplace',
            }])
            self.assertEqual(
                catalog.retired_fields[0].path.as_posix(),
                '.github/copilot/settings.json',
            )
            self.assertEqual(
                catalog.retired_fields[0].key,
                'enabledPlugins.superpowers@superpowers-marketplace',
            )

        invalid = (
            [{'path': '/absolute.json', 'key': 'value'}],
            [{'path': '../escape.json', 'key': 'value'}],
            [{'path': 'settings.json', 'key': ''}],
            [{'path': 'settings.json', 'key': 'bad..key'}],
            [{'path': 'settings.txt', 'key': 'value'}],
            [{'path': 'settings.json', 'key': 'value', 'extra': True}],
            [
                {'path': 'settings.json', 'key': 'value'},
                {'path': 'settings.json', 'key': 'value'},
            ],
        )
        for retired_fields in invalid:
            with self.subTest(retired_fields=retired_fields), tempfile.TemporaryDirectory() as temp_dir:
                self.temp_dir = temp_dir
                with self.assertRaises(ContractError):
                    load_with(retired_fields)

    def test_catalog_excludes_setup_control_plane(self):
        catalog = load_catalog(REPO_ROOT)

        targets = {
            asset.target.as_posix()
            for asset in catalog.assets
            if asset.target is not None
        }

        self.assertNotIn('.agents/skills/setup-project-agents', targets)
        matt_blueprints = {
            'skills/setup-matt-pocock-skills/issue-tracker-github.md',
            'skills/setup-matt-pocock-skills/triage-labels.md',
            'skills/setup-matt-pocock-skills/domain.md',
        }
        for asset in catalog.assets:
            with self.subTest(asset=asset.id):
                if asset.id == 'setup-project-agents':
                    self.assertEqual(asset.source.as_posix(), 'skills/setup-project-agents')
                elif asset.source.as_posix() in matt_blueprints:
                    self.assertEqual(asset.kind, 'blueprint')
                    self.assertTrue(asset.target.as_posix().startswith('docs/agents/'))
                elif asset.kind in {'rule', 'skill', 'agent', 'blueprint', 'template', 'wrapper'}:
                    self.assertTrue(asset.source.as_posix().startswith('setup-assets/'))

        self.assertEqual(
            {
                asset.source.as_posix()
                for asset in catalog.assets
                if asset.source.as_posix().startswith('skills/setup-matt-pocock-skills/')
            },
            matt_blueprints,
        )

    def test_project_config_loads_current_project_selections(self):
        config = load_project_config(None, catalog=load_catalog(REPO_ROOT))

        self.assertEqual(config.selected_rules, ())
        self.assertEqual(config.selected_skills, ())
        self.assertNotIn('setup-project-agents', config.selected_skills)
        self.assertEqual(config.selected_agents, ('change-set-verifier',))
        self.assertEqual(config.external_skills, ())

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
            (root / 'setup-assets' / 'catalog').mkdir(parents=True)
            (root / 'setup-assets' / 'catalog' / 'assets.json').write_text(
                json.dumps(
                    {
                        'plugin': {
                            'id': 'smartkit',
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

            config_path.write_text(
                json.dumps({'version': 1, 'platforms': ['codex']}), encoding='utf-8'
            )
            with self.assertRaisesRegex(ContractError, 'unknown project config fields'):
                load_project_config(config_path, catalog=catalog)

            config_path.write_text(
                json.dumps({'version': 1, 'hooks_enabled': True}), encoding='utf-8'
            )
            with self.assertRaisesRegex(ContractError, 'unknown project config fields'):
                load_project_config(config_path, catalog=catalog)

    def test_catalog_uses_semver_2_for_version_and_plugin_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / 'setup-assets' / 'catalog').mkdir(parents=True)
            catalog_path = root / 'setup-assets' / 'catalog' / 'assets.json'

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
                                    'id': 'smartkit',
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
                                    'id': 'smartkit',
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

    def test_project_external_skills_are_current_contracts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'config.json'
            path.write_text(
                json.dumps(
                    {
                        '$schema': 'project-config.schema.json',
                        'version': 1,
                        'skills': {
                            'external_sources': [
                                {
                                    'id': 'getsentry/plugin-codex',
                                    'url': 'https://github.com/getsentry/plugin-codex',
                                    'ref': 'main',
                                    'license': {'spdx': 'MIT', 'path': 'LICENSE'},
                                    'skills': [{
                                        'id': 'getsentry/sentry-debug-issue',
                                        'path': 'plugins/sentry/skills/sentry-debug-issue',
                                    }],
                                }
                            ]
                        },
                    }
                ),
                encoding='utf-8',
            )
            config = load_project_config(path, catalog=load_catalog(REPO_ROOT))
            external = {item.name: item for item in config.external_skills}
            self.assertEqual(set(external), {'sentry-debug-issue'})
            self.assertEqual(
                external['sentry-debug-issue'].path.as_posix(),
                'plugins/sentry/skills/sentry-debug-issue',
            )
            path.write_text(
                json.dumps(
                    {
                        'version': 1,
                        'skills': {
                            'external_sources': [
                                {
                                    'id': 'bad/repo',
                                    'url': 'https://example.invalid/repo.git',
                                    'ref': 'main',
                                    'license': {'spdx': 'MIT', 'path': 'LICENSE'},
                                    'skills': [{'id': 'bad/skill', 'path': 'skill'}],
                                }
                            ]
                        },
                    }
                ),
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ContractError, 'GitHub url'):
                load_project_config(path, catalog=load_catalog(REPO_ROOT))

    def test_project_config_rejects_duplicate_external_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'config.json'
            path.write_text(
                json.dumps(
                    {
                        'version': 1,
                        'skills': {
                            'external_sources': [
                                {
                                    'id': 'example/debug-mode',
                                    'url': 'https://github.com/example/debug-mode',
                                    'ref': 'main',
                                    'license': {'spdx': 'MIT', 'path': 'LICENSE'},
                                    'skills': [{'id': 'example/debug-mode', 'path': 'debug-mode'}],
                                },
                                {
                                    'id': 'other/debug-mode',
                                    'url': 'https://github.com/other/debug-mode',
                                    'license': {'spdx': 'MIT', 'path': 'LICENSE'},
                                    'skills': [{'id': 'other/debug-mode', 'path': 'debug-mode'}],
                                },
                            ]
                        },
                    }
                ),
                encoding='utf-8',
            )

            with self.assertRaisesRegex(ContractError, 'duplicate names'):
                load_project_config(path, catalog=load_catalog(REPO_ROOT))


if __name__ == '__main__':
    unittest.main()
