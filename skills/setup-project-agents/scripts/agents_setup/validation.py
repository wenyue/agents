from __future__ import annotations

import re
from pathlib import PurePosixPath

from .renderer import RenderError, RenderedState
from .structured import format_for_path, parse_document


_REFERENCE = re.compile(r'(?:Apply @|Follow `)(\.agents/[^`\s]+)')
def validate_rendered_state(rendered: RenderedState) -> None:
    """Validate staged native configs and wrapper references without touching the host."""
    files = rendered.files_by_path
    for path, content in files.items():
        relative = PurePosixPath(path)
        format_name = format_for_path(relative)
        if format_name is not None:
            parse_document(content, format_name)
        if path.endswith(('.md', '.mdc', '.toml')):
            for reference in _REFERENCE.findall(content.decode()):
                if reference not in files:
                    raise RenderError(f'wrapper reference is not rendered: {reference}')
