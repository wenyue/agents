---
name: write-rules-and-skills
description: Use when creating, rewriting, or materially updating repository Rules or Agent Skills, including project-local or shared artifacts, generation contracts, owned resources, and discovery or distribution surfaces.
---

# Write Rules and Skills

**Route first:** a Rule owns one policy; a Skill owns one complete job. Rebuild every selected
artifact from accepted intent and verified evidence. The existing artifact and diff are evidence of
change, never the shape of the final result.

Apply `writing-for-agents` first for context pointers, information hierarchy, relevance, pruning,
and Skill invocation mechanics. This Skill owns Rule-or-Skill routing, their shared authoring
contract, and the boundary between their specialized instructions.

Clarity, executability, and one unambiguous interpretation come before concision. Only then make the
artifact as concise as possible without hiding, merging, or removing information that changes its
meaning or behavior. Preserve every supported decision and safety boundary. Change no instruction
or requirement semantically without current evidence or explicit user approval.

## 1. Route the artifact

Classify the requested outcome by its semantics, not its current filename or directory:

| Target semantics | Route |
| --- | --- |
| A policy that governs behavior whenever its conditions apply | Read [`references/rule-authoring.md`](references/rule-authoring.md). |
| A triggered job with actions and explicit completion, stop, and failure exits | Read [`references/skill-authoring.md`](references/skill-authoring.md). |
| Both policy and procedure | Split them into separately owned artifacts and read both references. |

Before any write, read every selected reference completely and apply it with this shared contract.
When semantics remain ambiguous, inspect the intended authority, owner, application conditions, and
execution lifecycle. Resolve every unknown that could change the route before writing.

Routing is complete when every requested artifact has one supported type and owner, every mixed
artifact has been split, and every selected reference is loaded.

## 2. Gather shared evidence

Collect only evidence that can change the artifact's meaning, owner, applicability, execution,
distribution, or validation:

- the requested outcome, constraints, accepted decisions, safety boundaries, and excluded
  responsibilities;
- the owning artifact family, broader and narrower owners, real usage, enforcement or execution
  points, wrappers, registries, manifests, mirrors, and contract tests; and
- representative targets and supported overrides when claiming shared or generation behavior.

Use the existing artifact as evidence and an omission check, not as an outline. Keep runtime facts in
their owning configuration and change history outside the final artifact. When another owner falls
outside the approved scope, report the dependency and obtain approval before changing it.

Evidence is sufficient when every route, contract choice, and repository or platform claim that
could affect the result has support, and remaining unknowns cannot change the contract.

## 3. Rebuild the whole artifact

Write each selected artifact as it should exist today:

- Synthesize one complete candidate from accepted intent and verified evidence. Preserve intended
  outcomes, supported decisions, and safety boundaries; remove stale, duplicated, contradictory,
  transitional, or misplaced content.
- Lead with the artifact's governing model and boundary, not a taxonomy of topics. When one compact
  leading term organizes the work, define it once and use it consistently.
- Represent every current requirement exactly once in the narrowest artifact or owned resource that
  owns it. Modify only the resources, wrappers, registries, manifests, mirrors, generation inputs,
  and contract tests required to execute, load, or distribute the result.
- State the steady-state contract from current conditions and behavior. Retain migration behavior
  only while a current input can trigger it, with an explicit trigger and retirement condition.
- Use observable conditions and outcomes. Replace evaluative adjectives with the property that
  earns them.
- Prefer positive instructions. Use a negative only to block a plausible harmful shortcut, and pair
  it with the required alternative or enduring consequence.

Tracked artifacts use repository-relative, artifact-root-relative, or stable protocol-owned paths.
Derive runtime absolute paths from a discovered root or task input. Refer to another Rule or Skill by
its canonical name unless its path is part of the runtime contract.

## Markdown carries meaning

Markdown is semantic structure, not decoration. Every form must change how another Agent locates,
understands, or executes the artifact; remove formatting that leaves the result unchanged.

