from __future__ import annotations

from collections.abc import Mapping

from ..models import Platform
from .base import CapabilityResult, CapabilityStatus, CommandRunner
from .cursor import _at_least


class CopilotAdapter:
    platform = Platform.COPILOT

    def check_multi_agent(self, runner: CommandRunner | None) -> CapabilityResult:
        if runner is None:
            return CapabilityResult(CapabilityStatus.UNSUPPORTED, 'Copilot runner is unavailable')
        result = runner.run(('copilot', '--version'))
        if result.returncode == 0 and _at_least(result.stdout or '', (1, 0, 58)):
            return CapabilityResult(CapabilityStatus.READY, 'Copilot supports multi-agent workflows')
        return CapabilityResult(CapabilityStatus.UNSUPPORTED, 'Copilot 1.0.58 or newer is required')

    def hook_fields(self, enabled: bool) -> Mapping[str, object]:
        return {'disableAllHooks': False} if enabled else {}

    def plugin_refresh_command(self) -> tuple[str, ...]:
        return ('copilot', '--version')
