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
    def test_public_catalog_matches_native_plugin_version(self):
        public = load_json(
            'skills/setup-project-agents/references/public_assets.json'
        )
        self.assertEqual(
            public['catalog'],
            {'id': 'agents', 'version': '0.1.0', 'revision': 'v0.1.0'},
        )

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
