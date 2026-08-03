"""Platform capability adapters used by the deterministic renderer."""

from .codex import CodexAdapter
from .copilot import CopilotAdapter
from .cursor import CursorAdapter

__all__ = ('CodexAdapter', 'CopilotAdapter', 'CursorAdapter')
