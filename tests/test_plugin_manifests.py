import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_VERSION = '0.1.0'


def load_json(relative_path: str) -> dict:
    value = json.loads((REPO_ROOT / relative_path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise AssertionError(f'{relative_path} must contain an object')
    return value


class PluginManifestTest(unittest.TestCase):
    def test_public_catalog_matches_native_plugin_version(self):
        public = load_json(
            'agents/skills/setup-project-agents/references/public_assets.json'
        )
        self.assertEqual(
            public['catalog'],
            {'id': 'agents', 'version': PLUGIN_VERSION, 'revision': 'v0.1.0'},
        )

    def test_native_plugin_manifests_share_identity_version_and_skills(self):
        for path in (
            'agents/.codex-plugin/plugin.json',
            'agents/.cursor-plugin/plugin.json',
            'agents/plugin.json',
        ):
            with self.subTest(path=path):
                manifest = load_json(path)
                self.assertEqual(manifest['name'], 'agents')
                self.assertEqual(manifest['version'], PLUGIN_VERSION)
                self.assertEqual(manifest['skills'], './skills/')
                self.assertNotIn('hooks', manifest)
                self.assertTrue((REPO_ROOT / 'agents' / manifest['skills']).is_dir())

    def test_codex_marketplace_points_at_repository_plugin_root(self):
        marketplace = load_json('.agents/plugins/marketplace.json')
        self.assertEqual(marketplace['name'], 'wenyue-agents')
        self.assertEqual(marketplace['interface']['displayName'], 'wenyue/agents')
        self.assertEqual(
            marketplace['plugins'],
            [{
                'name': 'agents',
                'source': {'source': 'local', 'path': './agents'},
                'policy': {
                    'installation': 'AVAILABLE',
                    'authentication': 'ON_INSTALL',
                },
                'category': 'Developer Tools',
            }],
        )

    def test_cursor_and_copilot_marketplaces_point_at_repository_root(self):
        for path in (
            '.cursor-plugin/marketplace.json',
            '.github/plugin/marketplace.json',
        ):
            with self.subTest(path=path):
                marketplace = load_json(path)
                self.assertEqual(marketplace['name'], 'wenyue-agents')
                self.assertEqual(marketplace['plugins'][0]['name'], 'agents')
                self.assertEqual(marketplace['plugins'][0]['source'], './agents')
                self.assertEqual(marketplace['plugins'][0]['version'], PLUGIN_VERSION)


if __name__ == '__main__':
    unittest.main()
