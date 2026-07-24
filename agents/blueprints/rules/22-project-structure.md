# Project Structure

Strength: `Advisory`

Scope: Generation contract for the target repository's placement boundaries, module ownership,
dependency direction, and shared infrastructure locations.

## Generation Contract

Produce a complete target-owned `Project Structure` rule from observed repository organization and
verified dependency boundaries. Include the smallest responsibility map that lets an agent place
work correctly, find the right owner, and avoid invalid dependencies; do not narrate the directory
tree.

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

- Describe top-level application modules, other areas, packages, and composition roots only when
  their ownership is non-obvious or selecting the wrong owner would affect placement or dependency
  decisions. Give each selected entry one concise ownership description; do not enumerate internal
  directories or APIs.
- State where new feature code, shared code, tests, assets, configuration, scripts, generated
  sources, infrastructure, and documentation belong when the repository establishes those owners.
- State allowed and forbidden dependency directions, their scope, and the architectural boundary
  they protect. Reference the authoritative configuration for exact tiers or exclusions instead of
  duplicating drift-prone values.
- Distinguish reusable shared locations from feature-owned helpers so that convenience does not
  erase ownership.
- Name real enforcement mechanisms and authoritative configurations, but leave their invocation to
  `Project Tools`.
- Keep the final map concise and responsibility-ordered. Omit locations that add no placement,
  ownership, discovery, or dependency decision.

## Boundaries

- Keep toolchains, commands, services, build and test invocation, and verification capabilities in
  `Project Tools`.
- Keep API contracts, payload semantics, domain vocabulary, generated-file edit policy, lifecycle
  behavior, and lint interpretation in `Project Rules`.
- Exclude generic architecture advice, speculative future structure, temporary layout, and
  directory-by-directory inventory.
- Do not duplicate an ownership or dependency statement across sections or rules. When another
  artifact is authoritative, reference that owner instead of restating its contents.
