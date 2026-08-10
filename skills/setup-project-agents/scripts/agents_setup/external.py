from __future__ import annotations

import os
import json
import hashlib
import shutil
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

from .models import ExternalSourceSpec
from .ownership import OwnershipError, load_ownership_file
from .external_contract import (
    ExternalContractError,
    discover_license,
    COMMIT,
    resolve_ref,
    snapshot_skill_tree,
)


class ExternalSkillError(ValueError):
    """Raised when a configured external Skill cannot produce a safe snapshot."""


_SOURCE_FIELDS = frozenset({
    'id', 'url', 'requested_ref', 'resolved_ref', 'ref_kind', 'commit', 'license', 'skills',
})
_LICENSE_FIELDS = frozenset({'spdx', 'path', 'sha256'})
_SKILL_FIELDS = frozenset({'id', 'path', 'files'})


def validated_snapshot_metadata(
    specs: tuple[ExternalSourceSpec, ...],
    snapshots: Path,
) -> tuple[Mapping[str, object], ...]:
    """Validate private-session metadata and trees before attributing them to a source commit."""
    metadata_path = snapshots / 'sources.json'
    if metadata_path.is_symlink() or not metadata_path.is_file():
        raise ExternalSkillError('external Skill source metadata is missing or unsafe')
    try:
        document = json.loads(metadata_path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExternalSkillError('external Skill source metadata is invalid') from error
    if not isinstance(document, Mapping) or set(document) != {'version', 'sources'}:
        raise ExternalSkillError('external Skill source metadata is invalid')
    raw_sources = document.get('sources')
    if document.get('version') != 1 or not isinstance(raw_sources, list):
        raise ExternalSkillError('external Skill source metadata is invalid')
    if len(raw_sources) != len(specs):
        raise ExternalSkillError('external Skill source metadata does not match project config')
    result: list[Mapping[str, object]] = []
    for spec, raw_source in zip(specs, raw_sources):
        if not isinstance(raw_source, Mapping) or set(raw_source) != _SOURCE_FIELDS:
            raise ExternalSkillError('external Skill source metadata is invalid')
        if (
            raw_source.get('id') != spec.id
            or raw_source.get('url') != spec.url
            or raw_source.get('requested_ref') != spec.ref
            or raw_source.get('ref_kind') not in {'branch', 'tag', 'commit'}
            or not isinstance(raw_source.get('resolved_ref'), str)
            or not raw_source.get('resolved_ref')
            or not isinstance(raw_source.get('commit'), str)
            or COMMIT.fullmatch(raw_source['commit']) is None
        ):
            raise ExternalSkillError('external Skill source metadata does not match project config')
        license_item = raw_source.get('license')
        if not isinstance(license_item, Mapping) or set(license_item) != _LICENSE_FIELDS:
            raise ExternalSkillError('external Skill source metadata license is invalid')
        if (
            not isinstance(license_item.get('spdx'), str)
            or not isinstance(license_item.get('path'), str)
            or not isinstance(license_item.get('sha256'), str)
            or len(license_item['sha256']) != 64
            or any(character not in '0123456789abcdef' for character in license_item['sha256'])
        ):
            raise ExternalSkillError('external Skill source metadata license is invalid')
        raw_skills = raw_source.get('skills')
        if not isinstance(raw_skills, list) or len(raw_skills) != len(spec.skills):
            raise ExternalSkillError('external Skill source metadata does not match project config')
        compact_skills: list[Mapping[str, object]] = []
        for skill_spec, raw_skill in zip(spec.skills, raw_skills):
            if not isinstance(raw_skill, Mapping) or set(raw_skill) != _SKILL_FIELDS:
                raise ExternalSkillError('external Skill source metadata is invalid')
            files = raw_skill.get('files')
            if (
                raw_skill.get('id') != skill_spec.id
                or raw_skill.get('path') != skill_spec.path.as_posix()
                or not isinstance(files, Mapping)
                or not all(
                    isinstance(path, str)
                    and isinstance(digest, str)
                    and len(digest) == 64
                    and all(character in '0123456789abcdef' for character in digest)
                    for path, digest in files.items()
                )
            ):
                raise ExternalSkillError('external Skill source metadata does not match project config')
            try:
                tree = snapshot_skill_tree(
                    snapshots,
                    PurePosixPath(skill_spec.name),
                    skill_spec.name,
                    f'external Skill snapshot {skill_spec.id}',
                )
            except ExternalContractError as error:
                raise ExternalSkillError(str(error)) from error
            if dict(files) != tree.files:
                raise ExternalSkillError(f'external Skill snapshot changed: {skill_spec.id}')
            compact_skills.append({
                'id': skill_spec.id,
                'path': skill_spec.path.as_posix(),
            })
        result.append({
            'id': spec.id,
            'url': spec.url,
            'requested_ref': raw_source['requested_ref'],
            'resolved_ref': raw_source['resolved_ref'],
            'ref_kind': raw_source['ref_kind'],
            'commit': raw_source['commit'],
            'license': dict(license_item),
            'skills': compact_skills,
        })
    return tuple(result)


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment['GIT_TERMINAL_PROMPT'] = '0'
    return environment


def _run_git(*args: str) -> str:
    try:
        completed = subprocess.run(
            ('git', *args),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=_git_environment(),
        )
    except OSError as error:
        raise ExternalSkillError('Git is unavailable for external Skill setup') from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or 'Git command failed'
        raise ExternalSkillError(detail)
    return completed.stdout.strip()


def _previous_sources(path: Path | None) -> dict[str, dict[str, object]]:
    if path is None or not path.exists():
        return {}
    try:
        ownership = load_ownership_file(path)
    except OwnershipError as error:
        raise ExternalSkillError('existing SmartKit ownership manifest is invalid') from error
    assert ownership is not None
    return {str(source['id']): dict(source) for source in ownership.sources}


def _remove_checkouts(root: Path) -> None:
    if not root.exists():
        return
    try:
        for path in root.rglob('*'):
            if path.is_file():
                path.chmod(stat.S_IREAD | stat.S_IWRITE)
        shutil.rmtree(root)
    except OSError as error:
        raise ExternalSkillError('cannot remove external Skill checkout') from error


def snapshot_external_skills(
    specs: tuple[ExternalSourceSpec, ...],
    *,
    session: Path,
    existing_manifest: Path | None = None,
) -> Path | None:
    if not specs:
        return None
    snapshots = session / 'external-skills'
    checkouts = session / 'external-checkouts'
    snapshots.mkdir()
    checkouts.mkdir()
    previous_sources = _previous_sources(existing_manifest)
    try:
        lock_sources: list[dict[str, object]] = []
        for source_spec in specs:
            checkout = checkouts / source_spec.id.replace('/', '--')
            checkout.mkdir()
            _run_git('init', '--quiet', str(checkout))
            _run_git('-C', str(checkout), 'remote', 'add', 'origin', source_spec.url)
            try:
                resolution = resolve_ref(
                    source_spec.url,
                    source_spec.ref,
                    lambda arguments: _run_git(*arguments),
                )
            except ExternalContractError as error:
                raise ExternalSkillError(f'{source_spec.id}: {error}') from error
            _run_git(
                '-C', str(checkout), 'fetch', '--depth=1',
                'origin', resolution.fetch_ref,
            )
            _run_git('-C', str(checkout), 'checkout', '--quiet', '--detach', 'FETCH_HEAD')
            commit = _run_git('-C', str(checkout), 'rev-parse', 'HEAD')
            if (
                resolution.ref_kind == 'tag'
                and (previous := previous_sources.get(source_spec.id)) is not None
                and previous.get('requested_ref') == source_spec.ref
                and previous.get('commit') != commit
            ):
                raise ExternalSkillError(
                    f'external source tag moved: {source_spec.id}:{source_spec.ref}'
                )
            try:
                license_discovery = discover_license(
                    checkout, f'external source license {source_spec.id}'
                )
            except ExternalContractError as error:
                raise ExternalSkillError(str(error)) from error
            skill_locks: list[dict[str, object]] = []
            for spec in source_spec.skills:
                try:
                    tree = snapshot_skill_tree(
                        checkout, spec.path, spec.name, f'external Skill {spec.id}'
                    )
                except ExternalContractError as error:
                    raise ExternalSkillError(str(error)) from error
                shutil.copytree(tree.root, snapshots / spec.name)
                skill_locks.append({
                    'id': spec.id,
                    'path': spec.path.as_posix(),
                    'files': tree.files,
                })
            lock_sources.append({
                'id': source_spec.id,
                'url': source_spec.url,
                'requested_ref': source_spec.ref,
                'resolved_ref': resolution.resolved_ref,
                'ref_kind': resolution.ref_kind,
                'commit': commit,
                'license': {
                    'spdx': license_discovery.spdx,
                    'path': license_discovery.path.as_posix(),
                    'sha256': hashlib.sha256(license_discovery.content).hexdigest(),
                },
                'skills': skill_locks,
            })
        (snapshots / 'sources.json').write_text(
            json.dumps({'version': 1, 'sources': lock_sources}, indent=2) + '\n',
            encoding='utf-8',
        )
    finally:
        _remove_checkouts(checkouts)
    return snapshots
