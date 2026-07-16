# Dart And Flutter Guidelines

Strength: `Default`

Scope: Dart language shape and Flutter application architecture, state, lifecycle, UI, routing,
models, imports, and analysis defaults.

## Applicability

- Keep this rule reusable across Dart and Flutter applications.
- Do not put application names, project modules, custom lint packages, generated project paths, or
  project-only APIs in this rule.
- Put repository APIs, module boundaries, custom lints, build watchers, and application-specific
  helpers in project rules.

## Public Surface And Ownership

- Type public APIs explicitly. Let local variables infer types when their initializers are clear.
- Keep public boundaries narrow and product-driven. Do not expose helpers for tests or convenience.
- Put required domain inputs first and optional execution context, such as `BuildContext?`,
  `WidgetRef?`, or provider readers, last.
- Prefer named parameters for framework-facing helpers and functions with more than one optional
  input.
- Keep owner-local behavior as instance members by default.
- Use static members only for type-level behavior, static state, pre-instance work, or private
  construction support.
- Keep top-level functions for framework entry points, file-level declarations, shared algorithms,
  or logic with no clear owner.
- Put invariant-preserving creation or normalization on the value type that owns the invariant.

```dart
// BAD: `_isValid` exists only for `Parser` but is declared at file scope.
bool _isValid(String value) => value.isNotEmpty;

// GOOD: The helper stays with its owner.
class Parser {
  bool _isValid(String value) => value.isNotEmpty;
}
```

## Data Shape

- Keep generics concrete. Do not use raw generic types or `dynamic` unless the boundary requires it.
- Prefer immutable values. Use `final` by default and `const` for compile-time values.
- Use records only for small local tuple returns where a named type would not add clarity.
- Do not repeat record field types in destructuring when Dart can infer them.

```dart
// BAD: Destructuring repeats the record field types.
final (String title, int count) = readSummary();

// GOOD: The record shape already carries the field types.
final (title, count) = readSummary();
```

## Naming

- Use `PascalCase` for types, `camelCase` for members, `_privateName` for private declarations,
  `snake_case.dart` for files, and `kName` for constants.
- Name booleans as conditions, such as `isReady`, `hasFocus`, `canSubmit`, or `shouldRetry`.
- Name operations by their effects: `load`, `save`, `update`, `delete`, `remove`, or `clear`.
- Use `delete` for destroying owned persistent data.
- Use `remove` for taking an item out of a collection, relationship, selection, cache, or view.
- Use `clear` for emptying a container while keeping the container itself.

## Declaration Order

- Treat every section comment as a new member-ordering group.
- Within each group, order declarations as constructors, public static fields, private static
  fields, public instance fields, private instance fields, getters, setters, public static methods,
  private static methods, public instance methods, and private instance methods.
- Order public declaration modifiers as `protected`, `override`, no annotation, then
  `visibleForTesting`.

```dart
class SearchController {
  SearchController(this.query);

  static const maxResults = 50;
  static final _cache = <String, List<Result>>{};

  final String query;
  var _isLoading = false;

  bool get isLoading => _isLoading;

  static bool isCached(String query) => _cache.containsKey(query);

  Future<List<Result>> search() async => _readResults();

  Future<List<Result>> _readResults() async => _cache[query] ?? const [];
}
```

## Section Comments

- Use section comments only for top-level file regions or class and member groups.
- Do not use section comments as declaration documentation.
- Use exactly 20 `/` characters for each border line: `////////////////////`.
- Leave one blank line between a section comment and the first declaration in that section.

```dart
////////////////////
/// Public actions.
////////////////////

Future<void> refresh() async {
  await repository.refresh();
}
```

## Documentation And Comments

- Use comments for intent, invariants, lifecycle, constraints, and non-obvious failure handling.
- Do not restate the code.
- Use `///` for declaration documentation and file headers.
- Use `//` inside function bodies and for inline notes, TODOs, FIXMEs, and ignore comments.
- Start prose comments with an uppercase letter and end them with `.`, `?`, or `!`.
- Exempt short inline comments from punctuation when they contain no more than 16 characters and
  three words.
- Use `TODO(name): ...` and `FIXME(name): ...` with a concrete action or problem.
- Use phase comments only inside long, multi-step functions.

