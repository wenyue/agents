from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import bootstrap


_SESSION_PREFIX = 'setup-project-agents-'
_SESSION_MARKER = '.workflow-session'
_SESSION_MARKER_CONTENT = b'setup-project-agents-workflow-v1\n'
_WORKFLOW_CONTEXT = 'workflow.json'
_COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')


class WorkflowError(ValueError):
    """Raised when the public two-stage setup workflow cannot continue safely."""


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, 'is_junction') and path.is_junction()
    )


def _write_exclusive(path: Path, content: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
    finally:
        os.close(descriptor)


def _create_session() -> Path:
    session = Path(tempfile.mkdtemp(prefix=_SESSION_PREFIX)).absolute()
    try:
        if os.name == 'posix':
            session.chmod(0o700)
        _write_exclusive(session / _SESSION_MARKER, _SESSION_MARKER_CONTENT)
        return session
    except BaseException:
        shutil.rmtree(session, ignore_errors=True)
        raise


def _owned_session(value: Path) -> Path:
    session = Path(value).absolute()
    temporary_root = Path(tempfile.gettempdir()).absolute()
    if session.parent != temporary_root or not session.name.startswith(_SESSION_PREFIX):
        raise WorkflowError('session is not a workflow-owned system-temporary directory')
    current = Path(session.anchor)
    for part in session.parts[1:]:
        current /= part
        try:
            status = current.lstat()
        except OSError as error:
            raise WorkflowError(f'session path cannot be inspected: {current}') from error
        if stat.S_ISLNK(status.st_mode) or _is_link_like(current):
            raise WorkflowError(f'session path contains an unsafe link: {current}')
    status = session.stat()
    if not stat.S_ISDIR(status.st_mode):
        raise WorkflowError('session is not a directory')
    if os.name == 'posix' and (
        status.st_uid != os.geteuid() or stat.S_IMODE(status.st_mode) != 0o700
    ):
        raise WorkflowError('session must be private, exact mode 0700, and current-user-owned')
    marker = session / _SESSION_MARKER
    if _is_link_like(marker) or not marker.is_file():
        raise WorkflowError('session ownership marker is missing or unsafe')
    try:
        content = marker.read_bytes()
    except OSError as error:
        raise WorkflowError('session ownership marker cannot be read') from error
    if content != _SESSION_MARKER_CONTENT:
        raise WorkflowError('session ownership marker is invalid')
    return session


def _clear_readonly_files(root: Path) -> None:
    for directory, directories, files in os.walk(root, topdown=True, followlinks=False):
        parent = Path(directory)
        directories[:] = [
            name for name in directories if not _is_link_like(parent / name)
        ]
        for name in files:
            path = parent / name
            if not _is_link_like(path):
                path.chmod(stat.S_IREAD | stat.S_IWRITE)


def _remove_session(session: Path) -> None:
    owned = _owned_session(session)
    try:
        _clear_readonly_files(owned)
        shutil.rmtree(owned)
    except OSError as error:
        raise WorkflowError('cannot remove workflow session') from error
    if owned.exists():
        raise WorkflowError('workflow session still exists after cleanup')


def _read_json(path: Path, label: str) -> Mapping[str, object]:
    if _is_link_like(path) or not path.is_file():
        raise WorkflowError(f'{label} must be a regular file')
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(f'cannot read {label}') from error
    if not isinstance(document, Mapping):
        raise WorkflowError(f'{label} must be a JSON object')
    return document


def _write_workflow_context(session: Path, request_path: Path, request: Mapping[str, object]) -> None:
    context = {
        'version': 1,
        'target': request.get('target'),
        'source_root': request.get('source_root'),
        'source_commit': request.get('source_commit'),
        'request_sha256': hashlib.sha256(request_path.read_bytes()).hexdigest(),
    }
    content = (json.dumps(context, sort_keys=True, indent=2) + '\n').encode()
    try:
        _write_exclusive(session / _WORKFLOW_CONTEXT, content)
    except FileExistsError as error:
        raise WorkflowError('workflow context already exists') from error


def _emit(document: Mapping[str, object]) -> None:
    print(json.dumps(document, sort_keys=True))


def _start(args: argparse.Namespace) -> int:
    session = _create_session()
    try:
        forwarded = [
            'prepare', '--target', str(Path(args.target).absolute()),
            '--session', str(session),
        ]
        result = bootstrap.main(forwarded)
        if result != 0:
            _remove_session(session)
            return result
        request_path = session / 'request.json'
        request = _read_json(request_path, 'session request')
        _write_workflow_context(session, request_path, request)
        _emit({
            'version': 1,
            'phase': 'start',
            'session': str(session),
            'request': str(request_path),
            'generated': str(session / 'generated'),
            'source_root': request.get('source_root'),
            'source_commit': request.get('source_commit'),
            'platforms': request.get('platforms'),
            'generation_requests': request.get('generation_requests'),
        })
        return 0
    except BaseException as error:
        try:
            if session.exists():
                _remove_session(session)
        except BaseException as cleanup_error:
            print(f'ERROR: {error}; session cleanup failed: {cleanup_error}', file=sys.stderr)
            return 2
        if isinstance(error, (OSError, WorkflowError)):
            print(f'ERROR: {error}', file=sys.stderr)
            return 2
        raise


def _request_context(session: Path) -> tuple[Mapping[str, object], Path, Path, str]:
    request_path = session / 'request.json'
    request = _read_json(request_path, 'session request')
    context = _read_json(session / _WORKFLOW_CONTEXT, 'workflow context')
    if set(context) != {
        'version', 'target', 'source_root', 'source_commit', 'request_sha256'
    } or context.get('version') != 1:
        raise WorkflowError('workflow context has an invalid shape')
    try:
        request_digest = hashlib.sha256(request_path.read_bytes()).hexdigest()
    except OSError as error:
        raise WorkflowError('session request cannot be verified') from error
    if context.get('request_sha256') != request_digest:
        raise WorkflowError('session request changed after start')
    target_value = context.get('target')
    source_value = context.get('source_root')
    commit_value = context.get('source_commit')
    if any(
        request.get(key) != context.get(key)
        for key in ('target', 'source_root', 'source_commit')
    ):
        raise WorkflowError('session request differs from workflow context')
    if not isinstance(target_value, str) or not isinstance(source_value, str):
        raise WorkflowError('session request target or source root is invalid')
    target = Path(target_value).absolute()
    source = Path(source_value).absolute()
    if commit_value is None:
        commit = 'offline'
        expected_source = Path(__file__).resolve().parents[3]
    elif isinstance(commit_value, str) and _COMMIT.fullmatch(commit_value):
        commit = commit_value.lower()
        expected_source = session / 'source'
    else:
        raise WorkflowError('session request source commit is invalid')
    if os.path.normcase(str(source)) != os.path.normcase(str(expected_source.absolute())):
        raise WorkflowError('session request source root is outside the pinned workflow boundary')
    return request, target, source, commit


def _run_pinned(
    phase: str,
    *,
    session: Path,
    target: Path,
    source: Path,
    commit: str,
) -> Mapping[str, object]:
    command = (
        sys.executable,
        str(source / 'skills/setup-project-agents/scripts/setup_project_agents.py'),
        phase,
        '--target', str(target),
        '--session', str(session),
        '--source-root', str(source),
        '--source-commit', commit,
        '--no-bootstrap',
    )
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as error:
        raise WorkflowError(f'cannot execute pinned {phase}') from error
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end='')
    if completed.returncode != 0:
        raise WorkflowError(f'pinned {phase} failed with status {completed.returncode}')
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise WorkflowError(f'pinned {phase} returned invalid JSON') from error
    if not isinstance(result, Mapping) or result.get('phase') != phase:
        raise WorkflowError(f'pinned {phase} returned an invalid result')
    return result


