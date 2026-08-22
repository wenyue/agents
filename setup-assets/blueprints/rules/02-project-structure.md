# Project Structure

Strength: `Advisory`

Scope: Generation contract for the target repository's evidence-based placement recommendations.

## Generation Frame

Author `.agents/rules/02-project-structure.md` as a project-local Ordinary Advisory Rule. It answers
only where a change should live and how plausible architectural placements rank after the target's
Mandatory Project Contracts have been applied. Give every output an evidence-conditioned
recommendation such as `prefer`, `favors`, `points toward`, or `ranks higher`, never a validity,
ownership, delivery, or dependency constraint.

Write only that target during this authoring pass. Leave separately owned supporting changes to
their active owners and identify them in the handoff when the generated Rule depends on them.

Establish the target Rule's persistent placement scope and applicability,
evidence-to-recommendation mappings, supported exceptions, and ownership boundaries from current
repository evidence.

## Evidence and Recommendations

- Trace direct calls and imports, registry and schema relationships, generator flows, runtime entry
  points, and behavioral tests. These signals outrank directory names, co-location, naming, and
  plugin or package boundaries by themselves.
- Identify the narrowest established owner that decides the behavior or policy, the consumers that
  use it, and the tests that observe it. Favor local placement when one consumer keeps the decision,
  its realizing mechanism, and its observing tests cohesive with little knowledge leakage. Favor a
  shared seam when multiple independent consumers need the same stable decision or local copies
  repeat cross-owner coupling.
- Trace representational translation to the boundary that adapts upstream intent for a consumer,
  host, target, or rendered form. Favor that consumer-facing boundary when it projects upstream
  intent rather than decides the upstream behavior.
- Reconstruct conceptual flow from authoring intent through selection or transformation, runtime
  behavior, delivery, and observation when those stages exist. Repeated downstream policy or stable
  cross-target mechanics favor the earliest established owner with enough context; target-specific
  behavior favors locality when moving upstream would erase decision-making context.
- Add a target-local exception beside the broader recommendation only when direct evidence
  identifies its scope, selecting predicate, and reason local placement ranks higher.

## Ownership Boundaries

Mandatory Project Contracts own hard requirements for canonical and generated sources,
installation, delivery, dependencies, exposure, fixtures, and other validity boundaries. Reference
the applicable contract rather than restating its constraint as structure guidance. Keep command
execution, authoring workflow, and validation procedure with their active owners.

Exclude directory inventories, package tours, generic layering advice, speculative future
architecture, and unsupported placement claims. Mention a location only when it changes a real
placement comparison.

## Ambiguity, Validation, and Handoff

Stop before writing when current evidence still permits materially different Rule ownership,
strength, scope, precedence, or evidence-to-recommendation mappings. Report the exact unresolved
choice and the repository evidence needed to select it.

On an authoring or validation failure, leave the target unadopted, retain its last coherent state,
and report the failure and unverified obligations. A coincident material ambiguity remains
unresolved; the failure does not select a policy outcome.

Validate that every generated recommendation traces to authoritative target evidence and answers
a placement comparison without duplicating a Mandatory Project Contract.
Hand the real target to the current Ordinary Artifact route for target-owned machine validation,
Semantic Review, Acceptance, and handoff.
