from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator


LEGACY_PHASES = (
    'environment',
    'code-generation',
    'review',
    'verification',
    'testing',
    'integration',
    'waiting',
    'other',
)
TOOL_ACTIVITY_CATEGORIES = LEGACY_PHASES
STATE_DIRECTORY_NAME = 'codex-worktree-time'
SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1
TOKSCALE_TIMEOUT_SECONDS = 30
USAGE_FIELDS = (
    'input',
    'output',
    'reasoning',
    'cache_read',
    'cache_write',
    'message_count',
    'model_activity_ms',
    'timed_tokens',
    'sample_count',
)
TOKEN_FIELDS = ('input', 'output', 'reasoning', 'cache_read', 'cache_write')


class TimingError(RuntimeError):
    pass


def default_state_dir() -> Path:
    return Path(tempfile.gettempdir()) / STATE_DIRECTORY_NAME


def _timestamp(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise TimingError('Timing timestamps require timezone information.')
    return value.astimezone(timezone.utc)


def _serialize_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds')


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise TimingError(f'Ledger timestamp has no timezone: {value}')
    return parsed.astimezone(timezone.utc)


def _duration_microseconds(start: datetime, end: datetime) -> int:
    delta = end - start
    if delta.total_seconds() < 0:
        raise TimingError('Timing events must remain chronological.')
    return ((delta.days * 86400) + delta.seconds) * 1_000_000 + delta.microseconds


def _state_path(task_id: str, state_dir: Path) -> Path:
    return state_dir / f'{task_id}.json'


def _write_state(state: dict[str, Any], state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    target = _state_path(state['task_id'], state_dir)
    temporary = state_dir / f".{state['task_id']}.{uuid.uuid4().hex}.tmp"
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    os.replace(temporary, target)


@contextmanager
def _task_lock(task_id: str, state_dir: Path) -> Iterator[None]:
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / f'.{task_id}.lock'
    with lock_path.open('a+b') as lock_file:
        if os.name == 'nt':
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b'\0')
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def load_task(task_id: str, state_dir: Path | None = None) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    path = _state_path(task_id, root)
    if not path.is_file():
        raise TimingError(f'Task receipt not found: {path}')
    state = json.loads(path.read_text(encoding='utf-8'))
    if state.get('schema_version') not in (LEGACY_SCHEMA_VERSION, SCHEMA_VERSION):
        raise TimingError(f'Unsupported task receipt schema: {state.get("schema_version")}')
    return state


def session_id_matches(candidate: str, requested: str) -> bool:
    return candidate == requested or candidate.endswith(f'-{requested}')


def _integer(value: Any, field: str) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        raise TimingError(f'Tokscale field {field} must be numeric.')
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise TimingError(f'Tokscale field {field} must be numeric.') from error
    if result < 0:
        raise TimingError(f'Tokscale field {field} must not be negative.')
    return result


def _number(value: Any, field: str) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        raise TimingError(f'Tokscale field {field} must be numeric.')
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TimingError(f'Tokscale field {field} must be numeric.') from error
    if result < 0:
        raise TimingError(f'Tokscale field {field} must not be negative.')
    return result


def normalize_usage_row(row: dict[str, Any]) -> dict[str, Any]:
    performance = row.get('performance') or {}
    if not isinstance(performance, dict):
        raise TimingError('Tokscale performance data must be an object.')
    return {
        'client': str(row.get('client', '')),
        'session_id': str(row.get('sessionId', row.get('session_id', ''))),
        'provider': str(row.get('provider', '')),
        'model': str(row.get('model', 'unknown')),
        'input': _integer(row.get('input'), 'input'),
        'output': _integer(row.get('output'), 'output'),
        'reasoning': _integer(row.get('reasoning'), 'reasoning'),
        'cache_read': _integer(row.get('cacheRead', row.get('cache_read')), 'cacheRead'),
        'cache_write': _integer(row.get('cacheWrite', row.get('cache_write')), 'cacheWrite'),
        'cost': _number(row.get('cost'), 'cost'),
        'message_count': _integer(
            row.get('messageCount', row.get('message_count')), 'messageCount'
        ),
        'model_activity_ms': _integer(
            performance.get('totalDurationMs', row.get('model_activity_ms')),
            'performance.totalDurationMs',
        ),
        'timed_tokens': _integer(
            performance.get('timedTokens', row.get('timed_tokens')),
            'performance.timedTokens',
        ),
        'sample_count': _integer(
            performance.get('sampleCount', row.get('sample_count')),
            'performance.sampleCount',
        ),
    }


def session_usage_rows(
    payload: dict[str, Any], client: str, session_id: str
) -> list[dict[str, Any]]:
    entries = payload.get('entries', [])
    if not isinstance(entries, list):
        raise TimingError('Tokscale JSON field entries must be an array.')
    rows = []
    for row in entries:
        if not isinstance(row, dict):
            raise TimingError('Tokscale entries must contain objects.')
        candidate = str(row.get('sessionId', row.get('session_id', '')))
        if row.get('client') == client and session_id_matches(candidate, session_id):
            rows.append(normalize_usage_row(row))
    return rows


def _usage_groups(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for raw_row in rows:
        row = normalize_usage_row(raw_row)
        key = (row['provider'], row['model'])
        aggregate = grouped.setdefault(
            key,
            {
                'provider': row['provider'],
                'model': row['model'],
                **{field: 0 for field in USAGE_FIELDS},
                'cost': 0.0,
            },
        )
        for field in USAGE_FIELDS:
            aggregate[field] += row[field]
        aggregate['cost'] += row['cost']
    return grouped


def _empty_usage_totals() -> dict[str, int | float]:
    return {
        'input': 0,
        'output': 0,
        'reasoning': 0,
        'cache_read': 0,
        'cache_write': 0,
        'total_tokens': 0,
        'cost': 0.0,
        'message_count': 0,
        'model_activity_ms': 0,
        'timed_tokens': 0,
        'sample_count': 0,
    }


def usage_delta(
    client: str,
    session_id: str,
    baseline_rows: list[dict[str, Any]],
    final_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline = _usage_groups(
        [
            row
            for row in baseline_rows
            if session_id_matches(
                str(row.get('sessionId', row.get('session_id', ''))), session_id
            )
        ]
    )
    final = _usage_groups(
        [
            row
            for row in final_rows
            if session_id_matches(
                str(row.get('sessionId', row.get('session_id', ''))), session_id
            )
        ]
    )
    rows = []
    totals = _empty_usage_totals()
    for key in sorted(set(baseline) | set(final)):
        before = baseline.get(
            key,
            {'provider': key[0], 'model': key[1], **{field: 0 for field in USAGE_FIELDS}, 'cost': 0.0},
        )
        after = final.get(
            key,
            {'provider': key[0], 'model': key[1], **{field: 0 for field in USAGE_FIELDS}, 'cost': 0.0},
        )
        delta = {
            'client': client,
            'session_id': session_id,
            'provider': key[0],
            'model': key[1],
        }
        for field in USAGE_FIELDS:
            value = after[field] - before[field]
            if value < 0:
                raise TimingError(
                    f'Tokscale counter decreased for {client}/{session_id}/{key[1]}: {field}'
                )
            delta[field] = value
        cost = after['cost'] - before['cost']
        if cost < -1e-9:
            raise TimingError(
                f'Tokscale cost decreased for {client}/{session_id}/{key[1]}.'
            )
        delta['cost'] = max(0.0, cost)
        if any(delta[field] for field in USAGE_FIELDS) or delta['cost']:
            rows.append(delta)
            for field in USAGE_FIELDS:
                totals[field] += delta[field]
            totals['cost'] += delta['cost']
    totals['total_tokens'] = sum(int(totals[field]) for field in TOKEN_FIELDS)
    return {'rows': rows, 'totals': totals}


def _baseline(
    *,
    status: str,
    captured_at: datetime,
    rows: list[dict[str, Any]] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        'status': status,
        'captured_at': _serialize_timestamp(captured_at),
        'rows': [normalize_usage_row(row) for row in (rows or [])],
        'error': error,
    }


def start_task(
    task: str,
    repository: str,
    worktree: str,
    client: str | None = None,
    session_id: str | None = None,
    baseline_rows: list[dict[str, Any]] | None = None,
    baseline_error: str | None = None,
    state_dir: Path | None = None,
    now: datetime | None = None,
    tokscale_version: str | None = None,
) -> dict[str, Any]:
    if not task.strip():
        raise TimingError('Task summary must contain text.')
    if not repository.strip():
        raise TimingError('Repository must contain a path or identifier.')
    if not worktree.strip():
        raise TimingError('Worktree must contain a path or identifier.')
    if (client is None) != (session_id is None):
        raise TimingError('Client and session ID must be provided together.')
    started = _timestamp(now)
    sessions = []
    warnings = []
    if client is not None and session_id is not None:
        sessions.append(
            {
                'client': client,
                'session_id': session_id,
                'attached_at': _serialize_timestamp(started),
                'entire_session': False,
                'baseline': _baseline(
                    status='unavailable' if baseline_error else 'available',
                    captured_at=started,
                    rows=baseline_rows,
                    error=baseline_error,
                ),
            }
        )
    else:
        warnings.append('No agent session was registered at task start.')
    state = {
        'schema_version': SCHEMA_VERSION,
        'task_id': uuid.uuid4().hex,
        'task': task.strip(),
        'repository': repository.strip(),
        'worktree': worktree.strip(),
        'status': 'running',
        'started_at': _serialize_timestamp(started),
        'completed_at': None,
        'sessions': sessions,
        'attribution_gaps': [],
        'tokscale_version': tokscale_version,
        'metrics': None,
        'warnings': warnings,
    }
    _write_state(state, state_dir or default_state_dir())
    return state


def _attach_session_unlocked(
    task_id: str,
    client: str,
    session_id: str,
    entire_session: bool = False,
    baseline_rows: list[dict[str, Any]] | None = None,
    baseline_error: str | None = None,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    state = load_task(task_id, root)
    if state['schema_version'] != SCHEMA_VERSION:
        raise TimingError('Sessions can only be attached to schema-2 task receipts.')
    if state['status'] != 'running':
        raise TimingError(f"Task receipt is {state['status']}: {task_id}")
    if not client.strip() or not session_id.strip():
        raise TimingError('Client and session ID must contain text.')
    if any(
        session['client'] == client and session['session_id'] == session_id
        for session in state['sessions']
    ):
        raise TimingError(f'Session is already attached: {client}/{session_id}')
    attached = _timestamp(now)
    if entire_session:
        baseline = _baseline(status='zero', captured_at=attached)
    else:
        baseline = _baseline(
            status='unavailable' if baseline_error else 'available',
            captured_at=attached,
            rows=baseline_rows,
            error=baseline_error,
        )
    state['sessions'].append(
        {
            'client': client.strip(),
            'session_id': session_id.strip(),
            'attached_at': _serialize_timestamp(attached),
            'entire_session': entire_session,
            'baseline': baseline,
        }
    )
    _write_state(state, root)
    return state


def attach_session(
    task_id: str,
    client: str,
    session_id: str,
    entire_session: bool = False,
    baseline_rows: list[dict[str, Any]] | None = None,
    baseline_error: str | None = None,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    with _task_lock(task_id, root):
        return _attach_session_unlocked(
            task_id,
            client,
            session_id,
            entire_session,
            baseline_rows,
            baseline_error,
            root,
            now,
        )


def _record_attribution_gap_unlocked(
    task_id: str,
    label: str,
    reason: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    state = load_task(task_id, root)
    if state['schema_version'] != SCHEMA_VERSION:
        raise TimingError('Attribution gaps can only be added to schema-2 task receipts.')
    if state['status'] != 'running':
        raise TimingError(f"Task receipt is {state['status']}: {task_id}")
    if not label.strip() or not reason.strip():
        raise TimingError('Attribution gap label and reason must contain text.')
    gap = {
        'label': label.strip(),
        'reason': reason.strip(),
        'recorded_at': _serialize_timestamp(_timestamp(now)),
    }
    if any(
        existing['label'] == gap['label'] and existing['reason'] == gap['reason']
        for existing in state.get('attribution_gaps', [])
    ):
        raise TimingError(f"Attribution gap is already recorded: {gap['label']}")
    state.setdefault('attribution_gaps', []).append(gap)
    _write_state(state, root)
    return state


def record_attribution_gap(
    task_id: str,
    label: str,
    reason: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    with _task_lock(task_id, root):
        return _record_attribution_gap_unlocked(task_id, label, reason, root, now)


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
    clients: list[str],
    started_at: datetime,
    ended_at: datetime,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, list[dict[str, Any]]]:
    snapshots: dict[str, list[dict[str, Any]]] = {}
    for client in sorted(set(clients)):
        command = [
            tokscale_executable(),
            '--json',
            '--client',
            client,
            '--since',
            _tokscale_date(started_at),
            '--until',
            _tokscale_date(ended_at),
            '--group-by',
            'client,session,model',
            '--no-spinner',
        ]
        try:
            completed = runner(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=TOKSCALE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            raise TimingError(
                f'Tokscale timed out after {TOKSCALE_TIMEOUT_SECONDS} seconds for client {client}.'
            ) from error
        except OSError as error:
            raise TimingError(f'Tokscale could not run for client {client}: {error}') from error
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or 'unknown error'
            raise TimingError(f'Tokscale failed for client {client}: {detail}')
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise TimingError(f'Tokscale returned invalid JSON for client {client}.') from error
        if not isinstance(payload, dict) or not isinstance(payload.get('entries'), list):
            raise TimingError(f'Tokscale JSON for client {client} has no entries array.')
        snapshots[client] = payload['entries']
    return snapshots


def detect_current_session(
    client: str | None = None, session_id: str | None = None
) -> tuple[str | None, str | None]:
    if client or session_id:
        if not client or not session_id:
            raise TimingError('Client and session ID must be provided together.')
        return client, session_id
    codex_session = os.environ.get('CODEX_THREAD_ID')
    if codex_session:
        return 'codex', codex_session
    return None, None


def tokscale_cli_version(
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str | None:
    try:
        completed = runner(
            [tokscale_executable(), '--version'],
            capture_output=True,
            text=True,
            check=False,
            timeout=TOKSCALE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _classify_tool_activity(name: str, tool_input: str) -> str:
    text = f'{name} {tool_input}'.lower()
    normalized_name = name.lower().rsplit('.', 1)[-1]
    if normalized_name in ('wait', 'wait_agent') or any(
        marker in text for marker in ('request_user_input', 'tools.wait')
    ):
        return 'waiting'
    if any(
        marker in text
        for marker in (
            'python -m unittest',
            'pytest',
            'dart test',
            'flutter test',
            'cargo test',
            'go test',
            'npm test',
            'npm run test',
        )
    ):
        return 'testing'
    if any(
        marker in text
        for marker in (
            'git diff --check',
            'flutter analyze',
            ' lint',
            'analyzer',
            'cargo build',
            'npm run build',
        )
    ):
        return 'verification'
    if any(marker in text for marker in ('apply_patch', 'write_file', 'edit_file')):
        return 'code-generation'
    if any(
        marker in text
        for marker in ('git worktree remove', 'git rebase', 'git merge', 'worktree-integrate')
    ):
        return 'integration'
    if any(
        marker in text
        for marker in ('git worktree add', ' install', 'setup', 'dependency preparation')
    ):
        return 'environment'
    if any(
        marker in text
        for marker in (
            'git diff',
            'git status',
            'git show',
            'codegraph',
            'tools.view_image',
            ' rg ',
            ' sed ',
        )
    ):
        return 'review'
    return 'other'


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
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, TimingError):
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
            except (TimingError, ValueError):
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
        raise TimingError('Codex cached input exceeds total input tokens.')
    if reasoning > total_output:
        raise TimingError('Codex reasoning output exceeds total output tokens.')
    return {
        'input': total_input - cache_read - cache_write,
        'cache_read': cache_read,
        'cache_write': cache_write,
        'output': total_output - reasoning,
        'reasoning': reasoning,
        'total_tokens': total_input + total_output,
    }


def codex_turn_started_at(
    session_id: str, codex_home: Path | None = None
) -> datetime | None:
    root = codex_home or Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    latest = None
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
            is_user_boundary = (
                event.get('type') == 'event_msg' and payload.get('type') == 'user_message'
            ) or (
                event.get('type') == 'response_item'
                and payload.get('type') == 'message'
                and payload.get('role') == 'user'
            )
            if not is_user_boundary or not event.get('timestamp'):
                continue
            try:
                candidate = _parse_timestamp(str(event['timestamp']))
            except (TimingError, ValueError):
                continue
            if latest is None or candidate > latest:
                latest = candidate
    return latest


def analyze_codex_tool_activity(
    session_ids: list[str],
    started_at: datetime,
    ended_at: datetime,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    start = _timestamp(started_at)
    end = _timestamp(ended_at)
    root = codex_home or Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    durations = {category: 0 for category in TOOL_ACTIVITY_CATEGORIES}
    counts = {category: 0 for category in TOOL_ACTIVITY_CATEGORIES}
    warnings = []
    files_found = 0
    incomplete = 0
    for session_id in session_ids:
        paths = _codex_log_paths(root, session_id)
        if not paths:
            warnings.append(f'Codex log not found for registered session {session_id}.')
            continue
        files_found += len(paths)
        pending: dict[str, tuple[datetime, str]] = {}
        for path in paths:
            try:
                lines = path.read_text(encoding='utf-8').splitlines()
            except OSError as error:
                warnings.append(f'Codex log could not be read for session {session_id}: {error}')
                continue
            for line in lines:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    warnings.append(f'Codex log contains invalid JSON for session {session_id}.')
                    continue
                if event.get('type') != 'response_item' or not event.get('timestamp'):
                    continue
                try:
                    event_time = _parse_timestamp(str(event['timestamp']))
                except (TimingError, ValueError):
                    warnings.append(
                        f'Codex log contains an invalid timestamp for session {session_id}.'
                    )
                    continue
                payload = event.get('payload') or {}
                payload_type = payload.get('type')
                call_id = str(payload.get('call_id', ''))
                if payload_type in ('custom_tool_call', 'function_call') and start <= event_time <= end and call_id:
                    pending[call_id] = (
                        event_time,
                        _classify_tool_activity(
                            str(payload.get('name', '')),
                            str(payload.get('input', payload.get('arguments', ''))),
                        ),
                    )
                elif payload_type in ('custom_tool_call_output', 'function_call_output') and call_id in pending:
                    call_start, category = pending.pop(call_id)
                    call_end = min(event_time, end)
                    if call_end >= call_start:
                        durations[category] += _duration_microseconds(call_start, call_end)
                        counts[category] += 1
        incomplete += len(pending)
    if incomplete:
        warnings.append(f'{incomplete} tool call interval(s) had no completed log output.')
    return {
        'status': 'unavailable' if not files_found else ('partial' if warnings else 'available'),
        'durations_microseconds': durations,
        'counts': counts,
        'registered_sessions': len(session_ids),
        'log_files': files_found,
        'warnings': warnings,
    }


def _combine_usage(
    state: dict[str, Any], final_rows_by_client: dict[str, list[dict[str, Any]]], snapshot_error: str | None
) -> tuple[dict[str, Any], list[str]]:
    rows = []
    totals = _empty_usage_totals()
    unavailable = []
    reconciled_sessions = 0
    for session in state['sessions']:
        baseline = session['baseline']
        if baseline['status'] == 'unavailable':
            unavailable.append(
                f"{session['client']}/{session['session_id']}: {baseline.get('error') or 'baseline unavailable'}"
            )
            continue
        if snapshot_error:
            unavailable.append(
                f"{session['client']}/{session['session_id']}: {snapshot_error}"
            )
            continue
        client_rows = final_rows_by_client.get(session['client'], [])
        if not any(
            session_id_matches(
                str(row.get('sessionId', row.get('session_id', ''))),
                session['session_id'],
            )
            for row in client_rows
        ):
            unavailable.append(
                f"{session['client']}/{session['session_id']}: final snapshot has no matching row"
            )
            continue
        try:
            delta = usage_delta(
                session['client'],
                session['session_id'],
                [] if baseline['status'] == 'zero' else baseline['rows'],
                client_rows,
            )
        except TimingError as error:
            unavailable.append(f"{session['client']}/{session['session_id']}: {error}")
            continue
        reconciled_sessions += 1
        rows.extend(delta['rows'])
        for field in totals:
            totals[field] += delta['totals'][field]
    gaps = state.get('attribution_gaps', [])
    for gap in gaps:
        unavailable.append(f"{gap['label']}: {gap['reason']}")
    if not state['sessions']:
        status = 'unavailable'
        unavailable.append('No agent sessions were registered for this task.')
    elif not reconciled_sessions:
        status = 'unavailable'
    elif unavailable:
        status = 'partial'
    else:
        status = 'available'
    return {'status': status, 'rows': rows, 'totals': totals}, unavailable


def _analyze_v2_state(
    state: dict[str, Any],
    ended_at: datetime,
    final_rows_by_client: dict[str, list[dict[str, Any]]],
    snapshot_error: str | None,
    codex_home: Path | None,
) -> dict[str, Any]:
    analyzed = copy.deepcopy(state)
    usage, usage_warnings = _combine_usage(analyzed, final_rows_by_client, snapshot_error)
    codex_sessions = [
        session['session_id']
        for session in analyzed['sessions']
        if session['client'] == 'codex'
    ]
    tool_activity = analyze_codex_tool_activity(
        codex_sessions,
        _parse_timestamp(analyzed['started_at']),
        ended_at,
        codex_home,
    )
    gap_warnings = [
        f"Tool attribution gap for {gap['label']}: {gap['reason']}"
        for gap in analyzed.get('attribution_gaps', [])
    ]
    if gap_warnings:
        if tool_activity['status'] == 'available':
            tool_activity['status'] = 'partial'
        tool_activity['warnings'].extend(gap_warnings)
    analyzed['metrics'] = {
        'usage': usage,
        'tool_activity': tool_activity,
        'warnings': usage_warnings + tool_activity['warnings'],
    }
    return analyzed


def _finish_task_unlocked(
    task_id: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
    final_rows_by_client: dict[str, list[dict[str, Any]]] | None = None,
    snapshot_error: str | None = None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    state = load_task(task_id, root)
    if state['schema_version'] == LEGACY_SCHEMA_VERSION:
        return _finish_legacy_task(state, root, _timestamp(now))
    if state['status'] == 'completed':
        return state
    completed = _timestamp(now)
    if final_rows_by_client is None and snapshot_error is None:
        try:
            final_rows_by_client = capture_tokscale_snapshot(
                [session['client'] for session in state['sessions']],
                _parse_timestamp(state['started_at']),
                completed,
            )
        except TimingError as error:
            final_rows_by_client = {}
            snapshot_error = str(error)
    state = _analyze_v2_state(
        state, completed, final_rows_by_client or {}, snapshot_error, codex_home
    )
    state['status'] = 'completed'
    state['completed_at'] = _serialize_timestamp(completed)
    _write_state(state, root)
    return state


def finish_task(
    task_id: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
    final_rows_by_client: dict[str, list[dict[str, Any]]] | None = None,
    snapshot_error: str | None = None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    with _task_lock(task_id, root):
        return _finish_task_unlocked(
            task_id,
            root,
            now,
            final_rows_by_client,
            snapshot_error,
            codex_home,
        )


def snapshot_task(
    task_id: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    state = load_task(task_id, state_dir)
    if state['schema_version'] == LEGACY_SCHEMA_VERSION or state['status'] == 'completed':
        return state
    ended = _timestamp(now)
    snapshot_error = None
    try:
        rows = capture_tokscale_snapshot(
            [session['client'] for session in state['sessions']],
            _parse_timestamp(state['started_at']),
            ended,
        )
    except TimingError as error:
        rows = {}
        snapshot_error = str(error)
    analyzed = _analyze_v2_state(state, ended, rows, snapshot_error, codex_home)
    analyzed['completed_at'] = _serialize_timestamp(ended)
    return analyzed


def build_report(state: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    if state['schema_version'] == LEGACY_SCHEMA_VERSION:
        return _build_legacy_report(state, now)
    report_end = state.get('completed_at') or _serialize_timestamp(_timestamp(now))
    metrics = state.get('metrics') or {
        'usage': {'status': 'unavailable', 'rows': [], 'totals': _empty_usage_totals()},
        'tool_activity': {
            'status': 'unavailable',
            'durations_microseconds': {category: 0 for category in TOOL_ACTIVITY_CATEGORIES},
            'counts': {category: 0 for category in TOOL_ACTIVITY_CATEGORIES},
            'warnings': ['Task metrics have not been analyzed yet.'],
        },
        'warnings': ['Task metrics have not been analyzed yet.'],
    }
    return {
        'schema_version': SCHEMA_VERSION,
        'task_id': state['task_id'],
        'task': state['task'],
        'repository': state['repository'],
        'worktree': state['worktree'],
        'status': state['status'],
        'started_at': state['started_at'],
        'completed_at': report_end,
        'wall_clock_microseconds': _duration_microseconds(
            _parse_timestamp(state['started_at']), _parse_timestamp(report_end)
        ),
        'session_count': len(state['sessions']),
        'attribution_gap_count': len(state.get('attribution_gaps', [])),
        'tokscale_version': state.get('tokscale_version'),
        'usage': metrics['usage'],
        'tool_activity': metrics['tool_activity'],
        'warnings': state.get('warnings', []) + metrics.get('warnings', []),
    }


def format_duration(microseconds: int) -> str:
    total_milliseconds = microseconds // 1000
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}'


def _format_tokens(value: int | float) -> str:
    return f'{int(value):,}'


def render_markdown(report: dict[str, Any]) -> str:
    if report.get('schema_version') == LEGACY_SCHEMA_VERSION:
        return _render_legacy_markdown(report)
    usage = report['usage']
    totals = usage['totals']
    lines = [
        '### Worktree Task Metrics',
        '',
        f"Task: {report['task']}",
        f"Started: {report['started_at']}",
        f"Completed: {report['completed_at']}",
        f"Worktree: {report['worktree']}",
        '',
        '| Metric | Value |',
        '| --- | ---: |',
        f"| Wall-clock | {format_duration(report['wall_clock_microseconds'])} |",
        f"| Registered sessions | {report['session_count']} |",
        f"| Attribution gaps | {report['attribution_gap_count']} |",
        f"| Tokscale token and cost | {usage['status']} |",
        f"| Tool attribution | {report['tool_activity']['status']} |",
    ]
    if usage['status'] == 'unavailable':
        lines.extend(
            [
                '| Summed model activity | unavailable |',
                '',
                'Tokscale estimated API-equivalent cost: unavailable.',
            ]
        )
    else:
        lines.extend(
            [
                f"| Summed model activity | {format_duration(int(totals['model_activity_ms']) * 1000)} |",
                '',
                '| Token category | Count |',
                '| --- | ---: |',
                f"| input | {_format_tokens(totals['input'])} |",
                f"| cached input | {_format_tokens(totals['cache_read'])} |",
                f"| cache write | {_format_tokens(totals['cache_write'])} |",
                f"| output | {_format_tokens(totals['output'])} |",
                f"| reasoning | {_format_tokens(totals['reasoning'])} |",
                f"| total | {_format_tokens(totals['total_tokens'])} |",
                '',
                f"Tokscale estimated API-equivalent cost: ${totals['cost']:.6f} USD.",
                f"Pricing snapshot: {report['completed_at']}",
            ]
        )
        if usage['rows']:
            lines.extend(
                [
                    '',
                    '| Client | Session | Model | Tokens | Estimated cost (USD) |',
                    '| --- | --- | --- | ---: | ---: |',
                ]
            )
            for row in usage['rows']:
                row_tokens = sum(int(row[field]) for field in TOKEN_FIELDS)
                lines.append(
                    f"| {row['client']} | {row['session_id']} | {row['model']} | "
                    f"{_format_tokens(row_tokens)} | ${row['cost']:.6f} |"
                )
    if report.get('tokscale_version'):
        lines.append(f"Tokscale: {report['tokscale_version']}")
    activity = report['tool_activity']
    lines.extend(
        [
            '',
            '#### Observed Tool Activity',
            '',
            '| Category | Summed duration | Calls |',
            '| --- | ---: | ---: |',
        ]
    )
    for category in TOOL_ACTIVITY_CATEGORIES:
        duration = activity['durations_microseconds'][category]
        count = activity['counts'][category]
        if duration or count:
            lines.append(f'| {category} | {format_duration(duration)} | {count} |')
    if not any(activity['counts'].values()):
        lines.append('| unavailable | unavailable | 0 |')
    lines.extend(
        [
            '',
            'Wall-clock is elapsed task time. Model and tool activity are summed across registered '
            'sessions, may overlap, and are not a wall-clock phase partition.',
            'The Tokscale amount is an estimated API-equivalent cost, not an invoice or subscription '
            'charge.',
        ]
    )
    if report['warnings']:
        lines.extend(['', 'Warnings:'])
        lines.extend(f"- {warning}" for warning in report['warnings'])
    return '\n'.join(lines)


def _validate_legacy_phase(phase: str) -> str:
    if phase not in LEGACY_PHASES:
        raise TimingError(
            f"Unknown legacy phase '{phase}'. Expected one of: {', '.join(LEGACY_PHASES)}"
        )
    return phase


def _close_legacy_interval(state: dict[str, Any], ended: datetime) -> None:
    active_phase = state.get('active_phase')
    active_since = state.get('active_since')
    if active_phase is None or active_since is None:
        raise TimingError('Running legacy ledger has no active interval.')
    started = _parse_timestamp(active_since)
    state['segments'].append(
        {
            'phase': active_phase,
            'started_at': _serialize_timestamp(started),
            'ended_at': _serialize_timestamp(ended),
            'duration_microseconds': _duration_microseconds(started, ended),
        }
    )


def _transition_task_unlocked(
    task_id: str,
    phase: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    state = load_task(task_id, root)
    if state['schema_version'] != LEGACY_SCHEMA_VERSION:
        raise TimingError('Manual phase transitions are not supported by schema-2 receipts.')
    if state['status'] != 'running':
        raise TimingError(f"Legacy ledger is {state['status']}: {task_id}")
    next_phase = _validate_legacy_phase(phase)
    if state['active_phase'] == next_phase:
        return state
    changed = _timestamp(now)
    _close_legacy_interval(state, changed)
    state['active_phase'] = next_phase
    state['active_since'] = _serialize_timestamp(changed)
    _write_state(state, root)
    return state


def transition_task(
    task_id: str,
    phase: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    with _task_lock(task_id, root):
        return _transition_task_unlocked(task_id, phase, root, now)


def pause_task(
    task_id: str, state_dir: Path | None = None, now: datetime | None = None
) -> dict[str, Any]:
    return transition_task(task_id, 'waiting', state_dir, now)


def resume_task(
    task_id: str,
    phase: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    return transition_task(task_id, phase, state_dir, now)


def _finish_legacy_task(
    state: dict[str, Any], state_dir: Path, completed: datetime
) -> dict[str, Any]:
    if state['status'] == 'completed':
        return state
    _close_legacy_interval(state, completed)
    state['status'] = 'completed'
    state['completed_at'] = _serialize_timestamp(completed)
    state['active_phase'] = None
    state['active_since'] = None
    _write_state(state, state_dir)
    return state


def _build_legacy_report(
    state: dict[str, Any], now: datetime | None = None
) -> dict[str, Any]:
    phases: dict[str, int | None] = {phase: None for phase in LEGACY_PHASES}
    for segment in state['segments']:
        phase = _validate_legacy_phase(segment['phase'])
        phases[phase] = (phases[phase] or 0) + int(segment['duration_microseconds'])
    report_end = state.get('completed_at')
    if state['status'] == 'running':
        active_phase = _validate_legacy_phase(state['active_phase'])
        active_start = _parse_timestamp(state['active_since'])
        active_end = _timestamp(now)
        phases[active_phase] = (phases[active_phase] or 0) + _duration_microseconds(
            active_start, active_end
        )
        report_end = _serialize_timestamp(active_end)
    total = sum(value for value in phases.values() if value is not None)
    wall_total = _duration_microseconds(
        _parse_timestamp(state['started_at']), _parse_timestamp(report_end)
    )
    if total != wall_total:
        difference = wall_total - total
        if difference < 0:
            raise TimingError('Recorded legacy phase time exceeds complete wall-clock time.')
        phases['other'] = (phases['other'] or 0) + difference
        total += difference
    return {
        'schema_version': LEGACY_SCHEMA_VERSION,
        'task_id': state['task_id'],
        'task': state['task'],
        'repository': state['repository'],
        'status': state['status'],
        'started_at': state['started_at'],
        'completed_at': report_end,
        'phases': phases,
        'total': total,
    }


def _render_legacy_markdown(report: dict[str, Any]) -> str:
    lines = [
        '### Worktree Task Timing (Legacy Receipt)',
        '',
        f"Task: {report['task']}",
        f"Started: {report['started_at']}",
        f"Completed: {report['completed_at']}",
        '',
        '| Phase | Duration |',
        '| --- | ---: |',
    ]
    for phase in LEGACY_PHASES:
        value = report['phases'][phase]
        duration = 'not applicable' if value is None else format_duration(value)
        lines.append(f'| {phase} | {duration} |')
    lines.append(f"| total | {format_duration(report['total'])} |")
    lines.extend(
        [
            '',
            'This schema-1 ledger predates post-hoc session attribution; token and cost metrics are '
            'unavailable.',
        ]
    )
    return '\n'.join(lines)


def _capture_for_session(
    client: str, session_id: str, at: datetime
) -> tuple[list[dict[str, Any]], str | None]:
    try:
        snapshots = capture_tokscale_snapshot([client], at, at)
        rows = session_usage_rows({'entries': snapshots[client]}, client, session_id)
        return rows, None
    except TimingError as error:
        return [], str(error)


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
        usage = usage_delta(client, session_id, [], matching_rows)
        return {
            'client': client,
            'session_id': session_id,
            'captured_at': _serialize_timestamp(captured_at),
            'status': 'available',
            'source': 'tokscale',
            'cost_status': 'available',
            'rows': usage['rows'],
            'totals': usage['totals'],
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
        warnings.append('No matching Tokscale row or Codex token event was found.')
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


def render_session_usage_markdown(usage: dict[str, Any]) -> str:
    totals = usage['totals']
    lines = [
        '### Session Usage',
        '',
        f"Client: {usage['client']}",
        f"Session: {usage['session_id']}",
        f"Captured: {usage['captured_at']}",
        f"Source: {usage['source']}",
        '',
        '| Token category | Count |',
        '| --- | ---: |',
        f"| input | {_format_tokens(totals['input'])} |",
        f"| cached input | {_format_tokens(totals['cache_read'])} |",
        f"| cache write | {_format_tokens(totals['cache_write'])} |",
        f"| output | {_format_tokens(totals['output'])} |",
        f"| reasoning | {_format_tokens(totals['reasoning'])} |",
        f"| total | {_format_tokens(totals['total_tokens'])} |",
        '',
    ]
    if usage['cost_status'] == 'available':
        lines.append(
            f"Estimated API-equivalent cost: ${totals['cost']:.6f} USD."
        )
    else:
        lines.append('Estimated API-equivalent cost: unavailable.')
    if usage['warnings']:
        lines.extend(['', 'Warnings:'])
        lines.extend(f'- {warning}' for warning in usage['warnings'])
    return '\n'.join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Track a worktree task receipt and analyze logs after the task.'
    )
    parser.add_argument('--state-dir', type=Path, default=default_state_dir())
    subparsers = parser.add_subparsers(dest='command', required=True)

    start = subparsers.add_parser('start')
    start.add_argument('--task', required=True)
    start.add_argument('--repository', default='.')
    start.add_argument('--worktree', default='.')
    start.add_argument('--client')
    start.add_argument('--session-id')

    attach = subparsers.add_parser('attach')
    attach.add_argument('task_id')
    attach.add_argument('--client')
    attach.add_argument('--session-id')
    attach.add_argument('--entire-session', action='store_true')

    gap = subparsers.add_parser('gap')
    gap.add_argument('task_id')
    gap.add_argument('--label', required=True)
    gap.add_argument('--reason', required=True)

    usage = subparsers.add_parser('usage')
    usage.add_argument('--client')
    usage.add_argument('--session-id')

    finish = subparsers.add_parser('finish')
    finish.add_argument('task_id')

    report = subparsers.add_parser('report')
    report.add_argument('task_id')
    return parser


def _build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--state-dir', type=Path, default=default_state_dir())
    subparsers = parser.add_subparsers(dest='command', required=True)
    transition = subparsers.add_parser('transition', add_help=False)
    transition.add_argument('task_id')
    transition.add_argument('phase', choices=LEGACY_PHASES)
    pause = subparsers.add_parser('pause', add_help=False)
    pause.add_argument('task_id')
    resume = subparsers.add_parser('resume', add_help=False)
    resume.add_argument('task_id')
    resume.add_argument('phase', choices=LEGACY_PHASES)
    return parser


def _command_name(arguments: list[str]) -> str | None:
    skip_next = False
    for argument in arguments:
        if skip_next:
            skip_next = False
            continue
        if argument == '--state-dir':
            skip_next = True
            continue
        if not argument.startswith('-'):
            return argument
    return None


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print('ERROR: Python 3.11 or newer is required.', file=sys.stderr)
        return 2
    arguments = list(sys.argv[1:] if argv is None else argv)
    legacy_command = _command_name(arguments) in {'transition', 'pause', 'resume'}
    args = (
        _build_legacy_parser().parse_args(arguments)
        if legacy_command
        else build_parser().parse_args(arguments)
    )
    try:
        if args.command == 'start':
            captured = _timestamp()
            client, session_id = detect_current_session(args.client, args.session_id)
            task_started = (
                codex_turn_started_at(session_id)
                if client == 'codex' and session_id
                else None
            ) or captured
            rows: list[dict[str, Any]] = []
            error = None
            if client and session_id:
                rows, error = _capture_for_session(client, session_id, captured)
            state = start_task(
                args.task,
                str(Path(args.repository).resolve()),
                str(Path(args.worktree).resolve()),
                client,
                session_id,
                rows,
                error,
                args.state_dir,
                task_started,
                tokscale_cli_version(),
            )
            print(f"task_id={state['task_id']}")
            print(f"state={_state_path(state['task_id'], args.state_dir)}")
            if client and session_id:
                print(f'session={client}/{session_id}')
            if error:
                print(f'warning={error}')
        elif args.command == 'attach':
            captured = _timestamp()
            client, session_id = detect_current_session(args.client, args.session_id)
            if not client or not session_id:
                raise TimingError('No supported current session was detected; pass --client and --session-id.')
            rows: list[dict[str, Any]] = []
            error = None
            if not args.entire_session:
                rows, error = _capture_for_session(client, session_id, captured)
            state = attach_session(
                args.task_id,
                client,
                session_id,
                args.entire_session,
                rows,
                error,
                args.state_dir,
                captured,
            )
            print(f"task_id={state['task_id']} session={client}/{session_id}")
            if error:
                print(f'warning={error}')
        elif args.command == 'gap':
            state = record_attribution_gap(
                args.task_id,
                args.label,
                args.reason,
                args.state_dir,
            )
            print(f"task_id={state['task_id']} attribution_gap={args.label}")
        elif args.command == 'usage':
            captured = _timestamp()
            client, session_id = detect_current_session(args.client, args.session_id)
            if not client or not session_id:
                raise TimingError(
                    'No supported current session was detected; pass --client and --session-id.'
                )
            bounds = (
                codex_session_bounds(session_id)
                if client == 'codex'
                else None
            )
            started_at, ended_at = bounds or (captured, captured)
            rows = []
            error = None
            try:
                snapshots = capture_tokscale_snapshot(
                    [client], started_at, ended_at
                )
                rows = snapshots[client]
            except TimingError as usage_error:
                error = str(usage_error)
            usage_report = build_session_usage(
                client,
                session_id,
                captured,
                tokscale_rows=rows,
                snapshot_error=error,
            )
            print(render_session_usage_markdown(usage_report))
        elif args.command == 'transition':
            state = transition_task(args.task_id, args.phase, args.state_dir)
            print(f"task_id={state['task_id']} phase={state['active_phase']}")
        elif args.command == 'pause':
            state = pause_task(args.task_id, args.state_dir)
            print(f"task_id={state['task_id']} phase={state['active_phase']}")
        elif args.command == 'resume':
            state = resume_task(args.task_id, args.phase, args.state_dir)
            print(f"task_id={state['task_id']} phase={state['active_phase']}")
        elif args.command == 'finish':
            state = finish_task(args.task_id, args.state_dir)
            print(render_markdown(build_report(state)))
        else:
            state = snapshot_task(args.task_id, args.state_dir)
            print(render_markdown(build_report(state)))
    except (OSError, ValueError, json.JSONDecodeError, TimingError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
