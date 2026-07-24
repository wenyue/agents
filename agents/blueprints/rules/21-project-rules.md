# Project Rules

Strength: `Default`

Scope: Generation contract for the target repository's project-specific behavioral contracts,
domain conventions, generated-source policy, and lifecycle invariants.

## Generation Contract

Produce a complete target-owned `Project Rules` rule from stable repository evidence. Include only
project-specific behavior an agent must know before implementation because ordinary tooling does
not reliably detect violations, does not make the required correction clear, or detects them only
after broad or costly repair is required. Preserve verified exceptions to broader rules; omit
generic guidance and mechanical constraints that tooling reliably detects and agents can repair
locally at low cost.

## Evidence

- Inspect public APIs, routes, schemas, events, serialization, compatibility tests, and real call
  sites to identify behavior that consumers rely on.
- Inspect framework configuration, project analyzers, custom lints, and focused tests before
  treating a repeated pattern as a requirement or an exception to a base rule.
- Trace generated outputs to their source schemas, generator configuration, headers, and
  regeneration owner.
- Inspect domain models, persistence and migration code, state and lifecycle owners, cancellation,
  concurrency, and cleanup behavior.
- Inspect naming, terminology, localization sources, and user-visible copy where consistent usage
  or enforcement establishes a real project contract.
- Resolve conflicts in favor of the narrowest authoritative source. Treat unsupported convention,
  historical residue, personal preference, and lint detail with an obvious low-cost correction as
  omissions rather than policy.

## Content

- State public API, route, event, payload, serialization, and compatibility constraints when
  violating them crosses a consumer or compatibility boundary that tooling does not reliably
  protect.
- Let the owning formatter, analyzer, or linter describe ordinary mechanical violations whose
  diagnostics identify a local, low-cost correction. Mention a diagnostic only when its meaning
  affects architecture, ownership, accepted exceptions, or another non-local decision.
- Name the semantic source for generated outputs and external schemas, the regeneration obligation,
  and the files or regions that must not be edited by hand.
- State domain vocabulary, naming, identifiers, prefixes, localization, and user-visible copy rules
  only when they constrain valid changes and tooling does not reliably identify a local, low-cost
  correction.
- State persistence compatibility, migrations, state ownership, lifecycle transitions,
  cancellation, concurrency, and cleanup invariants where the repository defines them.
- Express each verified exception to a broader rule with its exact scope and condition. Do not
  silently weaken the broader policy outside that exception.
- Organize the final rule by owned behavior, not by the order in which evidence was discovered.

## Boundaries

- Keep runtimes, tool installation, command invocation, generator commands, services, and
  verification capabilities in `Project Tools`.
- Keep directory responsibility, file placement, module layout, and dependency direction in
  `Project Structure`.
- For generated outputs, this rule owns semantic source and edit boundaries; `Project Tools` owns
  how to invoke or discover the generator.
- Exclude generic language style already covered by base rules, speculative architecture,
  undocumented preferences, and duplicated facts whose authoritative owner is elsewhere.
