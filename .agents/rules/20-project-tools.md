# Project Tools

Strength: `Mandatory`

Scope: Placeholder for repository-wide tooling facts, runtime services, generated assets,
verification requirements, and workflow handoffs.

## Placeholder

This file is a project-local placeholder. Each repository that adopts these public agent rules must
replace this content with facts from that repository.

Do not keep this placeholder as project policy in a real project. Update it from concrete evidence
such as package manifests, scripts, build and test commands, runtime ports, MCP configuration,
service dependencies, generated-file requirements, and verification requirements.

Record facts and constraints here. Put executable procedural flows, such as worktree bootstrap,
review checkpoints, and merge-back, in a local project skill such as
`.agents/skills/project-development-workflow/`.

## Suggested Content

- Package manager, language/runtime versions, and workspace layout.
- Common scripts for development, testing, building, linting, generation, and verification.
- Runtime services, ports, environment variables, data directories, and health checks.
- MCP or platform runtime configuration that agents must preserve.
- Generated assets or files that should not be edited by hand.
- Verification requirements and the local project skills that execute them.
