from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

from .models import ExternalSkillSpec


class ExternalSkillError(ValueError):
    """Raised when a configured external Skill cannot produce a safe snapshot."""


_FRONTMATTER_NAME = re.compile(r'^---\s*\n(?:.*\n)*?name:\s*([^\s]+)\s*$', re.MULTILINE)


def _repository_url(repository: str) -> str:
    return f'https://github.com/{repository}.git'


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, 'is_junction') and path.is_junction()
    )


def _git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith('GIT_')
    }
    environment.update(
        {
            'GIT_TERMINAL_PROMPT': '0',
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': os.devnull,
        }
    )
    return environment


def _run_git(*args: str) -> None:
    try:
        completed = subprocess.run(
            ('git', *args),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            env=_git_environment(),
        )
    except OSError as error:
        raise ExternalSkillError('Git is unavailable for external Skill setup') from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or 'Git command failed'
        raise ExternalSkillError(detail)


def _reject_symlinks(root: Path, name: str) -> None:
    for path in root.rglob('*'):
        if _is_link_like(path):
            raise ExternalSkillError(f'external Skill contains a symlink: {name}')


def _validate_skill(root: Path, spec: ExternalSkillSpec) -> None:
    if _is_link_like(root) or not root.is_dir():
        raise ExternalSkillError(f'external Skill path is not a directory: {spec.name}')
    _reject_symlinks(root, spec.name)
    skill = root / 'SKILL.md'
    if not skill.is_file() or _is_link_like(skill):
        raise ExternalSkillError(f'external Skill is missing SKILL.md: {spec.name}')
    try:
        text = skill.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise ExternalSkillError(f'cannot read external Skill: {spec.name}') from error
    match = _FRONTMATTER_NAME.search(text)
    if match is None or match.group(1) != spec.name:
        raise ExternalSkillError(f'external Skill name does not match config: {spec.name}')


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
    specs: tuple[ExternalSkillSpec, ...],
    *,
    session: Path,
) -> Path | None:
    if not specs:
        return None
    snapshots = session / 'external-skills'
    checkouts = session / 'external-checkouts'
    snapshots.mkdir()
    checkouts.mkdir()
    try:
        for spec in specs:
            checkout = checkouts / spec.name
            checkout.mkdir()
            _run_git('init', '--quiet', str(checkout))
            repository = _repository_url(spec.repository)
            _run_git('-C', str(checkout), 'remote', 'add', 'origin', repository)
            _run_git('-C', str(checkout), 'fetch', '--depth=1', 'origin', spec.ref)
            _run_git('-C', str(checkout), 'checkout', '--quiet', '--detach', 'FETCH_HEAD')
            source = checkout.joinpath(*spec.path.parts)
            _validate_skill(source, spec)
            shutil.copytree(source, snapshots / spec.name)
    finally:
        _remove_checkouts(checkouts)
    return snapshots