```dart
/// Loads the first page and preserves existing content while refreshing.
Future<void> refresh() async {
  // Keep stale content visible until the new page arrives.
  final previous = state.valueOrNull;

  // TODO(owner): Remove the fallback after the migration completes.
  state = await AsyncValue.guard(() => repository.load(previous?.cursor));
}
```

## State Management

- Use Riverpod for shared, cross-widget, and feature-level state.
- Use `@riverpod` with generated providers when generation is already part of the application.
- Name providers with the `Provider` suffix.
- Use `ref.watch` in build methods, `ref.read` in event handlers, and `ref.listen` for side effects.
- Use `select` with `ref.watch` or `ref.listen` when only one part of a state object matters.
- Do not combine `ref.read` with `select`.
- Use `keepAlive: true` for services and repositories whose lifetime must not depend on one screen.
- Prefer widget-local state for simple local concerns that do not need provider identity.

```dart
final title = ref.watch(articleProvider.select((article) => article.title));

button.onPressed = () {
  ref.read(articleProvider.notifier).refresh();
};
```

## Provider Lifecycle

- Treat provider `build()` as reactive; it may run again whenever dependencies change.
- Register every `onDispose` callback immediately after creating its disposable resource.
- Register disposal before any `await`.
- Expect `onDispose` to run before rebuild and again when the provider is fully disposed.
- Do not assign `state`, read providers, or touch `Ref` inside `onDispose`.

```dart
@riverpod
class FeedSubscription extends _$FeedSubscription {
  @override
  Future<void> build() async {
    final subscription = feedStream.listen(_handleEvent);
    ref.onDispose(subscription.cancel);

    await _loadInitialPage();
  }
}
```

## Async Boundaries

- Add mounted checks only for lifecycle-bound objects used after an `await`.
- In widgets, one mounted check covers objects tied to the same widget lifecycle.
- In notifiers and providers, check `ref.mounted` before assigning `state`, reading providers again,
  or branching on provider-owned state after an `await`.
- Resolve stable dependencies before the async gap when they are needed later.
- Read changing provider state after the async gap and mounted check.

```dart
Future<void> save() async {
  final repository = ref.read(settingsRepositoryProvider);

  await repository.saveDraft();
  if (!ref.mounted) {
    return;
  }

  final current = ref.read(settingsProvider);
  state = AsyncData(current.markSaved());
}
```

## Widgets

- Prefer `StatelessWidget` or a small function for simple presentational UI.
- Prefer `HookWidget` and `HookConsumerWidget` when local controller lifecycle is required.
- Use `StatefulHookWidget` or `StatefulHookConsumerWidget` only when `initState`, `dispose`, or
  inherited-widget integration is required.
- Prefer `const` constructors and stable child widgets.
- Use `Theme.of(context)` before introducing application-specific theme extensions.
- Do not hardcode colors in reusable widgets.

## Routing

- Use `go_router` for Flutter navigation.
- Prefer generated typed routes when the application already uses generated routes.
- Use router APIs for pages.
- Use `Navigator.of(context).pop(result)` for dialogs, sheets, and overlays owned by Navigator.

## Data Models

- Use `json_serializable` and `json_annotation` for JSON boundaries.
- Use Freezed for immutable data models that require equality, unions, or `copyWith`.
- Keep persistence models separate from domain models when storage details differ from application
  logic.

## Imports

- Order imports as `dart:`, then `package:`, then relative imports.
- Prefer package imports across package or feature boundaries.
- Prefer relative imports within one package or tightly scoped feature boundary.

## Analysis

- Write code, identifiers, and comments in English.
- Keep lines at or below 100 characters.
- Prefer clear names and direct control flow over clever shorthand.
- Avoid `dynamic`, casts, and nullable escape hatches when a precise type or early return works.
- Use single quotes by default.
- Use trailing commas in multiline literals, parameter lists, and argument lists.
- Use braces for every control-flow body; do not place a body on the same line as its condition.
- Wrap code-like placeholders in documentation comments with backticks.
- Do not use `print`; use the application's logging mechanism.
- Do not use deprecated APIs.
- Use injectable or testable time sources when current time affects behavior.

```dart
// BAD: The branch body is hidden on the same line.
if (isReady) submit();

// GOOD: Control flow keeps a stable block shape.
if (isReady) {
  submit();
}
```
