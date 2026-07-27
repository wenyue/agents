# Project Tools

Strength: `Mandatory`

Scope: Repository runtime requirements, supported verification commands, and public-agent sync
tooling boundaries.

## Runtime

- Run repository-owned scripts from the repository root with Python 3.11 or newer.
- The Python scripts use the standard library, including `tomllib`; the repository declares no
  dependency installation or environment preparation step.
- Treat package managers, formatters, automatic fixers, analyzers, linters, build and packaging
  commands, runtime services, ports, credentials, and health checks as unavailable until repository
  evidence declares them.

## Verification Commands

Use these repository-supported checks:

| Purpose | Command | Behavior |
| --- | --- | --- |
| Public catalog, synchronization, ownership, mirror, wrapper, and timing contracts | `python -m unittest discover -s tests -p 'test_*.py'` | Repository-wide, non-fixing test suite with no declared narrower selector |
| Diff whitespace and conflict-marker integrity | `git diff --check` | Non-mutating check of the current working-tree diff |

Run both commands for every completed change set; together they form the required verification.

## Public Sync Tooling

- `agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py` is the English public
  implementation installed into target repositories under
  `.agents/skills/setup-project-agents/scripts/`.
- The sync tool reads `agents/skills/setup-project-agents/references/public_assets.json` as its
  public distribution manifest.
- A normal sync invocation mutates the target repository; `--check` reports target drift without
  writing target files. Neither invocation is a formatter, fixer, or replacement for this
  repository's test command.
- Run the sync tool against target repositories that consume the public catalog. Keep this
  repository's intentionally curated `.agents/` runtime under its independent owner.

## Boundaries

- Completed change verification belongs to `change-set-verification`.
- Treat project-local worktree environment setup as unavailable until new repository evidence
  establishes a real setup procedure.
- Keep public-source ownership and mirror policy in `Project Rules`.
- Keep directory responsibilities and dependency direction in `Project Structure`.
