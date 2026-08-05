from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from agents_setup.source import (
    CANONICAL_REF,
    CANONICAL_REPOSITORY,
    InvalidFetchedSource,
    SourceSnapshot,
    SourceUnavailable,
    fetch_canonical,
    validate_source,
)


_RESERVED_OPTIONS = ('--source-root', '--source-commit', '--no-bootstrap')


def _installed_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _has_reserved_option(argv: Sequence[str]) -> bool:
    return any(
        token == option or token.startswith(f'{option}=')
        for token in argv
        for option in _RESERVED_OPTIONS
    )


def _initial_prepare(argv: Sequence[str]) -> tuple[list[str], Path] | None:
    if not argv or argv[0] != 'prepare' or _has_reserved_option(argv):
        return None
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('phase')
    parser.add_argument('--session', type=Path)
    try:
        parsed, _ = parser.parse_known_args(argv)
    except SystemExit:
        return None
    if parsed.phase != 'prepare' or parsed.session is None:
        return None
    return list(argv), parsed.session.absolute()


def main(argv: Sequence[str] | None = None, *, installed_root: Path | None = None) -> int:
    """Fetch the canonical source once and hand only initial prepare to its pinned CLI."""
    forwarded_and_session = _initial_prepare(list(sys.argv[1:] if argv is None else argv))
    if forwarded_and_session is None:
        print('ERROR: bootstrap accepts only prepare with --session and no reserved options', file=sys.stderr)
        return 2
    forwarded, session = forwarded_and_session
    try:
        snapshot = fetch_canonical(CANONICAL_REPOSITORY, work_root=session)
    except SourceUnavailable:
        try:
            root = validate_source(installed_root if installed_root is not None else _installed_root())
        except InvalidFetchedSource as error:
            print(f'ERROR: installed fallback source is invalid: {error}', file=sys.stderr)
            return 1
        print(
            f'WARNING: canonical {CANONICAL_REF} is unavailable; '
            'using installed plugin source.',
            file=sys.stderr,
        )
        snapshot = SourceSnapshot(root, 'offline')
    except InvalidFetchedSource as error:
        print(f'ERROR: fetched canonical source is invalid: {error}', file=sys.stderr)
        return 1

    argv = [
        sys.executable,
        str(snapshot.root / 'skills/setup-project-agents/scripts/setup_project_agents.py'),
        *forwarded,
        '--source-root',
        str(snapshot.root),
        '--source-commit',
        snapshot.commit,
        '--no-bootstrap',
    ]
    try:
        completed = subprocess.run(argv, check=False)
    except OSError as error:
        print(f'ERROR: cannot execute pinned setup source: {error}', file=sys.stderr)
        return 1
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
