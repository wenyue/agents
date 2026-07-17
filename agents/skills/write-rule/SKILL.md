---
name: write-rule
description: Use when creating, rewriting, or materially updating repository rules, including project-local rules, shared rules, and rule-generation contracts.
---

# Write Rule

Create one coherent, evidence-backed rule that another agent can apply without hidden context.
Rebuild the complete policy within the rule's scope on every invocation instead of preserving the
shape of earlier edits.

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

Collect only evidence that can change the rule's content, ownership, or validation.

### Policy Evidence

Capture the user's outcome, constraints, examples, technical choices, thresholds, and compatibility
needs. Inspect the complete owned rule family, applicable broader and more-specific rules, current
precedence, and real usage.

Treat the existing rule as evidence and an omission check, not as the preferred outline. Separate
stable policy from change history, personal taste, reusable procedures, and runtime facts owned
elsewhere.

### Repository Evidence

For a project-local rule, inspect current code, configuration, schemas, commands, services, lints,
generated ownership, module boundaries, and enforcement points. Verify every concrete claim against
the repository's actual behavior.

### Distribution and Generation Evidence

Inspect manifests, catalogs, wrappers, mirrors, validators, and tests whenever distribution or
discovery can change. For a shared rule, inspect representative repositories to find the minimum
policy that remains directly applicable across them, including project-local precedence and
exceptions. For a shared rule-generation contract, identify the evidence categories every target
must collect, then inspect representative target rule families, precedence systems, generation
surfaces, and validators.

## Author

1. Define the complete policy the rule owns, the responsibilities it excludes, and the evidence for
   its class, strength, and applicability.
2. Synthesize the full candidate from current user intent and evidence. Preserve intended outcomes
   and verified decisions, including thresholds, technical choices, and exceptions; remove stale,
   duplicated, contradictory, or misplaced content. Organize the result as the rule you would author
   today, placing each requirement where it belongs instead of appending a note or preserving old
   order for a smaller diff.
3. Put each requirement in the rule responsible for it. If the requested rule does not own a requirement,
   do not add it there. Modify the owning rule only if it is already within the user's requested
   scope; otherwise get explicit user approval first.
4. Modify only rules and the wrappers, indexes, manifests, mirrors, and contract tests required to
   load or distribute them. Report any other required change as out of scope.
5. Read the complete candidate without the diff and revise it until every paragraph contributes
   unique, current, enforceable information.

Every requirement must have one clear interpretation. Make its subject, scope, conditions, strength,
and expected behavior explicit wherever they affect meaning. Do not broaden, narrow, weaken,
strengthen, or otherwise reinterpret it without new evidence or explicit user approval.

Prefer the desired state, observable conditions, and ownership over procedural narration. Give the
implementing agent freedom when several approaches are valid; prescribe ordered steps when sequence
affects correctness or safety. Use concise examples only to disambiguate behavior.

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

## Rule Contract

### Required Header

Start every rule with:

```markdown
# Rule Title

Strength: `Mandatory|Default|Advisory`

Scope: One sentence naming the rule's owned responsibility.
```

Add sections because the responsibility needs them, not to satisfy a universal template.

### Policy Body

A broader rule must not duplicate or silently override a more-specific rule.

Choose the policy body by applicability:

- project-local rules require H1, Strength, Scope, and responsibility-ordered policy; add Boundaries
  or Exceptions when needed to express verified target relationships, and do not create empty sections;
- shared rules require H1, Strength, Scope, and stable policy; add Boundaries or Precedence when
  needed, and make project-local precedence explicit without restating target-specific rules.

### Generation Contracts

Shared rule-generation contracts require Generation Contract, Evidence, Content, and Boundaries.
The contract must produce a complete target-owned candidate without mixing its authoring workflow
with final target policy.

## Validate

### Policy Review

- Verify classification, ownership, strength, scope, applicability, precedence, exceptions, and the
  complete policy by reading the final rule rather than only changed lines.
- Confirm changes are limited to rules and their owned surfaces.
- Check the final candidate for ambiguity or semantic drift: every requirement must have one clear
  interpretation, and its meaning may change only with new evidence or explicit user approval. If
  either condition fails, reject the candidate.
- Review each subsection by responsibility. Keep requirements that apply to every class in common
  text; state conditional requirements where their subject is owned; never create parallel class
  subsections merely for symmetry.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, strength, and behavior.

### Context Validation

- For a project-local rule, verify concrete claims, enforcement points, exceptions, and cross-rule
  relationships in the current repository.
- For a shared rule, test representative contexts that exercise project-local precedence, supported
  overrides, and the stable policy without relying on one repository's details.
- For a shared rule-generation contract, simulate at least one complete target rule and verify its
  evidence, content, and boundaries; use materially different targets when broad portability is claimed.

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
