import json
import os
import re
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    value = json.loads((REPO_ROOT / relative_path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise AssertionError(f'{relative_path} must contain an object')
    return value


def markdown_structure(text: str) -> tuple[str, ...]:
    blocks = re.split(r'\n[ \t]*\n', text.strip())
    structure = []
    for block in blocks:
        first_line = block.lstrip().splitlines()[0]
        if first_line == '---':
            structure.append('frontmatter')
        elif first_line.startswith('#'):
            structure.append(first_line.split(maxsplit=1)[0])
        elif first_line.startswith('```'):
            structure.append(first_line)
        elif first_line.startswith('- [ ] '):
            structure.append('checklist')
        elif first_line.startswith('- '):
            structure.append('unordered-list')
        elif re.match(r'\d+\. ', first_line):
            structure.append('ordered-list')
        elif first_line.startswith('|'):
            structure.append('table')
        else:
            structure.append('paragraph')
    return tuple(structure)


class PluginManifestTest(unittest.TestCase):
    def test_documentation_and_local_runtime_boundaries(self):
        self.assertFalse((REPO_ROOT / 'agents-zh').exists())

        chinese_docs = REPO_ROOT / 'docs' / 'zh-CN'
        self.assertTrue(chinese_docs.is_dir())
        self.assertTrue(any(chinese_docs.rglob('*.md')))
        self.assertFalse(any(path.suffix != '.md' for path in chinese_docs.rglob('*') if path.is_file()))

        self.assertEqual(
            {path.name for path in (REPO_ROOT / '.agents').iterdir()},
            {'plugins', 'rules', 'skills'},
        )

        for name in ('write-rule', 'write-skill'):
            with self.subTest(skill=name):
                wrapper = (
                    REPO_ROOT / '.agents' / 'skills' / name / 'SKILL.md'
                ).read_text(encoding='utf-8')
                self.assertIn(f'name: {name}', wrapper)
                self.assertEqual(wrapper.count('Apply @'), 1)
                self.assertIn(
                    f'Apply @setup-assets/skills/{name}/SKILL.md', wrapper
                )

    def test_repository_declares_current_contract_only(self):
        rule_path = '.agents/rules/21-project-rules.md'
        rule = (REPO_ROOT / rule_path).read_text(encoding='utf-8')
        entry = (REPO_ROOT / 'AGENTS.md').read_text(encoding='utf-8')

        self.assertIn('Strength: `Mandatory`', rule)
        self.assertIn('current contract', rule)
        self.assertIn('Do not add compatibility aliases', rule)
        self.assertIn(f'`{rule_path}` | `Mandatory`', entry)

    def test_chinese_documentation_has_one_to_one_english_mirrors(self):
        chinese_root = REPO_ROOT / 'docs' / 'zh-CN'
        source_paths = {Path('README.md')}
        for root_name in (
            'setup-assets/rules',
            'setup-assets/skills',
            'setup-assets/agents',
            'setup-assets/blueprints',
            'skills',
        ):
            source_paths.update(
                path.relative_to(REPO_ROOT)
                for path in (REPO_ROOT / root_name).rglob('*.md')
            )

        translated_paths = {
            path.relative_to(chinese_root)
            for path in chinese_root.rglob('*.md')
        }
        self.assertEqual(translated_paths, source_paths)

        for source_path in sorted(source_paths):
            with self.subTest(path=source_path.as_posix()):
                source = (REPO_ROOT / source_path).read_text(encoding='utf-8')
                translation = (chinese_root / source_path).read_text(encoding='utf-8')
                self.assertEqual(
                    markdown_structure(translation),
                    markdown_structure(source),
                )

    def test_readme_documents_plugin_setup_and_consent_flow(self):
        readme = (REPO_ROOT / 'README.md').read_text(encoding='utf-8')
        for expected in (
            'Codex',
            'Cursor',
            'GitHub Copilot',
            'setup-project-agents',
            'Hooks',
            'multi-agent',
            'Superpowers',
            'CodeGraph',
            'Tokscale',
            'explicit consent',
            'explicitly declines',
            'original task continues',
            'upgrade',
            '/hooks',
            'does not automatically trust',
            'SessionStart',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, readme)

    def test_setup_loads_authoring_contracts_from_its_pinned_source(self):
        setup = (
            REPO_ROOT / 'skills' / 'setup-project-agents' / 'SKILL.md'
        ).read_text(encoding='utf-8')

        for name in ('write-rule', 'write-skill'):
            self.assertIn(
                f'SOURCE_ROOT/setup-assets/skills/{name}/SKILL.md', setup
            )

    def test_project_catalog_matches_native_plugin_version(self):
        catalog = load_json('setup-assets/catalog/assets.json')
        version = (REPO_ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertEqual(catalog['plugin']['id'], 'smartkit')
        self.assertEqual(catalog['plugin']['version'], version)

    def test_repository_root_is_the_only_plugin_root(self):
        version = (REPO_ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertRegex(
            version,
            r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
            r'(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$',
        )
        manifests = (
            REPO_ROOT / '.codex-plugin' / 'plugin.json',
            REPO_ROOT / '.cursor-plugin' / 'plugin.json',
            REPO_ROOT / 'plugin.json',
        )
        for manifest_path in manifests:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            self.assertEqual(manifest['name'], 'smartkit')
            self.assertEqual(manifest['version'], version)
            self.assertEqual(manifest['skills'], './skills/')
        self.assertEqual(
            load_json('.codex-plugin/plugin.json')['interface']['displayName'],
            'WenYue SmartKit',
        )
        self.assertEqual(
            load_json('.cursor-plugin/plugin.json')['displayName'],
            'WenYue SmartKit',
        )
        self.assertFalse((REPO_ROOT / 'agents' / '.codex-plugin').exists())
        self.assertFalse((REPO_ROOT / 'agents' / 'skills').exists())

    def test_local_marketplaces_point_at_the_repository_root(self):
        version = (REPO_ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        for relative in (
            '.cursor-plugin/marketplace.json',
            '.github/plugin/marketplace.json',
        ):
            marketplace = load_json(relative)
            self.assertEqual(marketplace['name'], 'wenyue')
            self.assertEqual(marketplace['metadata']['version'], version)
            self.assertEqual(marketplace['plugins'][0]['name'], 'smartkit')
            self.assertEqual(marketplace['plugins'][0]['source'], './')
            self.assertEqual(marketplace['plugins'][0]['version'], version)
        codex = load_json('.agents/plugins/marketplace.json')
        self.assertEqual(codex['name'], 'wenyue')
        self.assertEqual(codex['interface']['displayName'], 'WenYue SmartKit')
        self.assertEqual(codex['plugins'][0]['name'], 'smartkit')
        self.assertEqual(codex['plugins'][0]['source']['path'], './')

    def test_root_manifests_expose_plugin_owned_hooks(self):
        codex = load_json('.codex-plugin/plugin.json')
        cursor = load_json('.cursor-plugin/plugin.json')
        copilot = load_json('plugin.json')

        self.assertNotIn('hooks', codex)
        self.assertEqual(cursor['hooks'], './hooks/cursor.json')
        self.assertEqual(copilot['hooks'], './hooks/copilot.json')
        for manifest in (codex, cursor, copilot):
            self.assertTrue((REPO_ROOT / manifest['skills']).is_dir())
            self.assertNotIn('agents', manifest)
            self.assertNotIn('rules', manifest)

        plugin_skills = {
            path.name
            for path in (REPO_ROOT / 'skills').iterdir()
            if path.is_dir()
        }
        self.assertEqual(plugin_skills, {'debug-mode', 'setup-project-agents'})
        self.assertTrue((REPO_ROOT / 'skills/debug-mode/SKILL.md').is_file())
        self.assertTrue((REPO_ROOT / 'skills/debug-mode/LICENSE').is_file())
        self.assertTrue(
            (
                REPO_ROOT
                / 'skills/setup-project-agents/scripts/_vendor/tomli/__init__.py'
            ).is_file()
        )
        self.assertFalse((REPO_ROOT / 'agents').exists())
        self.assertFalse((REPO_ROOT / 'rules').exists())
        self.assertFalse(any((REPO_ROOT / 'runtime').rglob('SKILL.md')))
        self.assertEqual(
            {path.name for path in (REPO_ROOT / 'setup-assets').iterdir() if path.is_dir()},
            {'agents', 'blueprints', 'catalog', 'rules', 'skills', 'templates'},
        )
        for retired_root in ('project', 'blueprints', 'catalog', 'config', 'templates'):
            self.assertFalse((REPO_ROOT / retired_root).exists())

        hook_paths = {
            'codex': REPO_ROOT / 'hooks/hooks.json',
            'cursor': REPO_ROOT / cursor['hooks'],
            'copilot': REPO_ROOT / copilot['hooks'],
        }
        for platform, path in hook_paths.items():
            with self.subTest(platform=platform):
                self.assertTrue(path.is_file())
                content = path.read_text(encoding='utf-8')
                expected_entry = (
                    'run_recommended_tools'
                    if platform == 'cursor'
                    else 'check_recommended_tools'
                )
                self.assertIn(expected_entry, content)
                self.assertIn('runtime/recommended-tools', content.replace('\\', '/'))
                self.assertIn(f'--platform {platform}', content)
                self.assertNotIn('.agents/', content)
                self.assertNotIn('.agents\\', content)
                self.assertNotIn(' install', content.lower())
                self.assertNotIn(' upgrade', content.lower())

        self.assertEqual(
            set(load_json('hooks/hooks.json')['hooks']),
            {'SessionStart'},
        )
        self.assertEqual(
            set(load_json('hooks/cursor.json')['hooks']),
            {'sessionStart', 'beforeSubmitPrompt'},
        )
        cursor_hooks = load_json('hooks/cursor.json')['hooks']
        self.assertIn(
            '--delivery context',
            cursor_hooks['sessionStart'][0]['command'],
        )
        self.assertNotIn(
            '--delivery context',
            cursor_hooks['beforeSubmitPrompt'][0]['command'],
        )
        self.assertEqual(
            set(load_json('hooks/copilot.json')['hooks']),
            {'sessionStart'},
        )

    def test_cursor_hook_uses_cross_platform_dispatcher(self):
        cursor_hooks = load_json('hooks/cursor.json')['hooks']
        commands = {
            cursor_hooks['sessionStart'][0]['command'],
            cursor_hooks['beforeSubmitPrompt'][0]['command'],
        }
        dispatcher = REPO_ROOT / 'runtime/recommended-tools/run_recommended_tools.cmd'

        self.assertTrue(dispatcher.is_file())
        for command in commands:
            self.assertIn('run_recommended_tools.cmd', command)
            self.assertNotRegex(command, r'\bpython3?\b')

        if os.name == 'nt':
            invocation = ['cmd.exe', '/d', '/c', str(dispatcher), '--help']
        else:
            self.assertTrue(os.access(dispatcher, os.X_OK))
            invocation = [
                'sh', '-c', '"$1" --help', 'smartkit-cursor-hook', str(dispatcher)
            ]
        result = subprocess.run(
            invocation,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('usage:', result.stdout.lower())

    def test_hook_platform_contract(self):
        contract_path = REPO_ROOT / 'setup-assets/catalog/platforms.json'
        self.assertTrue(contract_path.is_file())
        contract = load_json('setup-assets/catalog/platforms.json')

        self.assertEqual(contract['version'], 1)
        self.assertEqual(
            contract['requiredOperatingSystems'],
            ['windows', 'linux'],
        )
        self.assertEqual(
            set(contract['platforms']),
            {'codex', 'cursor', 'copilot'},
        )

        for platform, spec in contract['platforms'].items():
            with self.subTest(platform=platform):
                manifest = load_json(spec['hookManifest'])
                entry = manifest['hooks'][spec['hookEvent']][0]
                if 'hooks' in entry:
                    entry = entry['hooks'][0]
                for route in spec['hookRoutes'].values():
                    if route == 'dispatcher':
                        self.assertIn('run_recommended_tools.cmd', entry['command'])
                    else:
                        self.assertIn(route, entry)
                agent_template = (
                    REPO_ROOT / spec['agentTemplate']
                ).read_text(encoding='utf-8')
                self.assertRegex(agent_template, r'(?m)^model\s*[:=]')


if __name__ == '__main__':
    unittest.main()
