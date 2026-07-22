import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


TIMING_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / 'wenyue_agents'
    / 'agents'
    / 'skills'
    / 'report-session-usage'
    / 'scripts'
    / 'timing.py'
)


def load_timing_module():
    spec = importlib.util.spec_from_file_location('report_session_usage', TIMING_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load timing script: {TIMING_SCRIPT}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReportSessionUsageTest(unittest.TestCase):
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

    def test_parser_exposes_only_usage_command(self):
        parser = self.timing.build_parser()
        command_choices = next(
            action.choices
            for action in parser._actions
            if isinstance(getattr(action, 'choices', None), dict)
        )
        self.assertEqual(set(command_choices), {'usage'})

        args = parser.parse_args(
            ['usage', '--client', 'codex', '--session-id', 'session-main']
        )

        self.assertEqual(args.command, 'usage')
        self.assertEqual(args.client, 'codex')
        self.assertEqual(args.session_id, 'session-main')

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
        self.assertEqual(
            self.timing.build_session_reply(result),
            {
                'scope': 'whole session',
                'tokens': {
                    'status': 'available',
                    'input': 60,
                    'cache_read': 30,
                    'cache_write': 10,
                    'output': 15,
                    'reasoning': 5,
                    'total': 120,
                },
                'cost': '$0.250000 USD',
                'problems': [],
            },
        )

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
        reply = self.timing.build_session_reply(result)
        self.assertEqual(reply['tokens']['status'], 'partial')
        self.assertEqual(reply['cost'], 'unavailable')
        self.assertEqual(reply['problems'], ['Tokscale timed out.'])

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
