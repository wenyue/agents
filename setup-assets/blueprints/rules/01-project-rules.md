# Project Rules

Strength: `Default`

Scope: Generation contract for the target repository's project-specific behavioral contracts,
domain conventions, generated-source policy, and lifecycle invariants.

## Generation Frame

Produce a complete target-owned `Project Rules` rule from stable repository evidence. Include only
project-specific behavior an agent must know before implementation because ordinary tooling does
not reliably detect violations, does not make the required correction clear, or detects them only
after broad or costly repair is required. Omit generic guidance and mechanical constraints that
tooling reliably detects and agents can repair locally at low cost.

The generated artifact owns repository-specific policy, not discovery or execution procedure.
Express every included obligation through its scope, applicable predicate, required outcome,
exceptions, precedence, and ownership boundary. Choose the final organization from the target
evidence; do not copy this contract's headings or evidence order as a target outline.

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
- Resolve conflicts in favor of the narrowest authoritative source.

## Content

- State public API, route, event, payload, serialization, and compatibility constraints when
  violating them crosses a consumer or compatibility boundary that tooling does not reliably
  protect.
- Name the semantic source for generated outputs and external schemas, the regeneration obligation,
  and the files or regions whose changes must come through that source. Let `Project Tools` own
  generator discovery and invocation.
- State domain vocabulary, naming, identifiers, prefixes, localization, and user-visible copy rules
  only when they constrain valid changes and tooling does not reliably identify a local, low-cost
  correction.
- State persistence compatibility, migrations, state ownership, lifecycle transitions,
  cancellation, concurrency, and cleanup invariants where the repository defines them.
- Express each verified exception to a broader rule with its exact scope and condition, and preserve
  the broader policy outside that exception.

## Boundaries

- Keep runtimes, tool installation, command invocation, generator commands, services, and
  verification capabilities in `Project Tools`.
- Keep directory responsibility, file placement, module layout, and dependency direction in
  `Project Structure`.

## Validation and Handoff

Review every generated obligation against an authoritative target source and confirm that a Rule,
rather than tooling, documentation, or a Skill, is its narrowest reliable owner. Stop on unresolved
ownership, conflicting authoritative evidence, or an exception whose exact predicate cannot be
established.

Hand off the complete target-owned Rule with its supporting evidence and unresolved omissions. Do
not hand off unsupported guidance as policy.
