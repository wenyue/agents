from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from agents_setup.catalog import ContractError, load_catalog
from agents_setup.host_adapters import CodexAdapter, CopilotAdapter, CursorAdapter
from agents_setup.host_adapters.base import CapabilityResult, CapabilityStatus
from agents_setup.models import Catalog, Platform, ProjectConfig
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
    PurePosixPath('.agents/rules/20-project-tools.md'),
    PurePosixPath('.agents/rules/21-project-rules.md'),
    PurePosixPath('.agents/rules/22-project-structure.md'),
    PurePosixPath('.agents/skills/change-set-verification/SKILL.md'),
    PurePosixPath('.agents/skills/worktree-environment-setup/SKILL.md'),
)
_MODEL_KEYS = {
    Platform.CODEX: 'codex',
    Platform.CURSOR: 'cursor',
    Platform.COPILOT: 'github',
}


class SetupError(ValueError):
    """Raised when a pinned setup session cannot be used safely."""


class CheckDrift(PlanningError):
    """Raised after check has emitted its machine-readable drift result."""


@dataclass(frozen=True)
class _OutputState:
    capabilities: Mapping[str, Mapping[str, Mapping[str, str]]]
    refresh_actions: tuple[Mapping[str, object], ...]
    needs_restart: bool


class _HostRunner:
    """Run only host-adapter fixed argv commands without letting failures abort setup."""

    def run(self, argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                tuple(argv),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return subprocess.CompletedProcess(tuple(argv), 1, '', '')


def normalize_source_commit(source_commit: str) -> str | None:
    """Convert the bootstrap-only offline sentinel before any lock is built."""
    if source_commit == 'offline':
        return None
    if not isinstance(source_commit, str) or not _COMMIT.fullmatch(source_commit):
        raise ValueError('source_commit must be offline or a 40-character hexadecimal commit')
    return source_commit.lower()


def create_session() -> Path:
    """Allocate the private, system-temporary session required by normal orchestration."""
    session = Path(tempfile.mkdtemp(prefix='setup-project-agents-'))
    if os.name == 'posix':
        session.chmod(0o700)
    return session


def _private_session(value: Path) -> Path:
    session = Path(value).absolute()
    current = Path(session.anchor)
    for part in session.parts[1:]:
        current /= part
        try:
            status = current.lstat()
        except OSError as error:
            raise SetupError(f'session path cannot be inspected: {current}') from error
        if stat.S_ISLNK(status.st_mode):
            raise SetupError(f'session path contains a symlink: {current}')
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
) -> dict[str, object]:
    model_requests = _model_requests(config)
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
        'version': 1,
        'target': str(target),
        'source_root': str(source_root),
        'source_commit': source_commit,
        'platforms': [item.value for item in config.platforms],
        'hooks_enabled': config.hooks_enabled,
        'selected_rules': list(config.selected_rules),
        'selected_skills': list(config.selected_skills),
        'selected_agents': list(config.selected_agents),
        'model_requests': model_requests,
        'generation_requests': generation_requests,
    }


