from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Sequence

from agents_setup.source import InvalidFetchedSource, validate_source


_COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')


def normalize_source_commit(source_commit: str) -> str | None:
    """Convert the bootstrap-only offline sentinel before any lock is built."""
    if source_commit == 'offline':
        return None
    if not isinstance(source_commit, str) or not _COMMIT.fullmatch(source_commit):
        raise ValueError('source_commit must be offline or a 40-character hexadecimal commit')
    return source_commit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Prepare, apply, or check a pinned project-agent setup session.',
        allow_abbrev=False,
    )
    phases = parser.add_subparsers(dest='phase', required=True)
    for phase in ('prepare', 'apply', 'check'):
        command = phases.add_parser(phase, allow_abbrev=False)
        command.add_argument('--target', type=Path, required=True)
        command.add_argument('--session', type=Path, required=True)
        command.add_argument('--source-root', type=Path, required=True)
        command.add_argument('--source-commit', required=True)
        command.add_argument('--no-bootstrap', action='store_true', required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    try:
        validate_source(args.source_root)
        normalize_source_commit(args.source_commit)
    except (InvalidFetchedSource, ValueError) as error:
        print(f'ERROR: invalid pinned setup source: {error}', file=sys.stderr)
        return 2
    print(
        f'ERROR: {args.phase} orchestration is not implemented in this control-plane entrypoint.',
        file=sys.stderr,
    )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
