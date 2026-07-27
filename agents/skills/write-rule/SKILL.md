---
name: write-rule
description: Use when creating, rewriting, or materially updating repository rules, including project-local rules, shared rules, and rule-generation contracts.
---

# Write Rule

Create one coherent, evidence-backed rule that another agent can apply without hidden context.
Rebuild the complete policy within the requested rule's scope instead of preserving the shape of
earlier edits.

## Authoring Priorities

Clarity, executability, and unambiguous meaning are acceptance conditions. After all three pass, make
the rule as concise as possible without weakening them.

Every requirement must have one clear interpretation. Make its subject, scope, conditions, strength,
and expected behavior explicit wherever they affect meaning. Use observable predicates and direct
outcomes. Reject a shorter version if it hides, merges, or removes information that can change the
policy.

Do not broaden, narrow, weaken, strengthen, or otherwise reinterpret a requirement without new
evidence or explicit user approval.

## Classify

Use distribution, ownership, and the requested output to select one class before authoring.

| Condition | Class |
| --- | --- |
| One repository owns and directly applies the final policy | Project-local rule |
| The distributed rule directly applies stable policy across repositories | Shared rule |
| The distributed artifact authors a complete target-owned rule | Shared rule-generation contract |

Removing local details does not make a rule shared. Classify it as shared only when the policy
itself remains stable across repositories; otherwise keep it project-local.

## Evidence

Collect only evidence that can change content, ownership, applicability, or validation.

### Policy Evidence

Record the outcome, constraints, examples, technical choices, thresholds, compatibility, strength,
scope, precedence, and exceptions. Inspect the owned rule family, broader and more-specific rules,
and real usage. Use the existing rule only as evidence and an omission check; exclude change
history, personal taste, reusable procedures, and runtime facts owned elsewhere.

### Repository Evidence

For a project-local rule, verify the repository facts and enforcement points needed to apply the
policy, including generated ownership and module boundaries when relevant. Prove concrete claims
before using them.

### Distribution and Generation Evidence

Inspect discovery and distribution surfaces when they can change. For a shared rule, inspect
representative repositories and retain only directly applicable stable policy, project-local
precedence, and supported exceptions. For a shared rule-generation contract, define target evidence
and inspect representative rule families, precedence systems, generation surfaces, and validators.

## Author

1. Define the complete policy, its exclusions, class, strength, scope, applicability, precedence,
   and exceptions.
2. Synthesize the full candidate from current user intent and verified evidence. Preserve intended
   outcomes and verified decisions, including thresholds, technical choices, and exceptions; remove
   stale, duplicated, contradictory, or misplaced content. Organize the result as the rule you would
   author today, placing each requirement where it belongs instead of appending a note or preserving
   old order for a smaller diff.
3. Put each requirement in the rule responsible for it. If the requested rule does not own a
   requirement, do not add it there. Modify the owning rule only if it is already within the user's
   requested scope; otherwise get explicit user approval first.
4. Modify only rules and the wrappers, indexes, manifests, mirrors, and contract tests required to
   load or distribute them. Report any other required change as out of scope.
5. Write the final rule as a steady-state contract from current ownership, conditions, and behavior.
   Keep transition work in the implementation plan. Include transitional behavior in the rule only
   while active compatibility or migration depends on it, with an explicit trigger and retirement
   condition. Convert review history into the current decision rule: the subject, the observable
   property that selects the outcome, and the resulting behavior.
6. Use the smallest set of positive predicates that fully selects the outcome. Keep a former name,
   location, classifier, or implementation only when a current input can still present it and the
   agent must distinguish it.
7. Read the complete candidate without the diff. Resolve gaps and conflicting interpretations, then
   remove repetition, history, and non-actionable explanation. Give the implementing agent freedom
   when several approaches are valid; prescribe ordered steps when sequence affects correctness or
   safety.

Include a fact, configuration value, or implementation detail only when the agent needs it to decide
or perform an action, interpret evidence, satisfy a prerequisite, handle a failure, or report the
result. If none of those purposes needs the information, omit it. When awareness of an automatic
behavior matters but its exact configuration does not, state only the behavior.

Tracked rules use repository-relative or stable protocol-owned paths, never machine-specific
absolute paths. Keep one source of truth for each instruction and keep wrappers limited to required
platform metadata plus a source reference.

Refer to another rule or skill by the canonical name declared or recognized by the target system,
never by its filesystem path.

Use the selected rule class to set its content boundary:

- for a project-local rule, state the final policy from verified repository facts and keep related
  requirements, relationships, and exceptions in the narrowest rule that owns them;
- for a shared rule, state only stable cross-repository policy, semantic target conditions, and
  protocol-owned paths while leaving concrete implementation and narrower exceptions local;
