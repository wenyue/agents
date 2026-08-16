import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

TIMING_SCRIPT = (
    REPO_ROOT
    / 'skills'
    / 'diagnose-agent-session'
    / 'scripts'
    / 'timing.py'
)


def load_timing_module():
    spec = importlib.util.spec_from_file_location('diagnose_agent_session', TIMING_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load timing script: {TIMING_SCRIPT}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DiagnoseAgentSessionTest(unittest.TestCase):
    def setUp(self):
        self.timing = load_timing_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.codex_home = Path(self.temp_dir.name) / '.codex'
        self.captured_at = datetime(2026, 7, 21, 12, tzinfo=timezone.utc)

    def write_token_count(self, session_id='session-main'):
        path = self.codex_home / 'sessions' / f'rollout-{session_id}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'event_msg',
                'payload': {
                    'type': 'token_count',
                    'info': {
                        'total_token_usage': {
                            'input_tokens': 80,
                            'cached_input_tokens': 20,
                            'cache_write_input_tokens': 0,
                            'output_tokens': 10,
                            'reasoning_output_tokens': 2,
                            'total_tokens': 90,
                        }
                    },
                },
            },
            {
                'timestamp': '2026-07-21T12:00:00Z',
                'type': 'event_msg',
                'payload': {
                    'type': 'token_count',
                    'info': {
                        'total_token_usage': {
                            'input_tokens': 100,
                            'cached_input_tokens': 30,
                            'cache_write_input_tokens': 10,
                            'output_tokens': 20,
                            'reasoning_output_tokens': 5,
                            'total_tokens': 120,
                        }
                    },
                },
            },
        ]
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

    def write_tool_calls(self, session_id='session-main'):
        path = self.codex_home / 'sessions' / f'rollout-{session_id}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call',
                    'call_id': 'spawn-1',
                    'name': 'collaboration.spawn_agent',
                    'input': '{"task_name":"worker"}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:02Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call_output',
                    'call_id': 'spawn-1',
                    'output': '{"agent_id":"agent-1","nickname":"Worker"}',
                },
            },
            {
                'timestamp': '2026-07-21T11:01:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'wait-1',
                    'name': 'wait_agent',
                    'arguments': '{"timeout_ms":300000}',
                },
            },
            {
                'timestamp': '2026-07-21T11:01:03Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'wait-1',
                    'output': '{"status":{"agent-1":{"completed":"done"}},"timed_out":false}',
                },
            },
            {
                'timestamp': '2026-07-21T11:02:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call',
                    'call_id': 'pending-1',
                    'name': 'functions.exec',
                    'input': '{}',
                },
            },
        ]
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

    def write_turn_tokens(self, session_id='session-main'):
        path = self.codex_home / 'sessions' / f'rollout-{session_id}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T10:00:00Z',
                'type': 'event_msg',
                'payload': {
                    'type': 'token_count',
                    'info': {
                        'total_token_usage': {
                            'input_tokens': 100,
                            'cached_input_tokens': 30,
                            'cache_write_input_tokens': 10,
                            'output_tokens': 20,
                            'reasoning_output_tokens': 5,
                        }
                    },
                },
            },
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {'type': 'message', 'role': 'user', 'content': []},
            },
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'event_msg',
                'payload': {'type': 'user_message', 'message': 'redacted'},
            },
            {
                'timestamp': '2026-07-21T12:00:00Z',
                'type': 'event_msg',
                'payload': {
                    'type': 'token_count',
                    'info': {
                        'total_token_usage': {
                            'input_tokens': 160,
                            'cached_input_tokens': 50,
                            'cache_write_input_tokens': 10,
                            'output_tokens': 40,
                            'reasoning_output_tokens': 10,
                        }
                    },
                },
            },
        ]
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

    def write_wait_timeouts_and_failure(self, session_id='session-main'):
        path = self.codex_home / 'sessions' / f'rollout-{session_id}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'spawn-1',
                    'name': 'spawn_agent',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'spawn-1',
                    'output': '{"agent_id":"agent-1"}',
                },
            },
        ]
        for index in (1, 2):
            events.extend(
                [
                    {
                        'timestamp': f'2026-07-21T11:0{index}:00Z',
                        'type': 'response_item',
                        'payload': {
                            'type': 'function_call',
                            'call_id': f'wait-{index}',
                            'name': 'wait_agent',
                            'arguments': '{"targets":["agent-1"],"timeout_ms":300000}',
                        },
                    },
                    {
                        'timestamp': f'2026-07-21T11:0{index}:30Z',
                        'type': 'response_item',
                        'payload': {
                            'type': 'function_call_output',
                            'call_id': f'wait-{index}',
                            'output': '{"status":{},"timed_out":true}',
                        },
                    },
                ]
            )
        events.extend(
            [
                {
                    'timestamp': '2026-07-21T11:03:00Z',
                    'type': 'response_item',
                    'payload': {
                        'type': 'function_call',
                        'call_id': 'shell-1',
                        'name': 'shell_command',
                        'arguments': '{}',
                    },
                },
                {
                    'timestamp': '2026-07-21T11:03:01Z',
                    'type': 'response_item',
                    'payload': {
                        'type': 'function_call_output',
                        'call_id': 'shell-1',
                        'output': 'Script failed\nExit code: 1',
                    },
                },
            ]
        )
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

    def usage_row(self):
        return {
            'client': 'codex',
            'sessionId': 'rollout-session-main',
            'provider': 'openai',
            'model': 'gpt-test',
            'input': 60,
            'cacheRead': 30,
            'cacheWrite': 10,
            'output': 15,
            'reasoning': 5,
            'messageCount': 2,
            'cost': 0.25,
            'performance': {
                'totalDurationMs': 2000,
                'timedTokens': 120,
                'sampleCount': 2,
            },
        }

    def test_parser_exposes_only_diagnose_command(self):
        parser = self.timing.build_parser()
        command_choices = next(
            action.choices
            for action in parser._actions
            if isinstance(getattr(action, 'choices', None), dict)
        )
        self.assertEqual(set(command_choices), {'diagnose'})

        args = parser.parse_args(
            ['diagnose', '--client', 'codex', '--session-id', 'session-main']
        )

        self.assertEqual(args.command, 'diagnose')
        self.assertEqual(args.client, 'codex')
        self.assertEqual(args.session_id, 'session-main')
        self.assertEqual(args.scope, 'both')

    def test_public_job_supports_python_3_10(self):
        ast.parse(TIMING_SCRIPT.read_text(encoding='utf-8'), feature_version=(3, 10))
        public_files = [
            TIMING_SCRIPT,
            TIMING_SCRIPT.with_name('task-metrics.ps1'),
            TIMING_SCRIPT.with_name('task-metrics.sh'),
            REPO_ROOT / 'skills' / 'diagnose-agent-session' / 'SKILL.md',
            REPO_ROOT
            / 'docs'
            / 'zh-CN'
            / 'skills'
            / 'diagnose-agent-session'
            / 'SKILL.md',
        ]
        for path in public_files:
            text = path.read_text(encoding='utf-8')
            self.assertIn('3.10', text, path)
            self.assertNotIn('3.11', text, path)

    def test_windows_resolves_tokscale_cmd_for_python_subprocess(self):
        resolved = self.timing.tokscale_executable(
            os_name='nt',
            which=lambda name: 'C:/npm/tokscale.cmd' if name == 'tokscale.cmd' else None,
        )

        self.assertEqual(resolved, 'C:/npm/tokscale.cmd')

    def test_tokscale_snapshot_supports_non_codex_client_without_date_bounds(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return self.timing.subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({'entries': []}),
                stderr='',
            )

        result = self.timing.capture_tokscale_snapshot(
            'claude', None, None, runner=runner
        )

        self.assertEqual(result, [])
        self.assertIn('claude', calls[0][0])
        self.assertNotIn('--since', calls[0][0])
        self.assertNotIn('--until', calls[0][0])

    def test_reads_latest_codex_token_totals_without_message_content(self):
        self.write_token_count()

        result = self.timing.read_codex_token_totals('session-main', self.codex_home)

        self.assertEqual(
            result,
            {
                'input': 60,
                'cache_read': 30,
                'cache_write': 10,
                'output': 15,
                'reasoning': 5,
                'total_tokens': 120,
            },
        )

    def test_codex_session_bounds_cover_the_complete_log(self):
        self.write_token_count()

        result = self.timing.codex_session_bounds('session-main', self.codex_home)

        self.assertEqual(
            result,
            (
                datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
                datetime(2026, 7, 21, 12, tzinfo=timezone.utc),
            ),
        )

    def test_session_usage_prefers_tokscale_cost_when_available(self):
        result = self.timing.build_session_usage(
            'codex',
            'session-main',
            self.captured_at,
            tokscale_rows=[self.usage_row()],
            codex_home=self.codex_home,
        )

        self.assertEqual(result['status'], 'available')
        self.assertEqual(result['source'], 'tokscale')
        self.assertEqual(result['cost_status'], 'available')
        self.assertEqual(result['totals']['total_tokens'], 120)
        self.assertEqual(result['totals']['cost'], 0.25)
        self.assertEqual(result['totals']['message_count'], 2)
        self.assertEqual(result['totals']['model_activity_ms'], 2000)

    def test_session_usage_falls_back_to_tokens_when_tokscale_fails(self):
        self.write_token_count()

        result = self.timing.build_session_usage(
            'codex',
            'session-main',
            self.captured_at,
            tokscale_rows=[],
            snapshot_error='Tokscale timed out.',
            codex_home=self.codex_home,
        )

        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['source'], 'codex-log')
        self.assertEqual(result['cost_status'], 'unavailable')
        self.assertEqual(result['totals']['total_tokens'], 120)
        self.assertIn('Tokscale timed out.', result['warnings'])
        report = self.timing.build_diagnostic_report(
            result,
            self.timing.unavailable_tool_activity('unavailable'),
            None,
            selected_scope='session',
        )
        self.assertEqual(report['scopes'][0]['tokens']['status'], 'partial')
        self.assertEqual(report['scopes'][0]['cost'], 'unavailable')
        self.assertEqual(report['problems'], ['Tokscale timed out.', 'unavailable'])

    def test_tool_diagnostics_pair_calls_and_report_coordination(self):
        self.write_tool_calls()

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['completed_calls'], 2)
        self.assertEqual(result['incomplete_calls'], 1)
        self.assertEqual(result['observed_duration_ms'], 5000)
        self.assertEqual(result['coordination']['spawn_agent'], 1)
        self.assertEqual(result['coordination']['wait_agent'], 1)
        self.assertEqual(result['findings'], ['incomplete-tool-calls'])
        self.assertEqual(result['coordination']['spawn_successes'], 1)
        self.assertEqual(result['coordination']['completed_agents'], 1)
        self.assertEqual(result['coordination']['observed_peak_live_agents'], 1)
        self.assertEqual(
            result['tools'],
            [
                {
                    'name': 'exec',
                    'started': 1,
                    'completed': 0,
                    'failed': 0,
                    'incomplete': 1,
                    'duration_ms': 0,
                    'longest_ms': 0,
                },
                {
                    'name': 'spawn_agent',
                    'started': 1,
                    'completed': 1,
                    'failed': 0,
                    'incomplete': 0,
                    'duration_ms': 2000,
                    'longest_ms': 2000,
                },
                {
                    'name': 'wait_agent',
                    'started': 1,
                    'completed': 1,
                    'failed': 0,
                    'incomplete': 0,
                    'duration_ms': 3000,
                    'longest_ms': 3000,
                },
            ],
        )

    def test_spawn_aliases_reconcile_wait_and_list_identities(self):
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'spawn-1',
                    'name': 'spawn_agent',
                    'arguments': '{"task_name":"worker"}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'spawn-1',
                    'output': '{"agent_id":"uuid-1","task_name":"/root/worker"}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:02Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'wait-1',
                    'name': 'wait_agent',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:03Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'wait-1',
                    'output': '{"status":{"uuid-1":{"completed":"done"}},"timed_out":false}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:04Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'list-1',
                    'name': 'list_agents',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:05Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'list-1',
                    'output': '{"agents":[{"agent_name":"/root/worker","agent_status":{"completed":"done"}}]}',
                },
            },
        ]
        path = self.codex_home / 'sessions' / 'rollout-task-name-session.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8'
        )

        result = self.timing.analyze_codex_tool_activity(
            'task-name-session', self.codex_home
        )

        self.assertEqual(result['coordination']['spawn_successes'], 1)
        self.assertEqual(result['coordination']['completed_agents'], 1)
        self.assertEqual(result['coordination']['observed_peak_live_agents'], 1)
        self.assertEqual(result['coordination']['observed_live_agents_at_end'], 0)

    def test_current_turn_uses_latest_user_boundary_and_cumulative_delta(self):
        self.write_turn_tokens()

        bounds = self.timing.codex_current_turn_bounds(
            'session-main', self.codex_home
        )
        usage = self.timing.build_codex_turn_usage(
            'session-main', self.captured_at, bounds, self.codex_home
        )

        self.assertEqual(
            bounds,
            (
                datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
                datetime(2026, 7, 21, 12, tzinfo=timezone.utc),
            ),
        )
        self.assertEqual(
            usage['totals'],
            {
                'input': 40,
                'output': 15,
                'reasoning': 5,
                'cache_read': 20,
                'cache_write': 0,
                'total_tokens': 80,
                'cost': 0.0,
                'message_count': 0,
                'model_activity_ms': 0,
            },
        )

    def test_tool_failures_and_wait_timeouts_are_distinct_evidence(self):
        self.write_wait_timeouts_and_failure()

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['failed_calls'], 1)
        self.assertEqual(result['repeated_identical_calls'], 1)
        self.assertEqual(result['coordination']['wait_timeouts'], 2)
        self.assertEqual(result['coordination']['max_consecutive_wait_timeouts'], 2)
        self.assertEqual(result['coordination']['wait_without_observed_live_agent'], 0)
        self.assertIn('failed-tool-calls', result['findings'])

    def test_current_turn_inherits_observed_live_agent_from_prior_turn(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T10:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'spawn-1',
                    'name': 'spawn_agent',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T10:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'spawn-1',
                    'output': '{"agent_id":"agent-1"}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'event_msg',
                'payload': {'type': 'user_message'},
            },
            {
                'timestamp': '2026-07-21T11:01:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'wait-1',
                    'name': 'wait_agent',
                    'arguments': '{"targets":["agent-1"]}',
                },
            },
            {
                'timestamp': '2026-07-21T11:01:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'wait-1',
                    'output': '{"status":{"agent-1":{"completed":"done"}},"timed_out":false}',
                },
            },
        ]
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

        result = self.timing.analyze_codex_tool_activity(
            'session-main',
            self.codex_home,
            datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
            datetime(2026, 7, 21, 12, tzinfo=timezone.utc),
        )

        self.assertEqual(result['coordination']['wait_without_observed_live_agent'], 0)
        self.assertEqual(result['coordination']['observed_peak_live_agents'], 1)
        self.assertEqual(result['coordination']['completed_agents'], 1)

    def test_diagnostic_wrapper_does_not_report_itself_as_incomplete(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call',
                    'call_id': 'diagnose-1',
                    'name': 'exec',
                    'input': 'powershell -ExecutionPolicy Bypass -File .agents/skills/diagnose-agent-session/scripts/task-metrics.ps1 diagnose --scope both',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call',
                    'call_id': 'diagnose-2',
                    'name': 'exec',
                    'input': 'const r = await tools.shell_command({command:"sh ./skills/diagnose-agent-session/scripts/task-metrics.sh diagnose --scope both"}); text(r);',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:02Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call',
                    'call_id': 'diagnose-3',
                    'name': 'exec',
                    'input': 'const r = await tools.shell_command({"command":"powershell.exe -File ./skills/diagnose-agent-session/scripts/task-metrics.ps1 diagnose --scope both"}); text(r);',
                },
            },
        ]
        path.write_text(
            '\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8'
        )

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['started_calls'], 0)
        self.assertEqual(result['incomplete_calls'], 0)

    def test_inspecting_diagnostic_files_remains_visible(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call',
                    'call_id': 'inspect-1',
                    'name': 'exec',
                    'input': 'const r = await tools.shell_command({command:"rg \'powershell.exe -File skills/diagnose-agent-session/scripts/task-metrics.ps1 diagnose\' ."}); text(r);',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call_output',
                    'call_id': 'inspect-1',
                    'output': 'ok',
                },
            },
        ]
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['started_calls'], 1)
        self.assertEqual(result['completed_calls'], 1)

    def test_list_agents_updates_observed_lifecycle_lower_bounds(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T10:59:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'spawn-1',
                    'name': 'spawn_agent',
                    'arguments': '{"task_name":"worker"}',
                },
            },
            {
                'timestamp': '2026-07-21T10:59:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'spawn-1',
                    'output': '{"task_name":"/root/worker"}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'list-1',
                    'name': 'list_agents',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'list-1',
                    'output': json.dumps(
                        {
                            'agents': [
                                {
                                    'agent_name': '/root',
                                    'agent_status': {'running': 'root'},
                                },
                                {
                                    'agent_name': '/root/worker',
                                    'agent_status': {'running': 'working'},
                                },
                                {
                                    'agent_name': '/root/done',
                                    'agent_status': {'completed': 'done'},
                                },
                                {
                                    'agent_name': '/root/failed',
                                    'agent_status': {'failed': 'boom'},
                                },
                            ]
                        }
                    ),
                },
            },
            {
                'timestamp': '2026-07-21T11:00:02Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'list-2',
                    'name': 'list_agents',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:03Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'list-2',
                    'output': json.dumps(
                        {
                            'agents': [
                                {
                                    'agent_name': '/root',
                                    'agent_status': {'running': 'root'},
                                },
                                {
                                    'agent_name': '/root/worker',
                                    'agent_status': {'completed': 'done'},
                                },
                                {
                                    'agent_name': '/root/done',
                                    'agent_status': {'completed': 'done'},
                                },
                                {
                                    'agent_name': '/root/failed',
                                    'agent_status': {'failed': 'boom'},
                                },
                            ]
                        }
                    ),
                },
            },
            {
                'timestamp': '2026-07-21T11:01:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'wait-1',
                    'name': 'wait_agent',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:01:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'wait-1',
                    'output': '{"status":{},"timed_out":true}',
                },
            },
        ]
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['coordination']['observed_peak_live_agents'], 1)
        self.assertEqual(result['coordination']['completed_agents'], 2)
        self.assertEqual(result['coordination']['failed_agents'], 1)
        self.assertEqual(result['coordination']['observed_live_agents_at_end'], 0)
        self.assertEqual(result['coordination']['wait_without_observed_live_agent'], 1)

    def test_list_snapshot_clears_disappeared_spawned_agent(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'spawn-1',
                    'name': 'spawn_agent',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'spawn-1',
                    'output': '{"task_name":"/root/worker"}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:02Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'list-1',
                    'name': 'list_agents',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:03Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'list-1',
                    'output': '{"agents":[{"agent_name":"/root","agent_status":{"running":"root"}}]}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:04Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'wait-1',
                    'name': 'wait_agent',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:05Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'wait-1',
                    'output': '{"status":{},"timed_out":true}',
                },
            },
        ]
        path.write_text(
            '\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8'
        )

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['coordination']['observed_peak_live_agents'], 1)
        self.assertEqual(result['coordination']['observed_live_agents_at_end'], 0)
        self.assertEqual(result['coordination']['wait_without_observed_live_agent'], 1)

    def test_terminal_agent_counts_union_wait_and_list_identities(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'wait-1',
                    'name': 'wait_agent',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'wait-1',
                    'output': json.dumps(
                        {
                            'status': {
                                '/root/wait-done': {'completed': 'done'},
                                '/root/wait-failed': {'failed': 'boom'},
                            },
                            'timed_out': False,
                        }
                    ),
                },
            },
            {
                'timestamp': '2026-07-21T11:00:02Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call',
                    'call_id': 'list-1',
                    'name': 'list_agents',
                    'arguments': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:03Z',
                'type': 'response_item',
                'payload': {
                    'type': 'function_call_output',
                    'call_id': 'list-1',
                    'output': json.dumps(
                        {
                            'agents': [
                                {
                                    'agent_name': '/root/wait-done',
                                    'agent_status': {'completed': 'done'},
                                },
                                {
                                    'agent_name': '/root/wait-failed',
                                    'agent_status': {'failed': 'boom'},
                                },
                                {
                                    'agent_name': '/root/list-done',
                                    'agent_status': {'completed': 'done'},
                                },
                                {
                                    'agent_name': '/root/list-failed',
                                    'agent_status': {'failed': 'boom'},
                                },
                            ]
                        }
                    ),
                },
            },
        ]
        path.write_text(
            '\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8'
        )

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['coordination']['completed_agents'], 2)
        self.assertEqual(result['coordination']['failed_agents'], 2)

    def test_current_turn_timeout_streak_excludes_prior_turns(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = []
        for index, minute in enumerate((0, 1), start=1):
            events.extend(
                [
                    {
                        'timestamp': f'2026-07-21T10:0{minute}:00Z',
                        'type': 'response_item',
                        'payload': {
                            'type': 'function_call',
                            'call_id': f'wait-{index}',
                            'name': 'wait_agent',
                            'arguments': '{}',
                        },
                    },
                    {
                        'timestamp': f'2026-07-21T10:0{minute}:01Z',
                        'type': 'response_item',
                        'payload': {
                            'type': 'function_call_output',
                            'call_id': f'wait-{index}',
                            'output': '{"status":{},"timed_out":true}',
                        },
                    },
                ]
            )
        events.append(
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'event_msg',
                'payload': {'type': 'user_message'},
            }
        )
        path.write_text(
            '\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8'
        )

        result = self.timing.analyze_codex_tool_activity(
            'session-main',
            self.codex_home,
            datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
            datetime(2026, 7, 21, 12, tzinfo=timezone.utc),
        )

        self.assertEqual(result['coordination']['wait_agent'], 0)
        self.assertEqual(result['coordination']['wait_timeouts'], 0)
        self.assertEqual(result['coordination']['max_consecutive_wait_timeouts'], 0)

    def test_structured_tool_error_is_counted_without_persisting_output(self):
        path = self.codex_home / 'sessions' / 'rollout-session-main.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {
                'timestamp': '2026-07-21T11:00:00Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call',
                    'call_id': 'exec-1',
                    'name': 'exec',
                    'input': '{}',
                },
            },
            {
                'timestamp': '2026-07-21T11:00:01Z',
                'type': 'response_item',
                'payload': {
                    'type': 'custom_tool_call_output',
                    'call_id': 'exec-1',
                    'output': [{'type': 'text', 'text': 'Script error:\nExit code: 1'}],
                },
            },
        ]
        path.write_text('\n'.join(json.dumps(event) for event in events) + '\n', encoding='utf-8')

        result = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )

        self.assertEqual(result['failed_calls'], 1)
        self.assertNotIn('Script error', json.dumps(result))

    def test_diagnostic_output_keeps_usage_and_tool_evidence_separate(self):
        usage = self.timing.build_session_usage(
            'codex',
            'session-main',
            self.captured_at,
            tokscale_rows=[self.usage_row()],
            codex_home=self.codex_home,
        )
        self.write_tool_calls()
        activity = self.timing.analyze_codex_tool_activity(
            'session-main', self.codex_home
        )
        report = self.timing.build_diagnostic_report(
            usage,
            activity,
            (
                datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
                datetime(2026, 7, 21, 12, tzinfo=timezone.utc),
            ),
            selected_scope='session',
        )

        rendered = self.timing.render_diagnostic_markdown(report)

        self.assertIn('### Agent Session Diagnostics', rendered)
        self.assertIn('120 total', rendered)
        self.assertIn('spawn_agent=1', rendered)
        self.assertIn('wait_agent=1', rendered)
        self.assertIn('whole session: incomplete-tool-calls', rendered)

    def test_session_usage_is_unavailable_only_when_both_sources_fail(self):
        result = self.timing.build_session_usage(
            'codex',
            'missing-session',
            self.captured_at,
            tokscale_rows=[],
            snapshot_error='Tokscale executable was not found.',
            codex_home=self.codex_home,
        )

        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['cost_status'], 'unavailable')
        self.assertEqual(result['totals']['total_tokens'], 0)

    def test_non_codex_missing_session_reports_only_tokscale_problem(self):
        result = self.timing.build_session_usage(
            'claude',
            'missing-session',
            self.captured_at,
            tokscale_rows=[],
        )

        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(
            result['warnings'], ['No matching Tokscale session row was found.']
        )


if __name__ == '__main__':
    unittest.main()
