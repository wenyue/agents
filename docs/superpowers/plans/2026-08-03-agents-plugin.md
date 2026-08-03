# Agents Cross-Platform Plugin Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the repository root into the single Codex, Cursor, and GitHub Copilot plugin, with a `main`-tracking project setup control plane, transactional project snapshots, explicit Hooks, effective multi-agent checks, and user-approved external-tool maintenance.

**Architecture:** The repository root is the published plugin and owns one English runtime tree. A small bootstrap fetches remote `main`, pins the fetched commit for one run, and hands off to focused Python modules that build one desired-state plan and apply it transactionally. Projects store user choices in `.agents/config.json` and generated ownership in `.agents/lock.json`; platform directories contain only native configuration and thin wrappers.

**Tech Stack:** Python 3.11 standard library, `unittest`, JSON/JSONC, TOML through `tomllib` plus the existing vendored `tomli` fallback, Git CLI, POSIX shell, PowerShell, Codex/Cursor/Copilot plugin manifests.

## Global Constraints

- The repository root is the plugin root; do not add a nested plugin package or a `src/` to `dist/` build.
- Plugin ID is `agents`; `VERSION` and all three native manifests initially remain `0.1.0`.
- The canonical update source is `https://github.com/wenyue/agents.git`, ref `main`; do not use Releases, tags, `main.zip`, or an old project updater.
- Fetch `main` for every online setup run, then pin the resolved commit SHA for that run and record it in `.agents/lock.json`.
- If fetch is unavailable, continue from the installed plugin with a warning; if fetched content is invalid, fail before target mutation.
- Copy the complete selected Rules, Skills, and Agents snapshot, but never copy `setup-project-agents`; install Hooks only when explicitly enabled.
- Codex writes `features.hooks = true` only for explicit Hook enablement. Multi-agent support is detected from effective state and is never written merely to repeat a default.
- Setup may overwrite or delete only lock-owned paths or fields. An unmanaged collision is a blocking conflict.
- Do not mutate host plugin caches, editor trust databases, or third-party tools inside the project synchronization transaction.
- Keep runtime English-only. Move Chinese Markdown to `docs/zh-CN/`; no JSON, scripts, templates, or runtime manifests belong there.
- Do not preserve the old synchronizer, archive fallback, project-local updater, old manifest, or compatibility tests in the final tree.
- Use repository-relative paths in tracked files. Preserve unrelated work and stage only the current task's files.
- Run `uv run --python 3.11 --no-project python -m unittest discover -s tests -p 'test_*.py'` and `git diff --check` before every task commit.

## File Map

### Plugin and content roots

- `.codex-plugin/plugin.json`: Codex plugin metadata; exposes root `skills/`.
- `.cursor-plugin/plugin.json`: Cursor metadata; exposes root `skills/`, `rules/`, and `agents/`.
- `plugin.json`: Copilot metadata; exposes root `skills/` and `agents/`.
- `VERSION`: one semantic plugin version consumed by manifest tests.
- `rules/`, `skills/`, `agents/`, `blueprints/`: the only English runtime and generation sources.
- `catalog/project-assets.json`: the only machine-readable project payload declaration.
- `catalog/project-config.schema.json`: user configuration contract.
- `catalog/project-lock.schema.json`: generated ownership contract.
- `templates/project/`: project entry files, native config, Hooks, and wrappers.
- `config/recommended-tools/`: platform, Superpowers, CodeGraph, and Tokscale policy.

### Setup implementation

- `skills/setup-project-agents/scripts/bootstrap.py`: stable fetch-and-handoff protocol.
- `skills/setup-project-agents/scripts/setup_project_agents.py`: `prepare`, `apply`, and `check` CLI orchestration.
- `skills/setup-project-agents/scripts/agents_setup/models.py`: immutable data contracts.
- `skills/setup-project-agents/scripts/agents_setup/catalog.py`: Catalog/config/lock parsing and validation.
- `skills/setup-project-agents/scripts/agents_setup/source.py`: Git `main` fetch and source validation.
- `skills/setup-project-agents/scripts/agents_setup/project.py`: project inspection and safe path resolution.
- `skills/setup-project-agents/scripts/agents_setup/planner.py`: the single desired/current/lock diff engine.
- `skills/setup-project-agents/scripts/agents_setup/renderer.py`: asset, wrapper, generated-output, JSON/JSONC, and TOML rendering.
- `skills/setup-project-agents/scripts/agents_setup/validation.py`: staged-tree and native-config validation.
- `skills/setup-project-agents/scripts/agents_setup/transaction.py`: backup, atomic apply, and rollback.
- `skills/setup-project-agents/scripts/agents_setup/host_adapters/`: Codex, Cursor, and Copilot capability adapters.

### Tests and documentation

- `tests/test_plugin_manifests.py`: root package and marketplace contracts.
- `tests/test_setup_catalog.py`: Catalog, config, lock, and path contracts.
- `tests/test_setup_planner.py`: ownership, conflicts, and idempotence.
- `tests/test_setup_renderer.py`: native output and explicit Hook behavior.
- `tests/test_setup_transaction.py`: atomic apply and rollback.
- `tests/test_setup_source.py`: `main` fetch, pinning, fallback, and handoff.
- `tests/test_setup_cli.py`: prepare/apply/check integration.
- `tests/test_manage_agent_tools.py`: tool policy and non-mutating Hook mode.
- `.github/workflows/test.yml`: Python 3.11 Linux/macOS/Windows verification.
- `README.md` and `docs/zh-CN/`: public English documentation and Chinese reading mirror.

