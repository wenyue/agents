import json
import re
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
            {'plugins', 'rules'},
        )

    def test_chinese_documentation_has_one_to_one_english_mirrors(self):
        chinese_root = REPO_ROOT / 'docs' / 'zh-CN'
        source_paths = {Path('README.md')}
        for root_name in ('agents', 'blueprints', 'rules', 'skills'):
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

    def test_readme_documents_plugin_setup_and_safety_boundaries(self):
        readme = (REPO_ROOT / 'README.md').read_text(encoding='utf-8')
        for expected in (
            'Codex',
            'Cursor',
            'GitHub Copilot',
            'setup-project-agents',
            'remote `main`',
            'Hooks',
            'multi-agent',
            'doctor',
            'upgrade',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, readme)

    def test_project_catalog_matches_native_plugin_version(self):
        catalog = load_json('catalog/project-assets.json')
        self.assertEqual(catalog['plugin']['id'], 'smartkit')
        self.assertEqual(catalog['plugin']['version'], '0.1.0')

    def test_repository_root_is_the_only_plugin_root(self):
        version = (REPO_ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertEqual(version, '0.1.0')
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
        for relative in (
            '.cursor-plugin/marketplace.json',
            '.github/plugin/marketplace.json',
        ):
            marketplace = load_json(relative)
            self.assertEqual(marketplace['name'], 'wenyue')
            self.assertEqual(marketplace['plugins'][0]['name'], 'smartkit')
            self.assertEqual(marketplace['plugins'][0]['source'], './')
        codex = load_json('.agents/plugins/marketplace.json')
        self.assertEqual(codex['name'], 'wenyue')
        self.assertEqual(codex['interface']['displayName'], 'WenYue SmartKit')
        self.assertEqual(codex['plugins'][0]['name'], 'smartkit')
        self.assertEqual(codex['plugins'][0]['source']['path'], './')

    def test_root_manifests_keep_skills_as_their_only_runtime_entry_point(self):
        for relative in (
            '.codex-plugin/plugin.json',
            '.cursor-plugin/plugin.json',
            'plugin.json',
        ):
            with self.subTest(path=relative):
                manifest = load_json(relative)
                self.assertNotIn('hooks', manifest)
                self.assertTrue((REPO_ROOT / manifest['skills']).is_dir())


if __name__ == '__main__':
    unittest.main()
