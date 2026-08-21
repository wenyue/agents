---
name: write-rules-and-skills
description: Use when creating, rewriting, or materially updating a SmartKit Rule, Agent Skill, or Rule/Skill generation contract, including project-local or shared artifacts, owned resources, and discovery or distribution surfaces.
---

# Write Rules and Skills

Author the smallest complete artifact from accepted intent and verified evidence. Apply
`writing-for-agents` first for information hierarchy, purposeful Markdown, and Skill invocation
mechanics. This Skill owns the shared workflow; selected references own lifecycle and semantic-type
requirements.

## Route the candidate

Classify two independent properties before writing:

1. **Lifecycle** — an Ordinary Artifact is used directly; a Generation Contract instructs another
   Agent to author a future target.
2. **Semantic type** — Rule for one persistent policy; Skill for one triggered job.

A Generation Contract is a standalone instruction artifact. Its future target, not the contract's
file extension or packaging, selects the semantic-type reference.

| Candidate | Read completely |
| --- | --- |
| Ordinary Rule | [`references/ordinary-artifact.md`](references/ordinary-artifact.md) and [`references/rule.md`](references/rule.md) |
| Ordinary Skill | [`references/ordinary-artifact.md`](references/ordinary-artifact.md) and [`references/skill.md`](references/skill.md) |
| Rule Generation Contract | [`references/generation-contract.md`](references/generation-contract.md) and [`references/rule.md`](references/rule.md) |
| Skill Generation Contract | [`references/generation-contract.md`](references/generation-contract.md) and [`references/skill.md`](references/skill.md) |

When one request mixes durable policy with an executable job, create separately owned Rule and
Skill candidates. Routing is complete when every candidate has one lifecycle, one semantic type,
one owner, and both references loaded.

## Reach readiness

Before the first candidate write, establish from accepted intent and current evidence:

- the requested outcome, preserved semantics, approved changes, non-goals, and safety boundaries;
- the artifact owner, permitted writes, broader and narrower owners, and affected loading,
  resource, generation, and distribution surfaces; and
- the current behavior, applicable project Rules and host mechanics, validation seams, and any
  environmental fact that can change a policy, action, target, or exit.

Before writing, apply any Behavior Control required by the selected lifecycle reference and retain
its selected task and raw result for review.

Ask only when supported evidence still permits materially different behavior, ownership, write
targets, authority, side effects, or exits. Otherwise record the uniquely supported fact and
continue. Keep project facts in their active owners; the reusable Skill discovers them rather than
caching them.

Readiness passes when every selected reference can be applied without a material unknown.

## Build one Candidate Revision

Before writing, record one row for each independently changeable obligation:

| Obligation | Evidence | Owner | Disposition | Candidate location |
| --- | --- | --- | --- | --- |

Split rows only when a predicate, exception, owner, action, recovery, or exit can change
independently. Do not split wording choices that preserve the same behavior. Give every row one
owner and one `preserve`, `change`, `add`, `move`, or `retire` disposition. Stop when an unresolved
row permits materially different results.

Synthesize the whole candidate from the ledger. Use an existing artifact as omission evidence, not
as the new outline. Preserve supported decisions and safety boundaries. Represent each obligation
once in its narrowest owner. Keep working evidence, provenance, validation records, and reviewer
instructions outside a runtime artifact unless they change its execution.

A **Candidate Revision** is one complete current content state in the work area selected by the
active project or host. It is not a copied revision tree or mandatory report. Read it without its
predecessor or diff. Continue only when the lifecycle and semantic-type requirements pass and
another Agent can use the artifact without inventing a condition, fact, step, owner, or exit.

## Classify blocking findings

Use these classes throughout Pruning, Review, and correction:

- `uniquely-forced` — current evidence determines one in-scope correction without new policy,
  authority, behavior, scope, or side effects;
- `decision-required` — current evidence leaves two or more materially different supported
  outcomes, or the correction requires new intent, evidence, authority, scope, or external action.

Classify each finding independently. The number of findings does not change their class; apply all
current `uniquely-forced` corrections together. Every
`decision-required` finding names the exact unresolved choice, its decision owner, and the evidence
for each materially different supported outcome. Without those elements, classify the finding as
`uniquely-forced` or non-blocking rather than asking for confirmation.

## Run the Pruning Gate

Before machine validation, read [`references/pruning-agent.md`](references/pruning-agent.md)
completely and apply it with one fresh Pruning Agent that did not author the candidate.

Apply **Correct until stable** without adding behavior and keep the same Pruning Agent through
correction. Reconcile every revision with the ledger and require each baseline increase to map to a
distinct supported obligation.

The Pruning Agent writes no candidate file and cannot later serve as that candidate's Reviewer or
Acceptance Runner. Stop and report when a fresh Pruning Agent is unavailable.

## Validate and freeze

Run the active project's required checks for every changed owner and affected loading, resource,
generation, or distribution surface. Machine validation may prove schemas, identifiers,
registration, resource reachability, generated relationships, filesystem effects, script results,
state transitions, and process exits. It cannot prove natural-language meaning; keyword checks,
prose snapshots, complete-heading snapshots, copied expectations, or author-written policy
interpreters do not satisfy Semantic Review.

If a required machine check fails, stop before semantic gates. Report its exact command, final exit,
relevant output, unrun gates, and unverified surfaces. Do not call a walkthrough machine PASS.

Record successful commands, final exits, and untested surfaces in a bounded Review Packet. Create
no persistent validation report unless an active owner requires it.

Freeze candidate writes before review.

## Review and accept

Read [`references/semantic-review.md`](references/semantic-review.md) completely and apply it with
one fresh reviewer that did not author the candidate. For an Ordinary Artifact, also read
[`references/acceptance-runner.md`](references/acceptance-runner.md) completely before the reviewer
starts Acceptance.

The reviewer returns a Semantic Review `PASS` or `FAIL` first. Start Acceptance only after that
gate passes. Apply the selected lifecycle and semantic-type portfolio: Ordinary Artifact
Acceptance uses an isolated fresh Runner; Generation Contract Acceptance is a static reviewer
walkthrough with no Runner or target generation. Return a separate Acceptance `PASS` or `FAIL`.

Apply the shared finding classes to every blocking result.

Each candidate gets its own fresh reviewer; independent candidate reviews may run concurrently,
but they do not share evidence or verdicts. Stop and report an unavailable fresh reviewer.

## Correct until stable

Stop before correction on any valid `decision-required` finding and ask only for its exact missing
decision. When every finding is `uniquely-forced`, apply all current corrections together without asking for
confirmation. A content change creates a new Candidate Revision and invalidates every dependent
machine, Review, and Acceptance result; rerun those gates in their normal order. A corrected
revision receives whole-candidate Semantic Review and affected Acceptance, using a new isolated
Runner for each affected Ordinary Artifact case.

Continue until all gates pass. Stop for no progress when the same finding recurs unchanged after
its correction or a proposed correction would not change the candidate. Report that blocker
without asking the user to authorize another identical attempt.

Success requires the Pruning Gate, machine validation, Semantic Review, and Acceptance to pass for
the same Candidate Revision. Report the candidate's lifecycle, semantic type, owner, preserved and
approved changes, affected surfaces, size comparison, exact commands and exits, pruning, review,
acceptance, and correction verdicts, and every unresolved or untested surface. Every stop reports
the blocker, completed evidence, unrun gates, and next owner. Leave publication, installation,
commit, push, and other external actions to their owners.
