"""Golden contracts for harness-native setup-project-agent rendering."""
from __future__ import annotations

import json
import hashlib
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path, PurePosixPath
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

try:
    import tomllib
except ModuleNotFoundError:
    from _vendor import tomli as tomllib

from agents_setup.catalog import load_catalog, load_project_config  # noqa: E402
from agents_setup.models import (  # noqa: E402
    AssetSpec,
    Catalog,
    ChangeKind,
    OperatingSystem,
    Harness,
    ProjectConfig,
)
from agents_setup.planner import build_plan  # noqa: E402
from agents_setup.ownership import (  # noqa: E402
    OwnershipError,
    _actual_tree_digest,
    reconcile_ownership,
)
from agents_setup.project import inspect_project  # noqa: E402
from agents_setup.renderer import (  # noqa: E402
    RenderError,
    _copy_asset,
    _safe_leaves,
    render_desired_state,
)
from agents_setup.validation import validate_rendered_state  # noqa: E402


class SetupRendererTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_catalog(REPO_ROOT)

    def config(self) -> ProjectConfig:
        return ProjectConfig(
            (),
            (),
        )

    def generated_tree(self, root: Path) -> Path:
        generated = root / 'generated'
        rule = generated / '.agents/rules/00-project-tools.md'
        rule.parent.mkdir(parents=True, exist_ok=True)
        rule.write_text('# generated tooling rule\n', encoding='utf-8')
        skill = generated / '.agents/skills/change-set-verification/SKILL.md'
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text('# generated verification skill\n', encoding='utf-8')
        return generated

    def render(self, target: Path, generated: Path):
        return render_desired_state(
            REPO_ROOT,
            target,
            self.catalog,
            self.config(),
            generated,
        )

    def mcp_config(self, target: Path, servers: list[dict]) -> ProjectConfig:
        path = target / '.agents/config.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        document = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        document['mcp'] = servers
        path.write_text(
            json.dumps(document),
            encoding='utf-8',
        )
        return load_project_config(path, catalog=self.catalog)

    def project_agent_config(self, target: Path) -> ProjectConfig:
        source = target / '.agents/agents/l10n.md'
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('# L10n\n\nUse the project localization workflow.\n', encoding='utf-8')
        path = target / '.agents/config.json'
        path.write_text(json.dumps({
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
        return load_project_config(path, catalog=self.catalog)

    def render_with_config(
        self,
        target: Path,
        generated: Path,
        config: ProjectConfig,
        operating_system: OperatingSystem | None = None,
    ):
        return render_desired_state(
            REPO_ROOT,
            target,
            self.catalog,
            config,
            generated,
            operating_system=operating_system,
        )

    def test_project_mcp_renders_three_native_adapters_and_ownership_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config = self.mcp_config(target, [
                {
                    'id': 'sentry',
                    'url': 'https://mcp.sentry.dev/mcp',
                },
                {
                    'id': 'inspector',
                    'command': 'cache/inspector.exe',
                    'args': ['--port', '8181', '--flag', '--flag'],
                    'cwd': 'cache',
                    'env': ['INSPECTOR_TOKEN'],
                    'readiness': {
                        'harnesses': ['codex'],
                        'operatingSystems': ['windows'],
                        'checks': [],
                    },
                    'overrides': [
                        {
                            'when': {'operatingSystems': ['windows']},
                            'set': {
                                'command': '${workspaceFolder}/cache/inspector.exe',
                            },
                        },
                        {
                            'when': {'harnesses': ['codex']},
                            'set': {'command': 'cache/inspector.exe'},
                        },
                    ],
                },
            ])

            generated = self.generated_tree(root)
            rendered = self.render_with_config(
                target, generated, config, OperatingSystem.WINDOWS
            )
            codex = tomllib.loads(rendered.files_by_path['.codex/config.toml'].decode())
            cursor = json.loads(rendered.files_by_path['.cursor/mcp.json'])
            copilot = json.loads(rendered.files_by_path['.vscode/mcp.json'])
            lock = json.loads(rendered.files_by_path['.agents/smartkit.lock.json'])

            self.assertEqual(
                codex['mcp_servers']['sentry'],
                {'url': 'https://mcp.sentry.dev/mcp'},
            )
            self.assertEqual(
                cursor['mcpServers']['inspector']['command'],
                '${workspaceFolder}/cache/inspector.exe',
            )
            self.assertEqual(
                cursor['mcpServers']['inspector']['env'],
                {'INSPECTOR_TOKEN': '${env:INSPECTOR_TOKEN}'},
            )
            self.assertEqual(cursor['mcpServers']['inspector']['cwd'], 'cache')
            self.assertEqual(
                cursor['mcpServers']['inspector']['args'],
                ['--port', '8181', '--flag', '--flag'],
            )
            self.assertEqual(
                codex['mcp_servers']['inspector']['env_vars'],
                ['INSPECTOR_TOKEN'],
            )
            self.assertEqual(codex['mcp_servers']['inspector']['cwd'], 'cache')
            self.assertEqual(
                codex['mcp_servers']['inspector']['command'],
                'cache/inspector.exe',
            )
            self.assertNotIn('type', codex['mcp_servers']['inspector'])
            self.assertEqual(copilot['servers']['inspector']['type'], 'stdio')
            self.assertEqual(
                copilot['servers']['inspector']['env'],
                {'INSPECTOR_TOKEN': '${env:INSPECTOR_TOKEN}'},
            )
            self.assertEqual(
                copilot['servers']['inspector']['command'],
                '${workspaceFolder}/cache/inspector.exe',
            )
            linux_rendered = self.render_with_config(
                target, generated, config, OperatingSystem.LINUX
            )
            linux_cursor = json.loads(linux_rendered.files_by_path['.cursor/mcp.json'])
            self.assertEqual(
                linux_cursor['mcpServers']['inspector']['command'],
                'cache/inspector.exe',
            )
            mcp_assets = [asset for asset in lock['assets'] if asset['role'] == 'mcp']
            for path, prefix in (
                ('.codex/config.toml', 'mcp_servers'),
                ('.cursor/mcp.json', 'mcpServers'),
                ('.vscode/mcp.json', 'servers'),
            ):
                self.assertTrue(any(
                    asset['path'] == path and asset['key'].startswith(f'{prefix}.sentry.')
                    for asset in mcp_assets
                ))
                self.assertTrue(any(
                    asset['path'] == path and asset['key'].startswith(f'{prefix}.inspector.')
                    for asset in mcp_assets
                ))

    def test_project_mcp_adopts_equal_entry_but_rejects_unmanaged_conflict(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            cursor = target / '.cursor/mcp.json'
            cursor.parent.mkdir(parents=True)
            cursor.write_text(json.dumps({
                'mcpServers': {
                    'sentry': {'url': 'https://mcp.sentry.dev/mcp'},
                    'user-owned': {'type': 'http', 'url': 'https://example.invalid/mcp'},
                }
            }), encoding='utf-8')
            config = self.mcp_config(target, [{
                'id': 'sentry',
                'url': 'https://mcp.sentry.dev/mcp', 'harnesses': ['cursor'],
            }])

            rendered = self.render_with_config(target, self.generated_tree(root), config)
            desired = json.loads(rendered.files_by_path['.cursor/mcp.json'])
            self.assertIn('user-owned', desired['mcpServers'])

            self.materialize(target, rendered.files)
            converged = self.render_with_config(
                target, self.generated_tree(root), config
            )
            self.assertEqual(
                converged.files_by_path['.cursor/mcp.json'],
                rendered.files_by_path['.cursor/mcp.json'],
            )

            (target / '.agents/smartkit.lock.json').unlink()
            cursor.write_text(json.dumps({
                'mcpServers': {
                    'sentry': {'type': 'http', 'url': 'https://other.invalid/mcp'},
                }
            }), encoding='utf-8')
            with self.assertRaisesRegex(RenderError, 'conflicts with user configuration'):
                self.render_with_config(target, self.generated_tree(root), config)

    def test_removed_project_mcp_deletes_only_lock_owned_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            cursor = target / '.cursor/mcp.json'
            cursor.parent.mkdir(parents=True)
            cursor.write_text(json.dumps({'mcpServers': {
                'keep': {'type': 'http', 'url': 'https://keep.invalid/mcp'},
            }}), encoding='utf-8')
            owned = self.mcp_config(target, [{
                'id': 'retired', 'url': 'https://retired.invalid/mcp',
                'harnesses': ['cursor'],
            }])
            first = self.render_with_config(target, self.generated_tree(root), owned)
            self.materialize(target, first.files)

            rendered = self.render(target, self.generated_tree(root))
            desired = json.loads(rendered.files_by_path['.cursor/mcp.json'])

            self.assertEqual(set(desired['mcpServers']), {'keep'})

    def test_owned_stdio_mcp_can_move_harnesses_without_touching_user_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            cursor = target / '.cursor/mcp.json'
            cursor.parent.mkdir(parents=True)
            cursor.write_text(json.dumps({'mcpServers': {
                'user-owned': {
                    'type': 'stdio', 'command': 'keep-me', 'args': [],
                },
            }}), encoding='utf-8')
            old = self.mcp_config(target, [{
                'id': 'inspector', 'harnesses': ['cursor'], 'command': 'old-inspector',
            }])
            self.materialize(
                target,
                self.render_with_config(target, self.generated_tree(root), old).files,
            )
            config = self.mcp_config(target, [{
                'id': 'inspector',
                'harnesses': ['codex'], 'command': 'new-inspector',
            }])

            rendered = self.render_with_config(target, self.generated_tree(root), config)
            desired_cursor = json.loads(rendered.files_by_path['.cursor/mcp.json'])
            desired_codex = tomllib.loads(
                rendered.files_by_path['.codex/config.toml'].decode()
            )

            self.assertEqual(set(desired_cursor['mcpServers']), {'user-owned'})
            self.assertEqual(
                desired_codex['mcp_servers']['inspector'],
                {'command': 'new-inspector', 'args': []},
            )

    def test_owned_mcp_entry_can_update_on_the_same_harness(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            old = self.mcp_config(target, [{
                'id': 'sentry',
                'url': 'https://old.invalid/mcp',
                'harnesses': ['cursor'],
            }])
            self.materialize(
                target,
                self.render_with_config(target, self.generated_tree(root), old).files,
            )
            new = self.mcp_config(target, [{
                'id': 'sentry',
                'url': 'https://new.invalid/mcp',
                'harnesses': ['cursor'],
            }])

            rendered = self.render_with_config(target, self.generated_tree(root), new)

            desired = json.loads(rendered.files_by_path['.cursor/mcp.json'])
            self.assertEqual(
                desired['mcpServers']['sentry']['url'],
                'https://new.invalid/mcp',
            )

    def test_first_adoption_of_mcp_preserves_extra_user_entry_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            cursor = target / '.cursor/mcp.json'
            cursor.parent.mkdir(parents=True)
            cursor.write_text(json.dumps({'mcpServers': {
                'sentry': {
                    'type': 'http',
                    'url': 'https://mcp.sentry.dev/mcp',
                    'user-note': 'keep',
                },
            }}), encoding='utf-8')
            config = self.mcp_config(target, [{
                'id': 'sentry',
                'url': 'https://mcp.sentry.dev/mcp',
                'harnesses': ['cursor'],
            }])

            rendered = self.render_with_config(target, self.generated_tree(root), config)

            desired = json.loads(rendered.files_by_path['.cursor/mcp.json'])
            self.assertEqual(
                desired['mcpServers']['sentry'],
                {
                    'type': 'http',
                    'url': 'https://mcp.sentry.dev/mcp',
                    'user-note': 'keep',
                },
            )

    def test_project_snapshot_excludes_plugin_owned_hooks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rendered = self.render(root / 'target', self.generated_tree(root))

            self.assertNotIn('.codex/hooks.json', rendered.files_by_path)
            self.assertNotIn('.cursor/hooks.json', rendered.files_by_path)
            self.assertNotIn(
                '.github/hooks/project-agent-tool-check.json', rendered.files_by_path
            )
            self.assertNotIn(
                ('.codex/config.toml', 'features.hooks'), rendered.fields_by_key
            )
            self.assertNotIn(
                ('.github/copilot/settings.json', 'disableAllHooks'), rendered.fields_by_key
            )
            self.assertNotIn(
                '.agents/skills/refactor-code/SKILL.md', rendered.files_by_path
            )
            self.assertNotIn(
                '.agents/skills/setup-project-agents/SKILL.md', rendered.files_by_path
            )

            self.assertFalse(any(path.startswith('.cursor/rules/') for path in rendered.files_by_path))
            self.assertFalse(any(path.startswith('.github/instructions/') for path in rendered.files_by_path))
            validate_rendered_state(rendered)

    def test_rendered_project_config_includes_schema_and_round_trips(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            rendered = self.render(target, self.generated_tree(root))
            self.materialize(target, rendered.files)

            loaded = load_project_config(target / '.agents/config.json', catalog=self.catalog)

            rendered_config = json.loads(
                rendered.files_by_path['.agents/config.json'].decode()
            )
            self.assertEqual(
                rendered_config['$schema'],
                'https://raw.githubusercontent.com/wenyue/agents/master/'
                'setup-assets/catalog/project-config.schema.json',
            )
            self.assertEqual(
                {
                    key
                    for path, key in rendered.fields_by_key
                    if path == '.agents/config.json'
                },
                {'$schema'},
            )

    def test_owned_template_field_can_update_at_the_same_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            generated = self.generated_tree(root)
            first = self.render(target, generated)
            self.materialize(target, first.files)
            source = root / 'source'
            shutil.copytree(REPO_ROOT / 'setup-assets', source / 'setup-assets')
            plugin_agent = source / 'agents/codex/change-set-verifier.toml'
            plugin_agent.parent.mkdir(parents=True)
            shutil.copy2(
                REPO_ROOT / 'agents/codex/change-set-verifier.toml', plugin_agent,
            )
            template = source / 'setup-assets/templates/harness-config/agents.config.json'
            document = json.loads(template.read_text(encoding='utf-8'))
            document['$schema'] = 'https://example.invalid/project-config.schema.json'
            template.write_text(json.dumps(document), encoding='utf-8')

            rendered = render_desired_state(
                source,
                target,
                self.catalog,
                self.config(),
                generated,
            )

            updated = json.loads(rendered.files_by_path['.agents/config.json'])
            self.assertEqual(
                updated['$schema'],
                'https://example.invalid/project-config.schema.json',
            )

    def test_project_defaults_have_no_external_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'target'

            project = inspect_project(target, catalog=self.catalog)

            self.assertEqual(
                project.config.external_sources,
                (),
            )

    def test_setup_snapshots_project_external_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps(
                    {
                        'skills': [{
                            'source': 'example/local-check',
                            'ref': 'main',
                            'include': ['skills/local-check'],
                        }],
                    }
                ),
                encoding='utf-8',
            )
            project = inspect_project(target, catalog=self.catalog)
            self.assertEqual(
                [item.name for item in project.config.external_skills],
                ['local-check'],
            )
            external_root = root / 'external'
            for name in ('local-check',):
                skill = external_root / name / 'SKILL.md'
                skill.parent.mkdir(parents=True)
                skill.write_text(
                    f'---\nname: {name}\ndescription: Use for tests.\n---\n',
                    encoding='utf-8',
                )
            (external_root / 'sources.json').write_text(
                json.dumps({'sources': [{
                    'id': 'example/local-check',
                    'url': 'https://github.com/example/local-check',
                    'requested_ref': 'main',
                    'resolved_ref': 'main',
                    'ref_kind': 'branch',
                    'commit': 'a' * 40,
                    'license': {'spdx': 'MIT', 'path': 'LICENSE', 'sha256': 'b' * 64},
                    'skills': [{
                        'id': 'example/local-check',
                        'path': 'skills/local-check',
                        'files': {
                            'SKILL.md': hashlib.sha256(
                                (external_root / 'local-check/SKILL.md').read_bytes()
                            ).hexdigest(),
                        },
                    }],
                }]}) + '\n', encoding='utf-8'
            )

            rendered = render_desired_state(
                REPO_ROOT,
                target,
                self.catalog,
                project.config,
                self.generated_tree(root),
                external_root,
            )
            rendered_config = json.loads(
                rendered.files_by_path['.agents/config.json']
            )

            self.assertEqual(
                rendered_config['skills'],
                [{
                    'source': 'example/local-check',
                    'ref': 'main',
                    'include': ['skills/local-check'],
                }],
            )
            self.assertIn(
                '.agents/skills/local-check/SKILL.md',
                rendered.files_by_path,
            )
            self.assertIn(
                PurePosixPath('.agents/skills/local-check'),
                rendered.replace_roots,
            )

    def test_removed_external_source_is_deleted_not_rediscovered_as_project_owned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            project_owned = target / '.agents/skills/project-owned'
            project_owned.mkdir(parents=True)
            (project_owned / 'SKILL.md').write_text(
                '---\nname: project-owned\ndescription: Keep.\n---\n',
                encoding='utf-8',
            )
            external_root = root / 'external'
            external = external_root / 'retired-external'
            external.mkdir(parents=True)
            (external / 'SKILL.md').write_text(
                '---\nname: retired-external\ndescription: Retired.\n---\n', encoding='utf-8'
            )
            (external_root / 'sources.json').write_text(json.dumps({
                'sources': [{
                    'id': 'example/repository', 'url': 'https://github.com/example/repository',
                    'requested_ref': None, 'resolved_ref': 'main', 'ref_kind': 'branch',
                    'commit': 'a' * 40,
                    'license': {'spdx': 'MIT', 'path': 'LICENSE', 'sha256': 'b' * 64},
                    'skills': [{
                        'id': 'example/retired-external',
                        'path': 'skills/retired-external',
                        'files': {
                            'SKILL.md': hashlib.sha256(
                                (external / 'SKILL.md').read_bytes()
                            ).hexdigest(),
                        },
                    }],
                }],
            }), encoding='utf-8')
            config_path = target / '.agents/config.json'
            config_path.write_text(json.dumps({
                'skills': [{
                    'source': 'example/repository',
                    'include': ['skills/retired-external'],
                }],
            }), encoding='utf-8')
            first_config = load_project_config(config_path, catalog=self.catalog)
            first = render_desired_state(
                REPO_ROOT, target, self.catalog, first_config,
                self.generated_tree(root), external_root,
            )
            self.materialize(target, first.files)

            rendered = self.render(target, self.generated_tree(root))

            self.assertIn(
                PurePosixPath('.agents/skills/retired-external'),
                rendered.delete_paths,
            )
            self.assertIn(
                PurePosixPath('.agents/skills/project-owned/SKILL.md'),
                rendered.preserved_paths,
            )
            self.assertNotIn(
                PurePosixPath('.agents/skills/retired-external/SKILL.md'),
                rendered.preserved_paths,
            )

    def test_modified_installed_external_skill_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            external_root = root / 'external'
            skill = external_root / 'local-check/SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text(
                '---\nname: local-check\ndescription: Use for tests.\n---\n',
                encoding='utf-8',
            )
            (external_root / 'sources.json').write_text(json.dumps({
                'sources': [{
                    'id': 'example/local-check',
                    'url': 'https://github.com/example/local-check',
                    'requested_ref': None,
                    'resolved_ref': 'main',
                    'ref_kind': 'branch',
                    'commit': 'a' * 40,
                    'license': {'spdx': 'MIT', 'path': 'LICENSE', 'sha256': 'b' * 64},
                    'skills': [{
                        'id': 'example/local-check',
                        'path': 'skills/local-check',
                        'files': {'SKILL.md': hashlib.sha256(skill.read_bytes()).hexdigest()},
                    }],
                }],
            }), encoding='utf-8')
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({
                'skills': [{
                    'source': 'example/local-check',
                    'include': ['skills/local-check'],
                }],
            }), encoding='utf-8')
            config = load_project_config(config_path, catalog=self.catalog)
            first = render_desired_state(
                REPO_ROOT, target, self.catalog, config,
                self.generated_tree(root), external_root,
            )
            self.materialize(target, first.files)
            installed = target / '.agents/skills/local-check/SKILL.md'
            installed.write_text(installed.read_text() + '\nlocal drift\n', encoding='utf-8')

            with self.assertRaisesRegex(RenderError, 'modified outside setup'):
                render_desired_state(
                    REPO_ROOT, target, self.catalog, config,
                    self.generated_tree(root), external_root,
                )

    def test_managed_blueprint_rule_rename_is_delete_plus_create_not_project_discovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            first = self.render(target, self.generated_tree(root))
            self.materialize(target, first.files)
            old = PurePosixPath('.agents/rules/00-project-tools.md')
            new = PurePosixPath('.agents/rules/05-project-tools.md')
            assets = tuple(
                replace(asset, target=new)
                if asset.target == old else asset
                for asset in self.catalog.assets
            )
            renamed_catalog = replace(self.catalog, assets=assets)
            generated = self.generated_tree(root)
            old_generated = generated / old.as_posix()
            new_generated = generated / new.as_posix()
            new_generated.parent.mkdir(parents=True, exist_ok=True)
            old_generated.rename(new_generated)

            rendered = render_desired_state(
                REPO_ROOT, target, renamed_catalog, ProjectConfig(
                    tuple(asset.id for asset in assets if asset.kind == 'rule' and not asset.control_plane),
                    tuple(asset.id for asset in assets if asset.kind == 'skill' and not asset.control_plane),
                ), generated,
            )

            self.assertIn(old, rendered.delete_paths)
            self.assertIn(new.as_posix(), rendered.files_by_path)
            self.assertNotIn(old.as_posix(), rendered.preserved_paths)

    def test_unsafe_structured_template_field_is_rejected(self):
        with self.assertRaisesRegex(RenderError, 'unsafe template field'):
            tuple(_safe_leaves({'unsafe/key': 'control-plane/path'}))

    def test_existing_toml_inline_tables_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            codex = target / '.codex/config.toml'
            codex.parent.mkdir(parents=True)
            codex.write_text(
                'plugins = [{ name = "x", options = { active = true } }]\n',
                encoding='utf-8',
            )

            rendered = self.render(target, self.generated_tree(root))
            parsed = tomllib.loads(rendered.files_by_path['.codex/config.toml'].decode())

            self.assertEqual(
                parsed['plugins'],
                [{'name': 'x', 'options': {'active': True}}],
            )

    def test_existing_toml_omits_redundant_parent_tables_and_preserves_empty_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            codex = target / '.codex/config.toml'
            codex.parent.mkdir(parents=True)
            codex.write_text(
                '[mcp_servers.sentry]\n'
                'command = "npx"\n'
                '\n'
                '[intentionally_empty]\n',
                encoding='utf-8',
            )

            rendered = self.render(target, self.generated_tree(root))
            content = rendered.files_by_path['.codex/config.toml'].decode()

            self.assertNotIn('[mcp_servers]\n', content)
            self.assertIn('[mcp_servers.sentry]\n', content)
            self.assertIn('[intentionally_empty]\n', content)
            self.assertEqual(
                tomllib.loads(content)['mcp_servers']['sentry']['command'],
                'npx',
            )
            self.assertEqual(tomllib.loads(content)['intentionally_empty'], {})

    def test_dart_project_does_not_receive_project_specific_mcp_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            (target / 'pubspec.yaml').write_text('name: example\n', encoding='utf-8')

            rendered = self.render(target, self.generated_tree(root))
            parsed = tomllib.loads(rendered.files_by_path['.codex/config.toml'].decode())

            self.assertNotIn('mcp_servers', parsed)
            self.assertNotIn('.codex/config.dart-mcp.toml', rendered.files_by_path)

    def test_existing_jsonc_trailing_commas_do_not_change_string_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            settings = target / '.github/copilot/settings.json'
            settings.parent.mkdir(parents=True)
            original = (
                '{\n'
                '  // user-owned values\n'
                '  "unmanaged": "literal,}",\n'
                '  "items": [1, 2,],\n'
                '}\n'
            )
            settings.write_text(original, encoding='utf-8')

            rendered = self.render(target, self.generated_tree(root))

            self.assertNotIn('.github/copilot/settings.json', rendered.files_by_path)
            self.assertNotIn(
                PurePosixPath('.github/copilot/settings.json'),
                rendered.delete_paths,
            )
            self.assertEqual(settings.read_text(encoding='utf-8'), original)

    def test_historical_unowned_structured_fields_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            settings = target / '.github/copilot/settings.json'
            settings.parent.mkdir(parents=True)
            settings.write_text(
                json.dumps({
                    'extraKnownMarketplaces': {
                        'superpowers-marketplace': {'source': 'retired'},
                        'team-marketplace': {'source': 'kept'},
                    },
                    'enabledPlugins': {
                        'superpowers@superpowers-marketplace': True,
                        'team-tool@team-marketplace': True,
                    },
                    'editor': {'theme': 'team'},
                }),
                encoding='utf-8',
            )

            rendered = self.render(target, self.generated_tree(root))
            self.assertNotIn('.github/copilot/settings.json', rendered.files_by_path)
            self.assertNotIn(PurePosixPath('.github/copilot/settings.json'), rendered.delete_paths)

    def test_historical_unowned_structured_file_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            settings = target / '.github/copilot/settings.json'
            settings.parent.mkdir(parents=True)
            settings.write_text(
                json.dumps({
                    'extraKnownMarketplaces': {
                        'superpowers-marketplace': {'source': 'retired'},
                    },
                    'enabledPlugins': {
                        'superpowers@superpowers-marketplace': True,
                    },
                }),
                encoding='utf-8',
            )

            rendered = self.render(target, self.generated_tree(root))

            self.assertNotIn('.github/copilot/settings.json', rendered.files_by_path)
            self.assertNotIn(
                PurePosixPath('.github/copilot/settings.json'),
                rendered.delete_paths,
            )

    def test_transient_skill_cache_files_are_not_rendered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'skill'
            cache = source / '__pycache__'
            cache.mkdir(parents=True)
            (source / 'SKILL.md').write_text('kept\n', encoding='utf-8')
            (source / '.DS_Store').write_bytes(b'transient')
            (cache / 'cached.pyc').write_bytes(b'transient')
            files = {}

            _copy_asset(files, source, PurePosixPath('.agents/skills/example'))

            paths = tuple(path.as_posix() for path in files)
            self.assertEqual(paths, ('.agents/skills/example/SKILL.md',))

    def test_generated_tree_rejects_control_plane_and_undeclared_paths(self):
        rejected_paths = (
            '.agents/skills/setup-project-agents/SKILL.md',
            '.agents/lock.json',
            '.agents/config.json',
            '.agents/rules/undeclared.md',
        )
        for rejected in rejected_paths:
            with self.subTest(path=rejected), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                generated = self.generated_tree(root)
                path = generated.joinpath(*PurePosixPath(rejected).parts)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('must not enter desired state\n', encoding='utf-8')

                with self.assertRaisesRegex(RenderError, 'undeclared generated path'):
                    self.render(root / 'target', generated)

    def test_declared_blueprint_generated_content_overlays_shared_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'source'
            shared_source = source / 'rules/shared.md'
            shared_source.parent.mkdir(parents=True)
            shared_source.write_text('shared\n', encoding='utf-8')
            target_path = PurePosixPath('.agents/rules/shared.md')
            catalog = Catalog(
                'test',
                '1.0.0',
                'https://example.invalid/test.git',
                'main',
                (
                    AssetSpec(
                        'shared',
                        'rule',
                        PurePosixPath('rules/shared.md'),
                        target_path,
                        (Harness.CODEX,),
                    ),
                    AssetSpec(
                        'generated-shared',
                        'blueprint',
                        PurePosixPath('blueprints/shared.md'),
                        target_path,
                        (Harness.CODEX,),
                        'generate',
                    ),
                ),
            )
            generated = root / 'generated/.agents/rules'
            generated.mkdir(parents=True)
            (generated / 'shared.md').write_text('generated\n', encoding='utf-8')
            config = ProjectConfig(
                ('shared',),
                (),
            )

            rendered = render_desired_state(
                source,
                root / 'target',
                catalog,
                config,
                root / 'generated',
            )

            self.assertEqual(
                rendered.files_by_path[target_path.as_posix()],
                (generated / 'shared.md').read_bytes(),
            )

    def test_renderer_uses_catalog_metadata_without_a_legacy_references_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'source'
            shutil.copytree(
                REPO_ROOT,
                source,
                ignore=shutil.ignore_patterns('.git', '.superpowers', '__pycache__', '*.pyc'),
            )
            rendered = render_desired_state(
                source,
                root / 'target',
                load_catalog(source),
                self.config(),
                self.generated_tree(root),
            )

            self.assertIn('AGENTS.md', rendered.files_by_path)

    def test_renderer_rejects_symlinked_target_reads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            real_target = root / 'real-target'
            real_target.mkdir()
            linked_target = root / 'linked-target'
            linked_target.symlink_to(real_target, target_is_directory=True)
            generated = self.generated_tree(root)
            with self.assertRaisesRegex(RenderError, 'symlink'):
                self.render(linked_target, generated)

            outside = root / 'outside.json'
            outside.write_text('{}', encoding='utf-8')
            native = real_target / '.codex/config.toml'
            native.parent.mkdir(parents=True)
            native.symlink_to(outside)
            with self.assertRaisesRegex(RenderError, 'symlink'):
                self.render(real_target, generated)

    def test_removed_project_selection_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps({
                    'selected_rules': ['project-owned-rule'],
                }),
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ValueError, 'selected_rules'):
                load_project_config(config_path, catalog=self.catalog)

    def test_project_config_rejects_retired_version_field(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True)
            config_path.write_text('{"version": 2}\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'unknown project config fields: version'):
                load_project_config(config_path, catalog=self.catalog)

    def test_malformed_ownership_sources_and_seeded_assets_are_rejected(self):
        malformed_values = (
            {'sources': [123], 'seeded': []},
            {'sources': [], 'seeded': ['garbage']},
        )
        for malformed in malformed_values:
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                target = root / 'target'
                manifest = target / '.agents/smartkit.lock.json'
                manifest.parent.mkdir(parents=True)
                manifest.write_text(json.dumps({
                    'sources': malformed['sources'],
                    'assets': [],
                    'seeded': malformed['seeded'],
                }), encoding='utf-8')

                with self.assertRaisesRegex(RenderError, 'ownership manifest'):
                    self.render(target, self.generated_tree(root))

    def test_ownership_manifest_rejects_mismatched_external_skill_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            external_root = root / 'external'
            skill = external_root / 'local-check/SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text(
                '---\nname: local-check\ndescription: Use for tests.\n---\n',
                encoding='utf-8',
            )
            (external_root / 'sources.json').write_text(json.dumps({
                'sources': [{
                    'id': 'example/local-check',
                    'url': 'https://github.com/example/local-check',
                    'requested_ref': None,
                    'resolved_ref': 'main',
                    'ref_kind': 'branch',
                    'commit': 'a' * 40,
                    'license': {'spdx': 'MIT', 'path': 'LICENSE', 'sha256': 'b' * 64},
                    'skills': [{
                        'id': 'example/local-check',
                        'path': 'skills/local-check',
                        'files': {'SKILL.md': hashlib.sha256(skill.read_bytes()).hexdigest()},
                    }],
                }],
            }), encoding='utf-8')
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({
                'skills': [{
                    'source': 'example/local-check',
                    'include': ['skills/local-check'],
                }],
            }), encoding='utf-8')
            config = load_project_config(config_path, catalog=self.catalog)
            first = render_desired_state(
                REPO_ROOT, target, self.catalog, config,
                self.generated_tree(root), external_root,
            )
            self.materialize(target, first.files)
            manifest = target / '.agents/smartkit.lock.json'
            document = json.loads(manifest.read_text(encoding='utf-8'))
            tree = next(asset for asset in document['assets'] if asset['kind'] == 'tree')
            tree['source_path'] = 'skills/other'
            manifest.write_text(json.dumps(document), encoding='utf-8')

            with self.assertRaisesRegex(RenderError, 'Skill provenance is invalid'):
                render_desired_state(
                    REPO_ROOT, target, self.catalog, config,
                    self.generated_tree(root), external_root,
                )

    def test_managed_tree_rejects_junction_like_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            tree = target / 'owned'
            tree.mkdir()
            (tree / 'file.txt').write_text('content\n', encoding='utf-8')

            with mock.patch.object(
                Path,
                'is_junction',
                create=True,
                new=lambda path: path.name == 'owned',
            ):
                with self.assertRaisesRegex(OwnershipError, 'symlink|managed tree is unsafe'):
                    _actual_tree_digest(target, PurePosixPath('owned'))

    def test_reconciler_rejects_invalid_next_manifest_before_returning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(OwnershipError, 'manifest source'):
                reconcile_ownership(
                    Path(temp_dir),
                    (),
                    (),
                    (),
                    sources=({'secret': 'must-not-be-written'},),
                )

    def test_project_setup_renders_only_codex_plugin_agent_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            rendered = self.render(target, self.generated_tree(root))
            codex_path = '.codex/agents/change-set-verifier.toml'
            self.assertEqual(
                rendered.files_by_path[codex_path],
                (REPO_ROOT / 'agents/codex/change-set-verifier.toml').read_bytes(),
            )
            self.assertNotIn(
                '.cursor/agents/change-set-verifier.md', rendered.files_by_path,
            )
            self.assertNotIn(
                '.github/agents/change-set-verifier.agent.md', rendered.files_by_path,
            )
            lock = json.loads(rendered.files_by_path['.agents/smartkit.lock.json'])
            verifier = next(
                item for item in lock['assets'] if item['path'] == codex_path
            )
            self.assertEqual(verifier['kind'], 'file')
            self.assertEqual(verifier['role'], 'agent')

    def test_codex_plugin_agent_fallback_obeys_file_ownership_lifecycle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated = self.generated_tree(root)
            expected = (
                REPO_ROOT / 'agents/codex/change-set-verifier.toml'
            ).read_bytes()
            relative = PurePosixPath('.codex/agents/change-set-verifier.toml')

            adopted_target = root / 'adopted'
            adopted = adopted_target / relative
            adopted.parent.mkdir(parents=True)
            adopted.write_bytes(expected)
            first = self.render(adopted_target, generated)
            self.materialize(adopted_target, first.files)
            adopted.write_bytes(b'user modification\n')
            with self.assertRaisesRegex(RenderError, 'modified outside setup'):
                self.render(adopted_target, generated)

            conflicting_target = root / 'conflicting'
            conflicting = conflicting_target / relative
            conflicting.parent.mkdir(parents=True)
            conflicting.write_bytes(b'unowned conflict\n')
            with self.assertRaisesRegex(RenderError, 'cannot adopt conflicting'):
                self.render(conflicting_target, generated)

            removed_target = root / 'removed'
            installed = self.render(removed_target, generated)
            self.materialize(removed_target, installed.files)
            without_fallback = replace(
                self.catalog,
                assets=tuple(
                    asset for asset in self.catalog.assets
                    if asset.id != 'plugin-agents-codex'
                ),
            )
            removed = render_desired_state(
                REPO_ROOT,
                removed_target,
                without_fallback,
                self.config(),
                generated,
            )
            self.assertIn(relative, removed.delete_paths)

    def test_codex_plugin_agent_directory_tracks_add_rename_and_delete_per_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'source'
            agents = source / 'agents/codex'
            agents.mkdir(parents=True)
            (agents / 'old.toml').write_text('name = "old"\n', encoding='utf-8')
            (agents / 'keep.toml').write_text('name = "keep"\n', encoding='utf-8')
            catalog = Catalog(
                'smartkit',
                '0.1.0',
                'https://example.invalid/agents.git',
                'main',
                (
                    AssetSpec(
                        'plugin-agents-codex',
                        'agent',
                        PurePosixPath('agents/codex'),
                        PurePosixPath('.codex/agents'),
                        (Harness.CODEX,),
                    ),
                ),
            )
            generated = root / 'generated'
            generated.mkdir()
            target = root / 'target'

            first = render_desired_state(
                source, target, catalog, self.config(), generated,
            )
            self.materialize(target, first.files)
            unmanaged = target / '.codex/agents/user-owned.toml'
            unmanaged.write_text('name = "user-owned"\n', encoding='utf-8')

            (agents / 'old.toml').rename(agents / 'renamed.toml')
            (agents / 'keep.toml').unlink()
            (agents / 'added.toml').write_text('name = "added"\n', encoding='utf-8')
            second = render_desired_state(
                source, target, catalog, self.config(), generated,
            )

            self.assertEqual(
                {
                    path.as_posix()
                    for path in second.delete_paths
                },
                {
                    '.codex/agents/keep.toml',
                    '.codex/agents/old.toml',
                },
            )
            self.assertIn('.codex/agents/added.toml', second.files_by_path)
            self.assertIn('.codex/agents/renamed.toml', second.files_by_path)
            self.assertNotIn(
                PurePosixPath('.codex/agents/user-owned.toml'),
                second.delete_paths,
            )

    def test_project_agent_id_cannot_shadow_codex_plugin_agent_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            agent_source = target / '.agents/agents/change-set-verifier.md'
            agent_source.parent.mkdir(parents=True)
            agent_source.write_text('# Project verifier\n', encoding='utf-8')
            config_path = target / '.agents/config.json'
            config_path.write_text(json.dumps({
                'agents': [{
                    'id': 'change-set-verifier',
                    'source': '.agents/agents/change-set-verifier.md',
                    'description': 'Project verifier',
                    'harnesses': {'codex': {'sandbox_mode': 'workspace-write'}},
                }],
            }), encoding='utf-8')
            config = load_project_config(config_path, catalog=self.catalog)

            with self.assertRaisesRegex(
                RenderError,
                'Project Agent id conflicts with Codex Plugin Agent default',
            ):
                self.render_with_config(target, self.generated_tree(root), config)

    def test_project_agents_render_thin_host_adapters_and_preserve_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config = self.project_agent_config(target)

            rendered = self.render_with_config(target, self.generated_tree(root), config)

            self.assertNotIn('.agents/agents/l10n.md', rendered.files_by_path)
            self.assertIn(
                PurePosixPath('.agents/agents/l10n.md'), rendered.preserved_paths,
            )
            codex = rendered.files_by_path['.codex/agents/l10n.toml']
            self.assertEqual(tomllib.loads(codex.decode())['model'], 'gpt-5.6-terra')
            self.assertIn(b'Follow `.agents/agents/l10n.md`.', codex)
            self.assertIn(
                b'description: "Project-local agent: l10n"',
                rendered.files_by_path['.cursor/agents/l10n.md'],
            )
            self.assertIn(
                b'Apply @.agents/agents/l10n.md',
                rendered.files_by_path['.github/agents/l10n.agent.md'],
            )
            lock = json.loads(rendered.files_by_path['.agents/smartkit.lock.json'])
            agent_assets = {
                item['path'] for item in lock['assets'] if item['role'] == 'agent'
            }
            self.assertEqual(agent_assets, {
                '.codex/agents/change-set-verifier.toml',
                '.codex/agents/l10n.toml',
                '.cursor/agents/l10n.md',
                '.github/agents/l10n.agent.md',
            })
            project_config = json.loads(
                rendered.files_by_path['.agents/config.json']
            )
            self.assertEqual(
                [agent['id'] for agent in project_config['agents']], ['l10n']
            )
            validate_rendered_state(rendered)

    def test_project_agent_requires_existing_nonempty_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True)
            config_path.write_text(json.dumps({
                'agents': [{
                    'id': 'l10n',
                    'source': '.agents/agents/l10n.md',
                    'description': 'L10n',
                    'harnesses': {'cursor': {'readonly': False}},
                }],
            }), encoding='utf-8')
            config = load_project_config(config_path, catalog=self.catalog)

            with self.assertRaisesRegex(RenderError, 'source is missing'):
                self.render_with_config(target, self.generated_tree(root), config)

    def test_removing_project_agent_deletes_only_managed_host_adapters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config = self.project_agent_config(target)
            generated = self.generated_tree(root)
            first = self.render_with_config(target, generated, config)
            self.materialize(target, first.files)

            second = self.render(target, generated)

            self.assertEqual(
                set(second.delete_paths).intersection({
                    PurePosixPath('.codex/agents/l10n.toml'),
                    PurePosixPath('.cursor/agents/l10n.md'),
                    PurePosixPath('.github/agents/l10n.agent.md'),
                }),
                {
                    PurePosixPath('.codex/agents/l10n.toml'),
                    PurePosixPath('.cursor/agents/l10n.md'),
                    PurePosixPath('.github/agents/l10n.agent.md'),
                },
            )
            self.assertTrue((target / '.agents/agents/l10n.md').is_file())

    def test_project_rules_and_skills_are_discovered_without_becoming_managed_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            rule = target / '.agents/rules/40-domain-testing.md'
            rule.parent.mkdir(parents=True)
            rule.write_text(
                '# Testing\n\nStrength: `Default`\n\n'
                'Scope: Tests under `test/` and plugin test directories.\n',
                encoding='utf-8',
            )
            skill = target / '.agents/skills/local-check/SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text(
                '---\nname: local-check\ndescription: Use for local checks.\n---\n',
                encoding='utf-8',
            )

            rendered = self.render(target, self.generated_tree(root))
            agents = rendered.files_by_path['AGENTS.md'].decode()
            self.assertIn('`.agents/rules/40-domain-testing.md`', agents)
            self.assertNotIn('.agents/rules/40-domain-testing.md', rendered.files_by_path)
            self.assertNotIn('.agents/skills/local-check/SKILL.md', rendered.files_by_path)
            self.assertIn(
                PurePosixPath('.agents/skills/local-check/SKILL.md'),
                rendered.preserved_paths,
            )
            validate_rendered_state(rendered)

    def test_generated_blueprint_skills_are_not_rediscovered_as_project_owned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            generated = self.generated_tree(root)
            first = self.render(target, generated)
            self.materialize(target, first.files)
            verification_matrix = (
                target
                / '.agents/skills/change-set-verification/references/verification-matrix.md'
            )
            verification_matrix.parent.mkdir(parents=True)
            verification_matrix.write_text('# local matrix\n', encoding='utf-8')
            setup_script = (
                target / '.agents/skills/worktree-environment-setup/scripts/setup.ps1'
            )
            setup_script.parent.mkdir(parents=True)
            setup_script.write_text('Write-Output ready\n', encoding='utf-8')

            second = self.render(target, generated)

            self.assertNotIn(
                PurePosixPath('.agents/skills/change-set-verification/SKILL.md'),
                second.preserved_paths,
            )
            self.assertNotIn(
                PurePosixPath('.agents/skills/worktree-environment-setup/SKILL.md'),
                second.preserved_paths,
            )
            self.assertIn(
                PurePosixPath(
                    '.agents/skills/change-set-verification/references/verification-matrix.md'
                ),
                second.preserved_paths,
            )
            self.assertIn(
                PurePosixPath(
                    '.agents/skills/worktree-environment-setup/scripts/setup.ps1'
                ),
                second.preserved_paths,
            )
            self.assertNotIn(
                PurePosixPath('.agents/skills/change-set-verification'),
                second.replace_roots,
            )
            self.assertNotIn(
                PurePosixPath('.agents/skills/worktree-environment-setup'),
                second.replace_roots,
            )

    @staticmethod
    def materialize(target: Path, files) -> None:
        for item in files:
            path = target.joinpath(*item.path.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.content)

if __name__ == '__main__':
    unittest.main()
