# Owner Gate

The Owner Gate decides whether accepted obligations belong in a Rule, Skill, both, or neither. It
runs before Candidate Revision writes and also supplies the parent Skill's read-only Ownership
Review exit.

## Classify the obligations

Use the accepted request, semantic ledger, current artifact when one exists, broader and narrower
owners, and discoverable environment facts. Classify each independently:

- `rule` — a persistent policy that constrains decisions across triggered jobs;
- `skill` — work that starts from a trigger and produces one bounded outcome;
- `environment-owned` — a fact reliably available from code, configuration, schemas, tool output,
  or another active owner and therefore not worth caching in an artifact; or
- `ambiguous` — current evidence still supports materially different owners.

Return one complete verdict: `rule`, `skill`, `split`, `environment-owned`, or `ambiguous`.
`split` requires at least one independently owned Rule obligation and one independently owned Skill
obligation. For a Generation Contract, classify the future target obligations and keep target
runtime policy or procedure outside the contract itself.

## Compare ownership

Compare the supported verdict with the requested owner and, for an existing artifact, its current
owner.

- Continue without an ownership question when they align. Creating or editing a Rule does not
  require separate approval merely because it is a Rule.
- When they conflict, explain the evidence, the behavioral and loading effects of each supported
  placement, and the recommended retain, move, or split result. Return `decision-required` and stop
  before candidate writes until the user selects the owner.
- Apply the same boundary in both directions: Rule-to-Skill and Skill-to-Rule reassignment each
  require that explicit ownership decision.
- Return `decision-required` when the verdict is `ambiguous`. Do not use the requested packaging to
  settle semantic ownership.

When the complete verdict is `environment-owned`, identify the active owner and discoverable
evidence, return a no-candidate result, and stop without writing a Rule or Skill.

The selected owner must still satisfy its Rule or Skill semantics and the complete Acceptance
Standard. A user choice resolves ownership intent; it does not turn a persistent policy into a
triggered job or waive a semantic gate.

## Return an Ownership Review

For an explicitly read-only review, inspect the selected artifacts and the related owners needed to
detect duplication or displacement. Return for each artifact:

- its current and supported owner;
- each obligation classification and the complete verdict;
- the evidence, effects, recommendation, and any exact missing decision; and
- `PASS` when ownership aligns, otherwise `decision-required`.

State that no file was changed and stop without creating a Candidate Revision or starting Pruning,
machine validation, Semantic Review, or Acceptance.
