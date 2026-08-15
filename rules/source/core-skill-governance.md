# Skill Governance

Strength: `Mandatory`

Scope: Skill authority, precedence, and workflow routing across project, plugin, and external
Skills.

## Authority

- Apply every Skill within direct user instructions and all applicable Rules. A Skill may define a
  more specific procedure or completion gate, but it must not broaden authorization, weaken a
  Mandatory Rule, or redefine another owner's policy.
- When applicable Skills overlap, apply the more-specific Skill. At equal specificity, apply a
  project-local Skill before a plugin-distributed Skill; external provenance alone creates no
  additional precedence tier.

## Planning and Delivery

- Before state-changing implementation, determine whether the accepted conversation, issue, Spec,
  or other source already defines stable scope, decisions, and acceptance criteria.
- Recommend that the user invoke `to-spec` when material behavior, contracts, testing seams, or
  scope decisions remain implicit or need a durable reviewable source of truth.
- Recommend that the user invoke `to-tickets` when the accepted work contains multiple independently
  verifiable slices, blocking relationships, parallel work, or more work than one fresh
  implementation context should own. Tickets may start from an accepted Spec or the current
  conversation.
- Proceed without a Spec or Tickets when one accepted source already makes a single-scope task
  implementable and verifiable.
- Use `implement` to execute accepted implementation work from the conversation, an issue, a Spec,
  or Tickets. It owns implementation, verification, and code review within the workspace selected
  by `smartkit/core-workspace-policy`.
- When a Skill writes a planning or decision artifact under `.scratch/` or `docs/adr/`, write that
  artifact in English.

## Boundaries

- Apply `smartkit/core-workspace-policy` to every Skill instruction involving workspace selection,
  local Git state, commits, pushes, or pull requests.
- Leave Harness-native tools, capabilities, and event semantics to the matching Harness Adaptation.
