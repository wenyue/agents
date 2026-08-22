from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

from agents_setup.catalog import (
    ContractError,
    load_catalog,
    parse_external_skills,
    parse_mcp_servers,
    parse_project_agents,
)
from agents_setup.discovery import DiscoveryError
from agents_setup.external import ExternalSkillError, snapshot_external_skills
from agents_setup.models import Catalog, Harness, ProjectConfig
from agents_setup.planner import PlanningError, build_plan
from agents_setup.project import ProjectError, inspect_project
from agents_setup.renderer import RenderError, render_desired_state
from agents_setup.source import InvalidFetchedSource, validate_source
from agents_setup.transaction import TransactionError, apply_plan
from agents_setup.validation import validate_rendered_state


_COMMIT = re.compile(r'^[0-9a-fA-F]{40}$')
_REQUEST_NAME = 'request.json'
_GENERATED_NAME = 'generated'
_BLUEPRINT_TARGETS = (
    PurePosixPath('.agents/rules/00-project-tools.md'),
    PurePosixPath('.agents/rules/01-project-contracts.md'),
    PurePosixPath('.agents/rules/02-project-structure.md'),
    PurePosixPath('.agents/skills/change-set-verification/SKILL.md'),
    PurePosixPath('.agents/skills/worktree-environment-setup/SKILL.md'),
)
_HARNESSES = tuple(Harness)


class SetupError(ValueError):
    """Raised when a pinned setup session cannot be used safely."""


def normalize_source_commit(source_commit: str) -> str | None:
    """Convert the bootstrap-only offline sentinel at the pinned CLI boundary."""
    if source_commit == 'offline':
        return None
    if not isinstance(source_commit, str) or not _COMMIT.fullmatch(source_commit):
        raise ValueError('source_commit must be offline or a 40-character hexadecimal commit')
    return source_commit.lower()


def _private_session(value: Path) -> Path:
    session = Path(value).absolute()
    current = Path(session.anchor)
    for part in session.parts[1:]:
        current /= part
        try:
            status = current.lstat()
        except OSError as error:
            raise SetupError(f'session path cannot be inspected: {current}') from error
        if stat.S_ISLNK(status.st_mode) or (
            hasattr(current, 'is_junction') and current.is_junction()
        ):
            raise SetupError(f'session path contains an unsafe link: {current}')
    try:
        status = session.stat()
    except OSError as error:
        raise SetupError('session is unavailable') from error
    if not stat.S_ISDIR(status.st_mode):
        raise SetupError('session is not a directory')
    if os.name == 'posix' and (
        status.st_uid != os.geteuid() or stat.S_IMODE(status.st_mode) != 0o700
    ):
        raise SetupError('session must be private, exact mode 0700, and owned by the current user')
    return session


def _write_json(path: Path, document: Mapping[str, object]) -> None:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise SetupError(f'session file already exists: {path.name}') from error
    try:
        encoded = (json.dumps(document, sort_keys=True, indent=2) + '\n').encode('utf-8')
        remaining = encoded
        while remaining:
            written = os.write(descriptor, remaining)
            remaining = remaining[written:]
    finally:
        os.close(descriptor)


def _read_json(path: Path, label: str) -> Mapping[str, object]:
    try:
        if path.is_symlink() or not path.is_file():
            raise SetupError(f'{label} must be a regular file')
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise SetupError(f'cannot read {label}') from error
    if not isinstance(value, Mapping):
        raise SetupError(f'{label} must be a JSON object')
    return value


