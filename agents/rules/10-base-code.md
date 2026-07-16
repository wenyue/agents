# Code Design Goals

Strength: `Default`

Scope: Cross-language quality goals for ownership, boundaries, clarity, state integrity,
dependencies, abstractions, and documentation.

## Ownership And Boundaries

- Every behavior, state, invariant, and lifecycle has a clear owner.
- Single-owner logic remains cohesive with its owner, while shared logic has ownership that matches
  its actual reuse.
- Public interfaces express stable product or domain capabilities while remaining minimal and
  encapsulated.
- Do not add public APIs or move single-owner logic to shared or top-level locations solely for
  testing or call-site convenience.

## Clarity And Abstraction

- Names communicate domain roles, observable behavior, state, and conditions.
- Each code unit has a cohesive responsibility and a main decision path that can be understood
  locally.
- Abstractions represent real concepts, protect invariants, or remove meaningful duplication while
  reducing the cost of understanding and change.
- Side effects, failure modes, retries, and fallback behavior remain visible in names, contracts, or
  control flow.
- Do not add indirection, generic helpers, or abstractions without a clear concept or maintenance
  benefit.

## Data And State Integrity

- Data structures express domain meaning and valid states without ambiguity.
- State changes and lifecycle transitions have clear ownership and predictable creation, update,
  cancellation, and release behavior.
- Async and callback behavior preserves valid dependency lifetimes and distinguishes stable
  dependencies from changing state.
- Do not distribute state mutation or lifecycle ownership in ways that make valid state or
  responsibility difficult to determine.

## Dependencies And Architecture

- Each code unit receives only the capabilities it needs, with dependency direction kept explicit.
- Layer interactions respect domain boundaries, and every cross-layer dependency remains
  intentional and visible.
- Public APIs and adapters correspond to real product, domain, or external boundaries and provide a
  clear maintenance benefit.
- Do not pull dependencies from hidden globals or add adapters where no real boundary exists.

## Documentation

- Names, types, and structure communicate behavior directly.
- Comments preserve rationale, invariants, lifecycle constraints, external requirements, and edge
  cases that code cannot express clearly.
- Do not use comments to narrate code, record edit history, repeat names, or compensate for unclear
  design.
