#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path, PurePosixPath


PLATFORMS = ('codex', 'cursor', 'copilot')
OPERATING_SYSTEMS = ('windows', 'linux')
OUTPUTS = {
    'codex': Path('.mcp.json'),
    'cursor': Path('mcp/cursor.json'),
    'copilot': Path('mcp/copilot.json'),
}
REGISTRY_PATH = Path('mcp/registry.json')
SAFE_ID = re.compile(r'^[a-z0-9][a-z0-9-]*$')
VERSION = re.compile(r'^(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*)){2}$')
ENVIRONMENT_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
UNSAFE_PLAYWRIGHT_ARGS = frozenset({
    '--allow-unrestricted-file-access',
    '--no-sandbox',
    '--storage-state',
    '--user-data-dir',
})


class McpRegistryError(ValueError):
    pass


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise McpRegistryError(f'{label} must be an object')
    return value


def _fields(value: Mapping[str, object], allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise McpRegistryError(
            f'unknown {label} fields: {", ".join(sorted(str(item) for item in unknown))}'
        )


def _strings(value: object, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise McpRegistryError(f'{label} must be an array of non-empty strings')
    return list(value)


def _readiness_check(value: object, label: str) -> dict[str, object]:
    check = _object(value, label)
    kind = check.get('kind')
    if kind == 'command-exists':
        _fields(check, {'kind', 'command'}, label)
        command = check.get('command')
        if not isinstance(command, str) or not command:
            raise McpRegistryError(f'{label}.command must be a non-empty string')
    elif kind == 'runtime-version':
        _fields(check, {'kind', 'runtime', 'minimum'}, label)
        if check.get('runtime') != 'node':
            raise McpRegistryError(f'{label}.runtime is unsupported')
        minimum = check.get('minimum')
        if not isinstance(minimum, str) or VERSION.fullmatch(minimum) is None:
            raise McpRegistryError(f'{label}.minimum must be a numeric version')
    elif kind == 'workspace-path':
        _fields(check, {'kind', 'path', 'executable'}, label)
        raw_path = check.get('path')
        executable = check.get('executable', False)
        if (
            not isinstance(raw_path, str)
            or not raw_path
            or '\\' in raw_path
            or PurePosixPath(raw_path).is_absolute()
            or '..' in PurePosixPath(raw_path).parts
            or type(executable) is not bool
        ):
            raise McpRegistryError(f'{label} is invalid')
    elif kind == 'environment-variable':
        _fields(check, {'kind', 'name'}, label)
        name = check.get('name')
        if not isinstance(name, str) or ENVIRONMENT_NAME.fullmatch(name) is None:
            raise McpRegistryError(f'{label}.name is invalid')
    else:
        raise McpRegistryError(f'{label}.kind is unsupported')
    return dict(check)


def _readiness(
    value: object,
    label: str,
    enabled_platforms: list[str],
) -> dict[str, object]:
    readiness = _object(value, label)
    _fields(readiness, {'platforms', 'operatingSystems', 'checks'}, label)
    rendered: dict[str, object] = {}
    if 'platforms' in readiness:
        platforms = _strings(
            readiness['platforms'], f'{label}.platforms', allow_empty=False
        )
        if (
            len(platforms) != len(set(platforms))
            or set(platforms) - set(enabled_platforms)
        ):
            raise McpRegistryError(f'{label}.platforms is invalid')
        rendered['platforms'] = platforms
    if 'operatingSystems' in readiness:
        operating_systems = _strings(
            readiness['operatingSystems'],
            f'{label}.operatingSystems',
            allow_empty=False,
        )
        if (
            len(operating_systems) != len(set(operating_systems))
            or set(operating_systems) - set(OPERATING_SYSTEMS)
        ):
            raise McpRegistryError(f'{label}.operatingSystems is invalid')
        rendered['operatingSystems'] = operating_systems
    if 'checks' in readiness:
        checks = readiness['checks']
        if not isinstance(checks, list):
            raise McpRegistryError(f'{label}.checks must be an array')
        rendered['checks'] = [
            _readiness_check(check, f'{label}.checks[{index}]')
            for index, check in enumerate(checks)
        ]
    return rendered


def load_registry(path: Path) -> tuple[dict[str, object], ...]:
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise McpRegistryError(f'cannot load MCP registry: {path}') from error
    root = _object(document, 'MCP registry')
    _fields(root, {'version', 'servers'}, 'MCP registry')
    if root.get('version') != 1:
        raise McpRegistryError('MCP registry version must be 1')
    raw_servers = root.get('servers')
    if not isinstance(raw_servers, list):
        raise McpRegistryError('MCP registry servers must be an array')
    servers: list[dict[str, object]] = []
    ids: set[str] = set()
    for index, raw_server in enumerate(raw_servers):
        label = f'MCP registry servers[{index}]'
        server = _object(raw_server, label)
        _fields(
            server,
            {
                'id', 'transport', 'command', 'args', 'url', 'platforms', 'tools',
                'readiness',
            },
            label,
        )
        server_id = server.get('id')
        if not isinstance(server_id, str) or SAFE_ID.fullmatch(server_id) is None:
            raise McpRegistryError(f'{label}.id must be a safe name')
        if server_id in ids:
            raise McpRegistryError('MCP registry has duplicate server ids')
        ids.add(server_id)
        transport = server.get('transport')
        if transport not in {'stdio', 'http'}:
            raise McpRegistryError(f'{label}.transport is unsupported')
        platforms = _strings(server.get('platforms'), f'{label}.platforms', allow_empty=False)
        if len(platforms) != len(set(platforms)) or set(platforms) - set(PLATFORMS):
            raise McpRegistryError(f'{label}.platforms is invalid')
        if transport == 'stdio':
            if set(server).intersection({'url'}):
                raise McpRegistryError(f'{label} stdio server cannot declare url')
            command = server.get('command')
            if not isinstance(command, str) or not command:
                raise McpRegistryError(f'{label}.command must be a non-empty string')
            args = _strings(server.get('args', []), f'{label}.args')
            if server_id == 'playwright':
                if command != 'npx' or args != [
                    '-y', '@playwright/mcp@latest', '--isolated', '--headless'
                ]:
                    raise McpRegistryError(
                        'playwright must use the approved latest isolated headless launcher'
                    )
                if any(
                    argument in UNSAFE_PLAYWRIGHT_ARGS
                    or argument.startswith('--allowed-hosts=')
                    for argument in args
                ):
                    raise McpRegistryError('playwright declares an unsafe argument')
        else:
            if set(server).intersection({'command', 'args'}):
                raise McpRegistryError(f'{label} http server cannot declare stdio fields')
            url = server.get('url')
            if not isinstance(url, str) or not url.startswith(('https://', 'http://')):
                raise McpRegistryError(f'{label}.url must be an HTTP URL')
        tools = _strings(server.get('tools', ['*']), f'{label}.tools', allow_empty=False)
        if server_id == 'playwright' and tools != ['*']:
            raise McpRegistryError('playwright must expose all tools through host approval')
        if 'readiness' in server:
            _readiness(server['readiness'], f'{label}.readiness', platforms)
        servers.append(dict(server))
    return tuple(servers)


def render_platform(servers: tuple[dict[str, object], ...], platform: str) -> bytes:
    rendered: dict[str, object] = {}
    for server in servers:
        if platform not in server['platforms']:
            continue
        if server['transport'] == 'http':
            entry: dict[str, object] = {
                **({'type': 'http'} if platform != 'codex' else {}),
                'url': server['url'],
            }
        else:
            entry = {
                **(
                    {'type': 'local' if platform == 'copilot' else 'stdio'}
                    if platform != 'codex'
                    else {}
                ),
                'command': server['command'],
                'args': list(server.get('args', [])),
            }
        if platform == 'copilot':
            entry['tools'] = list(server.get('tools', ['*']))
        rendered[str(server['id'])] = entry
    return (json.dumps({'mcpServers': rendered}, indent=2) + '\n').encode()


def synchronize(root: Path, *, write: bool) -> tuple[Path, ...]:
    root = root.resolve()
    servers = load_registry(root / REGISTRY_PATH)
    changed: list[Path] = []
    for platform in PLATFORMS:
        relative = OUTPUTS[platform]
        desired = render_platform(servers, platform)
        path = root / relative
        try:
            current = path.read_bytes()
        except OSError:
            current = None
        if current == desired:
            continue
        changed.append(relative)
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(desired)
    return tuple(changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Synchronize plugin MCP host adapters.')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        changed = synchronize(args.root, write=not args.check)
    except McpRegistryError as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    if args.check and changed:
        print(
            'error: MCP adapter drift in: '
            + ', '.join(path.as_posix() for path in changed),
            file=sys.stderr,
        )
        return 1
    if args.check:
        print('Plugin MCP adapters are up to date.')
    else:
        print(f'Synchronized {len(changed)} plugin MCP adapter(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
