"""Golden contracts for platform-native setup-project-agent rendering."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup.catalog import load_catalog, load_project_config  # noqa: E402
from agents_setup.models import (  # noqa: E402
    AssetSpec,
    Catalog,
    ChangeKind,
    Platform,
    ProjectConfig,
)
from agents_setup.planner import build_plan  # noqa: E402
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
        self.models = {
            'agents': {
                'change-set-verifier': {
                    'codex': {'model': 'gpt-5', 'model_reasoning_effort': 'medium'},
                    'cursor': {'model': 'cursor-default'},
                    'github': {'model': 'copilot-default'},
                }
            }
        }

    def config(self) -> ProjectConfig:
        return ProjectConfig(
            1,
            ('00-global-rule-config',),
            ('refactor-code',),
            ('change-set-verifier',),
        )

    def generated_tree(self, root: Path) -> Path:
        generated = root / 'generated'
        rule = generated / '.agents/rules/20-project-tools.md'
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
            self.models,
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
            self.assertIn(
                '.agents/skills/refactor-code/SKILL.md', rendered.files_by_path
            )
            self.assertNotIn(
                '.agents/skills/setup-project-agents/SKILL.md', rendered.files_by_path
            )

            cursor_wrapper = rendered.files_by_path['.cursor/rules/00-global-rule-config.mdc']
            copilot_wrapper = rendered.files_by_path[
                '.github/instructions/00-global-rule-config.instructions.md'
            ]
            self.assertIn('.agents/rules/00-global-rule-config.md', cursor_wrapper.decode())
            self.assertIn('.agents/rules/00-global-rule-config.md', copilot_wrapper.decode())
            validate_rendered_state(rendered)

    def test_rendered_project_config_round_trips_and_owns_only_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            target.mkdir()
            rendered = self.render(target, self.generated_tree(root))
            self.materialize(target, rendered.files)

            loaded = load_project_config(target / '.agents/config.json', catalog=self.catalog)

            self.assertEqual(loaded.version, 1)
            self.assertEqual(
                {
                    key
                    for path, key in rendered.fields_by_key
                    if path == '.agents/config.json'
                },
                {'version'},
            )

    def test_unsafe_structured_template_field_is_rejected(self):
        with self.assertRaisesRegex(RenderError, 'unsafe template field'):
            tuple(_safe_leaves({'$schema': 'control-plane/path'}))

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

    def test_existing_jsonc_trailing_commas_do_not_change_string_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            settings = target / '.github/copilot/settings.json'
            settings.parent.mkdir(parents=True)
            settings.write_text(
                '{\n'
                '  // user-owned values\n'
                '  "unmanaged": "literal,}",\n'
                '  "items": [1, 2,],\n'
                '}\n',
                encoding='utf-8',
            )

            rendered = self.render(target, self.generated_tree(root))
            parsed = json.loads(
                rendered.files_by_path['.github/copilot/settings.json']
            )

            self.assertEqual(parsed['unmanaged'], 'literal,}')
            self.assertEqual(parsed['items'], [1, 2])

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
            '.agents/rules/00-global-rule-config.md',
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
                        (Platform.CODEX,),
                    ),
                    AssetSpec(
                        'generated-shared',
                        'blueprint',
                        PurePosixPath('blueprints/shared.md'),
                        target_path,
                        (Platform.CODEX,),
                        'generate',
                    ),
                ),
            )
            generated = root / 'generated/.agents/rules'
            generated.mkdir(parents=True)
            (generated / 'shared.md').write_text('generated\n', encoding='utf-8')
            config = ProjectConfig(
                1,
                ('shared',),
                (),
                (),
            )

            rendered = render_desired_state(
                source,
                root / 'target',
                catalog,
                config,
                root / 'generated',
                {},
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
                self.models,
            )

            self.assertIn('AGENTS.md', rendered.files_by_path)
            self.assertIn('.cursor/rules/00-global-rule-config.mdc', rendered.files_by_path)

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

    def test_first_setup_merges_user_config_without_owning_user_selections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps({
                    'version': 1,
                    'selected_rules': ['00-global-rule-config'],
                }),
                encoding='utf-8',
            )
            rendered = self.render(target, self.generated_tree(root))

            plan = build_plan(target, rendered.files, rendered.fields)
            desired_config = json.loads(rendered.files_by_path['.agents/config.json'])

            config_change = next(
                change
                for change in plan.changes
                if change.path.as_posix() == '.agents/config.json'
            )
            self.assertEqual(config_change.kind, ChangeKind.UPDATE)
            self.assertNotIn('platforms', desired_config)
            self.assertEqual(
                {
                    key
                    for path, key in rendered.fields_by_key
                    if path == '.agents/config.json'
                },
                {'version'},
            )

    def test_force_convergence_overwrites_conflicting_owned_config_field(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            config_path = target / '.agents/config.json'
            config_path.parent.mkdir(parents=True)
            config_path.write_text('{"version": 2}\n', encoding='utf-8')
            rendered = self.render(target, self.generated_tree(root))

            plan = build_plan(target, rendered.files, rendered.fields)
            change = next(
                item for item in plan.changes if item.path.as_posix() == '.agents/config.json'
            )
            self.assertEqual(change.kind, ChangeKind.UPDATE)
            self.assertEqual(json.loads(change.content)['version'], 1)

    def test_deselected_assets_are_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / 'target'
            stale_paths = (
                '.agents/rules/01-global-personality.md',
                '.agents/agents/change-set-verifier.md',
                '.cursor/rules/01-global-personality.mdc',
                '.github/agents/change-set-verifier.agent.md',
            )
            for relative in stale_paths:
                path = target.joinpath(*PurePosixPath(relative).parts)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('stale\n', encoding='utf-8')

            config = ProjectConfig(
                1,
                ('00-global-rule-config',),
                ('refactor-code',),
                (),
            )
            rendered = render_desired_state(
                REPO_ROOT,
                target,
                self.catalog,
                config,
                self.generated_tree(root),
                {},
            )
            plan = build_plan(
                target,
                rendered.files,
                rendered.fields,
                delete_paths=rendered.delete_paths,
                replace_roots=rendered.replace_roots,
            )
            deleted = {
                item.path.as_posix()
                for item in plan.changes
                if item.kind is ChangeKind.DELETE
            }

            self.assertTrue(set(stale_paths).issubset(deleted))

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
