# C++ Guidelines

Strength: `Default`

Scope: C++ ownership, interfaces, failure contracts, and concurrency beyond configured tooling.

## Interfaces And Ownership

- Keep public interfaces narrow and preserve existing ABI, FFI, and platform boundaries.
- Keep behavior with its owner and introduce an options type only when related inputs form a stable
  concept.
- Prefer RAII and value semantics.
- Prefer smart pointers over raw owning pointers.

## Failure And Concurrency

- Make expected failure part of the return contract; reserve exceptions for failures the surrounding
  boundary treats as exceptional.
- Synchronize shared mutable state through one clear owner and the narrowest suitable primitive.
- Preserve cleanup, cancellation, and thread-affinity requirements across native callbacks.

## Tool Ownership

- Let the repository formatter, compiler, and static-analysis configuration own mechanical style and
  naming.
- Test behavior boundaries where native ownership, failure handling, or ABI behavior can regress.
