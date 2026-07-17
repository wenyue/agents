# Project Rules

Strength: `Default`

Scope: Generation contract for the target repository's project-specific behavioral contracts,
domain conventions, generated-source policy, and lifecycle invariants.

## Generation Contract

Produce a complete target-owned `Project Rules` rule from stable repository evidence. State the
project-specific behavior implementation and review agents must preserve, including verified
exceptions to broader rules; omit generic guidance and patterns that carry no enforceable meaning.

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
  historical residue, and personal preference as omissions rather than policy.

## Content

- State public API, route, event, payload, serialization, and compatibility constraints at the
  level needed to implement or review changes safely.
- State project-specific framework behavior and explain how project analyzers, custom lints, or
  formatter results affect implementation decisions.
- Name the semantic source for generated outputs and external schemas, the regeneration obligation,
  and the files or regions that must not be edited by hand.
- State domain vocabulary, naming, identifiers, prefixes, localization, and user-visible copy rules
  only when they constrain valid changes.
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
  how to invoke the generator.
- Exclude generic language style already covered by base rules, speculative architecture,
  undocumented preferences, and duplicated facts whose authoritative owner is elsewhere.
