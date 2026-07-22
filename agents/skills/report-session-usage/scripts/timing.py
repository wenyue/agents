from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


TOKSCALE_TIMEOUT_SECONDS = 30
TOKEN_FIELDS = ('input', 'output', 'reasoning', 'cache_read', 'cache_write')


class UsageError(RuntimeError):
    pass


def _timestamp(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise UsageError('Usage timestamps require timezone information.')
    return value.astimezone(timezone.utc)


def _serialize_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds')


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise UsageError(f'Usage timestamp has no timezone: {value}')
    return parsed.astimezone(timezone.utc)


def session_id_matches(candidate: str, requested: str) -> bool:
    return candidate == requested or candidate.endswith(f'-{requested}')


def _integer(value: Any, field: str) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        raise UsageError(f'Tokscale field {field} must be numeric.')
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise UsageError(f'Tokscale field {field} must be numeric.') from error
    if result < 0:
        raise UsageError(f'Tokscale field {field} must not be negative.')
    return result


def _number(value: Any, field: str) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        raise UsageError(f'Tokscale field {field} must be numeric.')
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise UsageError(f'Tokscale field {field} must be numeric.') from error
    if result < 0:
        raise UsageError(f'Tokscale field {field} must not be negative.')
    return result


def normalize_usage_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        'client': str(row.get('client', '')),
        'session_id': str(row.get('sessionId', row.get('session_id', ''))),
        'provider': str(row.get('provider', '')),
        'model': str(row.get('model', 'unknown')),
        'input': _integer(row.get('input'), 'input'),
        'output': _integer(row.get('output'), 'output'),
        'reasoning': _integer(row.get('reasoning'), 'reasoning'),
        'cache_read': _integer(
            row.get('cacheRead', row.get('cache_read')), 'cacheRead'
        ),
        'cache_write': _integer(
            row.get('cacheWrite', row.get('cache_write')), 'cacheWrite'
        ),
        'cost': _number(row.get('cost'), 'cost'),
    }


def _empty_usage_totals() -> dict[str, int | float]:
    return {
        'input': 0,
        'output': 0,
        'reasoning': 0,
        'cache_read': 0,
        'cache_write': 0,
        'total_tokens': 0,
        'cost': 0.0,
    }


def _aggregate_usage(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int | float]]:
    normalized_rows = [normalize_usage_row(row) for row in rows]
    totals = _empty_usage_totals()
    for row in normalized_rows:
        for field in TOKEN_FIELDS:
            totals[field] += row[field]
        totals['cost'] += row['cost']
    totals['total_tokens'] = sum(int(totals[field]) for field in TOKEN_FIELDS)
    return normalized_rows, totals


def _tokscale_date(value: datetime) -> str:
    return value.astimezone().date().isoformat()


