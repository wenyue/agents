"""Golden contracts for platform-native setup-project-agent rendering."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'setup-project-agents' / 'scripts'))

from agents_setup.catalog import load_catalog  # noqa: E402
from agents_setup.host_adapters.base import (  # noqa: E402
    CapabilityResult,
    CapabilityStatus,
)
from agents_setup.host_adapters.codex import CodexAdapter  # noqa: E402
from agents_setup.host_adapters.copilot import CopilotAdapter  # noqa: E402
from agents_setup.host_adapters.cursor import CursorAdapter  # noqa: E402
from agents_setup.models import (  # noqa: E402
    Platform,
    ProjectConfig,
)
from agents_setup.planner import build_plan  # noqa: E402
from agents_setup.renderer import render_desired_state  # noqa: E402
from agents_setup.validation import validate_rendered_state  # noqa: E402


class ReadyAdapter:
    def __init__(self, platform: Platform) -> None:
        self.platform = platform

    def check_multi_agent(self, runner: object) -> CapabilityResult:
        return CapabilityResult(CapabilityStatus.READY, 'effective default enabled')

    def hook_fields(self, enabled: bool) -> dict[str, object]:
        if self.platform is Platform.CODEX:
            return {'features.hooks': enabled} if enabled else {}
        if self.platform is Platform.COPILOT:
            return {'disableAllHooks': not enabled} if enabled else {}
        return {}

    def plugin_refresh_command(self) -> tuple[str, ...]:
        return ('true',)


class RecordingRunner:
    def __init__(self, *outputs: str) -> None:
        self.outputs = list(outputs)
        self.argv: list[tuple[str, ...]] = []

    def run(self, argv):
        self.argv.append(tuple(argv))
        return subprocess.CompletedProcess(argv, 0, self.outputs.pop(0), '')


class SetupRendererTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_catalog(REPO_ROOT)
        self.adapters = {
            platform: ReadyAdapter(platform)
            for platform in Platform
        }
        self.models = {
            'agents': {
                'change-set-verifier': {
                    'codex': {'model': 'gpt-5', 'model_reasoning_effort': 'medium'},
                    'cursor': {'model': 'cursor-default'},
                    'github': {'model': 'copilot-default'},
                }
            }
        }

    def config(self, hooks_enabled: bool) -> ProjectConfig:
        return ProjectConfig(
            1,
            tuple(Platform),
            hooks_enabled,
            ('00-global-rule-config',),
            ('manage-agent-tools',),
            ('change-set-verifier',),
        )

    def generated_tree(self, root: Path) -> Path:
        generated = root / 'generated'
        rule = generated / '.agents/rules/20-project-tools.md'
        rule.parent.mkdir(parents=True, exist_ok=True)
        rule.write_text('# generated tooling rule\n', encoding='utf-8')
        skill = generated / '.agents/skills/change-set-verification/SKILL.md'
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text('# generated verification skill\n', encoding='utf-8')
        return generated

    def render(self, target: Path, generated: Path, hooks_enabled: bool):
        return render_desired_state(
            REPO_ROOT,
            target,
            self.catalog,
            self.config(hooks_enabled),
            generated,
            self.models,
            self.adapters,
        )

    def test_golden_platform_files_are_explicitly_hook_gated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            off = self.render(root / 'off', self.generated_tree(root), False)
            on = self.render(root / 'on', self.generated_tree(root), True)

            self.assertNotIn('.codex/hooks.json', off.files_by_path)
            self.assertNotIn('.cursor/hooks.json', off.files_by_path)
            self.assertNotIn('.github/hooks/project-agent-tool-check.json', off.files_by_path)
            self.assertNotIn(('.codex/config.toml', 'features.hooks'), off.fields_by_key)
            self.assertNotIn(('.github/copilot/settings.json', 'disableAllHooks'), off.fields_by_key)

            self.assertEqual(on.fields_by_key[('.codex/config.toml', 'features.hooks')], True)
            self.assertEqual(
                on.fields_by_key[('.github/copilot/settings.json', 'disableAllHooks')], False
            )
            self.assertIn('.codex/hooks.json', on.files_by_path)
            self.assertIn('.cursor/hooks.json', on.files_by_path)
            self.assertIn('.github/hooks/project-agent-tool-check.json', on.files_by_path)
            self.assertNotIn('.agents/skills/setup-project-agents/SKILL.md', on.files_by_path)

            cursor_wrapper = on.files_by_path['.cursor/rules/00-global-rule-config.mdc']
            copilot_wrapper = on.files_by_path[
                '.github/instructions/00-global-rule-config.instructions.md'
            ]
            self.assertIn('.agents/rules/00-global-rule-config.md', cursor_wrapper.decode())
            self.assertIn('.agents/rules/00-global-rule-config.md', copilot_wrapper.decode())
            for path in (
                '.codex/hooks.json',
                '.cursor/hooks.json',
                '.github/hooks/project-agent-tool-check.json',
            ):
                command_text = on.files_by_path[path].decode()
                self.assertIn(
                    '.agents/skills/manage-agent-tools/scripts/check_recommended_tools',
                    command_text,
                )
                self.assertNotIn('install', command_text.lower())

            validate_rendered_state(on)

    def test_turning_hooks_off_deletes_owned_hook_files_and_preserves_unmanaged_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'target'
            target.mkdir()
            generated = self.generated_tree(Path(temp_dir))
            initial = self.render(target, generated, True)
            initial_plan = build_plan(target, initial.files, initial.fields, lock=self.empty_lock())
            self.materialize(target, initial.files)
            self.write_lock(target, initial_plan.next_lock)

            codex_path = target / '.codex/config.toml'
            codex_path.write_text(
                codex_path.read_text(encoding='utf-8') + '\n[unmanaged]\nkeep = "yes"\n',
                encoding='utf-8',
            )
            copilot_path = target / '.github/copilot/settings.json'
            copilot = json.loads(copilot_path.read_text(encoding='utf-8'))
            copilot['unmanaged'] = {'keep': True}
            copilot_path.write_text(json.dumps(copilot), encoding='utf-8')

            disabled = self.render(target, generated, False)
            plan = build_plan(target, disabled.files, disabled.fields, initial_plan.next_lock)
            deleted = {change.path.as_posix() for change in plan.changes if change.content is None}

            self.assertTrue({
                '.codex/hooks.json',
                '.cursor/hooks.json',
                '.github/hooks/project-agent-tool-check.json',
            }.issubset(deleted))
            self.assertNotIn(('.codex/config.toml', 'features.hooks'), disabled.fields_by_key)
            self.assertNotIn(
                ('.github/copilot/settings.json', 'disableAllHooks'), disabled.fields_by_key
            )
            self.assertIn('keep = "yes"', disabled.files_by_path['.codex/config.toml'].decode())
            self.assertTrue(
                json.loads(disabled.files_by_path['.github/copilot/settings.json'])['unmanaged']['keep']
            )

    def test_host_adapters_inspect_effective_state_without_writing_host_storage(self):
        codex_runner = RecordingRunner('multi_agent\tenabled\n')
        codex = CodexAdapter()
        self.assertEqual(codex.check_multi_agent(codex_runner).status, CapabilityStatus.READY)
        self.assertEqual(codex_runner.argv, [('codex', 'features', 'list')])
        self.assertEqual(codex.hook_fields(True), {'features.hooks': True})
        self.assertEqual(codex.hook_fields(False), {})

        cursor = CursorAdapter()
        cursor_result = cursor.check_multi_agent(RecordingRunner('Cursor CLI 2026.01.27\n'))
        self.assertEqual(cursor_result.status, CapabilityStatus.READY)
        self.assertEqual(cursor.hook_fields(True), {})
        self.assertEqual(cursor.hook_fields(False), {})
        self.assertEqual(cursor.hook_trust_status().status, CapabilityStatus.NEEDS_APPROVAL)
        self.assertIn('Cursor', cursor.hook_trust_status().detail)

        copilot = CopilotAdapter()
        copilot_result = copilot.check_multi_agent(RecordingRunner('1.0.58\n'))
        self.assertEqual(copilot_result.status, CapabilityStatus.READY)
        self.assertEqual(copilot.hook_fields(True), {'disableAllHooks': False})
        self.assertEqual(copilot.hook_fields(False), {})

    @staticmethod
    def empty_lock():
        from agents_setup.models import LockState
        return LockState.empty()

    @staticmethod
    def materialize(target: Path, files) -> None:
        for item in files:
            path = target.joinpath(*item.path.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.content)

    @staticmethod
    def write_lock(target: Path, lock) -> None:
        path = target / '.agents/lock.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({
                'version': lock.version,
                'source_commit': lock.source_commit,
                'managed_files': [
                    {'path': item.path.as_posix(), 'sha256': item.sha256}
                    for item in lock.managed_files
                ],
                'managed_fields': [
                    {'path': item.path.as_posix(), 'key': item.key, 'sha256': item.sha256}
                    for item in lock.managed_fields
                ],
            }),
            encoding='utf-8',
        )


if __name__ == '__main__':
    unittest.main()
