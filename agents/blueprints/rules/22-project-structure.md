# Project Structure

Strength: `Advisory`

Scope: Generation contract for the target repository's placement boundaries, module ownership,
dependency direction, and shared infrastructure locations.

## Generation Contract

Produce a complete target-owned `Project Structure` rule from observed repository organization and
verified dependency boundaries. Include only locations and relationships that help an agent place
work correctly or avoid an invalid dependency; do not narrate the directory tree.

## Evidence

- Inspect repository and workspace trees together with package manifests, module declarations,
  build targets, and representative imports.
- Trace feature code, shared libraries, configuration, tests, assets, generated sources, scripts,
  infrastructure, and documentation to the responsibility each location actually serves.
- Inspect dependency checks, lint rules, package boundaries, visibility rules, and composition
  roots before declaring an allowed or forbidden direction.
- Use ownership files and repeated placement only when they establish a stable boundary. A
  self-explanatory directory name alone is not evidence of a policy.
- Distinguish enforced boundaries from advisory placement patterns and reflect that distinction in
  the wording.

## Content

- Describe only top-level areas, packages, modules, and composition roots whose responsibility is
  not obvious or whose boundary affects future placement.
- State where new feature code, shared code, tests, assets, configuration, scripts, generated
  sources, infrastructure, and documentation belong when the repository establishes those owners.
- State allowed and forbidden dependency directions, the scope to which they apply, and the
  architectural boundary they protect.
- Distinguish reusable shared locations from feature-owned helpers so that convenience does not
  erase ownership.
- Name real enforcement mechanisms and authoritative configurations, but leave their invocation to
  `Project Tools`.
- Keep the final map selective and responsibility-ordered. Omit locations that add no placement,
  ownership, or dependency decision.

## Boundaries

- Keep toolchains, commands, services, build and test invocation, and verification capabilities in
  `Project Tools`.
- Keep API contracts, payload semantics, domain vocabulary, generated-file edit policy, lifecycle
  behavior, and lint interpretation in `Project Rules`.
- Exclude generic architecture advice, speculative future structure, temporary layout, and
  directory-by-directory inventory.
- Do not duplicate an ownership or dependency statement across sections or rules. When another
  artifact is authoritative, reference that owner instead of restating its contents.
