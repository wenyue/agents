# Dart And Flutter Guidelines

Strength: `Default`

Scope: Dart and Flutter ownership, state, lifecycle, UI, routing, models, and analysis boundaries.

## Public Surface And Ownership

- Keep public APIs narrow and product-driven; do not expose helpers or move owner-local behavior for
  tests or convenience.
- Keep domain invariants with the value or service that owns them.
- Keep owner-local behavior as instance members by default.
- Keep top-level functions for framework entry points, file-level declarations, shared algorithms,
  or logic with no clear owner.

## Data Shape

- Prefer immutable, precisely typed data and represent meaningful states with named types.
- Use records only for small local tuple returns where a named type would not add clarity.

## State Management

- Use Riverpod for shared, feature-level, and cross-widget state; keep simple local concerns in the
  widget that owns them.
- Use generated providers when generation is already part of the application.
- Watch reactive state during build, read it from event handlers, and listen only for side effects.
- Use `select` with `ref.watch` or `ref.listen` when only one part of a state object matters.
- Use `keepAlive: true` for services and repositories whose lifetime must not depend on one screen.

## Provider Lifecycle

- Treat provider `build()` as reactive; it may run again whenever dependencies change.
- Register every `onDispose` callback immediately after creating its disposable resource.
- Register disposal before any `await`.
- Do not assign `state`, read providers, or touch `Ref` inside `onDispose`.

## Async Boundaries

- After an asynchronous gap, verify the owning widget or provider is still mounted before using its
  lifecycle-bound state.
- Resolve stable dependencies before the async gap when they are needed later.
- Read changing provider state after the async gap and mounted check.

## Widgets

- Prefer the simplest widget type that owns the required lifecycle.
- Keep presentational widgets small and stable; introduce controller lifecycle only when the
  interaction requires it.
- Use the application's established theme and UI abstractions before adding alternatives.

## Routing

- Use the application's established router and generated route abstractions for pages.
- Use `Navigator.of(context).pop(result)` for dialogs, sheets, and overlays owned by Navigator.

## Data Models

- Use the application's established serialization and immutable-model abstractions.
- Keep persistence models separate from domain models when storage details differ from application
  logic.

## Analysis

- Follow the target repository's formatter, analyzer, and lint configuration for mechanical style,
  naming, imports, types, comments, and deprecations.
- Write code, identifiers, and comments in English.
- Use injectable or testable time sources when current time affects behavior.
