# Project Tools

Strength: `Mandatory`

Scope: Placeholder and generation contract for repository-wide tooling facts, runtime services,
generated assets, verification requirements, and workflow handoffs.

## Generation Contract

This file is a project-local rule placeholder. During setup, `update-project-rules` creates the
target repository's `.agents/rules/20-project-tools.md` from this placeholder when that rule is
missing. The generated target rule must then be replaced or refreshed from concrete repository
evidence.

Do not keep this placeholder as project policy in a real project. Use evidence such as package
manifests, scripts, build and test commands, runtime ports, MCP configuration, service
dependencies, generated-file requirements, CI workflows, and verification requirements.

Record stable facts and constraints here. Put executable procedural flows, such as isolated
worktree bootstrap, review checkpoints, and merge-back, in a local project skill such as
`.agents/skills/project-development-workflow/`.

## What Belongs Here

- Package manager, language/runtime versions, and workspace layout.
- Common scripts for development, testing, building, linting, generation, and verification.
- Runtime services, ports, environment variables, data directories, and health checks.
- MCP or platform runtime configuration that agents must preserve.
- Generated assets or files that should not be edited by hand.
- Verification requirements and the local project skills that execute them.

## What Does Not Belong Here

- General code style; use base or project convention rules instead.
- Full worktree, bootstrap, review, or merge-back procedures; put those in
  `project-development-workflow`.
- Project-specific facts in `wenyue/agents`; only target repositories should contain real local
  tooling facts.
