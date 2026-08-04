"""Contracts for recommended-tool policies and non-mutating Hooks."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT / 'runtime' / 'recommended-tools'
    / 'check_recommended_tools.py'
)
MAINTAINER_PATH = (
    REPO_ROOT / 'runtime' / 'recommended-tools'
    / 'maintain_recommended_tools.py'
)
POLICY_ROOT = REPO_ROOT / 'policies' / 'recommended-tools'
RECOMMENDED_TOOL_POLICIES = POLICY_ROOT


def load_checker():
    spec = importlib.util.spec_from_file_location('task8_check_recommended_tools', CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load checker: {CHECKER_PATH}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_recommended_tool_checker_module():
    return load_checker()


def load_maintainer():
    spec = importlib.util.spec_from_file_location('task8_maintain_recommended_tools', MAINTAINER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load maintainer: {MAINTAINER_PATH}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RecommendedToolPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load_checker()

    def test_plugin_policies_are_centralized_and_codex_checks_only_effective_multi_agent(self):
        expected = {
            'codex': {'codex', 'superpowers', 'codegraph', 'tokscale'},
            'cursor': {'cursor-agent', 'superpowers', 'codegraph', 'tokscale'},
            'copilot': {'copilot', 'superpowers', 'codegraph', 'tokscale'},
        }
        for platform, tool_ids in expected.items():
            with self.subTest(platform=platform):
                policy = json.loads((POLICY_ROOT / f'{platform}.json').read_text(encoding='utf-8'))
                self.assertEqual(policy['platform'], platform)
                self.assertEqual({tool['id'] for tool in policy['tools']}, tool_ids)
                self.assertNotIn('hooks', json.dumps(policy).lower())
                self.assertEqual(
                    [item['id'] for item in policy.get('required_values', [])],
                    ['multi_agent'] if platform == 'codex' else [],
                )

    def test_default_policy_path_resolves_plugin_root_policy(self):
        self.assertEqual(
            self.checker.default_policy_path('codex'),
            POLICY_ROOT / 'codex.json',
        )

    def test_hook_mode_does_not_call_maintenance_runner(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            policy = Path(temp_dir) / 'codex.json'
            policy.write_text('{"platform": "codex", "tools": []}\n', encoding='utf-8')
            maintenance_runner = mock.Mock(side_effect=AssertionError('Hooks must not mutate tools'))
            with mock.patch.object(self.checker, 'check_policy', return_value=[]):
                with mock.patch.object(self.checker.subprocess, 'run', maintenance_runner):
                    result = self.checker.run_hook(
                        'codex', policy, policy.parent / 'cache', datetime(2026, 8, 4), force=True,
                    )
            self.assertTrue(result.ran)
            maintenance_runner.assert_not_called()


class RecommendedToolCheckerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load_recommended_tool_checker_module()

    def test_version_comparison_is_strict_and_suffix_tolerant(self):
        cases = (
            ('0.144.4', '0.144.0', True),
            ('0.144.0', '0.144.0', False),
            ('0.143.99', '0.144.0', False),
            ('2026.01.28-fd13201', '2026.01.27', True),
            ('1.0.59+build.7', '1.0.58', True),
            ('6.0.0-rc.1', '6.0.0', False),
        )
        for installed, target, expected in cases:
            with self.subTest(installed=installed, target=target):
                self.assertIs(
                    self.checker.is_strictly_greater(installed, target),
                    expected,
                )
        with self.assertRaises(ValueError):
            self.checker.parse_version('unknown')

    def test_platform_policies_keep_all_thresholds_out_of_python(self):
        policies = RECOMMENDED_TOOL_POLICIES
        expected = {
            'codex': {
                'codex': '0.144.0',
                'superpowers': '6.1.1',
                'codegraph': '1.4.1',
                'tokscale': '4.6.1',
            },
            'cursor': {
                'cursor-agent': '2026.01.27',
                'superpowers': '6.1.1',
                'codegraph': '1.4.1',
                'tokscale': '4.6.1',
            },
            'copilot': {
                'copilot': '1.0.58',
                'superpowers': '6.1.1',
                'codegraph': '1.4.1',
                'tokscale': '4.6.1',
            },
        }
        for platform, targets in expected.items():
            policy = json.loads((policies / f'{platform}.json').read_text(encoding='utf-8'))
            self.assertEqual(policy['platform'], platform)
            self.assertEqual(
                {tool['id']: tool['target_version'] for tool in policy['tools']},
                targets,
            )
        codex_policy = json.loads((policies / 'codex.json').read_text(encoding='utf-8'))
        self.assertEqual(
            [requirement['id'] for requirement in codex_policy['required_values']],
            ['multi_agent'],
        )
        self.assertEqual(codex_policy['required_values'][0]['expected'], 'true')

    def test_superpowers_policies_use_platform_plugin_installation_state_only(self):
        expected_detectors = {
            'codex': [
                {
                    'kind': 'json-command-item',
                    'command': [
                        'codex',
                        'plugin',
                        'list',
                        '--marketplace',
                        'openai-curated',
                        '--json',
                    ],
                    'items_path': 'installed',
                    'match_path': 'pluginId',
                    'match_value': 'superpowers@openai-curated',
                    'value_path': 'version',
                }
            ],
            'cursor': [
                {
                    'kind': 'json-manifest-glob',
                    'glob': (
                        '{home}/.cursor/plugins/cache/*/superpowers/*/'
                        '.cursor-plugin/plugin.json'
                    ),
                    'json_path': 'version',
                }
            ],
            'copilot': [
                {
                    'kind': 'command-regex',
                    'command': ['copilot', 'plugin', 'list'],
                    'pattern': 'superpowers@[^ ]+ \\(v([0-9]+(?:\\.[0-9]+)+)\\)',
                }
            ],
        }

        actual_detectors = {}
        for platform, expected in expected_detectors.items():
            with self.subTest(platform=platform):
                policy = json.loads(
                    (POLICY_ROOT / f'{platform}.json').read_text(encoding='utf-8')
                )
                superpowers = next(tool for tool in policy['tools'] if tool['id'] == 'superpowers')
                actual_detectors[platform] = superpowers['detectors']
                self.assertEqual(superpowers['detectors'], expected)

        serialized = json.dumps(actual_detectors)
        self.assertNotIn('.codex/superpowers', serialized)
        self.assertNotIn('.cache/copilot/marketplaces', serialized)
        self.assertNotIn('.copilot/installed-plugins', serialized)

    def test_policy_guidance_describes_actions_without_exposing_commands(self):
        forbidden = (
            'npm install',
            'codex plugin add',
            'copilot plugin install',
            'copilot plugin update',
            'copilot update',
            'agent update',
            'codegraph upgrade',
        )
        for policy_path in sorted(POLICY_ROOT.glob('*.json')):
            policy = json.loads(policy_path.read_text(encoding='utf-8'))
            for tool in policy['tools']:
                guidance = f'{tool["install"]}\n{tool["upgrade"]}'.lower()
                for command in forbidden:
                    with self.subTest(
                        platform=policy['platform'],
                        tool=tool['id'],
                        command=command,
                    ):
                        self.assertNotIn(command, guidance)

    def test_command_manifest_and_json_item_detectors_are_data_driven(self):
        checker = self.checker
        command_detector = {
            'kind': 'command-regex',
            'command': ['example', '--version'],
            'pattern': r'version ([0-9.]+)',
        }
        process = mock.Mock()
        process.stdout = io.BytesIO(b'example version 2.4.1\n')
        process.wait.return_value = 0
        with mock.patch.object(checker.subprocess, 'Popen', return_value=process) as popen:
            self.assertEqual(checker.run_detector(command_detector), '2.4.1')
        popen.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)
        self.assertIs(popen.call_args.kwargs['stderr'], checker.subprocess.STDOUT)

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / 'plugin.json'
            manifest.write_text('{"metadata": {"version": "6.1.1"}}\n', encoding='utf-8')
            detector = {
                'kind': 'json-manifest-glob',
                'glob': str(manifest),
                'json_path': 'metadata.version',
            }
            self.assertEqual(checker.run_detector(detector), '6.1.1')

        installed_plugins = {
            'installed': [
                {
                    'pluginId': 'superpowers@openai-curated',
                    'version': '6.2.0',
                    'installed': True,
                }
            ]
        }
        json_process = mock.Mock()
        json_process.stdout = io.BytesIO(
            b'WARNING: unable to create PATH aliases\n'
            + json.dumps(installed_plugins).encode('utf-8')
        )
        json_process.wait.return_value = 0
        detector = {
            'kind': 'json-command-item',
            'command': ['codex', 'plugin', 'list', '--json'],
            'items_path': 'installed',
            'match_path': 'pluginId',
            'match_value': 'superpowers@openai-curated',
            'value_path': 'version',
        }
        with mock.patch.object(checker.subprocess, 'Popen', return_value=json_process):
            self.assertEqual(checker.run_detector(detector), '6.2.0')

        installed_plugins['installed'][0]['pluginId'] = 'github@openai-curated'
        missing_process = mock.Mock()
        missing_process.stdout = io.BytesIO(json.dumps(installed_plugins).encode('utf-8'))
        missing_process.wait.return_value = 0
        with mock.patch.object(checker.subprocess, 'Popen', return_value=missing_process):
            self.assertIsNone(checker.run_detector(detector))

    def test_command_detector_resolves_path_entry_before_python_subprocess(self):
        checker = self.checker
        process = mock.Mock()
        process.stdout = io.BytesIO(b'example version 2.4.1\n')
        process.wait.return_value = 0
        resolved = 'C:/npm/example.cmd'

        with mock.patch.object(shutil, 'which', return_value=resolved) as which:
            with mock.patch.object(checker.subprocess, 'Popen', return_value=process) as popen:
                self.assertEqual(
                    checker._run_command(['example', '--version'], 5),
                    'example version 2.4.1\n',
                )

        which.assert_called_once_with('example')
        self.assertEqual(popen.call_args.args[0], [resolved, '--version'])

    def test_policy_findings_distinguish_missing_equal_and_unreadable(self):
        policy = {
            'platform': 'test',
            'tools': [
                {
                    'id': 'missing',
                    'name': 'Missing Tool',
                    'target_version': '1.0.0',
                    'comparison': '>',
                    'detectors': [{'kind': 'command-regex', 'command': ['missing']}],
                    'install': 'install missing',
                    'upgrade': 'upgrade missing',
                },
                {
                    'id': 'equal',
                    'name': 'Equal Tool',
                    'target_version': '2.0.0',
                    'comparison': '>',
                    'detectors': [{'kind': 'fixed', 'value': '2.0.0'}],
                    'install': 'install equal',
                    'upgrade': 'upgrade equal',
                },
                {
                    'id': 'bad',
                    'name': 'Bad Tool',
                    'target_version': '3.0.0',
                    'comparison': '>',
                    'detectors': [{'kind': 'fixed', 'value': 'unknown'}],
                    'install': 'install bad',
                    'upgrade': 'upgrade bad',
                },
            ],
        }

        findings = self.checker.check_policy(policy)

        self.assertEqual(
            [finding.code for finding in findings],
            ['tool-missing', 'version-not-greater', 'version-unreadable'],
        )
        self.assertEqual(
            [(finding.code, finding.tool, finding.guidance) for finding in findings],
            [
                ('tool-missing', 'Missing Tool', 'install missing'),
                ('version-not-greater', 'Equal Tool', 'upgrade equal'),
                ('version-unreadable', 'Bad Tool', 'upgrade bad'),
            ],
        )

    def test_policy_checks_required_effective_values(self):
        checker = self.checker
        base_requirement = {
            'id': 'multi_agent',
            'name': 'Codex multi-agent',
            'expected': 'true',
            'guidance': 'Enable multi-agent and start a new session.',
        }

        matching = checker.check_policy(
            {
                'platform': 'codex',
                'tools': [],
                'required_values': [
                    {
                        **base_requirement,
                        'detectors': [{'kind': 'fixed', 'value': 'true'}],
                    }
                ],
            }
        )
        mismatching = checker.check_policy(
            {
                'platform': 'codex',
                'tools': [],
                'required_values': [
                    {
                        **base_requirement,
                        'detectors': [{'kind': 'fixed', 'value': 'false'}],
                    }
                ],
            }
        )

        self.assertEqual(matching, [])
        self.assertEqual(len(mismatching), 1)
        self.assertEqual(mismatching[0].code, 'required-value-mismatch')
        self.assertEqual(
            mismatching[0].message,
            'is false; it must be true for this project',
        )

    def test_detector_timeout_is_retryable_and_equal_differs_from_lower(self):
        checker = self.checker
        tool = {
            'id': 'example',
            'name': 'Example Tool',
            'target_version': '2.0.0',
            'comparison': '>',
            'detectors': [{'kind': 'command-regex', 'command': ['example']}],
            'install': 'install it',
            'upgrade': 'upgrade it',
        }
        timed_out_process = mock.Mock()
        timed_out_process.stdout = io.BytesIO(b'')
        timed_out_process.wait.side_effect = (
            checker.subprocess.TimeoutExpired(['example'], 5),
            1,
        )
        with mock.patch.object(
            checker.subprocess,
            'Popen',
            return_value=timed_out_process,
        ):
            timeout = checker.check_policy({'platform': 'test', 'tools': [tool]})
        equal = checker.check_policy(
            {
                'platform': 'test',
                'tools': [{**tool, 'detectors': [{'kind': 'fixed', 'value': '2.0.0'}]}],
            }
        )
        lower = checker.check_policy(
            {
                'platform': 'test',
                'tools': [{**tool, 'detectors': [{'kind': 'fixed', 'value': '1.9.9'}]}],
            }
        )

        self.assertEqual(timeout[0].code, 'detector-error')
        self.assertEqual(equal[0].code, 'version-not-greater')
        self.assertEqual(lower[0].code, 'version-not-greater')

    def test_command_detector_terminates_when_output_exceeds_limit(self):
        checker = self.checker
        process = mock.Mock()
        process.stdout = io.BytesIO(b'x' * (checker._MAX_COMMAND_OUTPUT + 1))
        process.wait.return_value = 0
        with mock.patch.object(checker.subprocess, 'Popen', return_value=process):
            with self.assertRaises(checker.DetectorError):
                checker.run_detector(
                    {
                        'kind': 'command-regex',
                        'command': ['example', '--version'],
                    }
                )

        process.kill.assert_called()

    def test_daily_state_is_independent_per_project_and_platform(self):
        checker = self.checker
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache = root / 'cache'
            first_project = root / 'first-project'
            second_project = root / 'second-project'
            first_project.mkdir()
            second_project.mkdir()
            codex_policy = first_project / 'codex.json'
            other_codex_policy = second_project / 'codex.json'
            cursor_policy = first_project / 'cursor.json'
            codex_policy.write_text('{"platform":"codex","tools":[]}\n', encoding='utf-8')
            other_codex_policy.write_text(
                '{"platform":"codex","tools":[]}\n', encoding='utf-8'
            )
            cursor_policy.write_text('{"platform":"cursor","tools":[]}\n', encoding='utf-8')
            calls = []

            def evaluator(policy):
                calls.append(policy['platform'])
                return []

            today = datetime(2026, 7, 21, 9, tzinfo=timezone.utc)
            first = checker.run_hook('codex', codex_policy, cache, today, evaluator=evaluator)
            second = checker.run_hook('codex', codex_policy, cache, today, evaluator=evaluator)
            other_project = checker.run_hook(
                'codex', other_codex_policy, cache, today, evaluator=evaluator
            )
            cursor = checker.run_hook('cursor', cursor_policy, cache, today, evaluator=evaluator)

            self.assertTrue(first.ran)
            self.assertFalse(second.ran)
            self.assertTrue(other_project.ran)
            self.assertTrue(cursor.ran)
            self.assertEqual(calls, ['codex', 'codex', 'cursor'])

    def test_daily_state_reruns_next_day_after_policy_change_and_with_force(self):
        checker = self.checker
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            policy_path = root / 'codex.json'
            cache = root / 'cache'
            policy_path.write_text('{"platform":"codex","tools":[]}\n', encoding='utf-8')
            calls = []

            def evaluator(policy):
                calls.append(policy)
                return []

            day = datetime(2026, 7, 21, 9)
            checker.run_hook('codex', policy_path, cache, day, evaluator=evaluator)
            policy_path.write_text('{"platform":"codex","tools":[],"revision":2}\n', encoding='utf-8')
            changed = checker.run_hook('codex', policy_path, cache, day, evaluator=evaluator)
            forced = checker.run_hook(
                'codex', policy_path, cache, day, force=True, evaluator=evaluator
            )
            next_day = checker.run_hook(
                'codex', policy_path, cache, day + timedelta(days=1), evaluator=evaluator
            )

            self.assertTrue(changed.ran)
            self.assertTrue(forced.ran)
            self.assertTrue(next_day.ran)
            self.assertEqual(len(calls), 4)

    def test_findings_prompt_the_user_only_once_per_day(self):
        checker = self.checker
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            policy_path = root / 'codex.json'
            cache = root / 'cache'
            policy_path.write_text('{"platform":"codex","tools":[]}\n', encoding='utf-8')
            calls = []
            finding = checker.Finding(
                'tool-missing',
                'Example Tool',
                'is missing',
                'Install it.',
            )

            def missing(_policy):
                calls.append(True)
                return [finding]

            day = datetime(2026, 7, 21, 9)
            first = checker.run_hook(
                'codex', policy_path, cache, day, evaluator=missing
            )
            repeated = checker.run_hook(
                'codex', policy_path, cache, day, evaluator=missing
            )

            self.assertTrue(first.ran)
            self.assertFalse(repeated.ran)
            self.assertTrue(first.requires_user_prompt)
            self.assertFalse(repeated.requires_user_prompt)
            self.assertEqual(repeated.findings, ())
            self.assertEqual(len(calls), 1)

            next_day = checker.run_hook(
                'codex',
                policy_path,
                cache,
                day + timedelta(days=1),
                evaluator=missing,
            )

            self.assertTrue(next_day.ran)
            self.assertEqual(len(calls), 2)

    def test_hook_internal_failure_is_non_blocking_and_cached_for_the_day(self):
        checker = self.checker
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            policy_path = root / 'codex.json'
            policy_path.write_text('{"platform":"codex","tools":[]}\n', encoding='utf-8')

            def fail(_policy):
                raise RuntimeError('secret detector output')

            first = checker.run_hook('codex', policy_path, root / 'cache', evaluator=fail)
            second = checker.run_hook('codex', policy_path, root / 'cache', evaluator=fail)

            self.assertTrue(first.ran)
            self.assertFalse(second.ran)
            self.assertTrue(first.internal_error)
            rendered = json.loads(checker.render_hook_result(first, 'codex'))
            self.assertEqual(set(rendered), {'continue', 'systemMessage'})
            self.assertIs(rendered['continue'], True)

    def test_detector_error_finding_is_cached_for_the_day(self):
        checker = self.checker
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            policy_path = root / 'codex.json'
            policy_path.write_text('{"platform":"codex","tools":[]}\n', encoding='utf-8')
            calls = []

            def detector_error(_policy):
                calls.append(True)
                return [
                    checker.Finding(
                        'detector-error',
                        'Example Tool',
                        'version detection failed',
                        'Retry later.',
                    )
                ]

            first = checker.run_hook(
                'codex', policy_path, root / 'cache', evaluator=detector_error
            )
            second = checker.run_hook(
                'codex', policy_path, root / 'cache', evaluator=detector_error
            )

            self.assertTrue(first.ran)
            self.assertFalse(second.ran)
            self.assertFalse(first.requires_user_prompt)
            self.assertEqual(len(calls), 1)

    def test_hook_output_uses_each_platform_native_shape(self):
        checker = self.checker
        result = checker.HookResult(
            True,
            (
                checker.Finding(
                    'tool-missing',
                    'Example Tool',
                    'is missing',
                    'Install it.',
                ),
            ),
        )

        codex = json.loads(checker.render_hook_result(result, 'codex'))
        cursor = json.loads(checker.render_hook_result(result, 'cursor'))
        copilot = json.loads(checker.render_hook_result(result, 'copilot'))

        self.assertEqual(set(codex), {'continue', 'systemMessage'})
        self.assertIs(codex['continue'], True)
        self.assertIsInstance(codex['systemMessage'], str)
        self.assertEqual(set(cursor), {'additional_context'})
        self.assertIsInstance(cursor['additional_context'], str)
        self.assertEqual(set(copilot), {'additionalContext'})
        self.assertIsInstance(copilot['additionalContext'], str)
        self.assertEqual(
            checker.render_hook_result(checker.HookResult(False), 'codex'),
            '',
        )

    def test_hook_prompt_requests_tool_action_consent_without_showing_commands(self):
        checker = self.checker
        result = checker.HookResult(
            True,
            (
                checker.Finding(
                    'tool-missing',
                    'Example Tool',
                    'is missing',
                    'Install it.',
                ),
            ),
        )

        message = json.loads(
            checker.render_hook_result(result, 'codex')
        )['systemMessage']

        self.assertIn(
            'Tell the user which tools need installation or upgrade and ask whether they consent',
            message,
        )
        self.assertIn('Do not show the underlying maintenance commands', message)
        self.assertIn('maintain_recommended_tools.py', message)
        self.assertIn('plugin Hook support, not an exposed Skill', message)
        self.assertNotIn('approve those exact commands', message)
        self.assertNotIn('If that message requests the fixes, perform them', message)

    def test_live_lock_suppresses_duplicate_and_stale_lock_is_reclaimed(self):
        checker = self.checker
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache = root / 'cache'
            cache.mkdir()
            policy_path = root / 'codex.json'
            policy_path.write_text('{"platform":"codex","tools":[]}\n', encoding='utf-8')
            project_cache = cache / checker._project_cache_key(policy_path)
            project_cache.mkdir()
            lock = project_cache / 'codex.lock'
            lock.write_text('live\n', encoding='utf-8')
            calls = []

            busy = checker.run_hook(
                'codex', policy_path, cache, evaluator=lambda policy: calls.append(policy) or []
            )
            old = time.time() - 1_000
            os.utime(lock, (old, old))
            reclaimed = checker.run_hook(
                'codex', policy_path, cache, evaluator=lambda policy: calls.append(policy) or []
            )

            self.assertFalse(busy.ran)
            self.assertTrue(reclaimed.ran)
            self.assertEqual(len(calls), 1)
            self.assertFalse(lock.exists())

    def test_malformed_state_and_unwritable_cache_fail_open(self):
        checker = self.checker
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            policy_path = root / 'codex.json'
            policy_path.write_text('{"platform":"codex","tools":[]}\n', encoding='utf-8')
            cache = root / 'cache'
            project_cache = cache / checker._project_cache_key(policy_path)
            project_cache.mkdir(parents=True)
            (project_cache / 'codex.json').write_text('{bad', encoding='utf-8')
            calls = []

            malformed = checker.run_hook(
                'codex', policy_path, cache, evaluator=lambda policy: calls.append(policy) or []
            )
            cache_file = root / 'not-a-directory'
            cache_file.write_text('occupied\n', encoding='utf-8')
            uncached = checker.run_hook(
                'codex', policy_path, cache_file, evaluator=lambda policy: calls.append(policy) or []
            )

            self.assertTrue(malformed.ran)
            self.assertTrue(uncached.ran)
            self.assertFalse(uncached.internal_error)
            self.assertEqual(len(calls), 2)


class RecommendedToolMaintainerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maintainer = load_maintainer()

    def test_every_recommended_tool_has_install_and_upgrade_handling(self):
        for policy_path in sorted(POLICY_ROOT.glob('*.json')):
            policy = json.loads(policy_path.read_text(encoding='utf-8'))
            platform = policy['platform']
            for tool in policy['tools']:
                for action in ('install', 'upgrade'):
                    with self.subTest(platform=platform, tool=tool['id'], action=action):
                        recipe = self.maintainer.resolve_recipe(platform, tool['id'], action)
                        self.assertTrue(recipe.command or recipe.manual_guidance)
                        self.assertFalse(recipe.command and recipe.manual_guidance)

    def test_shared_maintenance_workflow_has_paired_entry_points(self):
        scripts = MAINTAINER_PATH.parent
        self.assertTrue((scripts / 'maintain_recommended_tools.sh').is_file())
        self.assertTrue((scripts / 'maintain_recommended_tools.ps1').is_file())

    def test_maintenance_requires_consent_before_execution(self):
        executor = mock.Mock()

        with self.assertRaises(self.maintainer.ApprovalRequired):
            self.maintainer.apply_maintenance(
                'codex',
                'superpowers',
                'install',
                approved=False,
                executor=executor,
            )

        executor.assert_not_called()

    def test_approved_maintenance_executes_allowlisted_recipe_and_hides_command(self):
        executor = mock.Mock(return_value=mock.Mock(returncode=0))
        with mock.patch.object(
            self.maintainer,
            'required_action',
            side_effect=('install', None),
        ):
            result = self.maintainer.apply_maintenance(
                'codex',
                'superpowers',
                'install',
                approved=True,
                executor=executor,
            )

        self.assertEqual(result.status, 'completed')
        executor.assert_called_once_with(
            ['codex', 'plugin', 'add', 'superpowers@openai-curated'],
            check=False,
        )
        rendered = self.maintainer.render_result(result)
        self.assertIn('Superpowers', rendered)
        self.assertIn('installation completed', rendered)
        self.assertNotIn('codex plugin add', rendered)
        self.assertNotIn('superpowers@openai-curated', rendered)

    def test_manual_recipe_returns_manual_action_without_execution(self):
        executor = mock.Mock()
        with mock.patch.object(self.maintainer, 'required_action', return_value='install'):
            result = self.maintainer.apply_maintenance(
                'cursor',
                'superpowers',
                'install',
                approved=True,
                executor=executor,
            )

        self.assertEqual(result.status, 'manual-action-required')
        self.assertIn('Cursor Marketplace', result.detail)
        executor.assert_not_called()


if __name__ == '__main__':
    unittest.main()
