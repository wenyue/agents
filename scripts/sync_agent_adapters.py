#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path, PurePosixPath


PLATFORMS = ('codex', 'cursor', 'copilot')
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
    _fields(registry, {'version', 'agents'}, 'Agent registry')
    if registry.get('version') != 1:
        raise AgentRegistryError('Agent registry version must be 1')
    raw_agents = registry.get('agents')
    if not isinstance(raw_agents, list):
        raise AgentRegistryError('Agent registry agents must be an array')

    agents: list[dict[str, object]] = []
    ids: set[str] = set()
    for index, raw_agent in enumerate(raw_agents):
        label = f'Agent registry agents[{index}]'
        agent = _object(raw_agent, label)
        _fields(agent, {'id', 'source', 'description', 'platforms'}, label)
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
        platforms = _object(agent.get('platforms'), f'{label}.platforms')
        _fields(platforms, set(PLATFORMS), f'{label}.platforms')
        if not platforms:
            raise AgentRegistryError(f'{label}.platforms must not be empty')
        rendered_platforms: dict[str, dict[str, object]] = {}
        for platform, raw_config in platforms.items():
            config = _object(raw_config, f'{label}.platforms.{platform}')
            if platform == 'codex':
                _fields(config, {'sandbox_mode'}, f'{label}.platforms.codex')
                rendered_platforms[platform] = {
                    'sandbox_mode': _nonempty(
                        config.get('sandbox_mode'), f'{label}.platforms.codex.sandbox_mode'
                    )
                }
            elif platform == 'cursor':
                _fields(config, {'readonly'}, f'{label}.platforms.cursor')
                readonly = config.get('readonly')
                if type(readonly) is not bool:
                    raise AgentRegistryError(
                        f'{label}.platforms.cursor.readonly must be a boolean'
                    )
                rendered_platforms[platform] = {'readonly': readonly}
            else:
                _fields(
                    config,
                    {'disable_model_invocation'},
                    f'{label}.platforms.copilot',
                )
                disabled = config.get('disable_model_invocation')
                if type(disabled) is not bool:
                    raise AgentRegistryError(
                        f'{label}.platforms.copilot.disable_model_invocation '
                        'must be a boolean'
                    )
                rendered_platforms[platform] = {'disable_model_invocation': disabled}

        agents.append({
            'id': agent_id,
            'source': source.as_posix(),
            'description': description,
            'instructions': instructions,
            'platforms': rendered_platforms,
        })
    return tuple(agents)


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_agent(agent: Mapping[str, object], platform: str) -> tuple[str, bytes]:
    agent_id = str(agent['id'])
    description = str(agent['description'])
    instructions = str(agent['instructions'])
    platforms = agent['platforms']
    assert isinstance(platforms, Mapping)
    config = platforms[platform]
    assert isinstance(config, Mapping)
    if platform == 'codex':
        name = f'{agent_id}.toml'
        content = (
            f'name = {_quoted(agent_id)}\n'
            f'description = {_quoted(description)}\n'
            f'sandbox_mode = {_quoted(str(config["sandbox_mode"]))}\n'
            'developer_instructions = """\n'
            f'{instructions}\n'
            '"""\n'
        )
    elif platform == 'cursor':
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
    desired = {platform: {} for platform in PLATFORMS}
    for agent in load_registry(root):
        platforms = agent['platforms']
        assert isinstance(platforms, Mapping)
        for platform in platforms:
            name, content = render_agent(agent, platform)
            desired[str(platform)][name] = content
    return desired


def synchronize(root: Path, *, write: bool) -> tuple[Path, ...]:
    root = root.resolve()
    desired = desired_adapters(root)
    changed: list[Path] = []
    for platform, relative_directory in OUTPUTS.items():
        directory = root / relative_directory
        actual = {
            path.name: path.read_bytes()
            for path in directory.iterdir()
            if path.is_file()
        } if directory.is_dir() else {}
        expected = desired[platform]
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
