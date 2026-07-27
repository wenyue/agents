# Go Guidelines

Strength: `Default`

Scope: Go package ownership, API shape, errors, context, concurrency, and logging beyond configured
tooling.

## Code Shape

- Keep code direct, scopes narrow, and the success path shallow.
- Keep public APIs product-driven; meet test needs without exporting names, adding interfaces, or
  introducing seams solely for tests or speculative reuse.
- Extract a helper or private type only when it names a real concept, clarifies data flow, or removes
  meaningful complexity.
- Initialize explicitly from constructors, `main`, or package-owned setup functions instead of
  adding `init()` functions.

## Errors

- Check every returned error and bind it to a named value rather than the blank identifier.
- Use `value, ok := x.(T)` when a type assertion can fail; use `x.(T)` only when a visible invariant
  guarantees the type.
- Wrap errors that cross package boundaries with useful context and `%w`; inspect them with
  `errors.Is` or `errors.As`.
- Prefer existing sentinel errors before creating dynamic errors.
- Avoid `panic`, `logger.Fatal`, and `os.Exit` outside top-level startup paths where continuing is
  impossible.

## Context And Concurrency

- Pass `context.Context` first where standard Go patterns apply and honor cancellation in loops and
  long-running work.
- Guard shared mutable state with the owning package's synchronization primitive.
- Keep package globals deliberate, stable, and initialized in one place.

## Logging

- Use the logger conventions of the owning package for runtime output instead of introducing
  `fmt.Print*` or the standard `log` package.
- Make log messages name the operation and include values needed to diagnose failure.

## Tool Ownership

- Let the repository formatter and linter own layout, naming, limits, imports, comments, and
  suppression syntax.
- Change configured thresholds in their owning configuration rather than duplicating them here.
