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


PATH_TOKEN = re.compile(
    r'(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.[A-Za-z0-9]+)'
)


class RuleConfigError(RuntimeError):
    pass


def plugin_root() -> Path:
    configured = os.environ.get('PLUGIN_ROOT') or os.environ.get('CURSOR_PLUGIN_ROOT')
    return Path(configured).resolve() if configured else Path(__file__).resolve().parents[2]


def load_registry(root: Path) -> list[dict[str, object]]:
    try:
        document = json.loads((root / 'rules/registry.json').read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuleConfigError(f'cannot load rules/registry.json: {error}') from error
    if not isinstance(document, dict) or document.get('version') != 1:
        raise RuleConfigError('Rule registry version must be 1')
    rules = document.get('rules')
    if not isinstance(rules, list) or not rules:
        raise RuleConfigError('Rule registry requires a non-empty rules array')
    ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict) or set(rule) != {'id', 'source', 'strength', 'trigger'}:
            raise RuleConfigError(f'invalid Rule at index {index}')
        rule_id = rule['id']
        if not isinstance(rule_id, str) or rule_id in ids:
            raise RuleConfigError(f'duplicate or invalid Rule id at index {index}')
        ids.add(rule_id)
        if rule['strength'] not in {'Mandatory', 'Default', 'Advisory'}:
            raise RuleConfigError(f'invalid strength for {rule_id}')
        source = rule['source']
        if not isinstance(source, str) or '\\' in source:
            raise RuleConfigError(f'invalid source for {rule_id}')
        relative = PurePosixPath(source)
        if relative.is_absolute() or '..' in relative.parts:
            raise RuleConfigError(f'invalid source for {rule_id}')
        trigger = rule['trigger']
        if not isinstance(trigger, dict) or trigger.get('type') not in {'always', 'file'}:
            raise RuleConfigError(f'invalid trigger for {rule_id}')
        if trigger['type'] == 'always' and set(trigger) != {'type'}:
            raise RuleConfigError(f'invalid always trigger for {rule_id}')
        if trigger['type'] == 'file':
            if set(trigger) != {'type', 'include_globs'}:
                raise RuleConfigError(f'invalid file trigger for {rule_id}')
            includes = trigger['include_globs']
            if not isinstance(includes, list) or not includes or not all(
                isinstance(item, str) and item and '\\' not in item
                for item in includes
            ):
                raise RuleConfigError(f'invalid include_globs for {rule_id}')
        if not root.joinpath('rules', *relative.parts).is_file():
            raise RuleConfigError(f'missing source for {rule_id}')
    first = rules[0]
    if (
        first['id'] != 'smartkit/core-rule-config'
        or first['strength'] != 'Mandatory'
        or first['trigger'] != {'type': 'always'}
    ):
        raise RuleConfigError('the first Rule must be mandatory always core-rule-config')
    return rules


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


def _loaded_rules(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuleConfigError(f'cannot read Rule activation state: {error}') from error
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuleConfigError('Rule activation state is invalid')
    return set(value)


def _store_loaded_rules(path: Path, loaded: set[str]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f'.{os.getpid()}.tmp')
        temporary.write_text(json.dumps(sorted(loaded)) + '\n', encoding='utf-8')
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
    selected = _selected_rules(root, payload, event)
    state_path = _state_path(root, payload, platform, state_root)
    loaded = _loaded_rules(state_path)
    if event == 'session':
        registered = load_registry(root)
        restored = [
            rule for rule in registered
            if rule['id'] in loaded and _is_file_rule(rule)
        ]
        context = _context(root, [*selected, *restored])
        if platform == 'copilot':
            return {'additionalContext': context}
        return {'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': context,
        }}

    if event == 'prompt':
        activated = [
            rule for rule in selected
            if _is_file_rule(rule) and rule['id'] not in loaded
        ]
        if activated:
            loaded.update(str(rule['id']) for rule in activated)
            _store_loaded_rules(state_path, loaded)
        context = _context(root, activated)
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
            if _is_file_rule(rule) and rule['id'] not in loaded
        ]
        if missing:
            loaded.update(str(rule['id']) for rule in missing)
            _store_loaded_rules(state_path, loaded)
            context = _context(root, missing)
            if not _is_write_tool(payload):
                if platform == 'copilot':
                    return {'additionalContext': context}
                return {'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'additionalContext': context,
                }}
            reason = (
                'SmartKit loaded file Rules required by this tool call. '
                'Retry the same operation after applying the injected Rules.'
            )
            if platform == 'copilot':
                return {
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': reason,
                    'additionalContext': context,
                }
            return {'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': reason,
                'additionalContext': context,
            }}
        return {}
    raise RuleConfigError(f'unsupported Rule delivery event: {event}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', choices=('codex', 'copilot'), required=True)
    parser.add_argument('--event', choices=('session', 'prompt', 'tool'), required=True)
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