---

### Task 1: Promote the Repository Root to the Plugin Root

**Files:**
- Create: `VERSION`
- Move: `agents/.codex-plugin/plugin.json` to `.codex-plugin/plugin.json`
- Modify: `.cursor-plugin/plugin.json`
- Move: `agents/plugin.json` to `plugin.json`
- Move: `agents/rules/` to `rules/`
- Move: `agents/skills/` to `skills/`
- Move: `agents/blueprints/` to `blueprints/`
- Move: `agents/agents/change-set-verifier.md` to `agents/change-set-verifier.md`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `.cursor-plugin/marketplace.json`
- Modify: `.github/plugin/marketplace.json`
- Modify: `tests/test_plugin_manifests.py`
- Modify: `tests/test_public_agent_assets.py`
- Modify: `tests/test_report_session_usage.py`

**Interfaces:**
- Consumes: current plugin version `0.1.0` and existing runtime files.
- Produces: root-native paths used by every later task; `VERSION` contains `0.1.0\n`.

- [ ] **Step 1: Replace manifest tests with the root-layout contract**

Add these assertions to `tests/test_plugin_manifests.py` before moving files:

```python
def test_repository_root_is_the_only_plugin_root(self):
    version = (REPO_ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    self.assertEqual(version, '0.1.0')
    manifests = (
        REPO_ROOT / '.codex-plugin' / 'plugin.json',
        REPO_ROOT / '.cursor-plugin' / 'plugin.json',
        REPO_ROOT / 'plugin.json',
    )
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        self.assertEqual(manifest['name'], 'agents')
        self.assertEqual(manifest['version'], version)
        self.assertEqual(manifest['skills'], './skills/')
    self.assertFalse((REPO_ROOT / 'agents' / '.codex-plugin').exists())
    self.assertFalse((REPO_ROOT / 'agents' / 'skills').exists())

def test_local_marketplaces_point_at_the_repository_root(self):
    for relative in (
        '.cursor-plugin/marketplace.json',
        '.github/plugin/marketplace.json',
    ):
        marketplace = load_json(relative)
        self.assertEqual(marketplace['plugins'][0]['source'], './')
    codex = load_json('.agents/plugins/marketplace.json')
    self.assertEqual(codex['plugins'][0]['source']['path'], './')
```

- [ ] **Step 2: Run the focused tests and verify they fail on the nested layout**

Run:

```sh
uv run --python 3.11 --no-project python -m unittest tests.test_plugin_manifests
```

Expected: FAIL because `VERSION` and `.codex-plugin/plugin.json` do not yet exist and marketplace sources are `./agents`.

- [ ] **Step 3: Move the runtime trees and manifests without duplicating them**

Use `git mv` for every path listed in this task. After the moves, update the three manifests to these path fields:

```json
{
  "name": "agents",
  "version": "0.1.0",
  "skills": "./skills/"
}
```

Preserve every existing metadata field. Add `"rules": "./rules/"` and `"agents": "./agents/"` only to `.cursor-plugin/plugin.json`; add `"agents": "./agents/"` to `plugin.json`. Change all local marketplace sources from `./agents` to `./`.

- [ ] **Step 4: Retarget existing tests to root-native paths**

Use these constants in the still-existing legacy test modules so the suite remains green during construction:

```python
REPO_SKILL_ROOT = REPO_ROOT / 'skills' / 'setup-project-agents'
MANAGE_AGENT_TOOLS_ROOT = REPO_ROOT / 'skills' / 'manage-agent-tools'
REPORT_SESSION_USAGE_ROOT = REPO_ROOT / 'skills' / 'report-session-usage'
```

Update repository-source fixtures from `source / 'agents' / 'skills'` to `source / 'skills'`. Do not add fallback branches for the old location.

- [ ] **Step 5: Run all tests and commit the root topology**

Run the global verification commands. Expected: 197 tests pass with the existing single skip.

```sh
git add VERSION .codex-plugin .cursor-plugin .github/plugin .agents/plugins \
  plugin.json rules skills agents blueprints tests
git diff --cached --check
git commit -m "refactor: promote agents plugin to repository root"
```

---

### Task 2: Define Catalog, Project Config, Lock, and Model Contracts

**Files:**
- Create: `catalog/project-assets.json`
- Create: `catalog/project-config.schema.json`
- Create: `catalog/project-lock.schema.json`
- Create: `skills/setup-project-agents/scripts/agents_setup/__init__.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/models.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/catalog.py`
- Create: `tests/test_setup_catalog.py`

**Interfaces:**
- Produces: `Platform`, `AssetSpec`, `ProjectConfig`, `ManagedFile`, `ManagedField`, `LockState`, `load_catalog`, `load_project_config`, and `load_lock`.
- Consumes: root `VERSION`, `rules/`, `skills/`, `agents/`, `blueprints/`, and `templates/project/` paths that later tasks create.

- [ ] **Step 1: Write failing contract and path-safety tests**

Create `tests/test_setup_catalog.py` with these core cases:

