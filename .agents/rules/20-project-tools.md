# Project Tools

Strength: `Mandatory`

Scope: Generation contract for repository-wide tool facts, capabilities, and invocation constraints,
runtime services, and generated-asset tooling.

## Generation Contract

Author the target rule from current repository evidence. Keep only stable facts that another agent
needs to invoke, scope, or preserve project tooling correctly.

## Evidence

- Package manifests, lock files, toolchain pins, workspace configuration, and package-manager files.
- Repository scripts, task runners, CI workflows, tool configuration, and command help output.
- Runtime entry points, service configuration, ports, environment templates, and health checks.
- Code-generation configuration, generated outputs, and repository-owned orchestration selectors.
- MCP and native agent-platform configuration that affects project tooling.

## Content

- Record runtime versions, package managers, workspace layout, and required working directories.
- Record development, setup, build, generation, formatting, analysis, lint, test, and packaging
  commands. For each command, include prerequisites, inputs, outputs, supported scope selection,
  mutation behavior, safe-fix capability, and relative cost.
- Record runtime services, ports, environment variables, data directories, credential requirements,
  startup dependencies, and health checks.
- Record generation entry points and their inputs and outputs. Keep semantic ownership and the ban on
  hand-editing generated files in `21-project-rules.md`.
- Record repository-owned selectors that generated project skills can invoke without duplicating
  their implementation.

## Boundaries

- Keep environment preparation order in `.agents/skills/worktree-environment-setup/` and completed
  change verification in `.agents/skills/change-set-verification/`.
- Exclude verification trigger timing, check ordering, deduplication, risk-based broadening,
  baseline comparison, and result policy; the generated verification skill owns those decisions.
- Keep API and domain conventions in `21-project-rules.md`, and module and dependency ownership in
  `22-project-structure.md`.
- Do not turn a command inventory into an instruction to run every command.
- Do not infer tools, commands, supported scopes, or costs that current evidence does not prove.
