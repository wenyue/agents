import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
def load_json(relative_path: str) -> dict:
    value = json.loads((REPO_ROOT / relative_path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise AssertionError(f'{relative_path} must contain an object')
    return value


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
        self.assertEqual(catalog['plugin']['id'], 'agents')
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
            self.assertEqual(manifest['name'], 'agents')
            self.assertEqual(manifest['version'], version)
            self.assertEqual(manifest['skills'], './skills/')
        self.assertFalse((REPO_ROOT / 'agents' / '.codex-plugin').exists())
        self.assertFalse((REPO_ROOT / 'agents' / 'skills').exists())

    def test_local_marketplaces_point_at_the_repository_root(self):
        for relative in (
            '.cursor-plugin/marketplace.json',
            '.github/plugin/marketplace.json',
        ):
            marketplace = load_json(relative)
            self.assertEqual(marketplace['plugins'][0]['source'], './')
        codex = load_json('.agents/plugins/marketplace.json')
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
