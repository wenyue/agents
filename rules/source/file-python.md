# Python Guidelines

Strength: `Default`

Scope: Cross-project Python API, typing, data-boundary, failure, and resource contracts beyond
repository-owned formatting, linting, and type-checking policy.

## API And Type Contracts

- Keep annotation-only changes behavior-preserving. When typing exposes an ambiguous runtime case,
  resolve it from code, tests, or project policy instead of selecting new behavior.
- Annotate parameters and return values at public or reusable boundaries, including `-> None` for
  side-effect-only functions. Use syntax supported by the repository's declared Python range.
- Use reflection, monkey patching, and metaprogramming only when a runtime boundary is inherently
  dynamic, and isolate them at that boundary.
- Use `*args` and `**kwargs` only for genuinely open or forwarding contracts; otherwise name the
  parameters. Make parameters keyword-only when a signature has several independently optional
  values.
- Use `Protocol` for structural APIs, dataclasses or typed domain types for data shapes, and
  `Literal`, enums, or named types for finite states. Do not encode meaningful state combinations
  as boolean flags or an implicit `None` sentinel.
- Import typing helpers only when needed and use the generic syntax supported by the project.

## Local Values And Functions

- Declare variables near first use, annotate ambiguous or empty initial values, and keep nullable
  values on the narrowest practical path.
- Give each value name one role and one type rather than reusing it for different values.
- Keep functions focused and the main path shallow with early returns for invalid, absent, or no-op
  inputs.

## Data Boundaries

- Make collection mutation explicit in boundary types: accept read-only abstractions such as
  `Mapping`, `Sequence`, and `Iterable` when mutation is not part of the contract, and require a
  mutable type when callers must permit mutation.
- Keep `Any` at genuinely dynamic or untyped boundaries, then validate or narrow it before passing
  values into typed domain logic.
- Validate external mappings, serialized data, and untyped provider values before constructing
  typed domain values.
- Return one stable shape from each function. Use a named result, enum, or exception when outcomes
  have distinct meanings.

## Failures And Resources

- Raise precise domain or integration exceptions for expected failures and preserve useful cause
  context when translating errors across a boundary.
- Catch broad exceptions only at a boundary that owns the failure policy; re-raise or translate any
  failure it cannot safely contain.
- Use assertions for internal invariants rather than user input or recoverable runtime failures.
- Annotate coroutine functions with the value produced after awaiting; annotate async generator
  functions with an async iterator or generator type.
- Capture stable dependencies before asynchronous or callback boundaries; read changing state when
  its current value is required.
- Give every acquired resource one cleanup owner and make ownership transfer explicit. On every
  path that retains ownership, guarantee cleanup with a context manager, `try/finally`, or an owner
  lifecycle method.

## Typing Changes

- Before a supported behavior change in a branch made ambiguous by new typing, add and run a
  focused test that establishes its current behavior.