```python
class SetupCatalogTest(unittest.TestCase):
    def test_catalog_excludes_setup_control_plane(self):
        catalog = load_catalog(REPO_ROOT)
        targets = {
            asset.target.as_posix()
            for asset in catalog.assets
            if asset.target is not None
        }
        self.assertNotIn('.agents/skills/setup-project-agents', targets)
        self.assertIn('.agents/skills/manage-agent-tools', targets)

    def test_project_config_defaults_to_all_hosts_and_hooks_off(self):
        config = load_project_config(None, catalog=load_catalog(REPO_ROOT))
        self.assertEqual(config.platforms, tuple(Platform))
        self.assertFalse(config.hooks_enabled)

    def test_catalog_rejects_escape_and_absolute_targets(self):
        for target in ('../escape', '/tmp/escape'):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ContractError, 'relative path'):
                    parse_asset({'id': 'bad', 'kind': 'file', 'source': 'README.md', 'target': target})
```

- [ ] **Step 2: Run the focused tests and verify import failure**

Run:

```sh
uv run --python 3.11 --no-project python -m unittest tests.test_setup_catalog
```

Expected: FAIL because `agents_setup.catalog` does not exist.

- [ ] **Step 3: Add immutable model contracts**

Implement these exact public types in `models.py`:

```python
class Platform(str, Enum):
    CODEX = 'codex'
    CURSOR = 'cursor'
    COPILOT = 'copilot'

@dataclass(frozen=True)
class AssetSpec:
    id: str
    kind: str
    source: PurePosixPath
    target: PurePosixPath | None
    platforms: tuple[Platform, ...]
    mode: str = 'copy'
    control_plane: bool = False

@dataclass(frozen=True)
class ProjectConfig:
    version: int
    platforms: tuple[Platform, ...]
    hooks_enabled: bool
    selected_rules: tuple[str, ...]
    selected_skills: tuple[str, ...]
    selected_agents: tuple[str, ...]

@dataclass(frozen=True)
class ManagedFile:
    path: PurePosixPath
    sha256: str

@dataclass(frozen=True)
class ManagedField:
    path: PurePosixPath
    key: str
    sha256: str

@dataclass(frozen=True)
class LockState:
    version: int
    source_commit: str | None
    managed_files: tuple[ManagedFile, ...]
    managed_fields: tuple[ManagedField, ...]
```

Also define `ContractError(ValueError)`, `LockState.empty() -> LockState`,
`LockState.from_files(files: Mapping[str, str]) -> LockState`, and a `Catalog` dataclass containing
plugin ID, plugin version, repository, ref, and `assets`.

- [ ] **Step 4: Implement strict parsers and schemas**

`catalog.py` must expose the exact signatures
`safe_relative(value: str, label: str) -> PurePosixPath`,
`parse_asset(value: Mapping[str, object]) -> AssetSpec`,
`load_catalog(source_root: Path) -> Catalog`,
`load_project_config(path: Path | None, *, catalog: Catalog) -> ProjectConfig`, and
`load_lock(path: Path | None) -> LockState`.

Reject unknown top-level and asset fields, duplicate IDs or targets, unsafe names, non-semver `VERSION`, non-40-hex lock commits, and a control-plane asset with a project target. Default config is all Catalog rule/skill/agent IDs, all three platforms, and Hooks disabled.

Populate `catalog/project-assets.json` with every current root Rule, every root Skill except `setup-project-agents`, `agents/change-set-verifier.md`, the five Blueprint-generated outputs, entry/config templates, and platform wrappers. Give `setup-project-agents` a Catalog record with `control_plane: true` and no target so exclusion is testable rather than implicit.

- [ ] **Step 5: Run tests and commit the contracts**

Run `tests.test_setup_catalog`, then the global verification commands.

```sh
git add catalog skills/setup-project-agents/scripts/agents_setup tests/test_setup_catalog.py
git commit -m "feat: define project agent catalog contracts"
```

---

### Task 3: Implement the Single Ownership-Aware Planner

**Files:**
- Modify: `skills/setup-project-agents/scripts/agents_setup/models.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/project.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/planner.py`
- Create: `tests/test_setup_planner.py`

**Interfaces:**
- Consumes: `ProjectConfig`, `LockState`, rendered desired files and fields.
- Produces: `DesiredFile`, `DesiredField`, `Change`, `ChangeKind`, `Plan`, `inspect_project`, and `build_plan`.

- [ ] **Step 1: Write failing planner tests for create, update, conflict, delete, and idempotence**

Use a temporary target and assert this public behavior:

```python
plan = build_plan(
    target_root=target,
    desired_files=(DesiredFile(PurePosixPath('.agents/rules/a.md'), b'new\n'),),
    desired_fields=(),
    lock=LockState.empty(),
)
self.assertEqual(plan.changes[0].kind, ChangeKind.CREATE)

(target / '.agents/rules/a.md').write_text('user\n', encoding='utf-8')
with self.assertRaisesRegex(PlanningError, 'unmanaged collision'):
    build_plan(target, desired_files, (), LockState.empty())

owned = LockState.from_files({'.agents/rules/a.md': sha256_bytes(b'old\n')})
(target / '.agents/rules/a.md').write_bytes(b'old\n')
self.assertEqual(build_plan(target, desired_files, (), owned).changes[0].kind, ChangeKind.UPDATE)
```

