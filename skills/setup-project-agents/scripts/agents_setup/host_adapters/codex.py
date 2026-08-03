from __future__ import annotations

from collections.abc import Mapping

from ..models import Platform
from .base import CapabilityResult, CapabilityStatus, CommandRunner


class CodexAdapter:
    platform = Platform.CODEX

    def check_multi_agent(self, runner: CommandRunner | None) -> CapabilityResult:
        if runner is None:
            return CapabilityResult(CapabilityStatus.UNSUPPORTED, 'Codex runner is unavailable')
        result = runner.run(('codex', 'features', 'list'))
        output = (result.stdout or '').lower()
        if result.returncode == 0 and 'multi_agent' in output:
            if any(token in output for token in ('enabled', 'true', 'on')):
                return CapabilityResult(CapabilityStatus.READY, 'Codex effective multi_agent is enabled')
            return CapabilityResult(
                CapabilityStatus.NEEDS_RESTART,
                'Codex effective multi_agent is disabled; enable it in the host feature UI.',
            )
        return CapabilityResult(CapabilityStatus.UNSUPPORTED, 'Codex multi_agent status is unavailable')

    def hook_fields(self, enabled: bool) -> Mapping[str, object]:
        return {'features.hooks': True} if enabled else {}

    def plugin_refresh_command(self) -> tuple[str, ...]:
        return ('codex', 'plugins', 'list')
