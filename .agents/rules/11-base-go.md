# Go Guidelines

Strength: `Default`

Scope: Go formatting, code shape, naming, errors, comments, concurrency, collections, and logging
defaults.

## Code Shape

- Write compact, polished, readable Go. Express the idea directly, keep scopes narrow, avoid
  repeated branches, and extract only when a helper names a real concept or removes meaningful
  complexity.
- Prefer early returns for invalid input, cancellation, and error paths so the success path stays
  shallow.
- Keep public APIs product-driven. Do not export names, add interfaces, or introduce seams only for
  tests or speculative reuse.
- Use small local structs or private helper types when they clarify data flow. Do not introduce broad
  package abstractions for one call site.
- Do not add `init()` functions. Initialize explicitly from constructors, `main`, or package-owned
  setup functions.

## Formatting And Limits

- Format with `golangci-lint-v2 fmt`. Do not hand-tune import grouping or wrapping against `gci`,
  `gofmt`, `gofumpt`, `goimports`, or `golines`.
- Keep the blank lines required by `wsl_v5`, `nlreturn`, and `whitespace`; readability means clear
  blocks, not dense walls of code.
- Keep lines within 100 characters and let `golines` wrap long calls and string concatenations.
- Group imports as standard library, third-party, then local module. Leave one blank line between
  groups and let the formatter sort them.
- Keep functions below `funlen` limits of 80 lines and 50 statements, and below `cyclop` 16,
  `gocyclo` 20, and `nestif` 8.
- Extract helpers when they flatten control flow, remove duplication, or name a domain step. Inline
  tiny one-use helpers when they obscure straightforward code.

## Naming

- Use `PascalCase` for exported identifiers and `camelCase` for unexported identifiers.
- Keep acronyms consistent: `ID`, `CID`, `IPFS`, `IPNS`, `DHT`, `URL`, `UDP`, and `TCP`.
- Name sentinel errors `ErrX` and end error type names with `Error`.
- Use short names only in tight scopes or for lint-allowed names: `err`, `ok`, `id`, `i`, `j`, `k`,
  `v`, `db`, and `to`. Name wider-scope values for their roles.
- Name booleans as predicates when practical, such as `ok`, `enabled`, `hasRoute`, or
  `shouldRetry`.

## Errors

- Check every returned error, including blank assignments and type assertions.
- Wrap errors that cross package boundaries with useful context and `%w`; inspect them with
  `errors.Is` or `errors.As`.
- Prefer existing sentinel errors before creating dynamic errors.
- Use the comma-ok form for type assertions. Do not use bare `x.(T)` in production code.
- Avoid `panic`, `logger.Fatal`, and `os.Exit` outside top-level startup paths where continuing is
  impossible.

## Comments

- Write comments for intent, invariants, concurrency, retry behavior, security trade-offs, or
  non-obvious domain rules. Do not narrate the following statement.
- Add doc comments to exported declarations. Start each comment with the identifier and end it with
  punctuation.
- Use short phase comments inside long, multi-step functions when they clarify the scan path.
- Write comments in English, capitalize them, and punctuate them so `godot`, `revive`, and
  `misspell` remain quiet.
- Use `TODO(name): ...` and `FIXME(name): ...` only with a concrete follow-up action.
- Add a concrete reason to every `//nolint:<linter>`. Prefer code that satisfies the lint.

## Context And Concurrency

- Pass `context.Context` first where standard Go patterns apply and honor cancellation in loops and
  long-running work.
- Do not create nested contexts inside loops or closures unless the code documents why the lifecycle
  is correct.
- Guard shared mutable state with the owning package's synchronization primitive.
- Keep package globals deliberate, stable, and initialized in one place.

## Data And Collections

- Use `const` for fixed values and named constants for tunable numbers. Do not put magic numbers in
  control flow.
- Preallocate slices and maps when their size is known or cheaply available.
- Deduplicate with `map[T]struct{}` or a small helper when it makes order and uniqueness explicit.
- Use struct tags consistently and let `tagalign` and `tagliatelle` determine formatting and naming.

## Logging

- Use the logger conventions of the owning package. Do not introduce `fmt.Print*` or the standard
  `log` package for runtime output.
- Make log messages name the operation and include values needed to diagnose failure.
- Prefer formatted logger methods for messages that include values.
