# Template-Driven Project Agent Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `setup-project-agents` reconcile readable, platform-native project configuration templates while a non-blocking daily hook checks only platform-relevant tools and strict minimum versions.

**Architecture:** Replace manifest `root_configs` operations with literal configuration templates and a generic partial deep-merge engine. Keep all Codex, Cursor, Copilot, MCP, hook, model, approval, sandbox, token, tool, and version values outside Python. Add one standard-library Python checker plus paired POSIX/PowerShell entry points; native hook templates call it and share per-user, per-platform daily state across repositories.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `datetime`, `hashlib`, `json`, `os`, `pathlib`, `re`, `subprocess`, `tempfile`, `time`, `tomllib`), TOML/JSON/JSONC/text templates, native Codex/Cursor/Copilot hook schemas, `unittest`.

## Global Constraints

- Sync never reads or modifies user configuration.
- Normal sync creates or updates template-owned project values; `--check` reports the same drift without writing.
- Template-external project values remain unchanged; arrays explicitly present in a template are complete owned values unless a manifest list-merge rule says otherwise.
- Python contains no platform configuration value, project config path, model, approval, sandbox, token limit, recommended-tool version, or installation instruction.
- Hooks inspect recommended tools only and always exit `0`.
- Full hook checks run once per user, platform, local day, and checker/policy fingerprint across all repositories.
- Installed tool versions must be strictly greater than policy targets.
- Public English Markdown changes have matching `agents-zh/` Simplified-Chinese mirrors.
- Do not update the consuming repository's `.agents/` runtime merely to mirror public-source changes.

---

### Task 1: Define Literal Project Configuration Templates

**Files:**
- Modify: `tests/test_public_agent_assets.py`
- Modify: `agents/skills/setup-project-agents/references/public_assets.json`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/codex.config.toml`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/cursor.cli.json`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/cursor.mcp.json`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/copilot.settings.json`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/copilot.mcp.json`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/vscode.mcp.json`

**Interfaces:**
- Removes manifest field: `root_configs`.
- Produces manifest field: `config_templates[]` with `path`, `template`, `format`, `merge`, optional `when`, optional `list_merges`, and optional `validations`.
- Template resolution remains confined to `assets/templates/`.

- [ ] **Step 1: Write failing manifest and content-contract tests**

  Assert `root_configs` is absent. Assert each existing native config path has a literal template. Parse the Codex TOML and Copilot/Cursor JSON templates and assert the approved values, including Codex cost controls, Copilot marketplace/plugin settings, and safe Cursor permissions.

- [ ] **Step 2: Verify RED**

  Run:

  ```bash
  python3.11 -m unittest tests.test_public_agent_assets.PublicAssetSyncTest.test_public_manifest_declares_config_templates
  ```

  Expected: failure because `config_templates` and the project-config templates do not exist.

- [ ] **Step 3: Add literal native templates**

  Use the approved Codex and Copilot values from the design. For Cursor, declare project permission policy without undocumented model or Max Mode fields. Express the four MCP roots as literal empty objects with the correct platform-owned root key.

- [ ] **Step 4: Replace manifest operations with template references**

  Use `deep-overwrite` for project configuration. Preserve the existing `path_glob_exists` condition for Codex multi-agent configuration as declarative manifest data only if the complete Codex template should be conditional; otherwise apply the approved team baseline unconditionally.

- [ ] **Step 5: Verify GREEN**

  Run the focused manifest tests and parse every template with `tomllib` or the test JSONC loader.

### Task 2: Replace Root-Config Mutation With a Generic Template Engine

**Files:**
- Modify: `tests/test_public_agent_assets.py`
- Modify: `agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`

**Interfaces:**
- Produces: `_reconcile_config_templates(context, public_config) -> None`.
- Produces: `_deep_merge_template(current, desired) -> merged` for mapping recursion and scalar/list replacement.
- Produces: `_load_native_config(path, format) -> tuple[str, dict]` and `_render_native_config(...) -> str`.
- Retires: `_reconcile_root_configs`, locked-value parsing, and native configuration values embedded in Python.

- [ ] **Step 1: Write failing deep-merge tests**

  Cover missing files, nested objects, scalar overwrite, array replacement, preservation of extra fields, `--check`, second-run idempotence, malformed target files, unsafe template paths, unsupported formats, and declarative conditions.

- [ ] **Step 2: Write failing TOML preservation and JSONC tests**

  Assert TOML comments and unrelated assignments survive template-leaf updates. Assert JSONC comments/trailing commas can be read, managed fields update, unrelated parsed fields survive, and emitted output remains valid JSON accepted by JSONC consumers.

- [ ] **Step 3: Verify RED**

  Run the focused configuration tests. Expected failures must show that sync still reads `root_configs` and lacks the generic template API.

- [ ] **Step 4: Implement format-neutral merge and validation**

  Recursively merge dictionaries. Treat arrays and scalars as owned leaves. Reject a mapping template applied through a non-mapping target. Strip JSONC comments/trailing commas with a string-aware scanner before `json.loads`; never use regex that can alter string literals.

