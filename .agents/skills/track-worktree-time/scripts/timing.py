from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASES = (
    'environment',
    'code-generation',
    'review',
    'verification',
    'testing',
    'integration',
    'waiting',
    'other',
)
STATE_DIRECTORY_NAME = 'codex-worktree-time'
SCHEMA_VERSION = 1


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
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise TimingError(f'Ledger timestamp has no timezone: {value}')
    return parsed.astimezone(timezone.utc)


def _duration_microseconds(start: datetime, end: datetime) -> int:
    delta = end - start
    if delta.total_seconds() < 0:
        raise TimingError('Timing events must remain chronological.')
    return ((delta.days * 86400) + delta.seconds) * 1_000_000 + delta.microseconds


def _validate_phase(phase: str) -> str:
    if phase not in PHASES:
        raise TimingError(f"Unknown phase '{phase}'. Expected one of: {', '.join(PHASES)}")
    return phase


def _state_path(task_id: str, state_dir: Path) -> Path:
    return state_dir / f'{task_id}.json'


def _write_state(state: dict[str, Any], state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    target = _state_path(state['task_id'], state_dir)
    temporary = state_dir / f".{state['task_id']}.{uuid.uuid4().hex}.tmp"
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    os.replace(temporary, target)


def load_task(task_id: str, state_dir: Path | None = None) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    path = _state_path(task_id, root)
    if not path.is_file():
        raise TimingError(f'Timing ledger not found: {path}')
    state = json.loads(path.read_text(encoding='utf-8'))
    if state.get('schema_version') != SCHEMA_VERSION:
        raise TimingError(f'Unsupported timing ledger schema: {state.get("schema_version")}')
    return state


def start_task(
    task: str,
    repository: str,
    phase: str = 'environment',
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not task.strip():
        raise TimingError('Task summary must contain text.')
    if not repository.strip():
        raise TimingError('Repository must contain a path or identifier.')
    active_phase = _validate_phase(phase)
    started = _timestamp(now)
    task_id = uuid.uuid4().hex
    state = {
        'schema_version': SCHEMA_VERSION,
        'task_id': task_id,
        'task': task.strip(),
        'repository': repository.strip(),
        'status': 'running',
        'started_at': _serialize_timestamp(started),
        'completed_at': None,
        'active_phase': active_phase,
        'active_since': _serialize_timestamp(started),
        'segments': [],
    }
    _write_state(state, state_dir or default_state_dir())
    return state


def _close_active_interval(state: dict[str, Any], ended: datetime) -> None:
    active_phase = state.get('active_phase')
    active_since = state.get('active_since')
    if active_phase is None or active_since is None:
        raise TimingError('Running timing ledger has no active interval.')
    started = _parse_timestamp(active_since)
    state['segments'].append(
        {
            'phase': active_phase,
            'started_at': _serialize_timestamp(started),
            'ended_at': _serialize_timestamp(ended),
            'duration_microseconds': _duration_microseconds(started, ended),
        }
    )


def transition_task(
    task_id: str,
    phase: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    state = load_task(task_id, root)
    if state['status'] != 'running':
        raise TimingError(f"Timing ledger is {state['status']}: {task_id}")
    next_phase = _validate_phase(phase)
    if state['active_phase'] == next_phase:
        return state
    changed = _timestamp(now)
    _close_active_interval(state, changed)
    state['active_phase'] = next_phase
    state['active_since'] = _serialize_timestamp(changed)
    _write_state(state, root)
    return state


def pause_task(
    task_id: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    return transition_task(task_id, 'waiting', state_dir, now)


def resume_task(
    task_id: str,
    phase: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    return transition_task(task_id, phase, state_dir, now)


def finish_task(
    task_id: str,
    state_dir: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = state_dir or default_state_dir()
    state = load_task(task_id, root)
    if state['status'] == 'completed':
        return state
    completed = _timestamp(now)
    _close_active_interval(state, completed)
    state['status'] = 'completed'
    state['completed_at'] = _serialize_timestamp(completed)
    state['active_phase'] = None
    state['active_since'] = None
    _write_state(state, root)
    return state


def build_report(
    state: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    phases: dict[str, int | None] = {phase: None for phase in PHASES}
    for segment in state['segments']:
        phase = _validate_phase(segment['phase'])
        phases[phase] = (phases[phase] or 0) + int(segment['duration_microseconds'])

    report_end = state.get('completed_at')
    if state['status'] == 'running':
        active_phase = _validate_phase(state['active_phase'])
        active_start = _parse_timestamp(state['active_since'])
        active_end = _timestamp(now)
        phases[active_phase] = (phases[active_phase] or 0) + _duration_microseconds(
            active_start, active_end
        )
        report_end = _serialize_timestamp(active_end)

    total = sum(value for value in phases.values() if value is not None)
    wall_total = _duration_microseconds(
        _parse_timestamp(state['started_at']),
        _parse_timestamp(report_end),
    )
    if total != wall_total:
        difference = wall_total - total
        if difference < 0:
            raise TimingError('Recorded phase time exceeds complete wall-clock time.')
        phases['other'] = (phases['other'] or 0) + difference
        total += difference

    return {
        'task_id': state['task_id'],
        'task': state['task'],
        'repository': state['repository'],
        'status': state['status'],
        'started_at': state['started_at'],
        'completed_at': report_end,
        'phases': phases,
        'total': total,
    }


def format_duration(microseconds: int) -> str:
    total_milliseconds = microseconds // 1000
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}'


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        '### Worktree Task Timing',
        '',
        f"Task: {report['task']}",
        f"Started: {report['started_at']}",
        f"Completed: {report['completed_at']}",
        '',
        '| Phase | Duration |',
        '| --- | ---: |',
    ]
    for phase in PHASES:
        value = report['phases'][phase]
        duration = 'not applicable' if value is None else format_duration(value)
        lines.append(f'| {phase} | {duration} |')
    lines.append(f"| total | {format_duration(report['total'])} |")
    return '\n'.join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Track wall-clock phases for a worktree task.')
    parser.add_argument('--state-dir', type=Path, default=default_state_dir())
    subparsers = parser.add_subparsers(dest='command', required=True)

    start = subparsers.add_parser('start')
    start.add_argument('--task', required=True)
    start.add_argument('--repository', default='.')
    start.add_argument('--phase', choices=PHASES, default='environment')

    transition = subparsers.add_parser('transition')
    transition.add_argument('task_id')
    transition.add_argument('phase', choices=PHASES)

    pause = subparsers.add_parser('pause')
    pause.add_argument('task_id')

    resume = subparsers.add_parser('resume')
    resume.add_argument('task_id')
    resume.add_argument('phase', choices=PHASES)

    finish = subparsers.add_parser('finish')
    finish.add_argument('task_id')

    report = subparsers.add_parser('report')
    report.add_argument('task_id')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == 'start':
            state = start_task(args.task, args.repository, args.phase, args.state_dir)
            print(f"task_id={state['task_id']}")
            print(f"state={_state_path(state['task_id'], args.state_dir)}")
            print(f"phase={state['active_phase']}")
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
            state = load_task(args.task_id, args.state_dir)
            print(render_markdown(build_report(state)))
    except (OSError, ValueError, json.JSONDecodeError, TimingError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
