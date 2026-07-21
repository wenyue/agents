#!/usr/bin/env python3
"""Check platform-recommended tools without inspecting user configuration."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


_DEFAULT_VERSION_PATTERN = r'(\d+(?:\.\d+)+(?:[-+][0-9A-Za-z.-]+)?)'
_MAX_COMMAND_OUTPUT = 16_384
_LOCK_STALE_SECONDS = 300


class PolicyError(RuntimeError):
    """Raised when a tool policy cannot be evaluated safely."""


class DetectorError(PolicyError):
    """Raised when a detector exists but cannot complete."""


class VersionUnreadable(PolicyError):
    """Raised when a detector responds without a usable version."""


@dataclass(frozen=True)
class Finding:
    code: str
    tool: str
    message: str
    guidance: str


@dataclass(frozen=True)
class HookResult:
    ran: bool
    findings: tuple[Finding, ...] = ()
    internal_error: bool = False

    @property
    def requires_user_prompt(self) -> bool:
        return not self.internal_error and any(
            finding.code != 'detector-error' for finding in self.findings
        )


def parse_version(value: str) -> tuple[int, ...]:
    match = re.search(r'\d+(?:\.\d+)+', value)
    if match is None:
        raise ValueError('version contains no ordered numeric components')
    return tuple(int(part) for part in match.group(0).split('.'))


def is_strictly_greater(installed: str, target: str) -> bool:
    installed_parts = parse_version(installed)
    target_parts = parse_version(target)
    width = max(len(installed_parts), len(target_parts))
    return installed_parts + (0,) * (width - len(installed_parts)) > target_parts + (
        0,
    ) * (width - len(target_parts))


def _json_path(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split('.'):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _expand(value: str) -> str:
    return value.format(home=str(Path.home()))


def _run_command(command: list[str], timeout: float) -> str | None:
    try:
        process = subprocess.Popen(
            [_expand(argument) for argument in command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except (FileNotFoundError, PermissionError):
        return None
    except OSError as error:
        raise DetectorError('detector command failed to start') from error
    if process.stdout is None:
        process.kill()
        raise DetectorError('detector command output is unavailable')

    captured = bytearray()
    overflow = threading.Event()

    def read_output() -> None:
        while True:
            chunk = process.stdout.read(4096)
            if not chunk:
                return
            remaining = _MAX_COMMAND_OUTPUT - len(captured)
            if remaining > 0:
                captured.extend(chunk[:remaining])
            if len(chunk) > remaining:
                overflow.set()
                process.kill()
                return

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        process.kill()
        process.wait()
        reader.join(timeout=1)
        raise DetectorError('detector command timed out') from error
    reader.join(timeout=1)
    if reader.is_alive():
        process.kill()
        process.wait()
        raise DetectorError('detector output reader did not finish')
    if overflow.is_set():
        raise DetectorError('detector command output exceeded the limit')
    if returncode != 0:
        raise DetectorError('detector command returned a failure status')
    return captured.decode('utf-8', errors='replace')


def run_detector(detector: dict[str, Any]) -> str | None:
    if not isinstance(detector, dict):
        raise PolicyError('detector must be an object')
    kind = detector.get('kind')
    if kind == 'fixed':
        value = detector.get('value')
        return value if isinstance(value, str) and value else None
    if kind == 'json-manifest-glob':
        pattern = detector.get('glob')
        json_path = detector.get('json_path')
        if not isinstance(pattern, str) or not isinstance(json_path, str):
            raise PolicyError('manifest detector requires glob and json_path')
        candidates = sorted(glob.glob(_expand(pattern)), reverse=True)
        unreadable = False
        for candidate in candidates:
            try:
                parsed = json.loads(Path(candidate).read_text(encoding='utf-8'))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                unreadable = True
                continue
            value = _json_path(parsed, json_path)
            if isinstance(value, (str, int, float)):
                return str(value)
            unreadable = True
        if unreadable:
            raise VersionUnreadable('manifest contains no usable version')
        return None
    if kind in {'command-regex', 'json-command'}:
        command = detector.get('command')
        if not isinstance(command, list) or not command or not all(
            isinstance(argument, str) and argument for argument in command
        ):
            raise PolicyError('command detector requires a non-empty command array')
        timeout = detector.get('timeout_seconds', 5)
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 30:
            raise PolicyError('command detector timeout must be between 0 and 30 seconds')
        output = _run_command(command, float(timeout))
        if output is None:
            return None
        if kind == 'json-command':
            json_path = detector.get('json_path')
            if not isinstance(json_path, str):
                raise PolicyError('JSON command detector requires json_path')
            try:
                value = _json_path(json.loads(output), json_path)
            except json.JSONDecodeError as error:
                raise VersionUnreadable('JSON command output is invalid') from error
            if not isinstance(value, (str, int, float)):
                raise VersionUnreadable('JSON command output contains no usable version')
            return str(value)
        pattern = detector.get('pattern', _DEFAULT_VERSION_PATTERN)
        if not isinstance(pattern, str):
            raise PolicyError('command detector pattern must be a string')
        match = re.search(pattern, output)
        if match is None:
            raise VersionUnreadable('command output contains no usable version')
        return match.group(1)
    raise PolicyError('unsupported detector kind')


def _validate_tool(tool: Any) -> dict[str, Any]:
    if not isinstance(tool, dict):
        raise PolicyError('each tool must be an object')
    for field in ('id', 'name', 'target_version', 'install', 'upgrade'):
        if not isinstance(tool.get(field), str) or not tool[field]:
            raise PolicyError(f'tool field {field} must be a non-empty string')
    if tool.get('comparison') != '>':
        raise PolicyError('tool comparison must be >')
    detectors = tool.get('detectors')
    if not isinstance(detectors, list) or not detectors:
        raise PolicyError('tool detectors must be a non-empty array')
    parse_version(tool['target_version'])
    return tool


def check_policy(policy: dict[str, Any]) -> list[Finding]:
    tools = policy.get('tools')
    if not isinstance(policy.get('platform'), str) or not isinstance(tools, list):
        raise PolicyError('policy requires platform and tools')
    findings: list[Finding] = []
    for raw_tool in tools:
        tool = _validate_tool(raw_tool)
        installed = None
        detector_failed = False
        version_unreadable = False
        for detector in tool['detectors']:
            try:
                installed = run_detector(detector)
            except VersionUnreadable:
                version_unreadable = True
                continue
            except (PolicyError, re.error):
                detector_failed = True
                continue
            if installed is not None:
                break
        if installed is None:
            if version_unreadable:
                findings.append(
                    Finding(
                        'version-unreadable',
                        tool['name'],
                        'has an unreadable installed version',
                        tool['upgrade'],
                    )
                )
            else:
                code = 'detector-error' if detector_failed else 'tool-missing'
                message = (
                    'version detection failed'
                    if detector_failed
                    else 'is not installed for this platform'
                )
                findings.append(Finding(code, tool['name'], message, tool['install']))
            continue
        try:
            greater = is_strictly_greater(installed, tool['target_version'])
        except ValueError:
            findings.append(
                Finding(
                    'version-unreadable',
                    tool['name'],
                    'has an unreadable installed version',
                    tool['upgrade'],
                )
            )
            continue
        if not greater:
            installed_parts = parse_version(installed)
            target_parts = parse_version(tool['target_version'])
            width = max(len(installed_parts), len(target_parts))
            normalized_installed = installed_parts + (0,) * (width - len(installed_parts))
            normalized_target = target_parts + (0,) * (width - len(target_parts))
            relation = 'equals the target version' if normalized_installed == normalized_target else 'is older than the target version'
            findings.append(
                Finding(
                    'version-not-greater',
                    tool['name'],
                    f'{relation}; it must be newer than {tool["target_version"]}',
                    tool['upgrade'],
                )
            )
    return findings


def load_policy(path: Path, platform: str | None = None) -> dict[str, Any]:
    try:
        policy = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PolicyError('unable to load recommended-tool policy') from error
    if not isinstance(policy, dict):
        raise PolicyError('recommended-tool policy must contain an object')
    if platform is not None and policy.get('platform') != platform:
        raise PolicyError('recommended-tool policy platform does not match invocation')
    return policy


def default_policy_path(platform: str) -> Path:
    return Path(__file__).resolve().parent.parent / 'assets' / 'templates' / 'recommended-tools' / f'{platform}.json'


def default_cache_root() -> Path:
    local_app_data = os.environ.get('LOCALAPPDATA')
    if os.name == 'nt' and local_app_data:
        return Path(local_app_data) / 'setup-project-agents'
    xdg_cache = os.environ.get('XDG_CACHE_HOME')
    if xdg_cache:
        return Path(xdg_cache) / 'setup-project-agents'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Caches' / 'setup-project-agents'
    return Path.home() / '.cache' / 'setup-project-agents'


def _fingerprint(policy_path: Path, checker_path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(policy_path.read_bytes())
    digest.update(checker_path.read_bytes())
    return digest.hexdigest()


def _load_state(
    path: Path,
    date: str,
    fingerprint: str,
) -> str | None:
    try:
        state = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(state, dict):
        return None
    if state.get('date') != date or state.get('fingerprint') != fingerprint:
        return None
    outcome = state.get('outcome')
    if outcome in {'passed', 'notified', 'error'} and set(state) == {
        'date',
        'fingerprint',
        'outcome',
    }:
        return outcome
    return None


def _write_state(
    path: Path,
    date: str,
    fingerprint: str,
    outcome: str,
) -> None:
    if outcome not in {'passed', 'notified', 'error'}:
        raise ValueError('daily state outcome must be passed, notified, or error')
    state: dict[str, Any] = {
        'date': date,
        'fingerprint': fingerprint,
        'outcome': outcome,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
            json.dump(state, output)
            output.write('\n')
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _acquire_lock(path: Path) -> str:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return 'uncached'
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            if time.time() - path.stat().st_mtime <= _LOCK_STALE_SECONDS:
                return 'busy'
            path.unlink()
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except (FileNotFoundError, FileExistsError):
            return 'busy'
        except OSError:
            return 'uncached'
    except OSError:
        return 'uncached'
    try:
        os.write(descriptor, str(os.getpid()).encode('ascii'))
    finally:
        os.close(descriptor)
    return 'owned'


def run_hook(
    platform: str,
    policy_path: Path,
    cache_root: Path | None = None,
    now: datetime | None = None,
    *,
    force: bool = False,
    evaluator: Callable[[dict[str, Any]], list[Finding]] = check_policy,
) -> HookResult:
    cache_root = cache_root or default_cache_root()
    now = now or datetime.now().astimezone()
    state_path = cache_root / f'{platform}.json'
    lock_path = cache_root / f'{platform}.lock'
    try:
        fingerprint = _fingerprint(policy_path, Path(__file__))
        date = now.date().isoformat()
        if not force and _load_state(state_path, date, fingerprint):
            return HookResult(False)
        lock_status = _acquire_lock(lock_path)
        if lock_status == 'busy':
            return HookResult(False)
        try:
            if not force and _load_state(state_path, date, fingerprint):
                return HookResult(False)
            policy = load_policy(policy_path, platform)
            findings = tuple(evaluator(policy))
            if not findings:
                try:
                    _write_state(state_path, date, fingerprint, 'passed')
                except OSError:
                    pass
            elif any(finding.code != 'detector-error' for finding in findings):
                try:
                    _write_state(state_path, date, fingerprint, 'notified')
                except OSError:
                    pass
            else:
                try:
                    _write_state(state_path, date, fingerprint, 'error')
                except OSError:
                    pass
            return HookResult(True, findings)
        except Exception:
            try:
                _write_state(state_path, date, fingerprint, 'error')
            except OSError:
                pass
            return HookResult(True, internal_error=True)
        finally:
            if lock_status == 'owned':
                try:
                    lock_path.unlink()
                except OSError:
                    pass
    except Exception:
        return HookResult(True, internal_error=True)


def render_findings(findings: list[Finding] | tuple[Finding, ...]) -> str:
    return '\n'.join(
        f'[setup-project-agents] {finding.tool}: {finding.message}. {finding.guidance}'
        for finding in findings
    )


def render_hook_result(result: HookResult, platform: str) -> str:
    if result.internal_error:
        message = '[setup-project-agents] Recommended-tool check could not complete; continuing.'
    else:
        findings = render_findings(result.findings)
        if result.requires_user_prompt:
            message = (
                f'{findings}\n'
                '[setup-project-agents] Stop the current task now. Ask the user whether to '
                'install or upgrade the listed tools, end this turn after the question, and '
                'wait for the next user message. If that message requests installation, '
                'perform it and force this check again. Any other user message may continue '
                'normally; no explicit decline is required.'
            )
        else:
            message = findings
    if not message:
        return ''
    if platform == 'codex':
        return json.dumps({'continue': True, 'systemMessage': message})
    if platform == 'cursor':
        return json.dumps({'additional_context': message})
    return json.dumps({'additionalContext': message})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    for command in ('check', 'hook'):
        child = subparsers.add_parser(command)
        child.add_argument('--platform', required=True, choices=('codex', 'cursor', 'copilot'))
        child.add_argument('--policy', type=Path)
        if command == 'hook':
            child.add_argument('--force', action='store_true')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    policy_path = args.policy or default_policy_path(args.platform)
    if args.command == 'hook':
        result = run_hook(args.platform, policy_path, force=args.force)
        output = render_hook_result(result, args.platform)
        if output:
            print(output)
        return 0
    try:
        findings = check_policy(load_policy(policy_path, args.platform))
    except Exception:
        print('[setup-project-agents] Recommended-tool check could not complete.', file=sys.stderr)
        return 2
    output = render_findings(findings)
    if output:
        print(output)
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
