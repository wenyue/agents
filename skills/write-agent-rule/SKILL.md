---
name: write-agent-rule
description: Use when creating, rewriting, or materially updating repository rules, including project-local rules, shared rules, and rule-generation contracts.
---

# Write Agent Rule

Apply `writing-for-agents` for general Agent-document structure, context pointers, relevance, and
pruning. This Skill owns Rule classification, policy boundaries, strength, scope, distribution, and
generation contracts.

Produce one coherent, evidence-backed policy that another Agent can apply without hidden context.
Rebuild the complete policy inside its approved scope instead of preserving the shape of earlier
edits.

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
   precedence, exceptions, and boundaries.
2. Synthesize the full candidate from current user intent and verified evidence. Preserve approved
   decisions; remove stale, duplicated, contradictory, transitional, or misplaced content.
3. Put each requirement in the narrowest Rule that owns it. Modify another owner only when it is
   already within the requested scope; otherwise report the dependency and request approval.
4. Modify only Rules and the wrappers, registries, manifests, mirrors, generation inputs, and
   contract tests required to load or distribute them.
5. Write steady-state policy from current conditions and behavior. Keep migration behavior only
   while a current input can trigger it, with an explicit trigger and retirement condition.
6. Use observable conditions and outcomes. Move an ordered execution procedure into a Skill unless
   the Rule is itself a generation contract whose authoring order affects the result.
7. Read the complete candidate without its diff and resolve every ownership, applicability,
   precedence, exception, or enforcement gap before validation.

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

### Policy and Ownership

- Read the final Rule rather than only changed lines. Verify its class, owner, strength, scope,
  applicability, precedence, exceptions, boundaries, and complete policy.
- Confirm each requirement has one executable interpretation and is supported by current evidence.
- Confirm the change is limited to the Rule's owned surfaces and required distribution artifacts.
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
distribution surface. Do not report success while evidence, policy, ownership, or required surfaces
remain unresolved or unverified.

## Result

Report the Rule class and owner, final policy structure, preserved decisions, removed or moved
content, changed generation and distribution surfaces, and exact validation outcomes.
