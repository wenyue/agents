from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


TOKSCALE_TIMEOUT_SECONDS = 30
TOKEN_FIELDS = ('input', 'output', 'reasoning', 'cache_read', 'cache_write')
USAGE_ACTIVITY_FIELDS = ('message_count', 'model_activity_ms')
COORDINATION_TOOLS = (
    'spawn_agent',
    'wait_agent',
    'list_agents',
    'send_message',
    'followup_task',
    'interrupt_agent',
)
TERMINAL_AGENT_STATES = ('completed', 'failed', 'cancelled', 'canceled', 'errored')


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


def _duration_milliseconds(start: datetime, end: datetime) -> int:
    delta = end - start
    if delta.total_seconds() < 0:
        raise UsageError('Diagnostic timestamps must remain chronological.')
    return int(delta.total_seconds() * 1000)


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
    performance = row.get('performance') or {}
    if not isinstance(performance, dict):
        raise UsageError('Tokscale performance data must be an object.')
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
        'message_count': _integer(
            row.get('messageCount', row.get('message_count')), 'messageCount'
        ),
        'model_activity_ms': _integer(
            performance.get('totalDurationMs', row.get('model_activity_ms')),
            'performance.totalDurationMs',
        ),
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
        'message_count': 0,
        'model_activity_ms': 0,
    }


def _aggregate_usage(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int | float]]:
    normalized_rows = [normalize_usage_row(row) for row in rows]
    totals = _empty_usage_totals()
    for row in normalized_rows:
        for field in TOKEN_FIELDS:
            totals[field] += row[field]
        for field in USAGE_ACTIVITY_FIELDS:
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


def _codex_events(
    session_id: str, codex_home: Path | None = None
) -> tuple[list[dict[str, Any]], list[str]]:
    root = codex_home or Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    events = []
    warnings = []
    invalid_json = 0
    for path in _codex_log_paths(root, session_id):
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except OSError as error:
            warnings.append(f'Codex log could not be read: {error}')
            continue
        for line in lines:
            try:
                event = json.loads(line)
                event['_parsed_timestamp'] = _parse_timestamp(str(event['timestamp']))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, UsageError):
                invalid_json += 1
                continue
            events.append(event)
    if invalid_json:
        warnings.append(f'{invalid_json} Codex log line(s) were invalid.')
    events.sort(key=lambda event: event['_parsed_timestamp'])
    return events, warnings


def codex_session_bounds(
    session_id: str, codex_home: Path | None = None
) -> tuple[datetime, datetime] | None:
    events, _ = _codex_events(session_id, codex_home)
    if not events:
        return None
    return events[0]['_parsed_timestamp'], events[-1]['_parsed_timestamp']


def codex_current_turn_bounds(
    session_id: str, codex_home: Path | None = None
) -> tuple[datetime, datetime] | None:
    events, _ = _codex_events(session_id, codex_home)
    if not events:
        return None
    user_boundaries = []
    for event in events:
        payload = event.get('payload') or {}
        if (
            event.get('type') == 'event_msg'
            and payload.get('type') == 'user_message'
        ) or (
            event.get('type') == 'response_item'
            and payload.get('type') == 'message'
            and payload.get('role') == 'user'
        ):
            user_boundaries.append(event['_parsed_timestamp'])
    if not user_boundaries:
        return None
    return max(user_boundaries), events[-1]['_parsed_timestamp']


def _normalize_tool_name(name: str) -> str:
    normalized = name.strip().lower().replace('__', '.').replace('::', '.')
    return normalized.rsplit('.', 1)[-1] or 'unknown'


