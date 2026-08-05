#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path


SEMVER = re.compile(
    r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
    r'(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)'
    r'(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?'
    r'(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$'
)
PLUGIN_NAME = 'smartkit'
MANIFEST_PATHS = (
    Path('.codex-plugin/plugin.json'),
    Path('.cursor-plugin/plugin.json'),
    Path('plugin.json'),
)
MARKETPLACE_PATHS = (
    Path('.cursor-plugin/marketplace.json'),
    Path('.github/plugin/marketplace.json'),
)
CATALOG_PATH = Path('setup-assets/catalog/assets.json')


class VersionSyncError(RuntimeError):
    pass


def read_version(root: Path) -> str:
    path = root / 'VERSION'
    try:
        version = path.read_text(encoding='utf-8').strip()
    except OSError as error:
        raise VersionSyncError(f'cannot read {path}') from error
    if not SEMVER.fullmatch(version):
        raise VersionSyncError('VERSION must be semantic version')
    return version


def update_json(
    root: Path,
    relative_path: Path,
    update: Callable[[dict[str, object]], None],
    *,
    write: bool,
) -> bool:
    path = root / relative_path
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except OSError as error:
        raise VersionSyncError(f'cannot read {path}') from error
    except json.JSONDecodeError as error:
        raise VersionSyncError(f'{relative_path.as_posix()} is not valid JSON') from error
    if not isinstance(document, dict):
        raise VersionSyncError(f'{relative_path.as_posix()} must contain an object')

    before = json.dumps(document, ensure_ascii=False, sort_keys=True)
    update(document)
    after = json.dumps(document, ensure_ascii=False, sort_keys=True)
    if before == after:
        return False
    if write:
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
    return True


def set_manifest_version(document: dict[str, object], version: str) -> None:
    if document.get('name') != PLUGIN_NAME:
        raise VersionSyncError(f'plugin manifest name must be {PLUGIN_NAME}')
    document['version'] = version


def set_marketplace_version(document: dict[str, object], version: str) -> None:
    metadata = document.get('metadata')
    plugins = document.get('plugins')
    if not isinstance(metadata, dict) or not isinstance(plugins, list):
        raise VersionSyncError('marketplace must contain metadata and plugins')
    matches = [
        plugin
        for plugin in plugins
        if isinstance(plugin, dict) and plugin.get('name') == PLUGIN_NAME
    ]
    if len(matches) != 1:
        raise VersionSyncError(
            f'marketplace must contain exactly one {PLUGIN_NAME} plugin'
        )
    metadata['version'] = version
    matches[0]['version'] = version


def set_catalog_version(document: dict[str, object], version: str) -> None:
    plugin = document.get('plugin')
    if not isinstance(plugin, dict) or plugin.get('id') != PLUGIN_NAME:
        raise VersionSyncError(f'catalog plugin id must be {PLUGIN_NAME}')
    plugin['version'] = version


def synchronize(root: Path, *, write: bool = True) -> tuple[str, tuple[Path, ...]]:
    root = root.resolve()
    version = read_version(root)
    changed: list[Path] = []
    for relative_path in MANIFEST_PATHS:
        if update_json(
            root,
            relative_path,
            lambda document, value=version: set_manifest_version(document, value),
            write=write,
        ):
            changed.append(relative_path)
    for relative_path in MARKETPLACE_PATHS:
        if update_json(
            root,
            relative_path,
            lambda document, value=version: set_marketplace_version(document, value),
            write=write,
        ):
            changed.append(relative_path)
    if update_json(
        root,
        CATALOG_PATH,
        lambda document: set_catalog_version(document, version),
        write=write,
    ):
        changed.append(CATALOG_PATH)
    return version, tuple(changed)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Synchronize plugin manifests from the root VERSION file.'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='report version drift without modifying files',
    )
    parser.add_argument(
        '--root',
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        version, changed = synchronize(args.root, write=not args.check)
    except VersionSyncError as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    if args.check:
        if changed:
            paths = ', '.join(path.as_posix() for path in changed)
            print(f'error: plugin version drift in: {paths}', file=sys.stderr)
            return 1
        print(f'Plugin version {version} is up to date.')
        return 0
    print(f'Synchronized plugin version {version} in {len(changed)} file(s).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