- for a shared rule-generation contract, separate authoring instructions from the rule they
  generate and describe evidence categories instead of inventing target facts.

## Instruction Forms

Use these forms to choose the clearest expression for each requirement; do not turn their names or
order into mandatory headings in every rule.

### Steps and Checklists

Use numbered steps (`1.`) only in a rule-generation contract when authoring order affects the result.
A final rule may use a Markdown task list (`- [ ]`) for independent policy obligations that are
scanned together. Each item must name one subject, required action or property, and observable
result. Use
`- [ ] When <condition>, <subject> must <action or property>; confirm <observable result>.`
Omit the condition only for an unconditional item. If the items prescribe a multi-step execution
workflow, move that procedure to a skill.

### Examples

Add an example only when it resolves a material ambiguity. Demonstrate one decisive distinction with
the smallest complete input/output, before/after, or boundary pair. Put bold `**Required**` and
`**Invalid**` labels before a binding contrast; use `**Preferred**` and `**Avoid**` for a default
with valid exceptions. Use a fenced block when exact syntax matters and one-line bullets when only
behavior matters. State every requirement in the normative text; an example must not introduce or
override one.

### Positive Requirements

Prefer the smallest set of positive requirements that fully selects the outcome. Use
`When <observable condition>, <subject> must <action>; the result must <observable property>.`
Omit the condition only when the requirement is unconditional. Define an output shape with its
required fields and conditional policy with explicit `If` or `When` predicates.

### Negative Requirements

Use a negative requirement only to exclude a plausible harmful shortcut not fully excluded by the
positive contract. Use
`Do not <forbidden action> when <observable trigger>; instead <required alternative>.`
If no alternative exists, state the enduring correctness, safety, or compatibility consequence. Do
not use an unscoped prohibition such as "never take shortcuts," "do not be vague," or "avoid
unnecessary work."

## Rule Contract

### Required Header

Start every rule with:

```markdown
# Rule Title

Strength: `Mandatory|Default|Advisory`

Scope: One sentence naming the rule's owned responsibility.
```

Add a section only when the responsibility needs it.

### Policy Body

A broader rule must not duplicate or silently override a more-specific rule.

Choose the policy body by applicability:

- project-local rules require H1, Strength, Scope, and responsibility-ordered policy; add Boundaries
  or Exceptions when needed for verified relationships or exceptions;
- shared rules require H1, Strength, Scope, and stable policy; add Boundaries or Precedence when
  needed, and make project-local precedence explicit without restating target-specific rules.

### Generation Contracts

Shared rule-generation contracts require Generation Contract, Evidence, Content, and Boundaries.
The contract must produce a complete target-owned candidate without mixing its authoring workflow
with final target policy.

## Validate

### Policy Review

- Read the final rule, not only changed lines. Verify classification, ownership, strength, scope,
  applicability, precedence, exceptions, and the complete policy.
- Confirm changes are limited to rules and their owned surfaces.
- Check the final candidate for ambiguity or semantic drift: every requirement must have one clear
  interpretation, and its meaning may change only with new evidence or explicit user approval. If
  either condition fails, reject the candidate.
- Reject requirements that cannot be applied from the stated context or became incomplete through
  compression.
- Read every requirement without the diff or prior implementation. Every negative requirement must
  identify its current trigger and enduring correctness, safety, or compatibility consequence;
  otherwise state the current desired behavior and ownership.
- Keep an alternative name, location, classifier, implementation, contrast, exception, or rationale
  only when a current input still requires that distinction.
- For every stated condition or contrast, vary it while holding the rule's positive predicates
  constant. If the required outcome does not change, remove that condition or contrast.
- Review each subsection by responsibility. Keep common requirements in common text and conditional
  requirements with the subject that owns them.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, strength, and behavior.

### Context Validation

- For a project-local rule, verify concrete claims, enforcement points, exceptions, and cross-rule
  relationships in the current repository.
- For a shared rule, test representative contexts that exercise project-local precedence, supported
  overrides, and stable policy without one repository's details.
- For a shared rule-generation contract, simulate at least one complete target rule and verify its
  evidence, content, and boundaries; use materially different targets when broad portability is
  claimed.

### Discovery Surfaces

Run the current validators, contract tests, and diff-integrity checks for every required discovery
surface. Confirm applicable wrappers, indexes, manifests, mirrors, and other distribution surfaces
remain aligned.

Do not report success while evidence is unresolved, claims are unsupported, required discovery
surfaces are stale or unreachable, or required checks fail or remain unreported.

## Result

Report the artifact class, owning artifact or repository, final document structure, preserved
decisions, removed or moved content, updated discovery and distribution surfaces and language
mirrors, and exact validation outcomes.
