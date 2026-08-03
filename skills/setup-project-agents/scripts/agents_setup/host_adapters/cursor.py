from __future__ import annotations

import re
from collections.abc import Mapping

from ..models import Platform
from .base import CapabilityResult, CapabilityStatus, CommandRunner


_VERSION = re.compile(r'\d+(?:\.\d+)+')
_MINIMUM = (2026, 1, 27)


def _at_least(output: str, minimum: tuple[int, ...]) -> bool:
    match = _VERSION.search(output)
    if match is None:
        return False
    value = tuple(int(part) for part in match.group(0).split('.'))
    return value + (0,) * (len(minimum) - len(value)) >= minimum


class CursorAdapter:
    platform = Platform.CURSOR

    def check_multi_agent(self, runner: CommandRunner | None) -> CapabilityResult:
        if runner is None:
            return CapabilityResult(CapabilityStatus.UNSUPPORTED, 'Cursor runner is unavailable')
        result = runner.run(('cursor', '--version'))
        if result.returncode == 0 and _at_least(result.stdout or '', _MINIMUM):
            return CapabilityResult(CapabilityStatus.READY, 'Cursor supports multi-agent workflows')
        return CapabilityResult(CapabilityStatus.UNSUPPORTED, 'Cursor 2026.01.27 or newer is required')

    def hook_fields(self, enabled: bool) -> Mapping[str, object]:
        return {}

    def hook_trust_status(self) -> CapabilityResult:
        return CapabilityResult(
            CapabilityStatus.NEEDS_APPROVAL,
            'Approve the Hook command in the official Cursor UI before it can run.',
        )

    def plugin_refresh_command(self) -> tuple[str, ...]:
        return ('cursor', '--version')