def _request(
    source_commit: str | None,
    config: ProjectConfig,
    catalog: Catalog,
    *,
    target: Path,
    source_root: Path,
    external_snapshot_sha256: str | None,
) -> dict[str, object]:
    blueprint_assets = {
        asset.target: asset
        for asset in catalog.assets
        if asset.kind == 'blueprint' and asset.target is not None
    }
    if set(blueprint_assets) != set(_BLUEPRINT_TARGETS):
        raise SetupError('catalog does not declare the required generation targets')
    generation_requests = [
        {
            'id': blueprint_assets[path].id,
            'source': blueprint_assets[path].source.as_posix(),
            'target': path.as_posix(),
        }
        for path in _BLUEPRINT_TARGETS
    ]
    return {
        'target': str(target),
        'source_root': str(source_root),
        'source_commit': source_commit,
        'external_snapshot_sha256': external_snapshot_sha256,
        'harnesses': [item.value for item in _HARNESSES],
        'selected_rules': list(config.selected_rules),
        'selected_skills': list(config.selected_skills),
        'external_sources': [
            {
                'source': source.id,
                **({'ref': source.ref} if source.ref is not None else {}),
                'include': [item.path.as_posix() for item in source.skills],
            }
            for source in config.external_sources
        ],
        'mcp_servers': [
            {
                'id': server.id,
                'harnesses': [harness.value for harness in server.harnesses],
                **({'command': server.command} if server.command is not None else {}),
                **({'args': list(server.args)} if server.args else {}),
                **({'cwd': server.cwd} if server.cwd is not None else {}),
                **({'env': list(server.env)} if server.env else {}),
                **({'url': server.url} if server.url is not None else {}),
                **({
                    'overrides': [
                        {
                            'when': {
                                **({
                                    'harnesses': [
                                        harness.value for harness in override.harnesses
                                    ]
                                } if override.harnesses is not None else {}),
                                **({
                                    'operatingSystems': [
                                        item.value for item in override.operating_systems
                                    ]
                                } if override.operating_systems is not None else {}),
                            },
                            'set': {
                                **({
                                    'command': override.command
                                } if override.command is not None else {}),
                                **({
                                    'args': list(override.args)
                                } if override.args is not None else {}),
                                **({'cwd': override.cwd} if override.cwd is not None else {}),
                                **({
                                    'env': list(override.env)
                                } if override.env is not None else {}),
                                **({'url': override.url} if override.url is not None else {}),
                            },
                        }
                        for override in server.overrides
                    ]
                } if server.overrides else {}),
                **({
                    'readiness': {
                        **({
                            'harnesses': [
                                harness.value for harness in server.readiness.harnesses
                            ]
                        } if server.readiness.harnesses is not None else {}),
                        **({
                            'operatingSystems': [
                                item.value for item in server.readiness.operating_systems
                            ]
                        } if server.readiness.operating_systems is not None else {}),
                        **({
                            'checks': [dict(check) for check in server.readiness.checks]
                        } if server.readiness.checks is not None else {}),
                    }
                } if server.readiness is not None else {}),
            }
            for server in config.mcp_servers
        ],
        'project_agents': [
            {
                'id': agent.id,
                'source': agent.source.as_posix(),
                'description': agent.description,
                'harnesses': {
                    **({
                        'codex': {
                            **({'model': agent.codex.model} if agent.codex.model else {}),
                            **({
                                'model_reasoning_effort':
                                agent.codex.model_reasoning_effort
                            } if agent.codex.model_reasoning_effort else {}),
                            'sandbox_mode': agent.codex.sandbox_mode,
                        }
                    } if agent.codex is not None else {}),
                    **({
                        'cursor': {
                            **({'model': agent.cursor.model} if agent.cursor.model else {}),
                            'readonly': agent.cursor.readonly,
                        }
                    } if agent.cursor is not None else {}),
                    **({
                        'copilot': {
                            **({'model': agent.copilot.model} if agent.copilot.model else {}),
                            'disable_model_invocation':
                            agent.copilot.disable_model_invocation,
                        }
                    } if agent.copilot is not None else {}),
                },
            }
            for agent in config.agents
        ],
        'generation_requests': generation_requests,
    }


def _selected_request_ids(
    value: object,
    *,
    catalog: Catalog,
    kind: str,
) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SetupError(f'session request {kind} selections must be an array of IDs')
    if len(value) != len(set(value)):
        raise SetupError(f'session request {kind} selections contain duplicates')
    available = {
        asset.id
        for asset in catalog.assets
        if asset.kind == kind and not asset.control_plane
    }
    if set(value) - available:
        raise SetupError(f'session request {kind} selections contain unknown IDs')
    return tuple(value)


