# Generation Contract

A Generation Contract is a standalone instruction artifact that guides another Agent in authoring
a complete future Rule or Skill. This reference owns the contract itself; the future target type
selects `rule.md` or `skill.md`.

## Establish the Generation Frame

Resolve every applicable part from active owner and project evidence:

- the authoring actor, invocation or trigger, accepted request, and required evidence;
- the future target's semantic type, owner, packaging or schema, write location, and permitted
  supporting changes;
- the future target's required obligations and selected Policy Frame or Skill Shape;
- the preservation boundary, target validation, and handoff; and
- completion, material-ambiguity stops, execution failures, recovery, and coincident-exit priority.

Together these form the Generation Frame. Apply active packaging mechanics without copying host or
project facts into this cross-project reference. The selected semantic-type reference defines what
the future target must contain. The contract must tell its Agent how to establish each applicable
target obligation from evidence and where to stop when evidence does not select one result.

Leave authoring method and order to Agent judgment by default. Prescribe an authoring action or
sequence only when evidence shows that it changes target correctness, permitted writes, validation,
recovery, or handoff.

## Author usable guidance

- Keep inputs, evidence sources, decisions, actions, exits, validation, and handoff discoverable at
  the point where another Agent needs them.
- State target obligations and selection evidence rather than copying a generated target outline or
  requiring an unsupported authoring recipe.
- Use observable predicates. Labels such as `valid`, `complete`, or `supported` do not replace the
  facts that make them true.
- Preserve existing target semantics unless current evidence or explicit approval supports a
  change. Keep target-owned runtime policy or procedure out of the contract.
- Stop before target writes when intent, owner, packaging, schema, write location, authority, or
  preserved behavior still permits materially different targets.
- Use an owned script only for repeated, fragile, deterministic work. Define and test its inputs,
  outputs, dependencies, failures, recovery, and public entry.
- Require a real target created later to enter the Ordinary Artifact route and pass its own current
  machine validation, Semantic Review, Acceptance, and handoff before adoption.

## Accept the contract statically

Do not start an Acceptance Runner, generate a fake target, or invent a project to qualify the
contract. After Semantic Review passes, the fresh reviewer walks the complete guidance against two
to four of the highest-risk supported inputs, chosen from:

- unclear intent or missing target evidence;
- unresolved owner, packaging, schema, write location, or authority;
- conflicting evidence or a requested change that would lose supported behavior; and
- a relevant validation, resource, failure, recovery, or coincident-exit boundary.

For each case, verify that another Agent can identify one next action or one explicit stop, the
evidence required to proceed, the permitted writes, the target validation, and the handoff without
inventing a fact or exit. Run contract-owned deterministic resources normally; static Acceptance
does not replace their machine tests.

Contract Acceptance passes when the guidance is complete and executable for every selected case.
It does not claim that an uncreated future target has passed. A target authored later is a new
Ordinary Artifact candidate, defaults to a different fresh reviewer, and inherits no contract
verdict.
