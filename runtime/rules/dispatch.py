#!/usr/bin/env python3
"""Deliver SmartKit plugin Rules for hosts that expose command Hooks."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath

from contract import RuleConfigError, load_registry


PATH_TOKEN = re.compile(
    r'(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.[A-Za-z0-9]+)'
)


def plugin_root() -> Path:
    configured = os.environ.get('PLUGIN_ROOT') or os.environ.get('CURSOR_PLUGIN_ROOT')
    return Path(configured).resolve() if configured else Path(__file__).resolve().parents[2]


def _paths(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        found.update(match.group(1).lstrip('./') for match in PATH_TOKEN.finditer(value))
    elif isinstance(value, dict):
        for key, child in value.items():
            if key in {
                'file_path', 'path', 'paths', 'prompt', 'transformedPrompt',
                'tool_input', 'toolInput', 'toolArgs', 'arguments', 'args',
            }:
                found.update(_paths(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_paths(child))
    return found


def _matches(trigger: dict[str, object], paths: set[str]) -> bool:
    if trigger['type'] == 'always':
        return True
    includes = trigger['include_globs']
    def matches(path: str, pattern: str) -> bool:
        return fnmatch.fnmatchcase(path, pattern) or (
            pattern.startswith('**/') and fnmatch.fnmatchcase(path, pattern[3:])
        )

    return any(
        any(matches(path, pattern) for pattern in includes)
        for path in paths
    )


def _selected_rules(root: Path, payload: object, event: str) -> list[dict[str, object]]:
    paths = _paths(payload) if event in {'prompt', 'tool'} else set()
    return [
        rule for rule in load_registry(root)
        if isinstance(rule['trigger'], dict) and _matches(rule['trigger'], paths)
    ]


def _is_file_rule(rule: dict[str, object]) -> bool:
    trigger = rule['trigger']
    return isinstance(trigger, dict) and trigger.get('type') == 'file'


def _is_write_tool(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    raw_name = payload.get('tool_name') or payload.get('toolName') or ''
    name = str(raw_name).casefold().replace('-', '_')
    write_markers = (
        'apply_patch', 'create_file', 'edit', 'insert', 'move', 'rename',
        'replace', 'update_file', 'write',
    )
    if any(marker in name for marker in write_markers):
        return True

    def contains_write_field(value: object) -> bool:
        if isinstance(value, dict):
            if any(
                str(key).casefold() in {
                    'content', 'edits', 'new_string', 'newtext', 'patch', 'replacement',
                }
                for key in value
            ):
                return True
            return any(contains_write_field(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_write_field(child) for child in value)
        return False

    return contains_write_field(
        payload.get('tool_input') or payload.get('toolInput') or payload.get('toolArgs')
    )


def _context(root: Path, rules: list[dict[str, object]]) -> str:
    blocks: list[str] = []
    for rule in rules:
        source = str(rule['source'])
        text = root.joinpath('rules', *PurePosixPath(source).parts).read_text(encoding='utf-8')
        blocks.append(
            f'<!-- Rule-ID: {rule["id"]}; Owner: plugin; Strength: {rule["strength"]}; '
            f'Source: rules/{source} -->\n{text.strip()}'
        )
    return '\n\n'.join(blocks) + ('\n' if blocks else '')


def context_for(root: Path, payload: object, event: str) -> str:
    return _context(root, _selected_rules(root, payload, event))


def _state_path(
    root: Path,
    payload: object,
    platform: str,
    state_root: Path | None = None,
) -> Path:
    session = None
    if isinstance(payload, dict):
        session = payload.get('session_id') or payload.get('sessionId')
    identity = str(session) if session else f'{Path.cwd().resolve()}:{os.getppid()}'
    digest = hashlib.sha256(f'{root.resolve()}:{platform}:{identity}'.encode()).hexdigest()
    base = state_root
    if base is None:
        configured = os.environ.get('PLUGIN_DATA')
        base = Path(configured) if configured else Path(tempfile.gettempdir()) / 'smartkit-rule-state'
    return base / 'rule-sessions' / f'{digest}.json'


def _empty_session_state() -> dict[str, object]:
    return {
        'activated_file_rule_ids': [],
        'context_generation': 0,
        'restored_generation': 0,
    }


def _session_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return _empty_session_state()
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except OSError as error:
        raise RuleConfigError(f'cannot read Rule activation state: {error}') from error
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _empty_session_state()
    if not isinstance(value, dict) or set(value) != {
        'activated_file_rule_ids',
        'context_generation',
        'restored_generation',
    }:
        return _empty_session_state()
    activated = value['activated_file_rule_ids']
    context_generation = value['context_generation']
    restored_generation = value['restored_generation']
    if (
        not isinstance(activated, list)
        or not all(isinstance(item, str) for item in activated)
        or len(set(activated)) != len(activated)
        or not isinstance(context_generation, int)
        or context_generation < 0
        or not isinstance(restored_generation, int)
        or restored_generation < 0
        or restored_generation > context_generation
    ):
        return _empty_session_state()
    return value


def _store_session_state(path: Path, state: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f'.{os.getpid()}.tmp')
        temporary.write_text(json.dumps(state, sort_keys=True) + '\n', encoding='utf-8')
        os.replace(temporary, path)
    except OSError as error:
        raise RuleConfigError(f'cannot write Rule activation state: {error}') from error


def delivery(
    root: Path,
    payload: object,
    event: str,
    platform: str,
    *,
    state_root: Path | None = None,
) -> dict[str, object]:
    state_path = _state_path(root, payload, platform, state_root)
    state = _session_state(state_path)
    activated = set(state['activated_file_rule_ids'])
    restore_required = state['restored_generation'] < state['context_generation']

    if event == 'compact':
        if platform != 'copilot':
            raise RuleConfigError('compact Rule delivery is supported only for Copilot')
        state['context_generation'] = int(state['context_generation']) + 1
        _store_session_state(state_path, state)
        return {}

    if event == 'stop':
        if platform != 'copilot':
            raise RuleConfigError('stop Rule delivery is supported only for Copilot')
        if not restore_required:
            return {}
        registered = load_registry(root)
        restored = [
            rule for rule in registered
            if not _is_file_rule(rule) or rule['id'] in activated
        ]
        context = _context(root, restored)
        state['restored_generation'] = state['context_generation']
        _store_session_state(state_path, state)
        return {
            'decision': 'block',
            'reason': (
                f'{context}\nSmartKit restored Rules after context compaction. '
                'Review the proposed answer against them, revise it if needed, '
                'and then finish the turn.'
            ),
        }

    if event == 'tool' and platform == 'copilot' and restore_required:
        registered = load_registry(root)
        paths = _paths(payload)
        activated.update(
            str(rule['id'])
            for rule in registered
            if _is_file_rule(rule) and _matches(rule['trigger'], paths)
        )
        restored = [
            rule for rule in registered
            if not _is_file_rule(rule) or rule['id'] in activated
        ]
        context = _context(root, restored)
        state['activated_file_rule_ids'] = sorted(activated)
        state['restored_generation'] = state['context_generation']
        _store_session_state(state_path, state)
        return {
            'permissionDecision': 'deny',
            'permissionDecisionReason': (
                f'{context}\nSmartKit restored Rules after context compaction. '
                'Apply them, then retry the same tool call.'
            ),
        }
    if event == 'tool' and not _paths(payload):
        return {}

    selected = _selected_rules(root, payload, event)

    if event == 'session':
        registered = load_registry(root)
        restored = [
            rule for rule in registered
            if rule['id'] in activated and _is_file_rule(rule)
        ]
        context = _context(root, [*selected, *restored])
        if restore_required:
            state['restored_generation'] = state['context_generation']
            _store_session_state(state_path, state)
        if platform == 'copilot':
            return {'additionalContext': context}
        return {'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': context,
        }}

    if event == 'prompt':
        newly_activated = [
            rule for rule in selected
            if _is_file_rule(rule) and rule['id'] not in activated
        ]
        activated_ids = set(state['activated_file_rule_ids'])
        activated_ids.update(str(rule['id']) for rule in newly_activated)
        if restore_required:
            registered = load_registry(root)
            delivered = [
                rule for rule in registered
                if not _is_file_rule(rule) or rule['id'] in activated_ids
            ]
            state['restored_generation'] = state['context_generation']
        else:
            delivered = newly_activated
        if newly_activated or restore_required:
            state['activated_file_rule_ids'] = sorted(activated_ids)
            _store_session_state(state_path, state)
        context = _context(root, delivered)
        if platform == 'copilot':
            original = ''
            if isinstance(payload, dict):
                original = str(
                    payload.get('transformedPrompt') or payload.get('prompt') or ''
                )
            prefix = f'{context}\n' if context else ''
            return {'modifiedTransformedPrompt': f'{prefix}{original}'}
        return {'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': context,
        }}

    if event == 'tool':
        missing = [
            rule for rule in selected
            if _is_file_rule(rule) and rule['id'] not in activated
        ]
        if missing:
            activated.update(str(rule['id']) for rule in missing)
            state['activated_file_rule_ids'] = sorted(activated)
            _store_session_state(state_path, state)
            context = _context(root, missing)
            reason = (
                f'{context}\nSmartKit loaded file Rules required by this tool call. '
                'Apply them, then retry the same operation.'
            )
            if platform == 'copilot':
                return {
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': reason,
                }
            if not _is_write_tool(payload):
                return {'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'additionalContext': context,
                }}
            return {'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': (
                    'SmartKit loaded file Rules required by this tool call. '
                    'Retry the same operation after applying the injected Rules.'
                ),
                'additionalContext': context,
            }}
        return {}
    raise RuleConfigError(f'unsupported Rule delivery event: {event}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', choices=('codex', 'copilot'), required=True)
    parser.add_argument(
        '--event',
        choices=('session', 'prompt', 'tool', 'compact', 'stop'),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.load(sys.stdin)
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {}
    try:
        output = delivery(plugin_root(), payload, args.event, args.platform)
    except (OSError, RuleConfigError) as error:
        print(f'SmartKit Rule delivery skipped: {error}', file=sys.stderr)
        return 1
    encoded = json.dumps(output)
    if output:
        print(
            'SmartKit Rule delivery attempted: '
            f'platform={args.platform}, event={args.event}, response_bytes={len(encoded.encode())}. '
            'Host trust, acceptance, spill, and truncation remain host-owned; '
            'inspect the host Hook diagnostics if expected Rule behavior is absent.',
            file=sys.stderr,
        )
    print(encoded)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
