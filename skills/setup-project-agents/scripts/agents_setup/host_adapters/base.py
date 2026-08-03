from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Protocol, Sequence

from ..models import Platform


class CapabilityStatus(str, Enum):
    READY = 'ready'
    NEEDS_APPROVAL = 'needs_approval'
    NEEDS_RESTART = 'needs_restart'
    UNSUPPORTED = 'unsupported'


@dataclass(frozen=True)
class CapabilityResult:
    status: CapabilityStatus
    detail: str


class CommandRunner(Protocol):
    def run(self, argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        raise NotImplementedError


class HostAdapter(Protocol):
    platform: Platform

    def check_multi_agent(self, runner: CommandRunner | None) -> CapabilityResult:
        raise NotImplementedError

    def hook_fields(self, enabled: bool) -> Mapping[str, object]:
        raise NotImplementedError

    def plugin_refresh_command(self) -> tuple[str, ...]:
        raise NotImplementedError
