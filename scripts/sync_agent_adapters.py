#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path, PurePosixPath


HARNESSES = ('codex', 'cursor', 'copilot')
OUTPUTS = {
    'codex': Path('agents/codex'),
    'cursor': Path('agents/cursor'),
    'copilot': Path('agents/copilot'),
}
REGISTRY_PATH = Path('agents/registry.json')
SAFE_ID = re.compile(r'^[a-z0-9][a-z0-9-]*$')


class AgentRegistryError(ValueError):
    pass


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AgentRegistryError(f'{label} must be an object')
    return value


def _fields(value: Mapping[str, object], allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise AgentRegistryError(
            f'unknown {label} fields: {", ".join(sorted(str(item) for item in unknown))}'
        )


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentRegistryError(f'{label} must be a non-empty string')
    return value


def _source_path(value: object, label: str) -> PurePosixPath:
    source = PurePosixPath(_nonempty(value, label))
    if (
        source.is_absolute()
        or '..' in source.parts
        or source.parts[:1] != ('source',)
        or source.suffix != '.md'
    ):
        raise AgentRegistryError(f'{label} must be a Markdown path under agents/source')
    return source


def load_registry(root: Path) -> tuple[dict[str, object], ...]:
    path = root / REGISTRY_PATH
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise AgentRegistryError(f'cannot load Agent registry: {path}') from error
    registry = _object(document, 'Agent registry')
    _fields(registry, {'agents'}, 'Agent registry')
    raw_agents = registry.get('agents')
    if not isinstance(raw_agents, list):
        raise AgentRegistryError('Agent registry agents must be an array')

    agents: list[dict[str, object]] = []
    ids: set[str] = set()
    for index, raw_agent in enumerate(raw_agents):
        label = f'Agent registry agents[{index}]'
        agent = _object(raw_agent, label)
        _fields(agent, {'id', 'source', 'description', 'harnesses'}, label)
        agent_id = _nonempty(agent.get('id'), f'{label}.id')
        if SAFE_ID.fullmatch(agent_id) is None:
            raise AgentRegistryError(f'{label}.id must be a safe name')
        if agent_id in ids:
            raise AgentRegistryError('Agent registry has duplicate agent ids')
        ids.add(agent_id)
        source = _source_path(agent.get('source'), f'{label}.source')
        source_file = root / 'agents' / source
        try:
            instructions = source_file.read_text(encoding='utf-8').strip()
        except OSError as error:
            raise AgentRegistryError(f'cannot read Agent source: {source_file}') from error
        if not instructions:
            raise AgentRegistryError(f'{label}.source must not be empty')
        if '"""' in instructions:
            raise AgentRegistryError(f'{label}.source cannot contain a TOML multiline delimiter')

        description = _nonempty(agent.get('description'), f'{label}.description')
        harnesses = _object(agent.get('harnesses'), f'{label}.harnesses')
        _fields(harnesses, set(HARNESSES), f'{label}.harnesses')
        if not harnesses:
            raise AgentRegistryError(f'{label}.harnesses must not be empty')
        rendered_harnesses: dict[str, dict[str, object]] = {}
        for harness, raw_config in harnesses.items():
            config = _object(raw_config, f'{label}.harnesses.{harness}')
            if harness == 'codex':
                _fields(config, {'sandbox_mode'}, f'{label}.harnesses.codex')
                rendered_harnesses[harness] = {
                    'sandbox_mode': _nonempty(
                        config.get('sandbox_mode'), f'{label}.harnesses.codex.sandbox_mode'
                    )
                }
            elif harness == 'cursor':
                _fields(config, {'readonly'}, f'{label}.harnesses.cursor')
                readonly = config.get('readonly')
                if type(readonly) is not bool:
                    raise AgentRegistryError(
                        f'{label}.harnesses.cursor.readonly must be a boolean'
                    )
                rendered_harnesses[harness] = {'readonly': readonly}
            else:
                _fields(
                    config,
                    {'disable_model_invocation'},
                    f'{label}.harnesses.copilot',
                )
                disabled = config.get('disable_model_invocation')
                if type(disabled) is not bool:
                    raise AgentRegistryError(
                        f'{label}.harnesses.copilot.disable_model_invocation '
                        'must be a boolean'
                    )
                rendered_harnesses[harness] = {'disable_model_invocation': disabled}

        agents.append({
            'id': agent_id,
            'source': source.as_posix(),
            'description': description,
            'instructions': instructions,
            'harnesses': rendered_harnesses,
        })
    return tuple(agents)


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_agent(agent: Mapping[str, object], harness: str) -> tuple[str, bytes]:
    agent_id = str(agent['id'])
    description = str(agent['description'])
    instructions = str(agent['instructions'])
    harnesses = agent['harnesses']
    assert isinstance(harnesses, Mapping)
    config = harnesses[harness]
    assert isinstance(config, Mapping)
    if harness == 'codex':
        name = f'{agent_id}.toml'
        content = (
            f'name = {_quoted(agent_id)}\n'
            f'description = {_quoted(description)}\n'
            f'sandbox_mode = {_quoted(str(config["sandbox_mode"]))}\n'
            'developer_instructions = """\n'
            f'{instructions}\n'
            '"""\n'
        )
    elif harness == 'cursor':
        name = f'{agent_id}.md'
        content = (
            '---\n'
            f'name: {_quoted(agent_id)}\n'
            f'description: {_quoted(description)}\n'
            f'readonly: {str(config["readonly"]).lower()}\n'
            '---\n\n'
            f'{instructions}\n'
        )
    else:
        name = f'{agent_id}.agent.md'
        content = (
            '---\n'
            f'name: {_quoted(agent_id)}\n'
            f'description: {_quoted(description)}\n'
            'disable-model-invocation: '
            f'{str(config["disable_model_invocation"]).lower()}\n'
            '---\n\n'
            f'{instructions}\n'
        )
    return name, content.encode()


def desired_adapters(root: Path) -> dict[str, dict[str, bytes]]:
    desired = {harness: {} for harness in HARNESSES}
    for agent in load_registry(root):
        harnesses = agent['harnesses']
        assert isinstance(harnesses, Mapping)
        for harness in harnesses:
            name, content = render_agent(agent, harness)
            desired[str(harness)][name] = content
    return desired


def synchronize(root: Path, *, write: bool) -> tuple[Path, ...]:
    root = root.resolve()
    desired = desired_adapters(root)
    changed: list[Path] = []
    for harness, relative_directory in OUTPUTS.items():
        directory = root / relative_directory
        actual = {
            path.name: path.read_bytes()
            for path in directory.iterdir()
            if path.is_file()
        } if directory.is_dir() else {}
        expected = desired[harness]
        for name in sorted(set(actual) | set(expected)):
            if actual.get(name) != expected.get(name):
                changed.append(relative_directory / name)
        if not write:
            continue
        directory.mkdir(parents=True, exist_ok=True)
        for name in set(actual) - set(expected):
            (directory / name).unlink()
        for name, content in expected.items():
            (directory / name).write_bytes(content)
    return tuple(changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Synchronize plugin Agent host adapters.')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        changed = synchronize(args.root, write=not args.check)
    except AgentRegistryError as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    if args.check and changed:
        print(
            'error: Agent adapter drift in: '
            + ', '.join(path.as_posix() for path in changed),
            file=sys.stderr,
        )
        return 1
    if args.check:
        print('Plugin Agent adapters are up to date.')
    else:
        print(f'Synchronized {len(changed)} plugin Agent adapter(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