def _request_config(
    request: Mapping[str, object],
    source_commit: str | None,
    *,
    target: Path,
    source_root: Path,
    catalog: Catalog,
) -> ProjectConfig:
    required = {
        'target', 'source_root', 'source_commit', 'harnesses', 'selected_rules',
        'selected_skills', 'external_sources', 'mcp_servers', 'generation_requests',
        'external_snapshot_sha256', 'project_agents',
    }
    if set(request) != required:
        raise SetupError('session request has an invalid shape')
    if request.get('source_commit') != source_commit:
        raise SetupError('session request source commit does not match this pinned source')
    if request.get('target') != str(target):
        raise SetupError('session request target does not match this invocation')
    if request.get('source_root') != str(source_root):
        raise SetupError('session request source root does not match this pinned source')
    try:
        snapshot_digest = request['external_snapshot_sha256']
        if snapshot_digest is not None and (
            not isinstance(snapshot_digest, str)
            or len(snapshot_digest) != 64
            or any(character not in '0123456789abcdef' for character in snapshot_digest)
        ):
            raise ValueError
        harnesses = tuple(Harness(item) for item in request['harnesses'])
        if harnesses != _HARNESSES:
            raise ValueError
        selections = (
            _selected_request_ids(request['selected_rules'], catalog=catalog, kind='rule'),
            _selected_request_ids(request['selected_skills'], catalog=catalog, kind='skill'),
        )
        generation = request['generation_requests']
        expected_generation = {
            asset.target.as_posix(): {
                'id': asset.id,
                'source': asset.source.as_posix(),
                'target': asset.target.as_posix(),
            }
            for asset in catalog.assets
            if asset.kind == 'blueprint' and asset.target is not None
        }
        if (
            not isinstance(generation, list)
            or len(generation) != len(_BLUEPRINT_TARGETS)
            or {
                item.get('target') for item in generation if isinstance(item, Mapping)
            } != set(expected_generation)
            or any(
                not isinstance(item, Mapping)
                or dict(item) != expected_generation.get(item.get('target'))
                for item in generation
            )
        ):
            raise ValueError
        external_sources = parse_external_skills(request['external_sources'], catalog)
        mcp_servers = parse_mcp_servers(request['mcp_servers'])
        project_agents = parse_project_agents(request['project_agents'])
        config = ProjectConfig(
            *selections, external_sources, mcp_servers, project_agents,
        )
    except (KeyError, TypeError, ValueError, SetupError) as error:
        raise SetupError('session request has invalid setup choices') from error
    return config


def _generated_root(session: Path) -> Path:
    root = session / _GENERATED_NAME
    try:
        status = root.lstat()
    except OSError as error:
        raise SetupError('generated output directory is missing') from error
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        raise SetupError('generated output directory is not a safe directory')
    expected = {path.as_posix() for path in _BLUEPRINT_TARGETS}
    files: set[str] = set()
    expected_directories = {PurePosixPath('.')}
    for expected_path in _BLUEPRINT_TARGETS:
        parent = expected_path.parent
        while parent != PurePosixPath('.'):
            expected_directories.add(parent)
            parent = parent.parent
    for path in root.rglob('*'):
        try:
            status = path.lstat()
        except OSError as error:
            raise SetupError('generated output cannot be inspected') from error
        if stat.S_ISLNK(status.st_mode):
            raise SetupError('generated output contains a symlink')
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if path.is_file():
            files.add(path.relative_to(root).as_posix())
        elif path.is_dir() and relative not in expected_directories:
            raise SetupError(
                'generated output contains an undeclared directory: '
                f'{relative.as_posix()}; write each generation_requests target '
                'unchanged under generated'
            )
        elif not path.is_dir():
            raise SetupError('generated output contains a non-file entry')
    if files != expected:
        raise SetupError(
            f'generated outputs must contain exactly {len(_BLUEPRINT_TARGETS)} requested files'
        )
    return root


