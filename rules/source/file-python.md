# Python Guidelines

Strength: `Default`

Scope: Python API shape, typing, data modeling, imports, errors, asynchronous resources, tests, and
tool ownership.

## Style And Types

- Write explicit, maintainable Python whose data shapes and control flow are easy to review.
- Keep behavior with the owner of its state or invariant; prefer direct code over reflection,
  monkey patching, clever metaprogramming, or broad utilities for one call site.
- Use annotations to clarify contracts without turning a type-only change into a hidden behavior
  refactor.
- Annotate public and reusable boundaries and make return types explicit, including `-> None` for
  side-effect-only functions.
- Keep annotation syntax compatible with the repository's declared Python range and nearby style.
- Express optional values consistently with nearby code and avoid implicit `None` sentinels when a
  named state makes the contract clearer.
- Use concrete collection types at boundaries and read-only abstractions such as `Mapping`,
  `Sequence`, and `Iterable` when mutation is not part of the contract.
- Keep `Any` at genuine dynamic boundaries and narrow it before passing values into domain logic.
- Prefer `Protocol`, dataclasses, enums, literals, and typed domain models when they make supported
  states and data shapes explicit.

## Functions And Data

- Declare variables near first use, annotate ambiguous or empty initial values, and keep nullable
  values on the narrowest practical path.
- Use one precise variable name per role instead of reusing a name for values of different types.
- Keep signatures explicit; reserve `*args` and `**kwargs` for framework or documented forwarding
  boundaries.
- Prefer keyword-only parameters for several optional values, and replace meaningful boolean flag
  combinations with an options type, enum, or separate operation.
- Keep functions focused and the main path shallow with early returns for invalid, absent, or no-op
  inputs.
- Return one stable shape from each function; use a named result, dataclass, enum, or exception when
  outcomes have distinct meanings.
- Validate external mappings, serialized data, and untyped provider values at the boundary before
  constructing typed domain values.

## Imports And Errors

- Follow the repository's import boundaries and group standard-library, third-party, and
  first-party imports according to local style.
- Import typing helpers only when needed and use the generic syntax supported by the project.
- Raise precise domain or integration exceptions for expected failures and preserve useful cause
  context when translating errors across a boundary.
- Catch broad exceptions only at a boundary that can intentionally and safely contain the failure.
- Use assertions for internal invariants rather than user input or recoverable runtime failures.

## Async And Resources

- Annotate async functions with the value produced after awaiting rather than a coroutine wrapper.
- Make resource ownership and cleanup explicit with context managers, `try/finally`, or owner
  lifecycle methods.
- Resolve stable dependencies before asynchronous or callback boundaries; read changing state at
  the point where its current value is required.

## Tests And Tooling

- Keep reusable test helpers and fixtures explicit about their input and result shapes.
- When new annotations expose an ambiguous branch, add focused tests before changing behavior.
- Let the repository formatter, linter, and type checker own layout, import formatting, suppression
  syntax, and configured thresholds.
- Introduce or replace Python tooling only when the task explicitly includes that project-level
  change.
