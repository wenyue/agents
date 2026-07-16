---
name: write-rule
description: Use when creating, rewriting, or materially updating repository rules, including project-local rules, shared rules, and rule-generation contracts.
---

# Write Rule

Create one coherent, evidence-backed rule that another agent can apply without hidden context.
Rebuild the complete owned policy on every invocation instead of preserving the shape of earlier edits.

## Classify

Use distribution and ownership evidence to select one class before authoring.

| Class | Owns | Specificity |
| --- | --- | --- |
| Project-local rule | Final policy for one repository | Verified repository-relative paths, commands, APIs, modules, lints, services, and exceptions |
| Shared rule | Stable policy applied directly across repositories | Cross-repository invariants, semantic project targets, and protocol-owned paths |
| Shared rule-generation contract | Authoring of a complete target-owned rule | Target evidence categories and the generated rule's contract, not its final project policy |

Catalogs, manifests, installation scope, sync ownership, wrappers, and the requested output are
stronger classification evidence than generic wording. Deleting local details does not make a rule
shared; redesign it around genuinely stable policy or keep it project-local.

## Evidence

Collect only evidence that can change the rule's content, ownership, or validation:

- the user's outcome, constraints, examples, technical choices, thresholds, and compatibility needs;
- the complete owned rule family, applicable broader and more-specific rules, and current precedence;
- manifests, catalogs, wrappers, mirrors, validators, tests, and real usage;
- for project-local rules, current code, configuration, schemas, commands, services, lints, generated
  ownership, and module boundaries;
- for shared artifacts, the minimum policy or evidence categories that remain valid across supported
  repositories.

Treat the existing rule as evidence and an omission check, not as the preferred outline. Separate
stable policy from change history, personal taste, reusable procedures, and runtime facts owned
elsewhere.

## Author

1. Define the complete policy the rule owns, the responsibilities it excludes, and the evidence for
   its class, strength, and applicability.
2. Synthesize the full candidate from current intent. Preserve supported direction, thresholds,
   technical choices, and exceptions; remove stale, duplicated, contradictory, or misplaced content.
3. Put each instruction at its natural owner. Update the requested file only when it owns the policy;
   otherwise update the actual owner or ask when that move would materially change the request.
4. Update owned wrappers, indexes, manifests, mirrors, and contract tests when applicability or
   distribution requires them.
5. Read the complete candidate without the diff and revise it until every paragraph contributes
   unique, current, enforceable information.

Prefer the desired state, observable conditions, and ownership over procedural narration. Allow the
implementing agent freedom when several approaches are valid; prescribe steps when sequence is part
of the policy or little useful discretion exists. Use concise examples only to disambiguate behavior.

Tracked rules use repository-relative or stable protocol-owned paths, never machine-specific
absolute paths. Keep one source of truth for each instruction and keep wrappers limited to required
platform metadata plus a source reference.

Refer to another rule or skill by the canonical name declared or recognized by the target system,
never by its filesystem path. Use paths only for owned files or resources whose location is part of
the current contract.

## Rule Contract

When the target uses this repository's format, start with:

```markdown
# Rule Title

Strength: `Mandatory|Default|Advisory`

Scope: One sentence naming the rule's owned responsibility.
```

Use the target system's supported title, strength, scope, numbering or applicability declaration,
and precedence vocabulary. Add sections because the responsibility needs them, not to satisfy a
universal template.

| Contract shape | Required content | Additional constraint |
| --- | --- | --- |
| Project-local direct rule | H1; Strength; Scope; responsibility-ordered policy; Boundaries or Exceptions when needed | State verified target policy and relationships |
| Shared direct rule | H1; Strength; Scope; stable policy; Boundaries or Precedence when needed | Leave target-specific policy to project-local rules |
| Shared rule-generation contract | Generation Contract; Evidence; Content; Boundaries | Produce a complete target-owned candidate without mixing authoring instructions with final target policy |

A broader rule must not duplicate or silently override a more-specific rule.

## Validate

- Verify classification, ownership, strength, scope, applicability, precedence, exceptions, and the
  complete policy by reading the final rule rather than only changed lines.
- For a project-local rule, verify its concrete claims and cross-rule relationships against current
  repository enforcement.
- For a shared rule, test representative contexts with project-local precedence and overrides.
- For a generation contract, simulate at least one complete target rule; use materially different
  targets when broad portability is claimed.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, strength, and behavior.
- Run the current validators, contract tests, and diff-integrity checks for every owned discovery
  surface.

Do not report success while evidence is unresolved, claims are unsupported, owned surfaces are
stale, or required checks fail or remain unreported.

## Result

Report the artifact class, natural owner, resulting contract shape, preserved decisions, removed or
moved content, updated discovery surfaces and mirrors, and exact validation outcomes.