def _emit_result(
    *,
    phase: str,
    source_commit: str | None,
    changed_paths: Sequence[str],
    harnesses: Sequence[str],
    external_skills: Sequence[str],
    preserved_paths: Sequence[str],
    drift: Mapping[str, object] | None = None,
) -> None:
    print(json.dumps({
        'phase': phase,
        'source_commit': source_commit,
        'changed_paths': sorted(changed_paths),
        'harnesses': list(harnesses),
        'external_skills': sorted(external_skills),
        'preserved_paths': sorted(preserved_paths),
        'drift': drift,
    }, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Prepare, apply, or check a pinned project-agent setup session.',
        allow_abbrev=False,
    )
    phases = parser.add_subparsers(dest='phase', required=True)
    for phase in ('prepare', 'apply', 'check'):
        command = phases.add_parser(phase, allow_abbrev=False)
        command.add_argument('--target', type=Path, required=True)
        command.add_argument('--session', type=Path, required=True)
        command.add_argument('--source-root', type=Path, required=True)
        command.add_argument('--source-commit', required=True)
        command.add_argument('--no-bootstrap', action='store_true', required=True)
    return parser


def _prepare(args: argparse.Namespace, session: Path, source_commit: str | None) -> None:
    catalog = load_catalog(args.source_root)
    project = inspect_project(args.target, catalog=catalog)
    config = project.config
    generated = session / _GENERATED_NAME
    generated_rules = generated / '.agents' / 'rules'
    generated_skills = generated / '.agents' / 'skills'
    try:
        generated_rules.mkdir(parents=True, exist_ok=False)
        generated_skills.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        raise SetupError('cannot create generated output directories') from error
    external_root = snapshot_external_skills(
        config.external_sources,
        session=session,
        existing_manifest=project.root / '.agents/smartkit.lock.json',
    )
    external_snapshot_sha256 = None
    if external_root is not None:
        metadata = external_root / 'sources.json'
        try:
            external_snapshot_sha256 = hashlib.sha256(metadata.read_bytes()).hexdigest()
        except OSError as error:
            raise SetupError('cannot bind external Skill source metadata') from error
    _write_json(
        session / _REQUEST_NAME,
        _request(
            source_commit,
            config,
            catalog,
            target=project.root,
            source_root=Path(args.source_root).absolute(),
            external_snapshot_sha256=external_snapshot_sha256,
        ),
    )


def _plan(args: argparse.Namespace, session: Path, source_commit: str | None):
    catalog = load_catalog(args.source_root)
    project = inspect_project(args.target, catalog=catalog)
    request = _read_json(session / _REQUEST_NAME, 'session request')
    config = _request_config(
        request,
        source_commit,
        target=project.root,
        source_root=Path(args.source_root).absolute(),
        catalog=catalog,
    )
    external_root = session / 'external-skills'
    expected_snapshot_digest = request['external_snapshot_sha256']
    if bool(config.external_sources) != (expected_snapshot_digest is not None):
        raise SetupError('session request external Skill snapshot binding is invalid')
    if expected_snapshot_digest is not None:
        try:
            actual_snapshot_digest = hashlib.sha256(
                (external_root / 'sources.json').read_bytes()
            ).hexdigest()
        except OSError as error:
            raise SetupError('external Skill source metadata is missing') from error
        if actual_snapshot_digest != expected_snapshot_digest:
            raise SetupError('external Skill source metadata changed after prepare')
    generated = _generated_root(session)
    rendered = render_desired_state(
        args.source_root,
        project.root,
        catalog,
        config,
        generated,
        external_root if config.external_sources else None,
    )
    validate_rendered_state(rendered)
    plan = build_plan(
        project.root,
        rendered.files,
        rendered.fields,
        delete_paths=rendered.delete_paths,
        replace_roots=rendered.replace_roots,
    )
    return plan, project.root, config, rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    try:
        session = _private_session(args.session)
        validate_source(args.source_root)
        source_commit = normalize_source_commit(args.source_commit)
        if args.phase == 'prepare':
            _prepare(args, session, source_commit)
            return 0
        plan, target, config, rendered = _plan(args, session, source_commit)
        result_context = {
            'harnesses': [item.value for item in _HARNESSES],
            'external_skills': [item.name for item in config.external_skills],
            'preserved_paths': [item.as_posix() for item in rendered.preserved_paths],
        }
        if args.phase == 'check':
            changed_paths = [
                change.path.as_posix()
                for change in plan.changes
                if change.kind.value != 'unchanged'
            ]
            _emit_result(
                phase=args.phase,
                source_commit=source_commit,
                changed_paths=changed_paths,
                **result_context,
                drift=(
                    {
                        'kind': 'desired_state_diff',
                        'message': 'desired state differs from the target project',
                        'paths': changed_paths,
                    }
                    if changed_paths else None
                ),
            )
            return 0 if not changed_paths else 1
        apply_plan(target, plan)
        _emit_result(
            phase=args.phase,
            source_commit=source_commit,
            changed_paths=[
                change.path.as_posix()
                for change in plan.changes
                if change.kind.value != 'unchanged'
            ],
            **result_context,
            drift=None,
        )
        return 0
    except (
        ContractError,
        DiscoveryError,
        ExternalSkillError,
        InvalidFetchedSource,
        OSError,
        PlanningError,
        ProjectError,
        RenderError,
        SetupError,
        TransactionError,
        ValueError,
    ) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
