from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import NamedTuple


COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')
GITHUB_URL = re.compile(
    r'^(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+)/'
    r'([A-Za-z0-9_.-]+?)(?:\.git)?$'
)
GIT_REF = re.compile(r'^[A-Za-z0-9._/-]+$')
FRONTMATTER_NAME = re.compile(
    r'(?m)^name:\s*["\']?([^\s"\']+)["\']?\s*$'
)
LICENSE_MARKERS: dict[str, tuple[str, ...]] = {
    'MIT': ('mit license', 'permission is hereby granted'),
    'Apache-2.0': ('apache license', 'version 2.0'),
    'BSD-2-Clause': ('redistribution and use', 'disclaimer'),
    'BSD-3-Clause': ('redistribution and use', 'neither the name'),
    'MPL-2.0': ('mozilla public license', 'version 2.0'),
    'ISC': ('permission to use, copy, modify', 'the software is provided'),
}
LICENSE_CANDIDATES = (
    PurePosixPath('LICENSE'),
    PurePosixPath('LICENSE.txt'),
    PurePosixPath('LICENSE.md'),
    PurePosixPath('COPYING'),
    PurePosixPath('COPYING.txt'),
    PurePosixPath('COPYING.md'),
)
LICENSE_DISCOVERY_ORDER = (
    'MIT',
    'Apache-2.0',
    'BSD-3-Clause',
    'BSD-2-Clause',
    'MPL-2.0',
    'ISC',
)


class ExternalContractError(ValueError):
    """Raised when a GitHub source cannot satisfy the shared snapshot contract."""


class RefResolution(NamedTuple):
    requested_ref: str | None
    fetch_ref: str
    resolved_ref: str
    ref_kind: str


class SkillTreeSnapshot(NamedTuple):
    root: Path
    files: dict[str, str]


class LicenseDiscovery(NamedTuple):
    spdx: str
    path: PurePosixPath
    content: bytes


GitRunner = Callable[[tuple[str, ...]], str]


def validate_source_identity(source_id: str, url: str) -> None:
    match = GITHUB_URL.fullmatch(url)
    if match is None or source_id.casefold() != (
        f'{match.group(1)}/{match.group(2)}'.casefold()
    ):
        raise ExternalContractError('source id and GitHub url must match')


def validate_ref(ref: str | None) -> None:
    if ref is not None and (
        not ref or ref.startswith('-') or GIT_REF.fullmatch(ref) is None
    ):
        raise ExternalContractError('source ref must be a safe Git argument')


def resolve_ref(url: str, requested_ref: str | None, run_git: GitRunner) -> RefResolution:
    validate_ref(requested_ref)
    if requested_ref is None:
        symbolic = run_git(('ls-remote', '--symref', url, 'HEAD'))
        match = re.search(r'ref: refs/heads/([^\s]+)\s+HEAD', symbolic)
        return RefResolution(None, 'HEAD', match.group(1) if match else 'HEAD', 'branch')
    if COMMIT.fullmatch(requested_ref):
        return RefResolution(requested_ref, requested_ref, requested_ref, 'commit')
    if run_git(('ls-remote', '--heads', url, requested_ref)):
        return RefResolution(requested_ref, requested_ref, requested_ref, 'branch')
    if run_git(('ls-remote', '--tags', url, f'refs/tags/{requested_ref}')):
        return RefResolution(requested_ref, requested_ref, requested_ref, 'tag')
    raise ExternalContractError(f'source ref does not exist: {requested_ref}')


def license_matches(spdx: str, content: bytes) -> bool:
    expected = LICENSE_MARKERS.get(spdx)
    if expected is None:
        raise ExternalContractError(f'unsupported SPDX license: {spdx}')
    try:
        text = content.decode('utf-8').casefold()
    except UnicodeDecodeError:
        return False
    return all(marker in text for marker in expected)


def discover_license(root: Path, label: str) -> LicenseDiscovery:
    discoveries: list[LicenseDiscovery] = []
    for relative in LICENSE_CANDIDATES:
        path = source_path(root, relative, label)
        if not path.exists():
            continue
        if not path.is_file():
            raise ExternalContractError(f'{label} is not a regular file: {relative}')
        try:
            content = path.read_bytes()
        except OSError as error:
            raise ExternalContractError(f'{label} cannot be read: {relative}') from error
        for spdx in LICENSE_DISCOVERY_ORDER:
            if license_matches(spdx, content):
                discoveries.append(LicenseDiscovery(spdx, relative, content))
                break
    if not discoveries:
        raise ExternalContractError(f'{label} was not found or recognized')
    signatures = {
        (item.spdx, hashlib.sha256(item.content).hexdigest())
        for item in discoveries
    }
    if len(signatures) != 1:
        paths = ', '.join(item.path.as_posix() for item in discoveries)
        raise ExternalContractError(f'{label} is ambiguous: {paths}')
    return discoveries[0]


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, 'is_junction') and path.is_junction()
    )


def source_path(root: Path, relative: PurePosixPath, label: str) -> Path:
    current = root
    if _is_link_like(current) or not current.is_dir():
        raise ExternalContractError(f'{label} source root is not a regular directory')
    for part in relative.parts:
        current /= part
        if _is_link_like(current):
            raise ExternalContractError(f'{label} path contains a symlink')
    return current


def snapshot_skill_tree(
    checkout_root: Path,
    relative: PurePosixPath,
    expected_name: str,
    label: str,
) -> SkillTreeSnapshot:
    root = source_path(checkout_root, relative, label)
    if _is_link_like(root) or not root.is_dir():
        raise ExternalContractError(f'{label} is not a regular directory')
    files: dict[str, str] = {}
    for path in sorted(root.rglob('*')):
        if _is_link_like(path):
            raise ExternalContractError(f'{label} contains a symlink')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ExternalContractError(f'{label} contains a non-regular file')
        relative_file = path.relative_to(root).as_posix()
        files[relative_file] = hashlib.sha256(path.read_bytes()).hexdigest()
    skill = root / 'SKILL.md'
    try:
        text = skill.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise ExternalContractError(f'{label} is missing a UTF-8 SKILL.md') from error
    if not text.startswith('---\n'):
        raise ExternalContractError(f'{label} SKILL.md has no YAML frontmatter')
    end = text.find('\n---', 4)
    match = FRONTMATTER_NAME.search(text[4:end]) if end >= 0 else None
    if match is None or match.group(1) != expected_name:
        raise ExternalContractError(f'{label} name does not match config')
    return SkillTreeSnapshot(root, files)
