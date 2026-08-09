import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginRuleContractTest(unittest.TestCase):
    def run_dispatch(
        self,
        platform: str,
        event: str,
        payload: dict[str, object],
        *,
        plugin_data: Path,
    ) -> dict[str, object]:
        environment = dict(os.environ)
        environment['PLUGIN_DATA'] = str(plugin_data)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / 'runtime/rules/dispatch.py'),
                '--platform',
                platform,
                '--event',
                event,
            ],
            input=json.dumps(payload).encode(),
            capture_output=True,
            cwd=ROOT,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return json.loads(result.stdout)

    def test_registry_order_and_platform_delivery_contract(self):
        registry = json.loads((ROOT / 'rules/registry.json').read_text(encoding='utf-8'))
        rules = registry['rules']
        self.assertEqual(rules[0]['id'], 'smartkit/core-rule-config')
        self.assertEqual(rules[0]['strength'], 'Mandatory')
        self.assertEqual(rules[0]['trigger'], {'type': 'always'})
        self.assertEqual(len({item['id'] for item in rules}), len(rules))
        self.assertTrue(all((ROOT / 'rules' / item['source']).is_file() for item in rules))
        self.assertEqual(
            json.loads((ROOT / '.cursor-plugin/plugin.json').read_text())['rules'],
            './rules/cursor/',
        )
        adapter_check = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/sync_cursor_rule_adapters.py'), '--check'],
            capture_output=True, cwd=ROOT, check=False,
        )
        self.assertEqual(adapter_check.returncode, 0, adapter_check.stderr.decode())

    def test_registry_rejects_removed_exclusion_globs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry = root / 'rules/registry.json'
            registry.parent.mkdir(parents=True)
            source = root / 'rules/source'
            source.mkdir()
            (source / 'core-rule-config.md').write_text('core\n', encoding='utf-8')
            (source / 'file-example.md').write_text('example\n', encoding='utf-8')
            registry.write_text(json.dumps({
                'version': 1,
                'rules': [
                    {
                        'id': 'smartkit/core-rule-config',
                        'source': 'source/core-rule-config.md',
                        'strength': 'Mandatory',
                        'trigger': {'type': 'always'},
                    },
                    {
                        'id': 'smartkit/file-example',
                        'source': 'source/file-example.md',
                        'strength': 'Default',
                        'trigger': {
                            'type': 'file',
                            'include_globs': ['**/*.example'],
                            'exclude_globs': ['vendor/**'],
                        },
                    },
                ],
            }), encoding='utf-8')
            environment = dict(os.environ)
            environment['PLUGIN_ROOT'] = str(root)
            environment['PLUGIN_DATA'] = str(root / 'data')
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'runtime/rules/dispatch.py'),
                    '--platform', 'codex', '--event', 'session',
                ],
                input=b'{}',
                capture_output=True,
                cwd=ROOT,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn('invalid file trigger', result.stderr.decode())

    def test_router_loads_always_then_matching_file_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            session = self.run_dispatch(
                'codex', 'session', {'session_id': 'router'}, plugin_data=plugin_data
            )
            always = session['hookSpecificOutput']['additionalContext']
            self.assertIn('smartkit/core-rule-config', always)
            self.assertNotIn('smartkit/file-flutter', always)

            prompt = self.run_dispatch(
                'codex',
                'prompt',
                {'session_id': 'router', 'prompt': 'Please edit src/widget.dart'},
                plugin_data=plugin_data,
            )
            context = prompt['hookSpecificOutput']['additionalContext']
            self.assertIn('smartkit/file-flutter', context)
            self.assertNotIn('smartkit/core-rule-config', context)
            self.assertNotIn('smartkit/file-cpp', context)

            root_file = self.run_dispatch(
                'codex',
                'prompt',
                {'session_id': 'root-file', 'prompt': 'Edit widget.dart'},
                plugin_data=plugin_data,
            )
            self.assertIn(
                'smartkit/file-flutter',
                root_file['hookSpecificOutput']['additionalContext'],
            )

    def test_copilot_uses_native_output_shapes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            session = self.run_dispatch(
                'copilot', 'session', {'sessionId': 'native'}, plugin_data=plugin_data
            )
            self.assertEqual(set(session), {'additionalContext'})
            prompt = self.run_dispatch(
                'copilot',
                'prompt',
                {'sessionId': 'native', 'transformedPrompt': 'Edit src/main.go'},
                plugin_data=plugin_data,
            )
            self.assertIn('smartkit/file-go', prompt['modifiedTransformedPrompt'])

    def test_hook_delivery_emits_a_visible_host_boundary_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            environment = dict(os.environ)
            environment['PLUGIN_DATA'] = temp_dir
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'runtime/rules/dispatch.py'),
                    '--platform',
                    'codex',
                    '--event',
                    'session',
                ],
                input=json.dumps({'session_id': 'diagnostic'}).encode(),
                capture_output=True,
                cwd=ROOT,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            diagnostic = result.stderr.decode()
            self.assertIn('Rule delivery attempted', diagnostic)
            self.assertIn('spill', diagnostic)
            self.assertIn('host-owned', diagnostic)

    def test_first_structured_write_loads_file_rules_and_requires_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            payload = {
                'sessionId': 'gate-session',
                'toolName': 'write_file',
                'toolInput': {'file_path': 'src/main.go', 'content': 'package main'},
            }

            first = self.run_dispatch(
                'codex', 'tool', payload, plugin_data=plugin_data
            )
            decision = first['hookSpecificOutput']
            self.assertEqual(decision['permissionDecision'], 'deny')
            self.assertIn('smartkit/file-go', decision['additionalContext'])

            second = self.run_dispatch(
                'codex', 'tool', payload, plugin_data=plugin_data
            )
            self.assertEqual(second, {})

    def test_prompt_activation_avoids_the_first_write_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            prompt = self.run_dispatch(
                'copilot',
                'prompt',
                {'sessionId': 'prompt-session', 'transformedPrompt': 'Edit src/main.go'},
                plugin_data=plugin_data,
            )
            self.assertIn('smartkit/file-go', prompt['modifiedTransformedPrompt'])

            tool = self.run_dispatch(
                'copilot',
                'tool',
                {
                    'sessionId': 'prompt-session',
                    'toolName': 'write_file',
                    'toolInput': {'path': 'src/main.go'},
                },
                plugin_data=plugin_data,
            )
            self.assertEqual(tool, {})

            repeated = self.run_dispatch(
                'copilot',
                'prompt',
                {'sessionId': 'prompt-session', 'transformedPrompt': 'Again src/main.go'},
                plugin_data=plugin_data,
            )
            self.assertEqual(repeated['modifiedTransformedPrompt'], 'Again src/main.go')

            compacted = self.run_dispatch(
                'copilot',
                'session',
                {'sessionId': 'prompt-session', 'source': 'compact'},
                plugin_data=plugin_data,
            )
            self.assertIn('smartkit/core-rule-config', compacted['additionalContext'])
            self.assertIn('smartkit/file-go', compacted['additionalContext'])

    def test_read_discovery_activates_rules_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            read = self.run_dispatch(
                'codex',
                'tool',
                {
                    'session_id': 'read-session',
                    'tool_name': 'Read',
                    'tool_input': {'file_path': 'src/main.go'},
                },
                plugin_data=plugin_data,
            )
            decision = read['hookSpecificOutput']
            self.assertNotIn('permissionDecision', decision)
            self.assertIn('smartkit/file-go', decision['additionalContext'])

            write = self.run_dispatch(
                'codex',
                'tool',
                {
                    'session_id': 'read-session',
                    'tool_name': 'Write',
                    'tool_input': {'file_path': 'src/main.go', 'content': 'package main'},
                },
                plugin_data=plugin_data,
            )
            self.assertEqual(write, {})


if __name__ == '__main__':
    unittest.main()
