import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'sync_agent_adapters.py'


def load_module():
    spec = importlib.util.spec_from_file_location('sync_agent_adapters', SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError('cannot load sync_agent_adapters')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncAgentAdaptersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_repository_adapters_match_registry(self):
        agents = self.module.load_registry(ROOT)
        self.assertEqual([agent['id'] for agent in agents], ['change-set-verifier'])
        self.assertEqual(set(agents[0]['platforms']), {'codex', 'cursor', 'copilot'})

        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--check'],
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        codex = (ROOT / 'agents/codex/change-set-verifier.toml').read_text()
        cursor = (ROOT / 'agents/cursor/change-set-verifier.md').read_text()
        copilot = (ROOT / 'agents/copilot/change-set-verifier.agent.md').read_text()
        for adapter in (codex, cursor, copilot):
            self.assertIn('.agents/skills/change-set-verification/SKILL.md', adapter)
            self.assertNotIn('model =', adapter)
            self.assertNotIn('model:', adapter)
        self.assertIn('sandbox_mode = "workspace-write"', codex)
        self.assertIn('readonly: false', cursor)
        self.assertIn('disable-model-invocation: false', copilot)

    def test_check_reports_drift_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'agents/source').mkdir(parents=True)
            (root / 'agents/source/example.md').write_text('Verify it.\n', encoding='utf-8')
            (root / 'agents/registry.json').write_text(json.dumps({
                'version': 1,
                'agents': [{
                    'id': 'example',
                    'source': 'source/example.md',
                    'description': 'Example verifier.',
                    'platforms': {'codex': {'sandbox_mode': 'read-only'}},
                }],
            }), encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(SCRIPT), '--root', str(root), '--check'],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse((root / 'agents/codex/example.toml').exists())

    def test_registry_rejects_unknown_fields_and_unsafe_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'agents').mkdir()
            path = root / 'agents/registry.json'
            invalid = (
                {'version': 1, 'agents': [], 'templates': {}},
                {'version': 1, 'agents': [{
                    'id': 'example', 'source': '../example.md',
                    'description': 'Example.',
                    'platforms': {'codex': {'sandbox_mode': 'read-only'}},
                }]},
                {'version': 1, 'agents': [{
                    'id': 'example', 'source': 'source/example.md',
                    'description': 'Example.',
                    'platforms': {'cursor': {'readonly': 'false'}},
                }]},
            )
            for document in invalid:
                with self.subTest(document=document):
                    path.write_text(json.dumps(document), encoding='utf-8')
                    with self.assertRaises(self.module.AgentRegistryError):
                        self.module.load_registry(root)


if __name__ == '__main__':
    unittest.main()
