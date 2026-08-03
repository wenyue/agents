from __future__ import annotations

import re
from collections.abc import Mapping

from ..models import Platform
from .base import CapabilityResult, CapabilityStatus, CommandRunner


class CodexAdapter:
    platform = Platform.CODEX

    def check_multi_agent(self, runner: CommandRunner | None) -> CapabilityResult:
        if runner is None:
            return CapabilityResult(CapabilityStatus.UNSUPPORTED, 'Codex runner is unavailable')
        result = runner.run(('codex', 'features', 'list'))
        state = None
        for line in (result.stdout or '').lower().splitlines():
            match = re.match(r'^\s*multi_agent(?:\s+|\s*[:=]\s*)(.*)$', line)
            if match is None:
                continue
            tokens = set(re.findall(r'[a-z]+', match.group(1)))
            enabled = tokens.intersection({'enabled', 'true', 'on'})
            disabled = tokens.intersection({'disabled', 'false', 'off'})
            if bool(enabled) != bool(disabled):
                state = bool(enabled)
            break
        if result.returncode == 0 and state is not None:
            if state:
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