def _jsonish(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _text_fragments(value: Any) -> list[str]:
    value = _jsonish(value)
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [fragment for item in value.values() for fragment in _text_fragments(item)]
    if isinstance(value, list):
        return [fragment for item in value for fragment in _text_fragments(item)]
    return []


def _structured_error(value: Any) -> bool:
    value = _jsonish(value)
    if isinstance(value, dict):
        if value.get('isError') is True or value.get('is_error') is True:
            return True
        if str(value.get('status', '')).lower() in ('error', 'failed'):
            return True
        return any(_structured_error(item) for item in value.values())
    if isinstance(value, list):
        return any(_structured_error(item) for item in value)
    return False


def _tool_failed(tool_name: str, output: Any) -> bool:
    if _structured_error(output):
        return True
    return any(
        re.search(
            r'^(?:execution error:|script (?:failed\b|error:)|tool error:|collab .* failed:)',
            text.strip().lower(),
        )
        for text in _text_fragments(output)
    )


def _call_fingerprint(tool_name: str, payload: dict[str, Any]) -> str:
    arguments = str(payload.get('input', payload.get('arguments', '')))
    return hashlib.sha256(f'{tool_name}\0{arguments}'.encode()).hexdigest()


def _shell_command(payload: dict[str, Any]) -> str | None:
    if _normalize_tool_name(str(payload.get('name', ''))) not in (
        'exec',
        'shell_command',
    ):
        return None
    arguments = payload.get('input', payload.get('arguments', ''))
    parsed = _jsonish(arguments)
    if isinstance(parsed, dict) and isinstance(parsed.get('command'), str):
        return parsed['command'].strip()
    if not isinstance(arguments, str):
        return None

    double_quoted = re.search(
        r'(?:(?:"command"|\'command\'|command))\s*:\s*'
        r'("(?:\\.|[^"\\])*")',
        arguments,
        re.DOTALL,
    )
    if double_quoted:
        try:
            return str(json.loads(double_quoted.group(1))).strip()
        except json.JSONDecodeError:
            return None
    single_quoted = re.search(
        r"(?:\"command\"|'command'|command)\s*:\s*'((?:\\.|[^'\\])*)'",
        arguments,
        re.DOTALL,
    )
    if single_quoted:
        return re.sub(r"\\(['\\])", r'\1', single_quoted.group(1)).strip()

    stripped = arguments.strip()
    if re.match(r'^(?:&\s*)?(?:powershell|pwsh)(?:\.exe)?\b', stripped, re.I):
        return stripped
    if re.match(r'^(?:sh|bash)\s+', stripped, re.I):
        return stripped
    return None


def _is_diagnostic_call(payload: dict[str, Any]) -> bool:
    command = _shell_command(payload)
    if not command:
        return False
    return bool(
        re.search(
            r'^\s*(?:&\s*)?(?:powershell|pwsh)(?:\.exe)?\b.*?'
            r'-file\s+"?\S*diagnose-agent-session[\\/]scripts[\\/]'
            r'task-metrics\.ps1"?\s+diagnose(?:\s|$)',
            command,
            re.IGNORECASE,
        )
        or re.search(
            r'^\s*(?:sh|bash)\s+"?\S*diagnose-agent-session/scripts/'
            r'task-metrics\.sh"?\s+diagnose(?:\s|$)',
            command,
            re.IGNORECASE,
        )
    )


def _spawned_agent_aliases(output: Any) -> tuple[str | None, set[str]]:
    data = _jsonish(output)
    if isinstance(data, dict):
        aliases = {
            str(data[field])
            for field in ('agent_id', 'task_name')
            if data.get(field)
        }
        if aliases:
            canonical = str(data.get('task_name') or data.get('agent_id'))
            return canonical, aliases
    return None, set()


def _wait_evidence(output: Any) -> tuple[bool, dict[str, str]]:
    data = _jsonish(output)
    if not isinstance(data, dict):
        return False, {}
    statuses = data.get('status') or {}
    terminal = {}
    if isinstance(statuses, dict):
        for agent_id, raw_status in statuses.items():
            if isinstance(raw_status, dict):
                state = next(
                    (name for name in TERMINAL_AGENT_STATES if name in raw_status),
                    '',
                )
            else:
                state = str(raw_status).lower()
            if state in TERMINAL_AGENT_STATES:
                terminal[str(agent_id)] = state
    return bool(data.get('timed_out')), terminal


def _listed_agent_evidence(output: Any) -> tuple[set[str], set[str], set[str]]:
    data = _jsonish(output)
    if not isinstance(data, dict) or not isinstance(data.get('agents'), list):
        return set(), set(), set()
    live = set()
    completed = set()
    failed = set()
    for agent in data['agents']:
        if not isinstance(agent, dict):
            continue
        name = str(agent.get('agent_name', ''))
        if not name or name == '/root':
            continue
        raw_status = agent.get('agent_status', '')
        if isinstance(raw_status, dict):
            statuses = {str(key).lower() for key in raw_status}
            status = next(
                (
                    candidate
                    for candidate in (
                        'running',
                        'idle',
                        'waiting',
                        *TERMINAL_AGENT_STATES,
                    )
                    if candidate in statuses
                ),
                '',
            )
        else:
            status = str(raw_status).lower()
        if status in ('running', 'idle', 'waiting'):
            live.add(name)
        elif status == 'completed':
            completed.add(name)
        elif status in ('failed', 'cancelled', 'canceled', 'errored'):
            failed.add(name)
    return live, completed, failed


def analyze_codex_tool_activity(
    session_id: str,
    codex_home: Path | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> dict[str, Any]:
    events, warnings = _codex_events(session_id, codex_home)
    if not events:
        return {
            'status': 'unavailable',
            'started_calls': 0,
            'completed_calls': 0,
            'failed_calls': 0,
            'incomplete_calls': 0,
            'repeated_identical_calls': 0,
            'observed_duration_ms': 0,
            'longest_call_ms': 0,
            'tools': [],
            'coordination': {},
            'findings': [],
            'warnings': warnings or ['Codex log was not found.'],
        }

    scope_start = _timestamp(started_at or events[0]['_parsed_timestamp'])
    scope_end = _timestamp(ended_at or events[-1]['_parsed_timestamp'])
    tool_rows: dict[str, dict[str, int | str]] = {}
    pending: dict[str, tuple[datetime, str, str, bool]] = {}
    live_agents: set[str] = set()
    agent_aliases: dict[str, str] = {}
    scope_spawned_agents: set[str] = set()
    scope_completed_agents: set[str] = set()
    scope_failed_agents: set[str] = set()
    scope_list_completed: set[str] = set()
    scope_list_failed: set[str] = set()
    observed_peak_live = 0
    wait_without_live = 0
    wait_timeouts = 0
    consecutive_wait_timeouts = 0
    max_consecutive_wait_timeouts = 0
    previous_fingerprint = None
    repeated_identical_calls = 0

    for event in events:
        event_time = event['_parsed_timestamp']
        if event_time > scope_end:
            break
        in_scope = scope_start <= event_time <= scope_end
        if in_scope:
            observed_peak_live = max(observed_peak_live, len(live_agents))
        if event.get('type') != 'response_item':
            continue
        payload = event.get('payload') or {}
        payload_type = payload.get('type')
        call_id = str(payload.get('call_id', ''))
        if payload_type in ('custom_tool_call', 'function_call') and call_id:
            if _is_diagnostic_call(payload):
                continue
            tool_name = _normalize_tool_name(str(payload.get('name', '')))
            fingerprint = _call_fingerprint(tool_name, payload)
            pending[call_id] = (event_time, tool_name, fingerprint, in_scope)
            if in_scope:
                row = tool_rows.setdefault(
                    tool_name,
                    {
                        'name': tool_name,
                        'started': 0,
                        'completed': 0,
                        'failed': 0,
                        'incomplete': 0,
                        'duration_ms': 0,
                        'longest_ms': 0,
                    },
                )
                row['started'] = int(row['started']) + 1
                if fingerprint == previous_fingerprint:
                    repeated_identical_calls += 1
                previous_fingerprint = fingerprint
                if tool_name == 'wait_agent' and not live_agents:
                    wait_without_live += 1
        elif (
            payload_type in ('custom_tool_call_output', 'function_call_output')
            and call_id in pending
        ):
            call_start, tool_name, _, call_in_scope = pending.pop(call_id)
            output = payload.get('output')
            failed = _tool_failed(tool_name, output)

            if tool_name == 'spawn_agent' and not failed:
                agent_id, aliases = _spawned_agent_aliases(output)
                if agent_id:
                    for alias in aliases:
                        agent_aliases[alias] = agent_id
                    live_agents.add(agent_id)
                    if call_in_scope:
                        scope_spawned_agents.add(agent_id)
            elif tool_name == 'wait_agent':
                timed_out, terminal = _wait_evidence(output)
                if call_in_scope:
                    if timed_out:
                        consecutive_wait_timeouts += 1
                        max_consecutive_wait_timeouts = max(
                            max_consecutive_wait_timeouts,
                            consecutive_wait_timeouts,
                        )
                        wait_timeouts += 1
                    else:
                        consecutive_wait_timeouts = 0
                for agent_id, state in terminal.items():
                    canonical_id = agent_aliases.get(agent_id, agent_id)
                    live_agents.discard(canonical_id)
                    if state == 'completed':
                        if call_in_scope:
                            scope_completed_agents.add(canonical_id)
                    else:
                        if call_in_scope:
                            scope_failed_agents.add(canonical_id)
            elif tool_name == 'list_agents' and not failed:
                listed_live, listed_completed, listed_failed = (
                    _listed_agent_evidence(output)
                )
                listed_live = {
                    agent_aliases.get(agent_id, agent_id)
                    for agent_id in listed_live
                }
                listed_completed = {
                    agent_aliases.get(agent_id, agent_id)
                    for agent_id in listed_completed
                }
                listed_failed = {
                    agent_aliases.get(agent_id, agent_id)
                    for agent_id in listed_failed
                }
                live_agents = listed_live
                if call_in_scope:
                    scope_list_completed.update(listed_completed)
                    scope_list_failed.update(listed_failed)
            if in_scope:
                observed_peak_live = max(observed_peak_live, len(live_agents))
            if call_in_scope:
                duration_ms = _duration_milliseconds(call_start, event_time)
                row = tool_rows[tool_name]
                row['completed'] = int(row['completed']) + 1
                row['duration_ms'] = int(row['duration_ms']) + duration_ms
                row['longest_ms'] = max(int(row['longest_ms']), duration_ms)
                if failed:
                    row['failed'] = int(row['failed']) + 1

    for _, tool_name, _, call_in_scope in pending.values():
        if call_in_scope:
            row = tool_rows[tool_name]
            row['incomplete'] = int(row['incomplete']) + 1

    started_calls = sum(int(row['started']) for row in tool_rows.values())
    completed_calls = sum(int(row['completed']) for row in tool_rows.values())
    failed_calls = sum(int(row['failed']) for row in tool_rows.values())
    incomplete_calls = sum(int(row['incomplete']) for row in tool_rows.values())
    if incomplete_calls:
        warnings.append(f'{incomplete_calls} tool call(s) had no completed log output.')

    findings = []
    if incomplete_calls:
        findings.append('incomplete-tool-calls')
    if failed_calls:
        findings.append('failed-tool-calls')
    if wait_without_live:
        findings.append('wait-without-observed-live-agent')
    if scope_failed_agents or scope_list_failed:
        findings.append('agent-failures')

    coordination = {name: 0 for name in COORDINATION_TOOLS}
    for name in COORDINATION_TOOLS:
        coordination[name] = int(tool_rows.get(name, {}).get('started', 0))
    coordination.update(
        {
            'spawn_successes': len(scope_spawned_agents),
            'spawn_failures': int(tool_rows.get('spawn_agent', {}).get('failed', 0)),
            'completed_agents': len(
                scope_completed_agents | scope_list_completed
            ),
            'failed_agents': len(scope_failed_agents | scope_list_failed),
            'observed_peak_live_agents': observed_peak_live,
            'observed_live_agents_at_end': len(live_agents),
            'wait_timeouts': wait_timeouts,
            'max_consecutive_wait_timeouts': max_consecutive_wait_timeouts,
            'wait_without_observed_live_agent': wait_without_live,
        }
    )
    return {
        'status': 'partial' if warnings else 'available',
        'started_calls': started_calls,
        'completed_calls': completed_calls,
        'failed_calls': failed_calls,
        'incomplete_calls': incomplete_calls,
        'repeated_identical_calls': repeated_identical_calls,
        'observed_duration_ms': sum(int(row['duration_ms']) for row in tool_rows.values()),
        'longest_call_ms': max(
            (int(row['longest_ms']) for row in tool_rows.values()), default=0
        ),
        'tools': [tool_rows[name] for name in sorted(tool_rows)],
        'coordination': coordination,
        'findings': findings,
        'warnings': warnings,
    }


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
    return _normalize_codex_token_totals(latest[1])


def _normalize_codex_token_totals(raw: dict[str, Any]) -> dict[str, int]:
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


def read_codex_token_delta(
    session_id: str,
    started_at: datetime,
    ended_at: datetime,
    codex_home: Path | None = None,
) -> dict[str, int] | None:
    events, _ = _codex_events(session_id, codex_home)
    before = None
    after = None
    for event in events:
        event_time = event['_parsed_timestamp']
        payload = event.get('payload') or {}
        info = payload.get('info') or {}
        raw = info.get('total_token_usage')
        if (
            event.get('type') != 'event_msg'
            or payload.get('type') != 'token_count'
            or not isinstance(raw, dict)
        ):
            continue
        totals = _normalize_codex_token_totals(raw)
        if event_time < started_at:
            before = totals
        if started_at <= event_time <= ended_at:
            after = totals
    if after is None:
        return None
    baseline = before or {field: 0 for field in (*TOKEN_FIELDS, 'total_tokens')}
    delta = {}
    for field in (*TOKEN_FIELDS, 'total_tokens'):
        value = after[field] - baseline[field]
        if value < 0:
            raise UsageError(f'Codex cumulative token counter decreased for {field}.')
        delta[field] = value
    return delta


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


def build_codex_turn_usage(
    session_id: str,
    captured_at: datetime,
    bounds: tuple[datetime, datetime] | None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    delta = (
        None
        if bounds is None
        else read_codex_token_delta(
            session_id, bounds[0], bounds[1], codex_home
        )
    )
    totals = _empty_usage_totals()
    warnings = []
    if delta is None:
        warnings.append('Current-turn cumulative token evidence was not found.')
    else:
        totals.update(delta)
    return {
        'client': 'codex',
        'session_id': session_id,
        'captured_at': _serialize_timestamp(captured_at),
        'status': 'unavailable' if delta is None else 'available',
        'source': 'codex-log-delta' if delta is not None else 'none',
        'cost_status': 'unavailable',
        'rows': [],
        'totals': totals,
        'warnings': warnings,
    }


def _format_tokens(value: int | float) -> str:
    return f'{int(value):,}'


def _unique_problems(messages: list[str]) -> list[str]:
    return list(dict.fromkeys(message.strip() for message in messages if message.strip()))


def _build_scope_report(
    name: str,
    usage: dict[str, Any],
    tool_activity: dict[str, Any],
    bounds: tuple[datetime, datetime] | None,
) -> dict[str, Any]:
    totals = usage['totals']
    return {
        'name': name,
        'span_ms': (
            None if bounds is None else _duration_milliseconds(bounds[0], bounds[1])
        ),
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
        'message_count': int(totals['message_count']),
        'model_activity_ms': (
            int(totals['model_activity_ms'])
            if usage['source'] == 'tokscale'
            else None
        ),
        'tool_activity': tool_activity,
        'findings': list(tool_activity.get('findings', [])),
        'problems': _unique_problems(
            list(usage.get('warnings', []))
            + list(tool_activity.get('warnings', []))
        ),
    }


def build_diagnostic_report(
    session_usage: dict[str, Any],
    session_activity: dict[str, Any],
    session_bounds: tuple[datetime, datetime] | None,
    *,
    turn_usage: dict[str, Any] | None = None,
    turn_activity: dict[str, Any] | None = None,
    turn_bounds: tuple[datetime, datetime] | None = None,
    selected_scope: str = 'both',
) -> dict[str, Any]:
    scopes = []
    if selected_scope in ('turn', 'both') and turn_usage is not None and turn_activity is not None:
        scopes.append(_build_scope_report('current turn', turn_usage, turn_activity, turn_bounds))
    if selected_scope in ('session', 'both'):
        scopes.append(
            _build_scope_report(
                'whole session', session_usage, session_activity, session_bounds
            )
        )
    problems = [problem for scope in scopes for problem in scope['problems']]
    if selected_scope in ('turn', 'both') and turn_usage is None:
        problems.append('Current-turn diagnostics are unavailable for this client.')
    findings = [
        f"{scope['name']}: {finding}"
        for scope in scopes
        for finding in scope['findings']
    ]
    return {
        'client': session_usage['client'],
        'session_id': session_usage['session_id'],
        'selected_scope': selected_scope,
        'scopes': scopes,
        'findings': _unique_problems(findings),
        'problems': _unique_problems(problems),
    }


def _render_scope(lines: list[str], scope: dict[str, Any]) -> None:
    tokens = scope['tokens']
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
    lines.extend(
        [
        f"#### {scope['name'].title()}",
        f"- Span: {scope['span_ms']} ms"
        if scope['span_ms'] is not None
        else '- Span: unavailable',
        f'- Tokens: {token_summary}',
        f"- Estimated API-equivalent cost: {scope['cost']}",
        (
            f"- Model activity: {scope['model_activity_ms']} ms across "
            f"{scope['message_count']} message(s)"
            if scope['model_activity_ms'] is not None
            else '- Model activity: unavailable'
        ),
        ]
    )
    activity = scope['tool_activity']
    if activity['status'] == 'unavailable':
        lines.extend(['- Tool calls: unavailable', '- Agent coordination: unavailable'])
    else:
        lines.append(
            f"- Tool calls: {activity['started_calls']} started, "
            f"{activity['completed_calls']} completed, {activity['failed_calls']} failed, "
            f"{activity['incomplete_calls']} incomplete"
        )
        lines.append(
            f"- Tool timing: {activity['observed_duration_ms']} ms summed, "
            f"{activity['longest_call_ms']} ms longest, "
            f"{activity['repeated_identical_calls']} consecutive identical repeat(s)"
        )
        tool_summary = ', '.join(
            f"{tool['name']}={tool['started']} started/{tool['failed']} failed "
            f"({tool['duration_ms']} ms)"
            for tool in activity['tools']
        ) or 'none'
        lines.append(f'- Tools: {tool_summary}')
        coordination = activity['coordination']
        calls = ', '.join(
            f'{name}={coordination.get(name, 0)}' for name in COORDINATION_TOOLS
        )
        lines.append(f'- Agent coordination calls: {calls}')
        lines.append(
            '- Agent lifecycle: '
            f"spawned={coordination.get('spawn_successes', 0)}, "
            f"spawn failures={coordination.get('spawn_failures', 0)}, "
            f"completed={coordination.get('completed_agents', 0)}, "
            f"failed={coordination.get('failed_agents', 0)}, "
            f"observed peak live={coordination.get('observed_peak_live_agents', 0)}, "
            f"observed live at end={coordination.get('observed_live_agents_at_end', 0)}"
        )
        lines.append(
            '- Wait behavior: '
            f"timeouts={coordination.get('wait_timeouts', 0)}, "
            f"max consecutive timeouts={coordination.get('max_consecutive_wait_timeouts', 0)}, "
            'without observed live agent='
            f"{coordination.get('wait_without_observed_live_agent', 0)}"
        )


def render_diagnostic_markdown(report: dict[str, Any]) -> str:
    lines = [
        '### Agent Session Diagnostics',
        f"- Session: {report['client']}/{report['session_id']}",
        f"- Requested scope: {report['selected_scope']}",
    ]
    for scope in report['scopes']:
        lines.append('')
        _render_scope(lines, scope)
    lines.append('')
    lines.append(
        f"- Findings: {'; '.join(report['findings'])}"
        if report['findings']
        else '- Findings: none from available evidence'
    )
    if report['problems']:
        lines.append(f"- Problems: {'; '.join(report['problems'])}")
    return '\n'.join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Diagnose one stable agent session.')
    subparsers = parser.add_subparsers(dest='command', required=True)
    diagnose = subparsers.add_parser('diagnose')
    diagnose.add_argument('--client')
    diagnose.add_argument('--session-id')
    diagnose.add_argument(
        '--scope', choices=('turn', 'session', 'both'), default='both'
    )
    return parser


def unavailable_tool_activity(problem: str) -> dict[str, Any]:
    return {
        'status': 'unavailable',
        'started_calls': 0,
        'completed_calls': 0,
        'failed_calls': 0,
        'incomplete_calls': 0,
        'repeated_identical_calls': 0,
        'observed_duration_ms': 0,
        'longest_call_ms': 0,
        'tools': [],
        'coordination': {},
        'findings': [],
        'warnings': [problem],
    }


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 10):
        print('ERROR: Python 3.10 or newer is required.', file=sys.stderr)
        return 2
    args = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        captured = _timestamp()
        client, session_id = detect_current_session(args.client, args.session_id)
        if not client or not session_id:
            raise UsageError(
                'No supported current session was detected; pass --client and --session-id.'
            )
        session_bounds = codex_session_bounds(session_id) if client == 'codex' else None
        started_at, ended_at = session_bounds or (None, None)
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
        if client == 'codex':
            session_activity = analyze_codex_tool_activity(
                session_id,
                started_at=session_bounds[0] if session_bounds else None,
                ended_at=session_bounds[1] if session_bounds else None,
            )
            turn_bounds = codex_current_turn_bounds(session_id)
            turn_usage = build_codex_turn_usage(
                session_id, captured, turn_bounds
            )
            turn_activity = (
                analyze_codex_tool_activity(
                    session_id,
                    started_at=turn_bounds[0],
                    ended_at=turn_bounds[1],
                )
                if turn_bounds
                else unavailable_tool_activity(
                    'Current-turn boundary was not found in the Codex log.'
                )
            )
        else:
            session_activity = unavailable_tool_activity(
                f'Local tool diagnostics are unavailable for client {client}.'
            )
            turn_bounds = None
            turn_usage = None
            turn_activity = None
        report = build_diagnostic_report(
            usage_report,
            session_activity,
            session_bounds,
            turn_usage=turn_usage,
            turn_activity=turn_activity,
            turn_bounds=turn_bounds,
            selected_scope=args.scope,
        )
        print(render_diagnostic_markdown(report))
    except (OSError, ValueError, json.JSONDecodeError, UsageError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
