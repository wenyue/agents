---
name: write-agent-rule
description: Use when creating, rewriting, or materially updating a repository Rule, including project-local Rules, shared Rules, Rule-generation contracts, or Rule discovery and distribution surfaces.
---

# Write Agent Rule

Apply `writing-for-agents` first for general Agent-document structure, context pointers, information
hierarchy, relevance, and pruning. This Skill owns Rule classification, policy boundaries, strength,
scope, distribution, and generation contracts.

Produce one coherent, executable, evidence-backed Rule that another Agent can apply without hidden
context. Rebuild the complete policy inside its approved scope instead of preserving the shape of
earlier edits.

## Authoring Standard

Clarity, executability, and one unambiguous interpretation are acceptance conditions. After they
pass, make the Rule as concise as possible without hiding, merging, or removing information that
changes its meaning. Make the subject, scope, conditions, strength, and outcome explicit wherever
they affect application. Do not broaden, narrow, weaken, strengthen, or otherwise reinterpret a
requirement without current evidence or explicit user approval.

## Classify

Choose one class from distribution, ownership, and the requested output before authoring.

| Condition | Class |
| --- | --- |
| One repository owns and directly applies the policy | Project-local Rule |
| A distributed Rule directly applies stable policy across repositories | Shared Rule |
| A distributed artifact authors a complete target-owned Rule | Shared Rule-generation contract |

Removing local details does not make a Rule shared. Use the shared class only when the policy itself
is stable across repositories.

## Evidence

Collect only evidence that can change policy, ownership, applicability, distribution, or validation:

- define the outcome, constraints, strength, scope, precedence, exceptions, and excluded
  responsibilities;
- inspect the owning Rule family, broader and more-specific Rules, real usage, enforcement points,
  wrappers, registries, manifests, mirrors, and contract tests;
- for a project-local Rule, verify every repository fact, generated owner, and module relationship
  needed to apply it;
- for a shared Rule, inspect representative repositories and retain only stable cross-repository
  policy and supported project-local overrides; and
- for a Rule-generation contract, inspect representative target Rule families, precedence systems,
  generation surfaces, and validators.

Use an existing Rule only as evidence and an omission check. Keep reusable procedures in Skills,
runtime facts in their owning configuration, and change history outside the final policy.

## Author

1. Select the class and define the complete policy, owner, strength, scope, applicability,
   precedence, exceptions, and boundaries. This step is complete when each field has one explicit
   value or a verified reason that it does not apply.
2. Synthesize the full candidate from current user intent and verified evidence. Preserve intended
   outcomes, supported decisions, and safety boundaries; remove stale, duplicated, contradictory,
   transitional, or misplaced content. Organize it as policy authored today rather than appended
   notes or edits shaped around a smaller diff. This step is complete when every current requirement
   and supported decision is represented once.
3. Put each requirement in the narrowest Rule that owns it. Modify another owner only when it is
   already within the requested scope; otherwise report the dependency and request approval. This
   step is complete when every requirement has one owner.
4. Modify only Rules and the wrappers, registries, manifests, mirrors, generation inputs, and
   contract tests required to load or distribute them. This step is complete when required surfaces
   agree and no unrelated owner changed.
5. Write steady-state policy from current conditions and behavior. Keep migration behavior only
   while a current input can trigger it, with an explicit trigger and retirement condition. This
   step is complete when no history-only behavior remains.
6. Use observable conditions and outcomes. Move an ordered execution procedure into a Skill unless
   the Rule is itself a generation contract whose authoring order affects the result. This step is
   complete when every requirement can be applied without inventing a procedure.
7. Read the complete candidate without its diff. Proceed to validation only after every ownership,
   applicability, precedence, exception, and enforcement gap is resolved.

Tracked Rules use repository-relative or stable protocol-owned paths. Refer to another Rule or Skill
by its canonical name unless its path is part of the runtime contract.

## Class Contracts

### Project-local Rule

State final policy from verified repository facts. Keep related requirements and exceptions in the
narrowest project Rule that owns them.

### Shared Rule

State only stable cross-repository policy, semantic target conditions, supported exceptions, and
project-local precedence. Leave concrete implementation and narrower project decisions local.

### Shared Rule-generation Contract

Separate the authoring workflow from the complete target-owned Rule it produces. Define evidence
categories and acceptance conditions without inventing target policy.

## Instruction Forms

- Use numbered steps only in a Rule-generation contract when authoring order affects the result.
  Use a checklist only for independent policy obligations; each item names the subject, required
  action or property, and observable result.
- Add an example only when it resolves a material ambiguity. Keep it minimal and state every
  requirement in normative text rather than introducing policy through the example.
- Prefer positive requirements with observable conditions and results. Use a negative requirement
  only for a plausible harmful shortcut, paired with the required alternative or enduring
  consequence.

## Rule Contract

Start every final Rule with:

```markdown
# Rule Title

Strength: `Mandatory|Default|Advisory`

Scope: One sentence naming the Rule's owned responsibility.
```

A broader Rule must not duplicate or silently override a more-specific Rule. Add `Boundaries`,
`Exceptions`, or `Precedence` only when the owned policy needs them. A generation contract must make
its generation evidence, complete target content, review, acceptance, and handoff independently
discoverable.

## Validate

### Content and Ownership

- Read the complete Rule rather than only changed lines. Verify its class, owner, strength, scope,
  applicability, precedence, exceptions, boundaries, and complete policy.
- Confirm the complete candidate satisfies the Authoring Standard and remains complete and
  executable after pruning.
- Confirm every requirement and repository claim is supported by current evidence.
- Confirm the change is limited to the Rule's owned surfaces and approved dependencies.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, strength, and behavior.

### Applicability

- For a project-local Rule, verify concrete claims, enforcement points, exceptions, and cross-Rule
  relationships in the current repository.
- For a shared Rule, exercise representative contexts with project-local precedence and supported
  overrides.
- For a generation contract, produce and review at least one complete representative target Rule;
  use materially different targets when broad portability is claimed.

### Distribution

Run the current validators, contract tests, and diff-integrity checks for every changed discovery or
distribution surface. Do not report success while evidence, policy, ownership, or a required surface
remains unresolved or unverified.

## Result

Report the Rule class and owner, final policy structure, preserved decisions, removed or moved
content, changed generation and distribution surfaces, approved dependencies, and exact validation
outcomes.
