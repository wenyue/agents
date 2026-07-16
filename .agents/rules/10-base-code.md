# Code Design

Strength: `Default`

Scope: Cross-language production-code ownership, public boundaries, naming, extraction, state,
dependencies, control flow, and comments.

## Ownership And Public Boundaries

- Keep behavior near the state, invariant, or module that owns it. A helper used by one class,
  service, model, or state owner belongs to that owner by default; being pure, stateless, or easier
  to test is not enough reason to make it top-level.
- Use top-level or free functions only when the operation is independent of one owner, such as
  shared domain logic, reusable normalization or parsing, ownerless factories, framework entry
  points, file-level declarations, or helpers used by multiple owners.
- Keep public boundaries product-driven. Do not add public APIs, test-only seams, extracted helpers,
  or adapters solely for test or call-site convenience.

## Naming

- Name code by its domain role and observable behavior, not its implementation detail.
- Use precise verbs for actions and state transitions. Avoid vague names such as `handle`,
  `process`, `manager`, or `utils` unless the surrounding domain makes the role specific.
- Name booleans for the condition they test, not the action a caller takes.

## Extraction

- Prefer direct, readable caller code over helper indirection.
- Extract a helper when it names a real concept, hides meaningful complexity, protects an invariant,
  or removes real duplication.
- Inline small, single-use helpers when their names add no information.
- Split long workflows at decision or resource boundaries, not at arbitrary line counts. A longer
  function with one clear sequence is better than scattered steps that must be read together.
- Prefer functions under roughly 80 lines, but treat this as a readability guideline. Do not
  extract helpers only to meet the line count.

## Data And State

- Prefer immutable values and explicit data shapes. Replace loose maps, raw tuples, flag clusters,
  and magic parameters with named types or options objects when they clarify the contract.
- Keep mutable state behind one owner. Make lifecycle, cancellation, and release paths explicit at
  that owner instead of distributing them across unrelated helpers.
- Cache stable dependencies before async or callback boundaries when ownership may become fragile;
  read changing state at the point of use.

## Dependencies

- Pass the narrow dependency a unit needs instead of a broad owner, service, or global context.
- Keep dependency direction visible from the caller. Do not let helpers reach across layers or pull
  dependencies from hidden globals when callers can supply them explicitly.
- Introduce adapters at real external boundaries, not between code that already shares one domain
  model.

## Control Flow

- Use early returns for invalid, empty, or completed cases so the main path stays visible.
- Handle expected failure locally with a typed result, status, or no-op return. Reserve exceptions
  and fatal paths for unexpected failures.
- Do not hide retries, fallback selection, or persistence side effects behind names that imply a
  simple getter or pure transform.

## Comments

- Add comments only when they preserve context that code cannot express clearly: intent,
  invariants, lifecycle constraints, external requirements, edge-case reasoning, non-obvious
  failure handling, or why an obvious alternative is wrong.
- Do not narrate the code, describe the edit, duplicate names, or compensate for structure that
  clearer code can express.
- Prefer names and small data types over comments that explain parameter order, boolean flags, or
  hidden ownership.
