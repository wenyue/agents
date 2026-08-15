from __future__ import annotations

import json
from pathlib import Path, PurePosixPath


SESSION_RULE_HARNESSES = frozenset({'codex', 'copilot'})


class RuleConfigError(RuntimeError):
    """Raised when the Plugin Rule registry violates its delivery contract."""


def load_registry(root: Path) -> list[dict[str, object]]:
    try:
        document = json.loads((root / 'rules/registry.json').read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuleConfigError(f'cannot load rules/registry.json: {error}') from error
    if not isinstance(document, dict) or set(document) != {'rules'}:
        raise RuleConfigError('Rule registry requires exactly a rules field')
    rules = document.get('rules')
    if not isinstance(rules, list) or not rules:
        raise RuleConfigError('Rule registry requires a non-empty rules array')
    ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict) or set(rule) != {'id', 'source', 'strength', 'trigger'}:
            raise RuleConfigError(f'invalid Rule at index {index}')
        rule_id = rule['id']
        if (
            not isinstance(rule_id, str)
            or not rule_id.startswith('smartkit/')
            or rule_id in ids
        ):
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
        if not isinstance(trigger, dict) or trigger.get('type') not in {
            'always', 'file', 'harness',
        }:
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
        if trigger['type'] == 'harness':
            if set(trigger) != {'type', 'harnesses'}:
                raise RuleConfigError(f'invalid harness trigger for {rule_id}')
            harnesses = trigger['harnesses']
            if (
                not isinstance(harnesses, list)
                or not harnesses
                or not all(isinstance(item, str) for item in harnesses)
                or len(harnesses) != len(set(harnesses))
                or set(harnesses) - SESSION_RULE_HARNESSES
            ):
                raise RuleConfigError(f'invalid harnesses for {rule_id}')
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
