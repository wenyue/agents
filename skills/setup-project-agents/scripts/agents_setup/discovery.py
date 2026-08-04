from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from .models import Catalog, ProjectRuleSpec, ProjectSkillSpec
from .project import ProjectError, confined_target


class DiscoveryError(ValueError):
    """Raised when project-owned Rule or Skill discovery is ambiguous or unsafe."""


_RULE_NAME = re.compile(r'^(\d{2})-[a-z0-9][a-z0-9-]*\.md$')
_STRENGTH = re.compile(r'^Strength:\s*`(Mandatory|Default|Advisory)`\s*$', re.MULTILINE)
_SCOPE = re.compile(r'^Scope:\s*(.+(?:\n(?!\s*$|[A-Za-z][A-Za-z ]+:|#).+)*)', re.MULTILINE)


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, 'is_junction') and path.is_junction()
    )


def _managed_targets(catalog: Catalog, kind: str) -> set[PurePosixPath]:
    return {
        asset.target
        for asset in catalog.assets
        if asset.target is not None
        and (
            asset.kind == kind
            or (
                asset.kind == 'blueprint'
                and asset.target.parts[:2] == ('.agents', f'{kind}s')
            )
        )
    }


def _rule_section(number: int) -> str:
    if number < 10:
        return 'global'
    if number < 20:
        return 'base'
    return 'project'


def _rule_metadata(path: Path, relative: PurePosixPath) -> ProjectRuleSpec:
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise DiscoveryError(f'cannot read project Rule: {relative.as_posix()}') from error
    strength = _STRENGTH.search(text)
    scope = _SCOPE.search(text)
    if strength is None or scope is None:
        raise DiscoveryError(
            f'project Rule requires Strength and Scope metadata: {relative.as_posix()}'
        )
    match = _RULE_NAME.fullmatch(path.name)
    assert match is not None
    read_when = ' '.join(line.strip() for line in scope.group(1).splitlines()).strip()
    if not read_when:
        raise DiscoveryError(f'project Rule Scope is empty: {relative.as_posix()}')
    return ProjectRuleSpec(
        relative,
        _rule_section(int(match.group(1))),
        read_when,
        strength.group(1),
    )


def discover_project_rules(target_root: Path, catalog: Catalog) -> tuple[ProjectRuleSpec, ...]:
    root_relative = PurePosixPath('.agents/rules')
    try:
        root = confined_target(target_root, root_relative)
    except ProjectError as error:
        raise DiscoveryError(str(error)) from error
    if not root.exists():
        return ()
    if not root.is_dir():
        raise DiscoveryError('project Rule root is not a directory')
    managed = _managed_targets(catalog, 'rule')
    result: list[ProjectRuleSpec] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if _is_link_like(path):
            raise DiscoveryError(f'project Rule path is a symlink: {path.name}')
        if not path.is_file() or _RULE_NAME.fullmatch(path.name) is None:
            continue
        relative = root_relative / path.name
        if relative in managed:
            continue
        result.append(_rule_metadata(path, relative))
    return tuple(result)


def discover_project_skills(
    target_root: Path,
    catalog: Catalog,
    *,
    external_names: frozenset[str] = frozenset(),
) -> tuple[ProjectSkillSpec, ...]:
    root_relative = PurePosixPath('.agents/skills')
    try:
        root = confined_target(target_root, root_relative)
    except ProjectError as error:
        raise DiscoveryError(str(error)) from error
    if not root.exists():
        return ()
    if not root.is_dir():
        raise DiscoveryError('project Skill root is not a directory')
    managed_roots: set[PurePosixPath] = set()
    for asset in catalog.assets:
        if asset.target is None:
            continue
        if asset.kind == 'skill' and asset.target.parts[:2] == ('.agents', 'skills'):
            managed_roots.add(asset.target)
        elif (
            asset.kind == 'blueprint'
            and asset.target.parts[:2] == ('.agents', 'skills')
            and asset.target.name == 'SKILL.md'
        ):
            managed_roots.add(asset.target.parent)
    result: list[ProjectSkillSpec] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if _is_link_like(path):
            raise DiscoveryError(f'project Skill path is a symlink: {path.name}')
        if not path.is_dir():
            continue
        relative = root_relative / path.name
        if relative in managed_roots or path.name in external_names:
            continue
        skill = path / 'SKILL.md'
        if _is_link_like(skill) or not skill.is_file():
            continue
        result.append(ProjectSkillSpec(path.name, relative))
    return tuple(result)


def discover_generated_skill_resources(
    target_root: Path,
    catalog: Catalog,
) -> tuple[PurePosixPath, ...]:
    """Discover project-owned files beside generated Skill entrypoints."""
    generated_entries = {
        asset.target
        for asset in catalog.assets
        if asset.kind == 'blueprint'
        and asset.target is not None
        and asset.target.parts[:2] == ('.agents', 'skills')
        and asset.target.name == 'SKILL.md'
    }
    result: set[PurePosixPath] = set()
    for entry in sorted(generated_entries, key=lambda item: item.as_posix()):
        root_relative = entry.parent
        try:
            root = confined_target(target_root, root_relative)
        except ProjectError as error:
            raise DiscoveryError(str(error)) from error
        if not root.exists():
            continue
        if not root.is_dir():
            raise DiscoveryError(
                f'generated Skill root is not a directory: {root_relative.as_posix()}'
            )
        for path in root.rglob('*'):
            if _is_link_like(path):
                raise DiscoveryError(
                    f'generated Skill resource is a symlink: '
                    f'{(root_relative / path.relative_to(root).as_posix()).as_posix()}'
                )
            if not path.is_file():
                continue
            relative = root_relative / path.relative_to(root).as_posix()
            if relative != entry:
                result.add(relative)
    return tuple(sorted(result, key=lambda item: item.as_posix()))