Add separate cases proving a removed lock-owned path becomes `DELETE`, a matching desired file becomes `UNCHANGED`, a modified lock-owned file becomes a conflict, and symlinked target components are rejected.

- [ ] **Step 2: Run focused tests and verify planner imports fail**

Expected: FAIL because `project.py` and `planner.py` do not exist.

- [ ] **Step 3: Implement project inspection and plan models**

Add:

```python
class ChangeKind(str, Enum):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    UNCHANGED = 'unchanged'

@dataclass(frozen=True)
class DesiredFile:
    path: PurePosixPath
    content: bytes

@dataclass(frozen=True)
class DesiredField:
    path: PurePosixPath
    key: str
    value: object
    format: str

@dataclass(frozen=True)
class Change:
    kind: ChangeKind
    path: PurePosixPath
    content: bytes | None

@dataclass(frozen=True)
class Plan:
    changes: tuple[Change, ...]
    next_lock: LockState
```

`project.py` must expose `confined_target(root, relative)` and reject absolute paths, `..`, existing symlink components, and a target root that is itself a symlink.

- [ ] **Step 4: Implement one deterministic planner used by check and apply**

Implement `sha256_bytes(content: bytes) -> str` and
`build_plan(target_root: Path, desired_files: Sequence[DesiredFile], desired_fields: Sequence[DesiredField], lock: LockState, *, source_commit: str | None = None) -> Plan`.
The planner must sort by POSIX path, compare SHA-256 bytes, allow updates/deletes only when the
current digest matches the previous lock, and construct `next_lock` only from desired managed files
and fields. It must never write. Field planning receives fully rendered file bytes from Task 4, so
file and field ownership share one conflict path.

- [ ] **Step 5: Run tests and commit**

Run focused and global verification.

```sh
git add skills/setup-project-agents/scripts/agents_setup tests/test_setup_planner.py
git commit -m "feat: plan lock-owned project agent changes"
```

---

### Task 4: Render Platform-Native Desired State and Explicit Hooks

**Files:**
- Create: `templates/project/entry-files/AGENTS.md`
- Create: `templates/project/platform-config/*.json`
- Create: `templates/project/platform-config/*.toml`
- Create: `templates/project/hooks/*.json`
- Create: `templates/project/wrappers/*`
- Create: `skills/setup-project-agents/scripts/agents_setup/renderer.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/validation.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/host_adapters/__init__.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/host_adapters/base.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/host_adapters/codex.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/host_adapters/cursor.py`
- Create: `skills/setup-project-agents/scripts/agents_setup/host_adapters/copilot.py`
- Create: `tests/test_setup_renderer.py`

**Interfaces:**
- Consumes: Catalog assets, project config, generated Blueprint outputs, model selections, and existing unmanaged native fields.
- Produces: `render_desired_state(source_root: Path, target_root: Path, catalog: Catalog, config: ProjectConfig, generated_root: Path, models: Mapping[str, object], adapters: Mapping[Platform, HostAdapter]) -> RenderedState`, `CapabilityStatus`, and three host adapters.

- [ ] **Step 1: Write failing golden tests for the three hosts**

Create fixtures that call `render_desired_state` with Hooks off and on. Assert:

```python
self.assertNotIn('.codex/hooks.json', off.files_by_path)
self.assertNotIn('.cursor/hooks.json', off.files_by_path)
self.assertNotIn('.github/hooks/project-agent-tool-check.json', off.files_by_path)
self.assertNotIn(('.codex/config.toml', 'features.hooks'), off.fields_by_key)

self.assertEqual(on.fields_by_key[('.codex/config.toml', 'features.hooks')], True)
self.assertEqual(on.fields_by_key[('.github/copilot/settings.json', 'disableAllHooks')], False)
self.assertIn('.cursor/hooks.json', on.files_by_path)
self.assertNotIn('.agents/skills/setup-project-agents/SKILL.md', on.files_by_path)
```

Also assert Cursor wrappers reference `.agents/rules/00-global-rule-config.md`, Copilot wrappers reference the
same shared source, and all Hook commands call
`.agents/skills/manage-agent-tools/scripts/check_recommended_tools` with relative paths.
Add a transition test that renders Hooks on, records the resulting lock, then renders Hooks off;
the second plan must delete all three lock-owned Hook files and remove only the two owned native
fields while preserving unrelated Codex and Copilot settings.

- [ ] **Step 2: Run the renderer tests and verify imports fail**

Expected: FAIL because renderer and adapters are absent.

- [ ] **Step 3: Establish and normalize root templates**

Copy the existing setup templates into the four `templates/project/` subdirectories while the old
suite still exercises the monolith; Task 9 deletes the old copy during cutover. Treat the new root
templates as canonical for all new modules. Preserve native JSON/TOML values, but remove
`features.hooks = true` from the unconditional Codex baseline; make it an owned field emitted only
when Hooks are enabled. Keep `.codex/hooks.json`, `.cursor/hooks.json`, and
`.github/hooks/project-agent-tool-check.json` as separate optional assets.

- [ ] **Step 4: Implement host adapter contracts**

In `base.py` define:

```python
class CapabilityStatus(str, Enum):
    READY = 'ready'
    NEEDS_APPROVAL = 'needs_approval'
    NEEDS_RESTART = 'needs_restart'
    UNSUPPORTED = 'unsupported'

@dataclass(frozen=True)
class CapabilityResult:
    status: CapabilityStatus
    detail: str

class CommandRunner(Protocol):
    def run(self, argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        raise NotImplementedError
```

