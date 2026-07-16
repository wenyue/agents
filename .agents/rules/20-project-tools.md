# Project Tools

Strength: `Mandatory`

Scope: Repository runtime requirements, supported verification commands, and public-agent sync
tooling boundaries.

## Runtime

- Run repository-owned scripts from the repository root with Python 3.11 or newer.
- The Python scripts use the standard library, including `tomllib`; the repository declares no
  dependency installation or environment preparation step.
- The repository declares no package manager, formatter, automatic fixer, analyzer, linter, build
  command, packaging command, runtime service, port, credential, or health check. Do not invent or
  substitute any of them.

## Verification Commands

Use these repository-supported checks:

| Purpose | Command | Behavior |
| --- | --- | --- |
| Public catalog, synchronization, ownership, mirror, wrapper, and timing contracts | `python -m unittest discover -s tests -p 'test_*.py'` | Repository-wide, non-fixing test suite with no declared narrower selector |
| Diff whitespace and conflict-marker integrity | `git diff --check` | Non-mutating check of the current working-tree diff |

Run both commands for a completed change set. Do not treat one as a substitute for the other.

## Public Sync Tooling

- `agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py` is the English public
  implementation installed into target repositories under
  `.agents/skills/setup-project-agents/scripts/`.
- The sync tool reads `agents/skills/setup-project-agents/references/public_assets.json` as its
  public distribution manifest.
- A normal sync invocation mutates the target repository; `--check` reports target drift without
  writing target files. Neither invocation is a formatter, fixer, or replacement for this
  repository's test command.
- Do not run the sync tool merely to make this repository's `.agents/` directory match `agents/`.
  The local runtime is intentionally curated and independently owned.

## Boundaries

- Completed change verification belongs to
  `.agents/skills/change-set-verification/SKILL.md`.
- The repository has no setup procedure, so do not create or invoke a project-local
  `worktree-environment-setup` skill without new repository evidence.
- Keep public-source ownership and mirror policy in `21-project-rules.md`.
- Keep directory responsibilities and dependency direction in `22-project-structure.md`.