def tokscale_executable(
    *,
    os_name: str | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> str:
    platform = os_name or os.name
    candidates = ('tokscale.cmd', 'tokscale.exe') if platform == 'nt' else ('tokscale',)
    for candidate in candidates:
        resolved = which(candidate)
        if resolved:
            return resolved
    return 'tokscale'


def capture_tokscale_snapshot(
    client: str,
    started_at: datetime | None,
    ended_at: datetime | None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[dict[str, Any]]:
    command = [
        tokscale_executable(),
        '--json',
        '--client',
        client,
    ]
    if started_at is not None and ended_at is not None:
        command.extend(
            [
                '--since',
                _tokscale_date(started_at),
                '--until',
                _tokscale_date(ended_at),
            ]
        )
    command.extend(['--group-by', 'client,session,model', '--no-spinner'])
    try:
        completed = runner(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=TOKSCALE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise UsageError(
            f'Tokscale timed out after {TOKSCALE_TIMEOUT_SECONDS} seconds for client {client}.'
        ) from error
    except OSError as error:
        raise UsageError(f'Tokscale could not run for client {client}: {error}') from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or 'unknown error'
        raise UsageError(f'Tokscale failed for client {client}: {detail}')
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise UsageError(f'Tokscale returned invalid JSON for client {client}.') from error
    if not isinstance(payload, dict) or not isinstance(payload.get('entries'), list):
        raise UsageError(f'Tokscale JSON for client {client} has no entries array.')
    return payload['entries']


def detect_current_session(
    client: str | None = None, session_id: str | None = None
) -> tuple[str | None, str | None]:
    if client or session_id:
        if not client or not session_id:
            raise UsageError('Client and session ID must be provided together.')
        return client, session_id
    codex_session = os.environ.get('CODEX_THREAD_ID')
    if codex_session:
        return 'codex', codex_session
    return None, None


def _codex_log_paths(codex_home: Path, session_id: str) -> list[Path]:
    paths = []
    for root in (codex_home / 'sessions', codex_home / 'archived_sessions'):
        if root.is_dir():
            paths.extend(
                path
                for path in root.rglob(f'*{session_id}.jsonl')
                if path.stem == session_id or path.stem.endswith(f'-{session_id}')
            )
    return sorted(set(paths))


def codex_session_bounds(
    session_id: str, codex_home: Path | None = None
) -> tuple[datetime, datetime] | None:
    root = codex_home or Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    earliest = None
    latest = None
    for path in _codex_log_paths(root, session_id):
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                event = json.loads(line)
                event_time = _parse_timestamp(str(event['timestamp']))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, UsageError):
                continue
            if earliest is None or event_time < earliest:
                earliest = event_time
            if latest is None or event_time > latest:
                latest = event_time
    if earliest is None or latest is None:
        return None
    return earliest, latest


def read_codex_token_totals(
    session_id: str, codex_home: Path | None = None
) -> dict[str, int] | None:
    root = codex_home or Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    latest: tuple[datetime, dict[str, Any]] | None = None
    for path in _codex_log_paths(root, session_id):
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get('payload') or {}
            info = payload.get('info') or {}
            totals = info.get('total_token_usage')
            if (
                event.get('type') != 'event_msg'
                or payload.get('type') != 'token_count'
                or not isinstance(totals, dict)
                or not event.get('timestamp')
            ):
                continue
            try:
                event_time = _parse_timestamp(str(event['timestamp']))
            except (UsageError, ValueError):
                continue
            if latest is None or event_time > latest[0]:
                latest = event_time, totals
    if latest is None:
        return None
    raw = latest[1]
    total_input = _integer(raw.get('input_tokens'), 'input_tokens')
    cache_read = _integer(raw.get('cached_input_tokens'), 'cached_input_tokens')
    cache_write = _integer(
        raw.get('cache_write_input_tokens'), 'cache_write_input_tokens'
    )
    total_output = _integer(raw.get('output_tokens'), 'output_tokens')
    reasoning = _integer(raw.get('reasoning_output_tokens'), 'reasoning_output_tokens')
    if cache_read + cache_write > total_input:
        raise UsageError('Codex cached input exceeds total input tokens.')
    if reasoning > total_output:
        raise UsageError('Codex reasoning output exceeds total output tokens.')
    return {
        'input': total_input - cache_read - cache_write,
        'cache_read': cache_read,
        'cache_write': cache_write,
        'output': total_output - reasoning,
        'reasoning': reasoning,
        'total_tokens': total_input + total_output,
    }


def build_session_usage(
    client: str,
    session_id: str,
    captured_at: datetime,
    *,
    tokscale_rows: list[dict[str, Any]],
    snapshot_error: str | None = None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    matching_rows = [
        row
        for row in tokscale_rows
        if row.get('client') == client
        and session_id_matches(
            str(row.get('sessionId', row.get('session_id', ''))), session_id
        )
    ]
    warnings = [snapshot_error] if snapshot_error else []
    if matching_rows:
        rows, totals = _aggregate_usage(matching_rows)
        return {
            'client': client,
            'session_id': session_id,
            'captured_at': _serialize_timestamp(captured_at),
            'status': 'available',
            'source': 'tokscale',
            'cost_status': 'available',
            'rows': rows,
            'totals': totals,
            'warnings': warnings,
        }
    if client == 'codex':
        log_totals = read_codex_token_totals(session_id, codex_home)
        if log_totals is not None:
            totals = _empty_usage_totals()
            totals.update(log_totals)
            if not snapshot_error:
                warnings.append('Tokscale returned no matching session row.')
            return {
                'client': client,
                'session_id': session_id,
                'captured_at': _serialize_timestamp(captured_at),
                'status': 'partial',
                'source': 'codex-log',
                'cost_status': 'unavailable',
                'rows': [],
                'totals': totals,
                'warnings': warnings,
            }
    if not snapshot_error:
        warnings.append(
            'No matching Tokscale row or Codex token event was found.'
            if client == 'codex'
            else 'No matching Tokscale session row was found.'
        )
    return {
        'client': client,
        'session_id': session_id,
        'captured_at': _serialize_timestamp(captured_at),
        'status': 'unavailable',
        'source': 'none',
        'cost_status': 'unavailable',
        'rows': [],
        'totals': _empty_usage_totals(),
        'warnings': warnings,
    }


def _format_tokens(value: int | float) -> str:
    return f'{int(value):,}'


def _unique_problems(messages: list[str]) -> list[str]:
    return list(dict.fromkeys(message.strip() for message in messages if message.strip()))


def build_session_reply(usage: dict[str, Any]) -> dict[str, Any]:
    problems = list(usage.get('warnings', []))
    if usage['status'] != 'available' and not problems:
        problems.append(f"Token evidence is {usage['status']}.")
    totals = usage['totals']
    return {
        'scope': 'whole session',
        'tokens': {
            'status': usage['status'],
            'input': int(totals['input']),
            'cache_read': int(totals['cache_read']),
            'cache_write': int(totals['cache_write']),
            'output': int(totals['output']),
            'reasoning': int(totals['reasoning']),
            'total': int(totals['total_tokens']),
        },
        'cost': (
            'unavailable'
            if usage['cost_status'] == 'unavailable'
            else f"{chr(36)}{totals['cost']:.6f} USD"
        ),
        'problems': _unique_problems(problems),
    }


def render_reply_markdown(reply: dict[str, Any]) -> str:
    tokens = reply['tokens']
    if tokens['status'] == 'unavailable':
        token_summary = 'unavailable'
    else:
        qualifier = '' if tokens['status'] == 'available' else f" ({tokens['status']})"
        token_summary = (
            f"{_format_tokens(tokens['total'])} total"
            f"{qualifier} (input {_format_tokens(tokens['input'])}, "
            f"cached input {_format_tokens(tokens['cache_read'])}, "
            f"cache write {_format_tokens(tokens['cache_write'])}, "
            f"output {_format_tokens(tokens['output'])}, "
            f"reasoning {_format_tokens(tokens['reasoning'])})"
        )
    lines = [
        '### Usage Metrics',
        f"- Scope: {reply['scope']}",
        f'- Tokens: {token_summary}',
        f"- Estimated API-equivalent cost: {reply['cost']}",
    ]
    if reply['problems']:
        lines.append(f"- Problems: {'; '.join(reply['problems'])}")
    return '\n'.join(lines)


def render_session_usage_markdown(usage: dict[str, Any]) -> str:
    return render_reply_markdown(build_session_reply(usage))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Report usage for one stable agent session.')
    subparsers = parser.add_subparsers(dest='command', required=True)
    usage = subparsers.add_parser('usage')
    usage.add_argument('--client')
    usage.add_argument('--session-id')
    return parser


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print('ERROR: Python 3.11 or newer is required.', file=sys.stderr)
        return 2
    args = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        captured = _timestamp()
        client, session_id = detect_current_session(args.client, args.session_id)
        if not client or not session_id:
            raise UsageError(
                'No supported current session was detected; pass --client and --session-id.'
            )
        bounds = codex_session_bounds(session_id) if client == 'codex' else None
        started_at, ended_at = bounds or (None, None)
        rows = []
        error = None
        try:
            rows = capture_tokscale_snapshot(client, started_at, ended_at)
        except UsageError as usage_error:
            error = str(usage_error)
        usage_report = build_session_usage(
            client,
            session_id,
            captured,
            tokscale_rows=rows,
            snapshot_error=error,
        )
        print(render_reply_markdown(build_session_reply(usage_report)))
    except (OSError, ValueError, json.JSONDecodeError, UsageError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
