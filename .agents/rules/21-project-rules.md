# Project Rules

Strength: `Default`

Scope: Placeholder for project APIs, generated-file boundaries, lint interpretation, lifecycle
rules, and domain conventions.

## Generation Contract

This file is a project-local rule placeholder. During setup, `setup-project-agents` refreshes the
target repository's `.agents/rules/21-project-rules.md` from concrete repository evidence every
time it runs.

Do not keep this placeholder as project policy in a real project. Update it from concrete evidence
such as source modules, framework conventions, API contracts, generated-file configs, custom lint
rules, domain terminology, storage behavior, state management, and lifecycle constraints.

Record stable conventions and behavioral contracts here. Put tooling commands in
`.agents/rules/20-project-tools.md` and directory ownership in
`.agents/rules/22-project-structure.md`.

## What Belongs Here

- Public API contracts, route boundaries, event names, payload fields, and compatibility rules.
- Framework or library conventions already used by the project.
- Generated-file ownership, external schema ownership, and regeneration requirements.
- Domain terms, naming conventions, prefixes, and user-visible copy conventions.
- Persistence, migration, ownership, lifecycle, or concurrency rules.
- Project-specific interpretations of lints, analyzers, or formatting tools.

## What Does Not Belong Here

- Tool, runtime, build, test, or verification commands; use `20-project-tools.md`.
- Top-level directory maps, module ownership, or dependency direction; use
  `22-project-structure.md`.
- General code style; use base language rules unless the project has a concrete override.
- Project-specific facts in `wenyue/agents`; only target repositories should contain real local
  project conventions.

## Suggested Generated Content

- Public API contracts, route boundaries, event names, payload fields, and compatibility rules.
- Framework or library conventions already used by the project.
- Generated files, external schema ownership, and regeneration requirements.
- Domain terms, naming conventions, prefixes, and user-visible copy conventions.
- Persistence, migration, ownership, lifecycle, or concurrency rules.
- Project-specific interpretations of lints, analyzers, or formatting tools.