Also define a `HostAdapter` Protocol with `platform`, `check_multi_agent(runner)`,
`hook_fields(enabled)`, and `plugin_refresh_command()` members. Codex adapter parses
`codex features list` for effective `multi_agent`; Cursor and Copilot adapters compare their CLI
versions with `2026.01.27` and `1.0.58` respectively. None writes a multi-agent setting. Cursor Hook
trust returns `NEEDS_APPROVAL` with an official-UI instruction; no adapter writes trust storage.

- [ ] **Step 5: Implement deterministic rendering and validation**

`render_desired_state` returns:

```python
@dataclass(frozen=True)
class RenderedState:
    files: tuple[DesiredFile, ...]
    fields: tuple[DesiredField, ...]
    capabilities: Mapping[Platform, CapabilityResult]
```

Add read-only `files_by_path` and `fields_by_key` properties used by the golden tests. Copy selected
shared assets, overlay generated Blueprint outputs, render wrappers from structured metadata, and
merge JSON/JSONC/TOML fields while preserving values absent from the template. `validation.py`
reparses every rendered native config, verifies wrapper references exist in the staged desired tree,
and rejects missing Hook checker scripts.

- [ ] **Step 6: Run tests and commit**

Run focused and global verification.

```sh
git add templates catalog/project-assets.json \
  skills/setup-project-agents/scripts/agents_setup tests/test_setup_renderer.py
git commit -m "feat: render aligned project agent configurations"
```

---

### Task 5: Apply Plans Transactionally with Rollback

**Files:**
- Create: `skills/setup-project-agents/scripts/agents_setup/transaction.py`
- Create: `tests/test_setup_transaction.py`

**Interfaces:**
- Consumes: a validated `Plan` and target root.
- Produces: `apply_plan(target_root: Path, plan: Plan) -> None`; no partial state after failure.

- [ ] **Step 1: Write failing transaction tests**

Cover create/update/delete, parent creation, atomic replacement, and injected failure:

```python
with mock.patch.object(transaction, '_replace', side_effect=[None, OSError('boom')]):
    with self.assertRaisesRegex(TransactionError, 'boom'):
        apply_plan(target, plan)
self.assertEqual((target / 'owned-a').read_bytes(), b'old-a')
self.assertEqual((target / 'owned-b').read_bytes(), b'old-b')
self.assertFalse((target / '.agents/lock.json').exists())
```

Assert unmanaged files remain byte-identical and a symlink introduced after planning aborts before the first replace.

- [ ] **Step 2: Run focused tests and verify import failure**

- [ ] **Step 3: Implement backup, apply, lock-last, and reverse rollback**

Use `tempfile.TemporaryDirectory(prefix='agents-setup-transaction-')`. Before writes, revalidate every target path, copy each existing managed file or record absence, write new bytes to a sibling temporary file, and call `os.replace`. Apply `.agents/lock.json` last. On any exception, restore backups in reverse order and raise `TransactionError` with the original error.

Expose `_replace = os.replace` as the sole injection point used by tests.

- [ ] **Step 4: Run tests and commit**

```sh
git add skills/setup-project-agents/scripts/agents_setup/transaction.py \
  tests/test_setup_transaction.py
git commit -m "feat: apply project agent plans transactionally"
```

---

### Task 6: Fetch Remote Main and Hand Off Through a Stable Bootstrap

**Files:**
- Create: `skills/setup-project-agents/scripts/agents_setup/source.py`
- Create: `skills/setup-project-agents/scripts/bootstrap.py`
- Create: `tests/test_setup_source.py`

**Interfaces:**
- Produces: `SourceSnapshot`, `fetch_main`, `validate_source`, and stable bootstrap arguments `--source-root`, `--source-commit`, `--no-bootstrap`.
- Consumes: Git executable and the installed plugin root as offline fallback.

- [ ] **Step 1: Write failing Git integration tests**

Build a temporary bare origin with `main`, then assert:

```python
snapshot = fetch_main(origin.as_uri(), work_root=temp_path)
self.assertEqual(snapshot.commit, run_git(origin_work, 'rev-parse', 'main').strip())
self.assertEqual(snapshot.root.joinpath('VERSION').read_text().strip(), '0.1.0')
self.assertFalse(snapshot.root.joinpath('.git').is_symlink())
```

Add tests for a new `main` commit, unavailable origin fallback, fetched invalid Catalog fail-closed
behavior, exact child arguments, persistence under `SESSION/source` through all three phases, and
cleanup only after the whole setup session ends.

- [ ] **Step 2: Run focused tests and verify failure**

- [ ] **Step 3: Implement `fetch_main` with fixed argv arrays**

Remote-bootstrap security boundary: `bootstrap.py` accepts an external `--session` path and safely
creates missing path components without following symlinks, but it always validates the final
`SESSION` as current-effective-user-owned with exact mode `0700`. It does not blindly trust an
external path. Normal Task 7 orchestration must create the session through `tempfile.mkdtemp` (or an
equivalent system-temporary secure creator) before passing it to bootstrap. Fetch uses a random
128-bit private candidate, held directory descriptors, inode guards, and no-replace publication to
protect against other-user pathname races. A same-UID process that can actively alter `SESSION`,
trace the process, or inject code is already trusted and is outside this filesystem protocol's threat
model. Failed candidates remain for session-end cleanup; after publication bootstrap never renames
or removes the current `SESSION/source` pathname.