- [ ] **Step 5: Implement minimal TOML leaf rendering**

  Reuse and generalize the existing TOML assignment writer. Walk parsed template leaves in document order, update root or table assignments, and validate the final text with `tomllib`. Reject template shapes that the writer cannot preserve safely.

- [ ] **Step 6: Implement generic manifest reconciliation**

  Validate paths stay below the target and template roots. Load the literal template, merge into the existing project file, render deterministically, and delegate writes to the existing `_write_bytes` check/idempotence path.

- [ ] **Step 7: Replace hard-coded reference validation**

  Move the Codex agent `config_file` existence rule to a generic manifest validation descriptor. The Python validator consumes object path, field name, and base path without naming Codex or `.codex/config.toml`.

- [ ] **Step 8: Remove obsolete root-config code and verify GREEN**

  Delete locked-value-only helpers and tests. Run all configuration-focused tests plus the existing wrapper/agent-reference tests.

### Task 3: Add Declarative Recommended-Tool Policies and Version Checking

**Files:**
- Modify: `tests/test_public_agent_assets.py`
- Create: `agents/skills/setup-project-agents/assets/templates/recommended-tools/codex.json`
- Create: `agents/skills/setup-project-agents/assets/templates/recommended-tools/cursor.json`
- Create: `agents/skills/setup-project-agents/assets/templates/recommended-tools/copilot.json`
- Create: `agents/skills/setup-project-agents/scripts/check_recommended_tools.py`

**Interfaces:**
- Command: `check_recommended_tools.py check --platform {codex,cursor,copilot} [--policy PATH]`.
- Command: `check_recommended_tools.py hook --platform {codex,cursor,copilot} [--policy PATH] [--force]`.
- Finding codes: `tool-missing`, `version-unreadable`, `version-not-greater`, `integration-missing`, `detector-error`.
- Exit: `check` returns nonzero for findings; `hook` always returns `0`.

- [ ] **Step 1: Write failing version-order tests**

  Test numeric semantic versions, Cursor calendar versions with build suffixes, equality failure, prerelease/build suffix handling, invalid versions, and versions greater/lower than targets.

- [ ] **Step 2: Write failing policy/detector tests**

  Use temporary executables and manifests to cover command-regex, JSON command output, JSON manifest glob, text command output, fallback detector order, platform applicability, bounded timeout, missing executable, malformed policy, and no secret/value echo.

- [ ] **Step 3: Verify RED**

  Run the focused checker tests. Expected: import failure because the checker does not exist.

- [ ] **Step 4: Add readable platform policies**

  Encode these strict thresholds as data: Codex CLI `0.144.0`, Cursor Agent `2026.01.27`, Copilot CLI `1.0.58`, Superpowers `6.0.0`, and CodeGraph `1.4.0`. Include only platform-applicable tools and their install/upgrade guidance.

- [ ] **Step 5: Implement generic version and detector engine**

  Normalize ordered numeric components, compare strictly, and keep detector execution data-driven. Expand only documented placeholders such as user home and platform config home. Apply timeouts and bounded output capture.

- [ ] **Step 6: Implement human and native-hook output**

  `check` prints concise actionable findings. `hook` adapts the same findings to the invoking platform's accepted output while guaranteeing exit `0` on findings and internal failures.

- [ ] **Step 7: Verify GREEN**

  Run all checker tests and direct fixture-based CLI invocations.

### Task 4: Add Cross-Project Per-Platform Daily State

**Files:**
- Modify: `tests/test_public_agent_assets.py`
- Modify: `agents/skills/setup-project-agents/scripts/check_recommended_tools.py`

**Interfaces:**
- Cache key: platform only; no repository path.
- Cache value: local date plus SHA-256 fingerprint of checker and policy bytes.
- Cache root: `%LOCALAPPDATA%/setup-project-agents`, `$XDG_CACHE_HOME/setup-project-agents`, `~/Library/Caches/setup-project-agents`, or `~/.cache/setup-project-agents`.

- [ ] **Step 1: Write failing daily-state tests**

  Freeze the clock and isolate cache. Assert same-platform invocations from two repositories run once, different platforms run independently, the next day runs, policy/checker changes rerun the same day, and `--force` bypasses state.

- [ ] **Step 2: Write failing concurrency and recovery tests**

  Assert a live exclusive lock suppresses a duplicate run, a stale lock is reclaimed, malformed/unwritable cache fails open, and internal detector failure records no successful state.

- [ ] **Step 3: Verify RED**

  Expected: repeated hook invocations both execute detectors.

- [ ] **Step 4: Implement platform cache resolution and fingerprinting**

  Store no project path, configuration data, command output, or secrets. Atomically replace state with a temporary sibling.

- [ ] **Step 5: Implement stale-safe exclusive locking**

  Use `os.open(..., O_CREAT | O_EXCL)` with a bounded stale age. Always release owned locks in `finally`.

