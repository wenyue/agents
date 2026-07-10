# Project Structure

Strength: `Advisory`

Scope: Placeholder for top-level modules, feature layout, dependency direction, shared locations,
and configuration ownership.

## Generation Contract

This file is a project-local rule placeholder. During setup, `setup-project-agents` refreshes the
target repository's `.agents/rules/22-project-structure.md` from concrete repository evidence every
time it runs.

Do not keep this placeholder as project policy in a real project. Update it from concrete evidence
such as the repository tree, package boundaries, import rules, module owners, feature directories,
shared libraries, configuration locations, and dependency enforcement tools.

Record stable ownership and dependency boundaries here. Put tooling commands in
`.agents/rules/20-project-tools.md` and API or domain conventions in
`.agents/rules/21-project-rules.md`.

## What Belongs Here

- Top-level directories and what each one owns.
- Feature/module layout and naming conventions.
- Allowed and forbidden dependency directions.
- Shared locations for config, test helpers, assets, generated sources, and scripts.
- Ownership boundaries for UI, backend, data, infrastructure, or documentation.
- Real dependency enforcement mechanisms, if the project has them.

## What Does Not Belong Here

- Tool, runtime, build, test, or verification commands; use `20-project-tools.md`.
- Public API contracts, payload fields, domain vocabulary, or lint interpretation; use
  `21-project-rules.md`.
- General architecture advice that is not proven by the target repository.
- Project-specific facts in `wenyue/agents`; only target repositories should contain real local
  structure facts.

## Suggested Generated Content

- Top-level directories and what each one owns.
- Feature/module layout and naming conventions.
- Allowed and forbidden dependency directions.
- Shared locations for config, test helpers, assets, generated sources, and scripts.
- Ownership boundaries for UI, backend, data, infrastructure, or documentation.
- Real dependency enforcement mechanisms, if the project has them.
