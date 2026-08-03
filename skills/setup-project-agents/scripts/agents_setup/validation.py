from __future__ import annotations

import re
from pathlib import PurePosixPath

from .renderer import RenderError, RenderedState, _format_for, _jsonc_load, tomllib


_REFERENCE = re.compile(r'(?:Apply @|Follow `)(\.agents/[^`\s]+)')
_HOOK_CHECKER = PurePosixPath('.agents/skills/manage-agent-tools/scripts/check_recommended_tools.py')


def validate_rendered_state(rendered: RenderedState) -> None:
    """Validate staged native configs and wrapper references without touching the host."""
    files = rendered.files_by_path
    for path, content in files.items():
        relative = PurePosixPath(path)
        format_name = _format_for(relative)
        if format_name == 'toml':
            tomllib.loads(content.decode())
        elif format_name in {'json', 'jsonc'}:
            _jsonc_load(content.decode())
        if path.endswith(('.md', '.mdc', '.toml')):
            for reference in _REFERENCE.findall(content.decode()):
                if reference not in files:
                    raise RenderError(f'wrapper reference is not rendered: {reference}')
    hook_paths = {
        '.codex/hooks.json',
        '.cursor/hooks.json',
        '.github/hooks/project-agent-tool-check.json',
    }
    if hook_paths.intersection(files) and _HOOK_CHECKER.as_posix() not in files:
        raise RenderError('Hook checker is not rendered')
