# Project Tools

Strength: `Mandatory`

Scope: Placeholder and generation contract for repository-wide tooling facts, runtime services,
generated assets, verification requirements, and workflow handoffs.

## Generation Contract

This file is a project-local rule placeholder. During setup, `setup-project-agents` refreshes the
target repository's `.agents/rules/20-project-tools.md` from concrete repository evidence every
time it runs.

Do not keep this placeholder as project policy in a real project. Use evidence such as package
manifests, scripts, build and test commands, runtime ports, MCP configuration, service
dependencies, generated-file requirements, CI workflows, and verification requirements.

Record stable facts and constraints here. Put the executable procedure that prepares an
already-created worktree in `.agents/skills/worktree-environment-setup/`.

## What Belongs Here

- Package manager, language/runtime versions, and workspace layout.
- Common scripts for development, testing, building, linting, generation, and verification.
- Runtime services, ports, environment variables, data directories, and health checks.
- MCP or platform runtime configuration that agents must preserve.
- Generated assets or files that should not be edited by hand.
- Verification requirements and the local project skills that execute them.

## What Does Not Belong Here

- General code style; use base or project convention rules instead.
- Worktree selection, creation, integration, or cleanup procedures; use their public workflow
  skills.
- The executable environment preparation sequence; generate it in
  `worktree-environment-setup` from the facts recorded here.
- Project-specific facts in `wenyue/agents`; only target repositories should contain real local
  tooling facts.

## Suggested Generated Content

- Concrete setup, install, lint, test, build, generation, and verification commands.
- Runtime services, ports, health checks, environment variables, and required credentials.
- MCP and platform runtime entries that agents must preserve.
- Generated files, regeneration owners, and files that must not be edited by hand.
- The target-owned `worktree-environment-setup` skill that executes project-specific preparation.