def _model_requests(config: ProjectConfig) -> list[dict[str, object]]:
    return [
        {
            'agent': agent,
            'platform': platform.value,
            'model_key': _MODEL_KEYS[platform],
            'required_fields': ['model'],
        }
        for agent in sorted(config.selected_agents)
        for platform in sorted(config.platforms, key=lambda item: item.value)
    ]


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
        'version', 'target', 'source_root', 'source_commit', 'platforms', 'hooks_enabled', 'selected_rules',
        'selected_skills', 'selected_agents', 'model_requests', 'generation_requests',
    }
    if set(request) != required or request.get('version') != 1:
        raise SetupError('session request has an invalid shape')
    if request.get('source_commit') != source_commit:
        raise SetupError('session request source commit does not match this pinned source')
    if request.get('target') != str(target):
        raise SetupError('session request target does not match this invocation')
    if request.get('source_root') != str(source_root):
        raise SetupError('session request source root does not match this pinned source')
    try:
        platforms = tuple(Platform(item) for item in request['platforms'])
        if not platforms or len(set(platforms)) != len(platforms):
            raise ValueError
        hooks_enabled = request['hooks_enabled']
        if type(hooks_enabled) is not bool:
            raise ValueError
        selections = (
            _selected_request_ids(request['selected_rules'], catalog=catalog, kind='rule'),
            _selected_request_ids(request['selected_skills'], catalog=catalog, kind='skill'),
            _selected_request_ids(request['selected_agents'], catalog=catalog, kind='agent'),
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
        config = ProjectConfig(1, platforms, hooks_enabled, *selections)
        if request['model_requests'] != _model_requests(config):
            raise ValueError
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
            raise SetupError('generated output contains an undeclared directory')
        elif not path.is_dir():
            raise SetupError('generated output contains a non-file entry')
    if files != expected:
        raise SetupError('generated outputs must contain exactly the five requested files')
    return root


def _adapters() -> dict[Platform, object]:
    return {
        Platform.CODEX: CodexAdapter(),
        Platform.CURSOR: CursorAdapter(),
        Platform.COPILOT: CopilotAdapter(),
    }


def _models_for_rendering(
    models: Mapping[str, object],
    config: ProjectConfig,
) -> Mapping[str, object]:
    agents = models.get('agents')
    if not isinstance(agents, Mapping):
        raise SetupError('models must contain an agents object')
    for request in _model_requests(config):
        agent_name = request['agent']
        platform_name = request['platform']
        model_key = request['model_key']
        agent = agents.get(agent_name)
        if not isinstance(agent, Mapping):
            raise SetupError(f'models agent is missing: {agent_name}')
        platform = agent.get(model_key)
        if not isinstance(platform, Mapping):
            raise SetupError(f'models platform is missing: {agent_name}:{model_key}')
        model = platform.get('model')
        if not isinstance(model, str) or not model.strip():
            raise SetupError(f'models model is missing: {agent_name}:{model_key}')
        if platform_name == Platform.CODEX.value:
            for key in ('model_reasoning_effort', 'sandbox_mode'):
                if key in platform and not isinstance(platform[key], str):
                    raise SetupError(f'models {key} must be a string: {agent_name}:{model_key}')
        if platform_name == Platform.CURSOR.value and (
            'readonly' in platform and type(platform['readonly']) is not bool
        ):
            raise SetupError(f'models readonly must be a boolean: {agent_name}:{model_key}')
    return {key: value for key, value in models.items() if key != 'runner'}


def _result_value(result: CapabilityResult) -> dict[str, str]:
    return {'status': result.status.value, 'detail': result.detail}


def _output_state(
    config: ProjectConfig,
    adapters: Mapping[Platform, object],
) -> _OutputState:
    runner = _HostRunner()
    capabilities: dict[str, dict[str, dict[str, str]]] = {}
    actions: list[Mapping[str, object]] = []
    needs_restart = False
    for platform in config.platforms:
        adapter = adapters[platform]
        result = adapter.check_multi_agent(runner)
        values = {'multi_agent': _result_value(result)}
        needs_restart = needs_restart or result.status is CapabilityStatus.NEEDS_RESTART
        if platform is Platform.CURSOR and config.hooks_enabled:
            trust = adapter.hook_trust_status()
            values['hook_trust'] = _result_value(trust)
            needs_restart = needs_restart or trust.status is CapabilityStatus.NEEDS_RESTART
        capabilities[platform.value] = values
        actions.append({'platform': platform.value, 'command': list(adapter.plugin_refresh_command())})
    return _OutputState(capabilities, tuple(actions), needs_restart)


def _emit_result(
    *,
    phase: str,
    source_commit: str | None,
    changed_paths: Sequence[str],
    output: _OutputState,
) -> None:
    print(json.dumps({
        'version': 1,
        'phase': phase,
        'source_commit': source_commit,
        'changed_paths': sorted(changed_paths),
        'capabilities': output.capabilities,
        'refresh_actions': output.refresh_actions,
        'needs_restart': output.needs_restart,
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
        if phase == 'prepare':
            command.add_argument(
                '--platform', choices=tuple(item.value for item in Platform), action='append'
            )
            command.add_argument('--hooks', choices=('enabled', 'disabled'), required=True)
        else:
            command.add_argument('--models', type=Path, required=True)
        command.add_argument('--source-root', type=Path, required=True)
        command.add_argument('--source-commit', required=True)
        command.add_argument('--no-bootstrap', action='store_true', required=True)
    return parser


def _prepare(args: argparse.Namespace, session: Path, source_commit: str | None) -> None:
    catalog = load_catalog(args.source_root)
    project = inspect_project(args.target, catalog=catalog)
    platforms = (
        tuple(Platform(item) for item in args.platform)
        if args.platform
        else project.config.platforms
    )
    if len(set(platforms)) != len(platforms):
        raise SetupError('platforms must not contain duplicates')
    config = ProjectConfig(
        1,
        platforms,
        args.hooks == 'enabled',
        project.config.selected_rules,
        project.config.selected_skills,
        project.config.selected_agents,
    )
    generated = session / _GENERATED_NAME
    generated_rules = generated / '.agents' / 'rules'
    generated_skills = generated / '.agents' / 'skills'
    try:
        generated_rules.mkdir(parents=True, exist_ok=False)
        generated_skills.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        raise SetupError('cannot create generated output directories') from error
    _write_json(
        session / _REQUEST_NAME,
        _request(
            source_commit,
            config,
            catalog,
            target=project.root,
            source_root=Path(args.source_root).absolute(),
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
    generated = _generated_root(session)
    models_path = Path(args.models).absolute()
    if models_path != session / 'models.json':
        raise SetupError('models path must be SESSION/models.json')
    models = _models_for_rendering(_read_json(models_path, 'models'), config)
    adapters = _adapters()
    output = _output_state(config, adapters)
    rendered = render_desired_state(
        args.source_root,
        project.root,
        catalog,
        config,
        generated,
        models,
        adapters,
    )
    validate_rendered_state(rendered)
    try:
        plan = build_plan(
            project.root,
            rendered.files,
            rendered.fields,
            project.lock,
            source_commit=source_commit,
        )
    except PlanningError as error:
        if args.phase == 'check':
            _emit_result(
                phase=args.phase,
                source_commit=source_commit,
                changed_paths=(),
                output=output,
            )
            raise CheckDrift() from error
        raise
    return plan, project.root, output


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
        try:
            plan, target, output = _plan(args, session, source_commit)
        except CheckDrift:
            return 1
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
                output=output,
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
            output=output,
        )
        return 0
    except (
        ContractError,
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
