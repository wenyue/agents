import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / 'scripts' / 'sync_mcp_adapters.py'


def load_module():
    spec = importlib.util.spec_from_file_location('sync_mcp_adapters', SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncMcpAdaptersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_repository_registry_generates_three_current_adapters(self):
        servers = self.module.load_registry(REPO_ROOT / 'mcp/registry.json')

        self.assertEqual([server['id'] for server in servers], ['playwright'])
        for platform, relative in self.module.OUTPUTS.items():
            with self.subTest(platform=platform):
                self.assertEqual(
                    (REPO_ROOT / relative).read_bytes(),
                    self.module.render_platform(servers, platform),
                )

        codex = json.loads((REPO_ROOT / '.mcp.json').read_text())
        cursor = json.loads((REPO_ROOT / 'mcp/cursor.json').read_text())
        copilot = json.loads((REPO_ROOT / 'mcp/copilot.json').read_text())
        expected_args = ['-y', '@playwright/mcp@latest', '--isolated', '--headless']
        self.assertEqual(codex['mcpServers']['playwright']['args'], expected_args)
        self.assertEqual(servers[0]['readiness']['checks'], [
            {'kind': 'runtime-version', 'runtime': 'node', 'minimum': '18.0.0'},
            {'kind': 'command-exists', 'command': 'npx'},
        ])
        self.assertNotIn('type', codex['mcpServers']['playwright'])
        self.assertEqual(cursor['mcpServers']['playwright']['type'], 'stdio')
        self.assertEqual(copilot['mcpServers']['playwright']['type'], 'local')
        self.assertEqual(copilot['mcpServers']['playwright']['tools'], ['*'])

    def test_check_reports_drift_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'mcp').mkdir()
            (root / 'mcp/registry.json').write_text(
                json.dumps({
                    'version': 1,
                    'servers': [{
                        'id': 'example', 'transport': 'http',
                        'url': 'https://example.invalid/mcp',
                        'platforms': ['codex', 'cursor', 'copilot'],
                    }],
                }),
                encoding='utf-8',
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), '--root', str(root), '--check'],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse((root / '.mcp.json').exists())

    def test_registry_rejects_unknown_fields_and_unsafe_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'registry.json'
            invalid = (
                {'version': 1, 'servers': [{'id': 'x', 'transport': 'stdio', 'command': 'x', 'platforms': ['codex'], 'script': 'run'}]},
                {'version': 1, 'servers': [{'id': 'x', 'transport': 'stdio', 'command': 'x', 'platforms': ['codex'], 'readiness': {'checks': [{'kind': 'shell', 'command': 'x'}]}}]},
                {'version': 1, 'servers': [{'id': 'x', 'transport': 'stdio', 'command': 'x', 'platforms': ['codex'], 'readiness': {'checks': [{'kind': 'runtime-version', 'runtime': 'python', 'minimum': '3.10.0'}]}}]},
            )
            for document in invalid:
                with self.subTest(document=document):
                    path.write_text(json.dumps(document), encoding='utf-8')
                    with self.assertRaises(self.module.McpRegistryError):
                        self.module.load_registry(path)

    def test_playwright_registry_rejects_unapproved_launcher_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'registry.json'
            for args in (
                ['-y', '@playwright/mcp@latest', '--isolated'],
                [
                    '-y', '@playwright/mcp@latest', '--isolated', '--headless',
                    '--no-sandbox',
                ],
            ):
                with self.subTest(args=args):
                    path.write_text(json.dumps({
                        'version': 1,
                        'servers': [{
                            'id': 'playwright',
                            'transport': 'stdio',
                            'command': 'npx',
                            'args': args,
                            'platforms': ['codex', 'cursor', 'copilot'],
                            'tools': ['*'],
                        }],
                    }), encoding='utf-8')
                    with self.assertRaises(self.module.McpRegistryError):
                        self.module.load_registry(path)


if __name__ == '__main__':
    unittest.main()
