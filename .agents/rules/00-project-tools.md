# Project Tools

Strength: `Mandatory`

Scope: Repository runtime, authorized mutation tools, required verification, setup control plane,
and public adapter synchronization.

Use only the runtime, mutation, and verification surfaces declared here. `AGENTS.md` owns this
Rule's applicability; the SmartKit Rule configuration owns precedence.

## Runtime

- Run repository-owned scripts from the repository root with Python 3.10 or newer.
- The Python scripts use the standard library and a vendored `tomli` fallback for Python 3.10; the
  repository declares no dependency installation or environment preparation step.
- Treat package managers, formatters, automatic fixers, analyzers, linters, build and packaging
  commands, runtime services, ports, credentials, and health checks as unavailable until repository
  evidence declares them.

## Managed Plugin Version

- Treat root `VERSION` as the only manually maintained plugin version. After changing it, run
  `python scripts/sync_plugin_version.py` and review the generated manifest, marketplace, and catalog
  diffs as part of the same change set.
- Use `python scripts/sync_plugin_version.py --check` for read-only drift detection; CI must reject
  version fields that do not match `VERSION`.

## External Plugin Skills

- Use `python scripts/update_external_skills.py --check` for read-only registry, upstream, lock,
  license, and installed-file drift detection.
- Run `python scripts/update_external_skills.py --update`, with optional
  `--source owner/repository`, only when repository evidence establishes maintainer authority.
  Without that evidence, treat the update as unauthorized. Review all Skill, lock, and license
  changes afterward.
- The updater is transactional, uses ambient GitHub credentials, and changes only registry-declared
  external Skill roots, `vendor/external-skills.lock.json`, and license snapshots.

## Plugin MCP Adapters

- Treat `mcp/registry.json` as the only manually maintained Plugin MCP declaration. After changing
  it, run `python scripts/sync_mcp_adapters.py` and review all three host adapters.
- Use `python scripts/sync_mcp_adapters.py --check` for read-only adapter drift detection. Plugin
  MCP adapters are configuration artifacts; the synchronizer must not download or vendor an MCP
  server implementation.

## Plugin Agent Adapters

- Treat `agents/registry.json` and `agents/source/` as the manually maintained Plugin Agent
  declaration and shared instructions. After changing either, run
  `python scripts/sync_agent_adapters.py` and review all three host adapters.
- Use `python scripts/sync_agent_adapters.py --check` for read-only adapter drift detection. Host
  adapters inherit the host's selected model and retain only host-native metadata.

## Required Verification

Use these repository-supported checks:

| Purpose | Command | Behavior |
| --- | --- | --- |
| Public catalog, synchronization, ownership, mirror, wrapper, and timing contracts | `python -m unittest discover -s tests -p 'test_*.py'` | Repository-wide, non-fixing test suite with no declared narrower selector |
| Plugin Agent adapter drift | `python scripts/sync_agent_adapters.py --check` | Read-only comparison of the canonical registry and shared instructions with all host adapters |
| Plugin MCP adapter drift | `python scripts/sync_mcp_adapters.py --check` | Read-only comparison of the canonical registry with all host adapters |
| Diff whitespace and conflict-marker integrity | `git diff --check` | Non-mutating check of the current working-tree diff |

Run the repository test suite, both adapter drift checks, and the diff-integrity check for every
completed change set; together they form the required verification.

## Project Setup Tooling

- `skills/setup-project-agents/scripts/workflow.py`, reached through
  `setup_project_agents.sh` or `setup_project_agents.ps1`, is the public
  `start`/`finish`/`cancel` control plane. The pinned
  `setup_project_agents.py` prepare/apply/check phases are internal workflow operations.
- Start creates and owns the private session, reads `setup-assets/catalog/assets.json`, attempts to
  fetch canonical `master`, and uses the validated installed plugin source only when that source is
  unavailable. It then captures Rules, Skills, Agents, and MCP intent, snapshots external Skills,
  and creates the request. Finish preserves project Rules, Skills, and Agent sources, renders
  declared Agent and MCP adapters, reconciles setup-managed content, checks convergence,
  summarizes, and cleans up. Cancel safely cleans up an unfinished workflow-owned session.
- The unified ownership manifest records setup-managed Rule and Skill files, Agent adapters, MCP
  fields, and configuration with deterministic digests. Setup updates or deletes only entries
  authorized by the previous manifest; a modified owned asset or conflicting first-adoption target
  stops before writes.
- `check` reports desired-state drift without writes. The setup control plane is not a formatter,
  fixer, or replacement for this repository's test command.
- Keep this repository's local `.agents/` directory limited to its `plugins/` marketplace
  configuration and `rules/` development instructions.

## Boundaries

- Completed change verification belongs to `change-set-verification`.
- Treat project-local worktree environment setup as unavailable until new repository evidence
  establishes a real setup procedure.
- Keep public-source ownership and mirror policy in `Project Rules`.
- Keep directory responsibilities and dependency direction in `Project Structure`.