Run these commands without Shell interpolation:

```python
('git', 'init', '--quiet', str(checkout))
('git', '-C', str(checkout), 'remote', 'add', 'origin', repository)
('git', '-C', str(checkout), 'fetch', '--depth=1', 'origin', 'main')
('git', '-C', str(checkout), 'checkout', '--quiet', '--detach', 'FETCH_HEAD')
('git', '-C', str(checkout), 'rev-parse', 'HEAD')
```

Validate the 40-hex commit, all native manifests, `VERSION`, Catalog plugin identity, and setup entrypoint. Distinguish `SourceUnavailable` from `InvalidFetchedSource`; only the former permits installed-source fallback.

- [ ] **Step 4: Implement stable bootstrap handoff**

`bootstrap.py` accepts only the initial `prepare` phase. It fetches `main` into
`SESSION/source`, pins that checkout for the lifetime of the setup session, and runs:

```python
argv = [
    sys.executable,
    str(snapshot.root / 'skills/setup-project-agents/scripts/setup_project_agents.py'),
    *forwarded,
    '--source-root', str(snapshot.root),
    '--source-commit', snapshot.commit,
    '--no-bootstrap',
]
completed = subprocess.run(argv, check=False)
return completed.returncode
```

When offline, use the installed plugin root, pass `--source-commit offline`, convert that sentinel to
`None` before building `LockState`, and print one warning to stderr. Keep these argument names stable
for all post-redesign versions. Bootstrap must not delete `SESSION/source`; the Skill owns session
cleanup after `check` finishes.

- [ ] **Step 5: Run tests and commit**

```sh
git add skills/setup-project-agents/scripts/bootstrap.py \
  skills/setup-project-agents/scripts/agents_setup/source.py tests/test_setup_source.py
git commit -m "feat: bootstrap project setup from remote main"
```

---

### Task 7: Add Prepare, Apply, and Check Orchestration

**Files:**
- Create: `skills/setup-project-agents/scripts/setup_project_agents.py`
- Create: `skills/setup-project-agents/scripts/setup_project_agents.sh`
- Create: `skills/setup-project-agents/scripts/setup_project_agents.ps1`
- Rewrite: `skills/setup-project-agents/SKILL.md`
- Create: `tests/test_setup_cli.py`

**Interfaces:**
- Produces: `prepare`, `apply`, and `check` CLI subcommands sharing renderer and planner.
- Consumes: a system-temporary setup session containing `request.json`, `generated/`, and `models.json`.

- [ ] **Step 1: Write failing CLI integration tests**

Assert `prepare` writes a session request with source commit, selected platforms, Hook choice, model requests, and five generation requests. Assert `apply` refuses missing generated outputs, writes a complete project, and `check` returns `0` unchanged or `1` on drift without writing.
Assert normal orchestration creates its system-temporary session as current-euid-owned exact `0700`,
and that a session with any other owner or mode is rejected before source fetch or project mutation.

```python
self.assertEqual(main(['check', '--session', str(session), *source_args]), 0)
(target / '.agents/rules/00-global-rule-config.md').write_text('drift\n')
before = snapshot_tree(target)
self.assertEqual(main(['check', '--session', str(session), *source_args]), 1)
self.assertEqual(snapshot_tree(target), before)
```

- [ ] **Step 2: Run focused tests and verify the CLI is absent**

- [ ] **Step 3: Implement the session protocol and commands**

Normal orchestration must allocate `SESSION` with `tempfile.mkdtemp` (or an equivalent secure
system-temporary creator), retain that private directory for `prepare`, `apply`, and `check`, and
pass it to bootstrap. Bootstrap still validates the supplied `--session` path on every fetch rather
than relying on the caller's creation step.

The parser must require exactly one subcommand:

```text
prepare --target PATH --session PATH [--platform PLATFORM] --hooks enabled|disabled
apply   --target PATH --session PATH --models PATH
check   --target PATH --session PATH --models PATH
```

`--platform` is repeatable. All commands also accept the internal bootstrap arguments from Task 6.
`prepare` performs source and project inspection but no target write, then records generation
destinations under `SESSION/generated/.agents/rules/` and `SESSION/generated/.agents/skills/`.
`apply` and `check` validate the same generated tree, call the same `render_desired_state` and
`build_plan`, and differ only in whether `apply_plan` runs.

- [ ] **Step 4: Rewrite the Skill around the new control-plane protocol**

The Skill workflow must:

1. Ask once for enabled platforms and explicit Hook enablement, defaulting to all platforms and Hooks off when `.agents/config.json` is absent.
2. Create a current-euid-owned exact-`0700` session using `tempfile.mkdtemp` (or an equivalent
   system-temporary secure creator), then run `bootstrap.py prepare` with that session; this fetches and retains
   `SESSION/source` at one fixed commit.
3. Fill `models.json` from `request.json`.
4. Execute each Rule Blueprint with `write-rule` and each Skill Blueprint with `write-skill`, targeting `SESSION/generated` rather than the project.
5. Run `SESSION/source/skills/setup-project-agents/scripts/setup_project_agents.py apply` with the
   same session, model file, source root, and source commit recorded by `prepare`.
