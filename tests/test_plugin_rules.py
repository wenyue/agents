import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginRuleContractTest(unittest.TestCase):
    def run_adapter_sync(self, root: Path, action: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / 'scripts/sync_cursor_rule_adapters.py'),
                action,
                '--root',
                str(root),
            ],
            capture_output=True,
            cwd=ROOT,
            check=False,
        )

    def run_dispatch(
        self,
        harness: str,
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
                '--harness',
                harness,
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

    def run_raw_dispatch(
        self,
        harness: str,
        event: str,
        payload: bytes,
        *,
        plugin_data: Path,
    ) -> subprocess.CompletedProcess[bytes]:
        environment = dict(os.environ)
        environment['PLUGIN_DATA'] = str(plugin_data)
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / 'runtime/rules/dispatch.py'),
                '--harness',
                harness,
                '--event',
                event,
            ],
            input=payload,
            capture_output=True,
            cwd=ROOT,
            env=environment,
            check=False,
        )

    def test_registry_order_and_harness_delivery_contract(self):
        registry = json.loads((ROOT / 'rules/registry.json').read_text(encoding='utf-8'))
        rules = registry['rules']
        self.assertEqual(rules[0]['id'], 'smartkit/core-rule-config')
        self.assertEqual(rules[0]['strength'], 'Mandatory')
        self.assertEqual(rules[0]['trigger'], {'type': 'always'})
        rule_ids = [item['id'] for item in rules]
        self.assertIn('smartkit/core-skill-governance', rule_ids)
        self.assertIn('smartkit/core-workspace-policy', rule_ids)
        self.assertNotIn('smartkit/core-skill-config', rule_ids)
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
        self.assertFalse((ROOT / 'rules/cursor/harness-codex.mdc').exists())

    def test_codex_harness_rule_is_session_scoped_and_ordered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            for source in ('startup', 'resume', 'clear', 'compact'):
                with self.subTest(source=source):
                    session = self.run_dispatch(
                        'codex',
                        'session',
                        {'session_id': f'harness-{source}', 'source': source},
                        plugin_data=plugin_data,
                    )
                    context = session['hookSpecificOutput']['additionalContext']
                    self.assertEqual(context.count('Rule-ID: smartkit/harness-codex;'), 1)
                    self.assertLess(
                        context.index('Rule-ID: smartkit/core-rule-config;'),
                        context.index('Rule-ID: smartkit/harness-codex;'),
                    )
                    self.assertLess(
                        context.index('Rule-ID: smartkit/harness-codex;'),
                        context.index('Rule-ID: smartkit/core-personality;'),
                    )
                    self.assertLess(len(context.encode()), 50000)

            prompt = self.run_dispatch(
                'codex',
                'prompt',
                {'session_id': 'harness-prompt', 'prompt': 'hello'},
                plugin_data=plugin_data,
            )
            self.assertNotIn(
                'smartkit/harness-codex',
                prompt['hookSpecificOutput']['additionalContext'],
            )
            copilot = self.run_dispatch(
                'copilot',
                'session',
                {'sessionId': 'harness-copilot'},
                plugin_data=plugin_data,
            )
            self.assertNotIn('smartkit/harness-codex', copilot['additionalContext'])

    def test_codex_compact_session_restores_harness_and_activated_file_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            payload = {
                'session_id': 'codex-compact',
                'prompt': 'Edit src/main.go',
            }
            prompt = self.run_dispatch(
                'codex', 'prompt', payload, plugin_data=plugin_data
            )
            self.assertIn(
                'smartkit/file-go',
                prompt['hookSpecificOutput']['additionalContext'],
            )

            compact = self.run_dispatch(
                'codex',
                'session',
                {'session_id': 'codex-compact', 'source': 'compact'},
                plugin_data=plugin_data,
            )['hookSpecificOutput']['additionalContext']
            self.assertEqual(compact.count('Rule-ID: smartkit/harness-codex;'), 1)
            self.assertIn('smartkit/core-rule-config', compact)
            self.assertIn('smartkit/file-go', compact)

            retry = self.run_dispatch(
                'codex',
                'tool',
                {
                    'session_id': 'codex-compact',
                    'tool_name': 'view_file',
                    'tool_input': {'path': 'src/main.go'},
                },
                plugin_data=plugin_data,
            )
            self.assertEqual(retry, {})

    def test_registry_rejects_invalid_harness_trigger(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'rules/source'
            source.mkdir(parents=True)
            (source / 'core-rule-config.md').write_text('core\n', encoding='utf-8')
            (source / 'harness-bad.md').write_text('bad\n', encoding='utf-8')
            for invalid in ('cursor', 'vscode'):
                with self.subTest(invalid=invalid):
                    (root / 'rules/registry.json').write_text(json.dumps({'rules': [
                        {
                            'id': 'smartkit/core-rule-config',
                            'source': 'source/core-rule-config.md',
                            'strength': 'Mandatory',
                            'trigger': {'type': 'always'},
                        },
                        {
                            'id': 'smartkit/harness-bad',
                            'source': 'source/harness-bad.md',
                            'strength': 'Default',
                            'trigger': {'type': 'harness', 'harnesses': [invalid]},
                        },
                    ]}), encoding='utf-8')
                    environment = dict(os.environ)
                    environment['PLUGIN_ROOT'] = str(root)
                    environment['PLUGIN_DATA'] = str(root / 'data')
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / 'runtime/rules/dispatch.py'),
                            '--harness', 'codex', '--event', 'session',
                        ],
                        input=b'{}',
                        capture_output=True,
                        cwd=ROOT,
                        env=environment,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn('invalid harnesses', result.stderr.decode())

    def test_dispatch_rejects_retired_platform_option(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / 'runtime/rules/dispatch.py'),
                '--platform', 'codex', '--event', 'session',
            ],
            input=b'{}',
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('required: --harness', result.stderr.decode())

    def test_codex_rule_hooks_allow_large_additional_context(self):
        hooks = json.loads((ROOT / 'hooks/hooks.json').read_text(encoding='utf-8'))['hooks']

        for event in ('SessionStart', 'UserPromptSubmit', 'PreToolUse'):
            with self.subTest(event=event):
                handlers = [
                    handler
                    for group in hooks[event]
                    for handler in group['hooks']
                    if 'runtime/rules/dispatch.py' in handler['command']
                ]
                self.assertEqual(len(handlers), 1)
                self.assertEqual(handlers[0]['additionalContextLimit'], 50000)

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
                    '--harness', 'codex', '--event', 'session',
                ],
                input=b'{}',
                capture_output=True,
                cwd=ROOT,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn('invalid file trigger', result.stderr.decode())

    def test_runtime_and_cursor_sync_share_missing_source_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry = root / 'rules/registry.json'
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({
                'rules': [{
                    'id': 'smartkit/core-rule-config',
                    'source': 'source/core-rule-config.md',
                    'strength': 'Mandatory',
                    'trigger': {'type': 'always'},
                }],
            }), encoding='utf-8')

            environment = dict(os.environ)
            environment['PLUGIN_ROOT'] = str(root)
            environment['PLUGIN_DATA'] = str(root / 'data')
            runtime = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'runtime/rules/dispatch.py'),
                    '--harness', 'codex', '--event', 'session',
                ],
                input=b'{}',
                capture_output=True,
                cwd=ROOT,
                env=environment,
                check=False,
            )
            adapter = self.run_adapter_sync(root, '--check')

            self.assertEqual(runtime.returncode, 1)
            self.assertEqual(adapter.returncode, 2)
            expected = 'missing source for smartkit/core-rule-config'
            self.assertIn(expected, runtime.stderr.decode())
            self.assertIn(expected, adapter.stderr.decode())

    def test_cursor_rule_adapter_sync_tracks_rename_and_delete_from_registry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / 'rules/source'
            source.mkdir(parents=True)
            (source / 'core-rule-config.md').write_text('core\n', encoding='utf-8')
            (source / 'file-old.md').write_text('old\n', encoding='utf-8')
            registry = root / 'rules/registry.json'

            def write_registry(rule_id: str | None, filename: str | None) -> None:
                rules = [{
                    'id': 'smartkit/core-rule-config',
                    'source': 'source/core-rule-config.md',
                    'strength': 'Mandatory',
                    'trigger': {'type': 'always'},
                }]
                if rule_id is not None and filename is not None:
                    rules.append({
                        'id': rule_id,
                        'source': f'source/{filename}',
                        'strength': 'Default',
                        'trigger': {'type': 'file', 'include_globs': ['**/*.txt']},
                    })
                registry.write_text(
                    json.dumps({'rules': rules}),
                    encoding='utf-8',
                )

            write_registry('smartkit/file-old', 'file-old.md')
            first = self.run_adapter_sync(root, '--update')
            self.assertEqual(first.returncode, 0, first.stderr.decode())
            self.assertTrue((root / 'rules/cursor/file-old.mdc').is_file())

            (source / 'file-old.md').rename(source / 'file-new.md')
            write_registry('smartkit/file-new', 'file-new.md')
            renamed = self.run_adapter_sync(root, '--update')
            self.assertEqual(renamed.returncode, 0, renamed.stderr.decode())
            self.assertFalse((root / 'rules/cursor/file-old.mdc').exists())
            self.assertTrue((root / 'rules/cursor/file-new.mdc').is_file())

            write_registry(None, None)
            deleted = self.run_adapter_sync(root, '--update')
            self.assertEqual(deleted.returncode, 0, deleted.stderr.decode())
            self.assertFalse((root / 'rules/cursor/file-new.mdc').exists())
            self.assertEqual(self.run_adapter_sync(root, '--check').returncode, 0)

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

    def test_python_rule_activates_for_python_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for extension in ('py', 'pyi'):
                with self.subTest(extension=extension):
                    prompt = self.run_dispatch(
                        'codex',
                        'prompt',
                        {
                            'session_id': f'python-{extension}',
                            'prompt': f'Edit src/service.{extension}',
                        },
                        plugin_data=Path(temp_dir),
                    )

                    context = prompt['hookSpecificOutput']['additionalContext']
                    self.assertIn('smartkit/file-python', context)
                    self.assertNotIn('smartkit/file-go', context)

    def test_hook_delivery_emits_a_visible_host_boundary_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            environment = dict(os.environ)
            environment['PLUGIN_DATA'] = temp_dir
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'runtime/rules/dispatch.py'),
                    '--harness',
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

    def test_tool_without_file_path_skips_rule_and_state_loading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            environment = dict(os.environ)
            environment['PLUGIN_ROOT'] = str(root)
            environment['PLUGIN_DATA'] = str(root / 'data')
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'runtime/rules/dispatch.py'),
                    '--harness',
                    'codex',
                    '--event',
                    'tool',
                ],
                input=json.dumps({
                    'session_id': 'no-path',
                    'tool_name': 'list_agents',
                    'tool_input': {},
                }).encode(),
                capture_output=True,
                cwd=ROOT,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual(json.loads(result.stdout), {})
            self.assertFalse((root / 'data').exists())

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

            state_files = list((plugin_data / 'rule-sessions').iterdir())
            self.assertEqual(len(state_files), 1)
            self.assertRegex(state_files[0].name, r'^[0-9a-f]{64}\.json$')
            self.assertEqual(
                set(json.loads(state_files[0].read_text(encoding='utf-8'))),
                {
                    'activated_file_rule_ids',
                    'context_generation',
                    'restored_generation',
                },
            )

    def test_invalid_session_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            payload = {
                'sessionId': 'invalid-state',
                'transformedPrompt': 'Edit src/main.go',
            }
            self.run_dispatch('copilot', 'prompt', payload, plugin_data=plugin_data)
            state_file, = (plugin_data / 'rule-sessions').iterdir()

            valid_state = json.loads(state_file.read_text(encoding='utf-8'))
            versioned_state = dict(valid_state, version=1)
            boolean_context_generation = dict(valid_state, context_generation=True)
            boolean_restored_generation = dict(valid_state, restored_generation=False)

            for invalid_state in (
                '["smartkit/file-go"]\n',
                '{invalid json',
                json.dumps(versioned_state),
                json.dumps(boolean_context_generation),
                json.dumps(boolean_restored_generation),
            ):
                with self.subTest(invalid_state=invalid_state):
                    state_file.write_text(invalid_state, encoding='utf-8')
                    result = self.run_raw_dispatch(
                        'copilot',
                        'prompt',
                        json.dumps({
                            'sessionId': 'invalid-state',
                            'transformedPrompt': 'Continue',
                        }).encode(),
                        plugin_data=plugin_data,
                    )

                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b'')
                    self.assertIn(b'invalid Rule activation state', result.stderr)

    def test_invalid_hook_payload_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            for payload in (b'{invalid json', b'[]'):
                with self.subTest(payload=payload):
                    result = self.run_raw_dispatch(
                        'codex', 'tool', payload, plugin_data=plugin_data
                    )

                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b'')
                    self.assertIn(b'invalid Hook payload', result.stderr)

    def test_copilot_pre_compact_restores_rules_before_next_tool(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            self.run_dispatch(
                'copilot',
                'prompt',
                {'sessionId': 'compact-tool', 'transformedPrompt': 'Edit src/main.go'},
                plugin_data=plugin_data,
            )

            compact = self.run_dispatch(
                'copilot',
                'compact',
                {'sessionId': 'compact-tool', 'trigger': 'auto'},
                plugin_data=plugin_data,
            )
            self.assertEqual(compact, {})

            payload = {
                'sessionId': 'compact-tool',
                'toolName': 'view',
                'toolArgs': {'path': 'src/main.py'},
            }
            blocked = self.run_dispatch(
                'copilot', 'tool', payload, plugin_data=plugin_data
            )
            self.assertEqual(blocked['permissionDecision'], 'deny')
            reason = blocked['permissionDecisionReason']
            self.assertIn('smartkit/core-rule-config', reason)
            self.assertIn('smartkit/file-go', reason)
            self.assertIn('smartkit/file-python', reason)
            self.assertNotIn('smartkit/harness-codex', reason)

            retry = self.run_dispatch(
                'copilot', 'tool', payload, plugin_data=plugin_data
            )
            self.assertEqual(retry, {})

    def test_copilot_prompt_after_compaction_restores_rules_without_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            self.run_dispatch(
                'copilot',
                'prompt',
                {'sessionId': 'compact-prompt', 'transformedPrompt': 'Edit src/main.go'},
                plugin_data=plugin_data,
            )
            self.run_dispatch(
                'copilot',
                'compact',
                {'sessionId': 'compact-prompt', 'trigger': 'manual'},
                plugin_data=plugin_data,
            )

            restored = self.run_dispatch(
                'copilot',
                'prompt',
                {'sessionId': 'compact-prompt', 'transformedPrompt': 'Continue'},
                plugin_data=plugin_data,
            )['modifiedTransformedPrompt']
            self.assertIn('smartkit/core-rule-config', restored)
            self.assertIn('smartkit/file-go', restored)
            self.assertNotIn('smartkit/harness-codex', restored)
            self.assertTrue(restored.endswith('Continue'))

            tool = self.run_dispatch(
                'copilot',
                'tool',
                {
                    'sessionId': 'compact-prompt',
                    'toolName': 'bash',
                    'toolArgs': {'command': 'pwd'},
                },
                plugin_data=plugin_data,
            )
            self.assertEqual(tool, {})

    def test_copilot_stop_after_compaction_forces_rule_aware_review_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            self.run_dispatch(
                'copilot',
                'prompt',
                {'sessionId': 'compact-stop', 'transformedPrompt': 'Edit src/main.go'},
                plugin_data=plugin_data,
            )
            self.run_dispatch(
                'copilot',
                'compact',
                {'sessionId': 'compact-stop', 'trigger': 'auto'},
                plugin_data=plugin_data,
            )

            blocked = self.run_dispatch(
                'copilot',
                'stop',
                {'sessionId': 'compact-stop', 'stop_hook_active': False},
                plugin_data=plugin_data,
            )
            self.assertEqual(blocked['decision'], 'block')
            self.assertIn('smartkit/core-rule-config', blocked['reason'])
            self.assertIn('smartkit/file-go', blocked['reason'])
            self.assertNotIn('smartkit/harness-codex', blocked['reason'])

            repeated = self.run_dispatch(
                'copilot',
                'stop',
                {'sessionId': 'compact-stop', 'stop_hook_active': True},
                plugin_data=plugin_data,
            )
            self.assertEqual(repeated, {})

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

    def test_copilot_tool_discovery_blocks_once_to_deliver_file_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_data = Path(temp_dir)
            payload = {
                'sessionId': 'copilot-tool-discovery',
                'toolName': 'view',
                'toolArgs': {'path': 'src/main.go'},
            }

            blocked = self.run_dispatch(
                'copilot', 'tool', payload, plugin_data=plugin_data
            )
            self.assertEqual(blocked['permissionDecision'], 'deny')
            self.assertIn('smartkit/file-go', blocked['permissionDecisionReason'])

            retry = self.run_dispatch(
                'copilot', 'tool', payload, plugin_data=plugin_data
            )
            self.assertEqual(retry, {})


if __name__ == '__main__':
    unittest.main()