def _finish(args: argparse.Namespace) -> int:
    try:
        session = _owned_session(args.session)
    except WorkflowError as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    try:
        request, target, source, commit = _request_context(session)
        apply_result = _run_pinned(
            'apply', session=session, target=target, source=source, commit=commit
        )
        check_result = _run_pinned(
            'check', session=session, target=target, source=source, commit=commit
        )
        if check_result.get('changed_paths') != [] or check_result.get('drift') is not None:
            raise WorkflowError('post-apply check did not converge')
        result = {
            'version': 1,
            'phase': 'finish',
            'source_commit': request.get('source_commit'),
            'platforms': request.get('platforms'),
            'changed_paths': apply_result.get('changed_paths'),
            'external_skills': apply_result.get('external_skills'),
            'preserved_paths': apply_result.get('preserved_paths'),
            'check': 'clean',
        }
        _remove_session(session)
        _emit(result)
        return 0
    except BaseException as error:
        try:
            if session.exists():
                _remove_session(session)
        except BaseException as cleanup_error:
            print(f'ERROR: {error}; session cleanup failed: {cleanup_error}', file=sys.stderr)
            return 2
        if isinstance(error, (OSError, WorkflowError)):
            print(f'ERROR: {error}', file=sys.stderr)
            return 2
        raise


def _cancel(args: argparse.Namespace) -> int:
    try:
        session = _owned_session(args.session)
        _remove_session(session)
        _emit({'version': 1, 'phase': 'cancel', 'cancelled': True})
        return 0
    except (OSError, WorkflowError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Run the public two-stage project-agent setup workflow.',
        allow_abbrev=False,
    )
    phases = parser.add_subparsers(dest='phase', required=True)
    start = phases.add_parser('start', allow_abbrev=False)
    start.add_argument('--target', type=Path, required=True)
    finish = phases.add_parser('finish', allow_abbrev=False)
    finish.add_argument('--session', type=Path, required=True)
    cancel = phases.add_parser('cancel', allow_abbrev=False)
    cancel.add_argument('--session', type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    if args.phase == 'start':
        return _start(args)
    if args.phase == 'finish':
        return _finish(args)
    return _cancel(args)


if __name__ == '__main__':
    raise SystemExit(main())