6. Run the same pinned entrypoint with `check`, report the source commit and changed managed paths,
   then delete the system-temporary session.
7. Present any host adapter plugin-refresh command or official UI action, execute only an approved
   command, and report `needs_restart` without treating host refresh as part of the project-file
   transaction.

The new shell and PowerShell wrappers are thin launchers for `bootstrap.py`; remove every reference
to archive fallback or project-local setup copies. Task 9 deletes the old wrapper names during the
final cutover.

- [ ] **Step 5: Run tests and commit**

```sh
git add skills/setup-project-agents tests/test_setup_cli.py
git commit -m "feat: orchestrate transactional project agent setup"
```

---

### Task 8: Centralize Tool Policy and Keep Hooks Diagnostic-Only

**Files:**
- Move: `skills/manage-agent-tools/references/recommended-tools/*.json` to `config/recommended-tools/*.json`
- Modify: `skills/manage-agent-tools/scripts/check_recommended_tools.py`
- Modify: `skills/manage-agent-tools/scripts/check_recommended_tools.sh`
- Modify: `skills/manage-agent-tools/scripts/check_recommended_tools.ps1`
- Rewrite: `skills/manage-agent-tools/SKILL.md`
- Create: `tests/test_manage_agent_tools.py`
- Modify: `catalog/project-assets.json`

**Interfaces:**
- Consumes: root policies when running as a plugin and copied Skill-local policies when running from a project Hook.
- Produces: read-only `doctor`, approval-gated `upgrade`, and Hook exit/output contracts.

- [ ] **Step 1: Extract failing tool-policy tests from the legacy suite**

Move the existing `RecommendedToolCheckerTest` cases into `tests/test_manage_agent_tools.py`. Add assertions that Codex policy contains only the effective `multi_agent` requirement, none of the three policies contains a Hook required value, and Hook mode never calls an install or upgrade runner.

- [ ] **Step 2: Run focused tests and verify policy lookup still points at the old directory**

- [ ] **Step 3: Move policies and implement two-root lookup**

Policy resolution must be:

```python
def default_policy_path(platform: str) -> Path:
    skill_root = Path(__file__).resolve().parents[1]
    project_copy = skill_root / 'references' / 'recommended-tools' / f'{platform}.json'
    if project_copy.is_file():
        return project_copy
    plugin_root = skill_root.parents[1]
    return plugin_root / 'config' / 'recommended-tools' / f'{platform}.json'
```

Renderer must copy the selected policy files into the project snapshot under `.agents/skills/manage-agent-tools/references/recommended-tools/`. Keep the current daily cache, lock, timeout, and platform-native Hook output behavior.

- [ ] **Step 4: Rewrite maintenance instructions around native managers**

Keep `doctor` read-only. For `upgrade`, show exact commands and obtain approval before execution. Use `copilot plugin update` for Copilot plugins, Codex marketplace refresh/native install flow where supported, and Cursor's official UI when no stable non-interactive update exists. Never edit plugin caches or trust stores. Stop when CodeGraph or Tokscale installation provenance is ambiguous.

- [ ] **Step 5: Run tests and commit**

```sh
git add config catalog/project-assets.json skills/manage-agent-tools \
  tests/test_manage_agent_tools.py
git commit -m "refactor: centralize recommended agent tool policy"
```

---

### Task 9: Cut Over, Remove the Legacy Synchronizer, and Prove End-to-End Behavior

**Files:**
- Delete: `skills/setup-project-agents/scripts/sync_public_agent_assets.py`
- Delete: `skills/setup-project-agents/scripts/sync_public_agent_assets.sh`
- Delete: `skills/setup-project-agents/scripts/sync_public_agent_assets.ps1`
- Delete: `skills/setup-project-agents/references/public_assets.json`
- Delete: `skills/setup-project-agents/references/project-config.schema.json`
- Delete: `skills/setup-project-agents/assets/`
- Delete: `skills/setup-project-agents/scripts/_vendor/`
- Delete: `tests/test_public_agent_assets.py`
- Expand: `tests/test_setup_cli.py`
- Expand: `tests/test_setup_source.py`
- Expand: `tests/test_setup_transaction.py`

**Interfaces:**
- Consumes: all new modules and tests from Tasks 2-8.
- Produces: no legacy path, no archive fallback, and one end-to-end setup implementation.

- [ ] **Step 1: Add end-to-end tests before deleting legacy code**

Use a temporary origin and target to prove:

- installed bootstrap fetches the current `main` commit and applies it;
- a later `main` commit changes only lock-owned files;
- a second run is idempotent;
- network unavailability uses installed source with a warning;
- invalid fetched source causes zero target mutation;
- unmanaged collision blocks the transaction;
- injected failure restores every original byte;
- Hooks off/on and all three platform outputs match the approved matrix;
- setup control-plane files are absent from the project snapshot.

- [ ] **Step 2: Run the new test modules and verify they pass while legacy files still exist**

Run:

```sh
uv run --python 3.11 --no-project python -m unittest \
  tests.test_setup_catalog tests.test_setup_planner tests.test_setup_renderer \
  tests.test_setup_transaction tests.test_setup_source tests.test_setup_cli \
  tests.test_manage_agent_tools
```