| Form | Use it for |
| --- | --- |
| Headings | Stable semantic regions or genuine branches. Keep the governing model above branch detail. |
| Numbered lists | Ordered actions whose sequence changes correctness, safety, or the generated result. |
| Bullets | Peer requirements or reference items with no execution order. |
| Checklists | Independent obligations or gates with a named subject, action or property, and observable result. |
| **Bold** | A few leading terms, invariants, or exact contrasts that organize the artifact. |
| Fenced blocks | Exact syntax, templates, commands, or output shapes. State every normative requirement outside the block. |
| Blockquotes | A short literal statement, prediction, or contrast that must stand apart. |
| Tables | Exact mappings or repeated-field comparisons, not long prose or ordered work. |
| Links | Context pointers whose surrounding text says when the target must be read. |

Keep nesting shallow enough that the governing model remains visible. Add an example only when it
resolves a material ambiguity; keep it minimal and state the requirement normatively outside it.

## Whole-Artifact Gate

Read every complete candidate without its diff and walk every selected branch. The result passes
only when:

- another Agent can discover when each artifact applies and use its complete contract without hidden
  context or an invented condition, step, or exit;
- the type, owner, boundaries, and every field required by the selected reference are explicit or
  verifiably inapplicable;
- every current requirement and supported decision appears once under its one owner;
- every claim is supported, every required owned and distribution surface agrees, and no unrelated
  owner changed;
- every selected reference's specialized gate passes; and
- clarity and executability still hold after pruning.

If any routing, ownership, boundary, evidence, branch, or specialized-gate gap remains, return to the
relevant step. The artifact is not ready for validation.

## Prove it

- Run the proof required by every selected reference. When both types are present, preserve separate
  evidence for the Rule and Skill gates.
- Compare language mirrors structurally. Preserve paths, commands, identifiers, code blocks,
  artifact classes, and behavior.
- Run the current validators, contract tests, and diff-integrity checks for every changed owned,
  discovery, generation, or distribution surface.
- Report any command failure with its exact command, final exit status, relevant output, and every
  surface left unverified.

## Get independent review

Treat review as an attempt to falsify the candidate, not an approval formality. Every authored or
materially updated Rule and Skill requires a fresh subagent review after its applicable proof runs.
The author does not satisfy this gate by reviewing its own work.

1. Start a fresh reviewer for each candidate. Give it the complete candidate, its owned resources
   and discovery or distribution surfaces, the accepted request and evidence, and exact validation
   results. Require it to apply this Skill and the selected authoring reference. Do not give it the
   diff, the author's reasoning, a suspected defect, an intended fix, or an expected answer.
2. Instruct the reviewer to return `PASS` or `FAIL`, apply the Whole-Artifact Gate and the selected
   specialized review, walk every material branch, and cite the artifact evidence for its verdict.
   `PASS` means no blocking defect remains. `FAIL` names each violated gate, the concrete failing
   scenario, and whether current evidence forces one correction or a new decision is required.
3. Automatically fix a `FAIL` only when the correction is uniquely determined by accepted intent
   and verified evidence, remains inside the approved scope and owner, and requires no new policy,
   behavior, authority, or external side effect. Apply the fix in the authoring agent, rerun every
   affected proof, then send the complete revised candidate to a different fresh reviewer.
4. Stop and report to the user when a finding permits multiple materially different corrections,
   requires missing intent, evidence, authority, scope, or an external side effect, or conflicts
   with an accepted requirement. Report the exact finding, why it cannot be fixed safely, the
   decision needed, and every surface still unreviewed or unverified.

If a fresh subagent cannot be started, report review as unavailable and do not claim the artifact is
done. Independent review is complete only when the latest fresh reviewer returns `PASS` and every
earlier finding is either fixed and re-reviewed or explicitly resolved by the user.

## Done

The work is done only when the Whole-Artifact Gate, every selected specialized gate, every
applicable proof, and independent review pass. Report each artifact's type and owner, final
structure, preserved decisions, material changes, moved or removed content and resources, every
changed discovery or distribution surface, approved dependencies, review verdict and fixes,
unresolved or untested surfaces, and exact validation outcomes.