- [ ] **Step 6: Gate only hook mode and verify GREEN**

  Keep manual `check` uncached. Run all daily, cross-project, cross-platform, force, fingerprint, race, and failure tests.

### Task 5: Distribute Native Hooks and Paired Entry Points Through Templates

**Files:**
- Modify: `tests/test_public_agent_assets.py`
- Modify: `agents/skills/setup-project-agents/references/public_assets.json`
- Modify: `agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`
- Create: `agents/skills/setup-project-agents/scripts/check_recommended_tools.sh`
- Create: `agents/skills/setup-project-agents/scripts/check_recommended_tools.ps1`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/codex.hooks.json`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/cursor.hooks.json`
- Create: `agents/skills/setup-project-agents/assets/templates/project-config/copilot.tool-check.hooks.json`

**Interfaces:**
- Codex target: `.codex/hooks.json`, `SessionStart`.
- Cursor target: `.cursor/hooks.json`, `sessionStart`.
- Copilot target: `.github/hooks/project-agent-tool-check.json`, `sessionStart`.
- Shared-list reconciliation: manifest declares list path and setup-owned command marker; unrelated hook entries survive.

- [ ] **Step 1: Write failing hook-template tests**

  Parse every hook template and assert its native event, platform argument, wrapper command, and non-blocking contract. Verify POSIX and PowerShell wrappers forward arguments to the same Python checker.

- [ ] **Step 2: Write failing shared-hook merge tests**

  Cover absent files, existing unrelated hooks, previous owned entry, duplicate owned entries, malformed JSON, `--check`, and second-run idempotence.

- [ ] **Step 3: Verify RED**

  Expected: no hook templates or owned-list reconciliation exist.

- [ ] **Step 4: Implement generic owned-list merge**

  For manifest-declared list paths, replace entries containing the owned marker with the template entry, collapse duplicates, and preserve unrelated entries and order. Keep all event names and markers in manifest/template data.

- [ ] **Step 5: Add paired wrappers and literal hook templates**

  Wrappers discover the repository/installed skill root without persisting machine-specific paths, then invoke Python with unchanged arguments. Native templates supply platform-specific commands and output schema.

- [ ] **Step 6: Verify GREEN**

  Run hook merge, wrapper, direct hook, malformed-file, and idempotence tests.

### Task 6: Rewrite the Shared Setup Skill and Chinese Mirror

**Files:**
- Modify: `tests/test_public_agent_assets.py`
- Modify: `agents/skills/setup-project-agents/SKILL.md`
- Modify: `agents-zh/skills/setup-project-agents/SKILL.md`

**Interfaces:**
- Skill class: shared orchestrator.
- Start: repository initialization or catalog update.
- Completion: public assets and template-owned project config reconciled; uncached tool check reported; hook installed.
- Excludes: user config reads/writes, project-field classification/removal, and separate config repair.

- [ ] **Step 1: Add failing content-contract tests**

  Require both language versions to state template ownership, generic partial merge, automatic project config repair, `--check`, no user-config access, tool-only hooks, strict version comparison, cross-project per-platform daily state, and non-blocking output.

- [ ] **Step 2: Verify RED**

  Expected: the current skill still describes the old deterministic root-config workflow and lacks template/tool-hook contracts.

- [ ] **Step 3: Rewrite the English skill as one coherent shared orchestrator**

  Preserve Ownership, Managed Assets, Reconciliation Workflow, Review Gate, Acceptance Gate, Validation, and Output. Point deterministic behavior to owned templates and scripts instead of restating values in prose.

- [ ] **Step 4: Update the Chinese mirror**

  Preserve section structure, paths, commands, identifiers, version semantics, and stop/continue decisions.

- [ ] **Step 5: Read both complete candidates and verify GREEN**

  Run content-contract tests, compare headings and command blocks, and ensure no stale user-config or cleanup language remains.

### Task 7: End-to-End Acceptance and Regression Verification

**Files:**
- Test: `tests/test_public_agent_assets.py`
- Review: every file changed by Tasks 1–6

- [ ] **Step 1: Sync a representative temporary repository**

  Seed extra native config values and unrelated hooks. Run setup twice and assert template-owned values, preserved extras, installed hooks, copied scripts/policies, and second-run idempotence.

- [ ] **Step 2: Exercise check mode**

  Introduce drift, snapshot bytes, run `--check`, assert drift reporting and byte-identical files.

- [ ] **Step 3: Exercise all tool hooks**

  Use fixture tools/manifests to verify missing, equal, lower, higher, malformed, and platform-inapplicable versions; verify one full cross-project daily run per platform and exit `0` throughout.

- [ ] **Step 4: Run complete repository verification**

  ```bash
  python3.11 -m unittest discover -s tests -p 'test_*.py'
  git diff --check
  ```

  Expected: all tests pass and no whitespace/conflict-marker errors appear.

- [ ] **Step 5: Review final source-of-truth boundaries**

  Confirm all managed values and version thresholds are visible in templates, no user-config code exists, Python has no platform config values, the English/Chinese skill pair is aligned, and the main checkout remains untouched.
