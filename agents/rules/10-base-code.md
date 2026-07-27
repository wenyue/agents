# Code Design Goals

Strength: `Default`

Scope: Cross-language ownership, boundaries, clarity, state integrity, dependencies, abstractions,
and documentation.

## Ownership And APIs

- Give every behavior, state, invariant, and lifecycle one clear owner.
- Keep owner-local logic cohesive with its owner; move logic only when its reuse or boundary is real.
- Keep public interfaces minimal and aligned with stable product or domain capabilities.
- Meet test and call-site needs through the owning contract rather than widening APIs, moving
  owner-local logic, or adding indirection solely for convenience.

## Clarity And Abstraction

- Use names, types, and structure to make responsibilities, valid states, and the main decision path
  understandable locally.
- Keep side effects, failure modes, retries, fallbacks, and lifecycle transitions visible in the
  contract or control flow.
- Introduce an abstraction only when it represents a real concept, protects an invariant, or removes
  meaningful duplication while reducing maintenance cost.
- Avoid helpers, adapters, and generic layers that obscure ownership or serve only one trivial use.

## State And Dependencies

- Keep state mutation and lifecycle transitions predictable from creation through cleanup.
- Preserve valid dependency lifetimes across asynchronous work and callbacks.
- Give each unit only the capabilities it needs, with dependency direction and cross-layer
  boundaries explicit.
- Provide dependencies through visible owners and keep state placement consistent with that
  ownership.

## Documentation

- Use comments to preserve rationale, invariants, lifecycle constraints, external requirements, and
  non-obvious edge cases.
- Keep code narration, repeated names, and edit history out of comments; when design is unclear,
  improve the design instead of explaining around it.