Expected: PASS.

- [ ] **Step 3: Delete every legacy implementation and compatibility assertion**

Remove only the paths listed above. Search and require no matches outside history:

```sh
rg -n 'sync_public_agent_assets|public_assets\.json|master\.zip|source_ref.*v0\.1\.0|legacy.*setup' \
  --hidden -g '!.git/**' -g '!docs/superpowers/**'
```

Expected: no runtime, test, Rule, Skill, template, or README match. The design and implementation plan may mention removed names only in historical/non-goal text.

- [ ] **Step 4: Run all tests and commit the cutover**

```sh
git add -A skills/setup-project-agents tests
git commit -m "refactor: replace legacy agent synchronization runtime"
```

---

### Task 10: Move the Chinese Mirror to Documentation and Update Repository Rules

**Files:**
- Move: `agents-zh/README.md` to `docs/zh-CN/README.md`
- Move: `agents-zh/**/*.md` to matching `docs/zh-CN/**` paths
- Delete: `agents-zh/`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `.agents/rules/00-global-rule-config.md`
- Modify: `.agents/rules/20-project-tools.md`
- Modify: `.agents/rules/21-project-rules.md`
- Modify: `.agents/rules/22-project-structure.md`
- Delete: `.agents/skills/write-rule/`
- Delete: `.agents/skills/write-skill/`
- Create: `.github/workflows/test.yml`
- Modify: `tests/test_plugin_manifests.py`

**Interfaces:**
- Produces: public installation/update docs, docs-only Chinese content, minimal repository development rules, and three-OS CI.

- [ ] **Step 1: Add failing documentation and repository-boundary tests**

Assert `agents-zh` is absent; every file under `docs/zh-CN` is Markdown; root runtime directories contain no Chinese mirror; `.agents` contains only `plugins/` and `rules/`; README names all three hosts, explicit setup, remote `main`, explicit Hooks, and native tool maintenance.

- [ ] **Step 2: Run the boundary tests and verify they fail on old paths**

- [ ] **Step 3: Move and rewrite documentation**

Move only Markdown. Rewrite `README.md` around plugin installation, manual per-project setup, `main`-tracking upgrades, Hook trust, tool doctor/upgrade, and the repository layout. Update `docs/zh-CN/README.md` as a natural Chinese document rather than a runtime mirror contract. Remove machine paths and obsolete nested-root commands.

- [ ] **Step 4: Rewrite project-maintenance rules for the new owners**

Keep `.agents/rules/` as this repository's source of truth. Replace references to `agents/`, `agents-zh/`, `public_assets.json`, and the old synchronizer with `rules/`, `skills/`, `agents/`, `catalog/project-assets.json`, `templates/project/`, and `docs/zh-CN/`. Keep the verification command and Python 3.11 floor. Remove `.agents/skills/` so this repository is not a generated project snapshot.

- [ ] **Step 5: Add cross-platform CI**

Create `.github/workflows/test.yml` with `ubuntu-latest`, `macos-latest`, and `windows-latest`,
`actions/setup-python` version `3.11`, the unittest discovery command, and `git diff --check` on all
three runners.

- [ ] **Step 6: Run all tests and commit**

```sh
git add -A README.md AGENTS.md .agents docs agents-zh .github/workflows tests \
  rules skills agents catalog templates config
git commit -m "docs: publish the agents plugin architecture"
```

---

### Task 11: Final Contract Audit and Release-Readiness Verification

**Files:**
- Modify only files revealed by this audit.

**Interfaces:**
- Consumes: completed Tasks 1-10.
- Produces: verified root plugin with no obsolete paths, no unmanaged drift, and passing platform contracts.

- [ ] **Step 1: Require a clean starting tree and validate source-of-truth uniqueness**

Run:

```sh
test -z "$(git status --short)"
test ! -d agents-zh
test ! -f skills/setup-project-agents/scripts/sync_public_agent_assets.py
test ! -f skills/setup-project-agents/references/public_assets.json
rg -n '/home/|[A-Za-z]:\\Users\\|source.*\./agents' --hidden -g '!.git/**' || true
```

Expected: obsolete files are absent and no machine-specific or nested-plugin path is reported.

- [ ] **Step 2: Validate root manifests and Catalog ownership**

Run manifest tests and a setup dry run against a temporary project. Confirm the lock has the fetched 40-character commit, all managed paths are repository-relative, Hooks are absent by default, and setup control-plane files are absent.

- [ ] **Step 3: Run complete verification twice**

Run:

```sh
uv run --python 3.11 --no-project python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Run the same commands a second time. Expected both times: all tests pass with only intentional, named skips; no working-tree changes are created.

- [ ] **Step 4: Review the complete branch diff against the design**

Check every section of `docs/superpowers/specs/2026-08-03-agents-plugin-design.md` against the implementation. Correct only concrete gaps, rerun Step 3, and ensure `git status --short` contains only the current audit correction, if any.

- [ ] **Step 5: Commit audit corrections when Step 4 changed tracked files**

```sh
git add -u
git diff --cached --check
git commit -m "fix: close agents plugin release audit gaps"
```

Because Step 1 requires a clean tree, `git add -u` can stage only Task 11 corrections. If Step 4 did
not change tracked files, do not run Step 5 and do not create an empty commit.
