from __future__ import annotations

import os
import json
import hashlib
import shutil
import stat
import subprocess
from pathlib import Path

from .models import ExternalSourceSpec
from .external_contract import (
    ExternalContractError,
    license_matches,
    resolve_ref,
    snapshot_skill_tree,
    source_path,
)


class ExternalSkillError(ValueError):
    """Raised when a configured external Skill cannot produce a safe snapshot."""


def _license_matches(spdx: str, content: bytes) -> bool:
    try:
        return license_matches(spdx, content)
    except ExternalContractError as error:
        raise ExternalSkillError(str(error)) from error


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
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExternalSkillError('existing external Skill lock is invalid') from error
    if not isinstance(document, dict) or document.get('version') != 1:
        raise ExternalSkillError('existing external Skill lock is invalid')
    sources = document.get('sources')
    if not isinstance(sources, list):
        raise ExternalSkillError('existing external Skill lock is invalid')
    result: dict[str, dict[str, object]] = {}
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get('id'), str):
            raise ExternalSkillError('existing external Skill lock is invalid')
        result[source['id']] = source
    return result


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
    existing_lock: Path | None = None,
) -> Path | None:
    if not specs:
        return None
    snapshots = session / 'external-skills'
    checkouts = session / 'external-checkouts'
    snapshots.mkdir()
    checkouts.mkdir()
    previous_sources = _previous_sources(existing_lock)
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
                license_path = source_path(
                    checkout, source_spec.license.path, f'external source {source_spec.id}'
                )
            except ExternalContractError as error:
                raise ExternalSkillError(str(error)) from error
            try:
                license_bytes = license_path.read_bytes()
            except OSError as error:
                raise ExternalSkillError(f'external source license is missing: {source_spec.id}') from error
            if not _license_matches(source_spec.license.spdx, license_bytes):
                raise ExternalSkillError(f'external source license does not match: {source_spec.id}')
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
                    'spdx': source_spec.license.spdx,
                    'path': source_spec.license.path.as_posix(),
                    'sha256': hashlib.sha256(license_bytes).hexdigest(),
                },
                'skills': skill_locks,
            })
        (snapshots / 'external-skills.lock.json').write_text(
            json.dumps({'version': 1, 'sources': lock_sources}, indent=2) + '\n',
            encoding='utf-8',
        )
    finally:
        _remove_checkouts(checkouts)
    return snapshots
