# Project Tools

Strength: `Mandatory`

Scope: Repository runtime requirements, supported verification commands, and public-agent sync
tooling boundaries.

## Runtime

- Run repository-owned scripts from the repository root with Python 3.10 or newer.
- The Python scripts use the standard library and a vendored `tomli` fallback for Python 3.10; the
  repository declares no dependency installation or environment preparation step.
- Treat package managers, formatters, automatic fixers, analyzers, linters, build and packaging
  commands, runtime services, ports, credentials, and health checks as unavailable until repository
  evidence declares them.

## Plugin Version

- Treat root `VERSION` as the only manually maintained plugin version. After changing it, run
  `python scripts/sync_plugin_version.py` and review the generated manifest, marketplace, and catalog
  diffs as part of the same change set.
- Use `python scripts/sync_plugin_version.py --check` for read-only drift detection; CI must reject
  version fields that do not match `VERSION`.

## External Plugin Skills

- Use `python scripts/update_external_skills.py --check` for read-only registry, upstream, lock,
  license, and installed-file drift detection.
- Only a repository maintainer may run `python scripts/update_external_skills.py --update`, with
  optional `--source owner/repository`. Review all Skill, lock, and license changes afterward.
- The updater is transactional, uses ambient GitHub credentials, and changes only registry-declared
  external Skill roots, `vendor/external-skills.lock.json`, and license snapshots.

## Plugin MCP Adapters

- Treat `mcp/registry.json` as the only manually maintained Plugin MCP declaration. After changing
  it, run `python scripts/sync_mcp_adapters.py` and review all three host adapters.
- Use `python scripts/sync_mcp_adapters.py --check` for read-only adapter drift detection. Plugin
  MCP adapters are configuration artifacts; the synchronizer must not download or vendor an MCP
  server implementation.

## Verification Commands

Use these repository-supported checks:

| Purpose | Command | Behavior |
| --- | --- | --- |
| Public catalog, synchronization, ownership, mirror, wrapper, and timing contracts | `python -m unittest discover -s tests -p 'test_*.py'` | Repository-wide, non-fixing test suite with no declared narrower selector |
| Plugin MCP adapter drift | `python scripts/sync_mcp_adapters.py --check` | Read-only comparison of the canonical registry with all host adapters |
| Diff whitespace and conflict-marker integrity | `git diff --check` | Non-mutating check of the current working-tree diff |

Run both commands for every completed change set; together they form the required verification.

## Project Setup Tooling

- `skills/setup-project-agents/scripts/workflow.py`, reached through the paired shell wrappers, is
  the public `start`/`finish`/`cancel` control plane. The pinned
  `setup_project_agents.py` prepare/apply/check phases are internal workflow operations.
- Start creates and owns the private session, reads `setup-assets/catalog/assets.json`, fetches
  canonical `master`, snapshots external Skills, and creates the request and models template. Finish
  discovers project-owned Rules and Skills, force-converges catalog-managed, generated, and
  configured external content, checks convergence, summarizes, and cleans up without a project
  lock. Cancel safely cleans up an unfinished workflow-owned session.
- Setup preserves structured fields outside catalog templates and project-owned Rule and Skill
  content. Project MCP declarations render through host adapters and use
  `.agents/project-mcp.lock.json` for entry-level update and deletion ownership. Setup removes
  deselected known catalog outputs, paths declared by `retired_assets`, and stale files inside a
  managed Skill directory.
- `check` reports desired-state drift without writes. Neither command is a formatter, fixer, or
  replacement for this repository's test command.
- Keep this repository's local `.agents/` directory limited to its `plugins/` marketplace
  configuration, `rules/` development instructions, and thin Skill discovery wrappers.

## Boundaries

- Completed change verification belongs to `change-set-verification`.
- Treat project-local worktree environment setup as unavailable until new repository evidence
  establishes a real setup procedure.
- Keep public-source ownership and mirror policy in `Project Rules`.
- Keep directory responsibilities and dependency direction in `Project Structure`.
