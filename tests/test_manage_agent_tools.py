"""Contracts for recommended-tool policies and non-mutating Hooks."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / 'skills' / 'manage-agent-tools' / 'scripts' / 'check_recommended_tools.py'
POLICY_ROOT = REPO_ROOT / 'config' / 'recommended-tools'


def load_checker():
    spec = importlib.util.spec_from_file_location('task8_check_recommended_tools', CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load checker: {CHECKER_PATH}')
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

    def test_default_policy_path_falls_back_to_plugin_root_policy(self):
        self.assertEqual(
            self.checker.default_policy_path('codex'),
            POLICY_ROOT / 'codex.json',
        )

    def test_project_snapshot_policy_takes_precedence_over_plugin_policy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_root = Path(temp_dir) / 'skills' / 'manage-agent-tools'
            project_policy = skill_root / 'references' / 'recommended-tools' / 'codex.json'
            project_policy.parent.mkdir(parents=True)
            project_policy.write_text('{"platform": "codex", "tools": []}\n', encoding='utf-8')
            checker_path = skill_root / 'scripts' / 'check_recommended_tools.py'
            checker_path.parent.mkdir()
            checker_path.write_text(CHECKER_PATH.read_text(encoding='utf-8'), encoding='utf-8')
            spec = importlib.util.spec_from_file_location('task8_project_checker', checker_path)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            self.assertEqual(module.default_policy_path('codex'), project_policy)

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


if __name__ == '__main__':
    unittest.main()
