# Project Rules

Strength: `Default`

Scope: Generation contract for project APIs, domain conventions, generated-file ownership, lint
interpretation, persistence, and lifecycle behavior.

## Generation Contract

Author the target rule from stable behavioral evidence. Record constraints that implementation and
review agents must preserve; omit conventions that are merely common practice or personal taste.

## Evidence

- Public APIs, routes, schemas, event definitions, serialization code, and compatibility tests.
- Framework configuration, established call sites, custom lints, and repository-specific analyzers.
- Generated-file headers, source schemas, generator configuration, and ownership documentation.
- Domain models, persistence and migration code, lifecycle owners, and concurrency boundaries.
- Existing naming, terminology, localization, and user-visible copy conventions with repeated use.

## Content

- Record public API, route, event, payload, and compatibility contracts.
- Record project-specific framework use and interpretations of formatter, analyzer, or lint output.
- Record semantic owners for generated files and external schemas, regeneration requirements, and
  files that must not be edited by hand.
- Record domain terms, naming constraints, prefixes, identifiers, and user-visible copy conventions.
- Record persistence, migration, state ownership, lifecycle, cancellation, and concurrency rules.
- State exceptions to base rules only when current project evidence establishes a real override.

## Boundaries

- Keep tool invocations, generation commands, runtimes, and verification capabilities in
  `20-project-tools.md`.
- Keep directory ownership, module layout, and dependency direction in `22-project-structure.md`.
- Exclude generic language style already covered by base rules and unsupported architectural advice.
- Do not duplicate the same generated-file fact here and in `20-project-tools.md`: this rule owns
  semantic ownership and edit boundaries; the tooling rule owns how the generator is invoked.
