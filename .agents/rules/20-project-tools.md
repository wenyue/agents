# Project Tools

Strength: `Mandatory`

Scope: Placeholder and generation contract for repository-wide tool facts, capabilities, and
invocation constraints, runtime services, and generated assets.

## Generation Contract

This file is a project-local rule placeholder. During setup, `setup-project-agents` refreshes the
target repository's `.agents/rules/20-project-tools.md` from concrete repository evidence every
time it runs.

Do not keep this placeholder as project policy in a real project. Use evidence such as package
manifests, scripts, build and test commands, runtime ports, MCP configuration, service
dependencies, generated-file requirements, and CI workflows.

Record stable tool facts and constraints here. Put the workflows that select and order those tools
in the generated `.agents/skills/worktree-environment-setup/` and
`.agents/skills/project-verification/` skills.

## What Belongs Here

- Package manager, language/runtime versions, and workspace layout.
- Common scripts for development, testing, building, linting, generation, and verification.
- Each tool's exact invocation, required working directory, supported scope selection, mutation
  behavior, safe-fix capability, prerequisites, environment, outputs, and relative cost.
- Runtime services, ports, environment variables, data directories, and health checks.
- MCP or platform runtime configuration that agents must preserve.
- Generated assets or files that should not be edited by hand.
- Existing repository-owned selectors or orchestration entry points that generated project skills
  can reuse without copying their implementation.

## What Does Not Belong Here

- General code style; use base or project convention rules instead.
- Worktree selection, creation, integration, or cleanup procedures; use their public workflow
  skills.
- Environment preparation sequencing, verification trigger timing, check ordering, deduplication,
  risk-based broadening, baseline-failure handling, or result-reporting policy; generate those
  workflows in their owning project skills from the facts recorded here.
- Unconditional instructions to run every listed command. Listing a tool describes a capability,
  not a workflow requirement.
- Project-specific facts in `wenyue/agents`; only target repositories should contain real local
  tooling facts.

## Suggested Generated Content

- Concrete setup, install, lint, test, build, generation, and verification commands with their
  supported scopes, mutation modes, safe fixes, prerequisites, outputs, and relative costs.
- Runtime services, ports, health checks, environment variables, and required credentials.
- MCP and platform runtime entries that agents must preserve.
- Generated files, regeneration owners, and files that must not be edited by hand.
- References to the target-owned `worktree-environment-setup` and `project-verification` skills
  that own project-specific execution policy.
