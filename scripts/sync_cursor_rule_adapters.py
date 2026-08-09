#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class AdapterError(RuntimeError):
    pass


def desired_adapters(root: Path) -> dict[str, str]:
    try:
        registry = json.loads((root / 'rules/registry.json').read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AdapterError(f'cannot read Rule registry: {error}') from error
    rules = registry.get('rules') if isinstance(registry, dict) else None
    if registry.get('version') != 1 or not isinstance(rules, list):
        raise AdapterError('Rule registry has an invalid shape')
    adapters: dict[str, str] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            raise AdapterError('Rule registry has an invalid Rule')
        rule_id = rule.get('id')
        source = rule.get('source')
        trigger = rule.get('trigger')
        if (
            not isinstance(rule_id, str)
            or not rule_id.startswith('smartkit/')
            or not isinstance(source, str)
            or not isinstance(trigger, dict)
        ):
            raise AdapterError('Rule registry has an invalid Rule')
        name = rule_id.split('/', 1)[1]
        if trigger.get('type') == 'always':
            frontmatter = 'alwaysApply: true'
            limitation = ''
        elif trigger.get('type') == 'file':
            includes = trigger.get('include_globs')
            if set(trigger) != {'type', 'include_globs'} or not isinstance(includes, list):
                raise AdapterError(f'Rule has invalid file globs: {rule_id}')
            frontmatter = (
                f'globs: {json.dumps(",".join(includes))}\n'
                'alwaysApply: false'
            )
            limitation = ''
        else:
            raise AdapterError(f'Rule has an unsupported trigger: {rule_id}')
        adapters[f'{name}.mdc'] = (
            f'---\n{frontmatter}\n---\n\n'
            f'Apply @../{source}{limitation}\n'
        )
    return adapters


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Check or update Cursor Rule adapters.')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--update', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        desired = desired_adapters(root)
        destination = root / 'rules/cursor'
        actual = {
            path.name: path.read_text(encoding='utf-8')
            for path in destination.glob('*.mdc')
        } if destination.is_dir() else {}
        if args.check:
            if actual != desired:
                print('Cursor Rule adapters have drift.', file=sys.stderr)
                return 1
            print(f'Cursor Rule adapters are up to date: {len(desired)} rules.')
            return 0
        destination.mkdir(parents=True, exist_ok=True)
        for path in destination.glob('*.mdc'):
            if path.name not in desired:
                path.unlink()
        for name, content in desired.items():
            (destination / name).write_text(content, encoding='utf-8')
        print(f'Updated Cursor Rule adapters: {len(desired)} rules.')
        return 0
    except AdapterError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
