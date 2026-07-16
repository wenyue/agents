# C++ Guidelines

Strength: `Default`

Scope: C++ language, naming, function shape, data ownership, errors, testing, standard-library use,
and concurrency defaults.

## Language And Documentation

- Write code and documentation in English.
- Use explicit types and follow the One Definition Rule.
- Use Doxygen documentation for public APIs.

## Naming

- Use `PascalCase` for classes, `camelCase` for variables and functions, `ALL_CAPS` for constants
  and macros, and `snake_case` for files.
- Start function names with verbs.
- Name booleans as predicates such as `isX`, `hasX`, or `canX`.
- Use named constants instead of magic numbers.

## Functions

- Keep each function focused on one purpose and typically under 20 lines.
- Use early returns to keep the main path flat.
- Replace clusters of flag or mode parameters with a structured options type.

```cpp
// BAD: Deep nesting and several flag parameters obscure the operation.
void process(int x, bool flag, bool verbose, int mode) {
  if (flag) {
    if (verbose) {
      /* ... */
    }
  }
}

// GOOD: Structured options and early returns keep the main path visible.
struct ProcessOpts {
  bool flag;
  bool verbose;
  int mode;
};

void process(int x, const ProcessOpts& opts) {
  if (!opts.flag) {
    return;
  }
  if (!opts.verbose) {
    return;
  }
  /* ... */
}
```

## Data And Classes

- Use `const` for values that do not change and `constexpr` for compile-time constants.
- Use `std::optional` for nullable values.
- Follow SOLID principles and prefer composition over inheritance.
- Keep classes under roughly 200 lines.

## Resource Safety

- Follow the Rule of Zero or Rule of Five as ownership requires.
- Prefer smart pointers over raw owning pointers.
- Use RAII for every resource.

## Errors

- Use exceptions for truly unexpected failures.
- Use `std::optional`, `std::expected`, or error codes for expected failure modes.

## Testing

- Structure tests as Arrange, Act, Assert.
- Add one unit test for each public function.
- Add integration tests at module boundaries.

## Standard Library And Concurrency

- Prefer standard types and containers, including `std::string`, `std::vector`, `std::map`,
  `std::optional`, `std::variant`, `std::filesystem`, and `std::chrono`.
- Prefer `std::vector` over C-style arrays.
- Use `std::thread`, `std::mutex`, and `std::lock_guard` for concurrency.
- Use `std::atomic` for lock-free shared state.
