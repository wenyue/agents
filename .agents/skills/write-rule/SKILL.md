---
name: write-rule
description: Use when creating, rewriting, or materially updating any repository rule, including project-local rules, shared rules, and shared rule-generation contracts. Rebuilds the complete rule from current evidence, assigns the correct ownership and contract shape, prevents patch-style accumulation, and validates the full rule before handoff.
---

# Write Rule

Create one coherent rule contract that another agent can apply without hidden context. Classify its
distribution and contract role before writing, then own the quality of the whole rule on every
invocation even when the request names only one defect.

## Whole-Rule Rewrite Invariant

- Treat every creation or update as a fresh synthesis from the rule's complete current purpose.
- Treat the existing rule and its discovery surfaces as evidence and an omission checklist, not as
  an immutable scaffold or preferred outline.
- Reconstruct distribution, ownership, `Strength`, `Scope`, precedence, boundaries, exceptions,
  and discovery surfaces before deciding which existing wording still belongs.
- Produce a complete candidate and replace the owned artifact coherently. The diff is only a
  delivery mechanism; never optimize the rule for the smallest textual patch.
- Integrate each valid requirement at its natural owner. Remove superseded, duplicated,
  contradictory, misplaced, and change-history content.
- Do not append a new exception, note, addendum, or trailing section merely to address the latest
  request. Rewrite the governing sections and then review the entire rule again.
- Preserve the rule's established direction, technical choices, thresholds, `Strength`, and valid
  exceptions when current intent and evidence still support them, but do not preserve weak
  structure or stale wording solely because it already exists.

## Classify Before Authoring

Determine the ownership scope first. A shared artifact is either a shared rule, which applies its
policy directly, or a shared rule-generation contract, which authors a complete target-owned rule.
Use manifests, catalogs, sync ownership, installation scope, wrapper generation, and the requested
output as evidence.

| Class | Purpose and evidence | Allowed specificity | Required boundary |
| --- | --- | --- | --- |
| Project-local rule | Serves one target repository and is owned by that repository, whether handwritten or generated | Current repository-relative paths, real APIs, commands, modules, lints, services, and project policy | Optimize for target accuracy; do not publish or generalize unsupported facts |
| Shared rule | Is distributed across repositories and applies its policy directly | Cross-repository invariants and stable protocol-owned paths | Resolve project facts at application time and defer target-specific policy to project-local rules |
| Shared rule-generation contract | Is distributed across repositories to author a complete target-owned rule from target evidence | Semantic evidence categories and stable protocol-owned paths only | Describe authoring and the generated contract; do not act like the final target rule |

A project-local rule normally contains the final policy for its repository. If a project-local
rule-generation contract is explicitly required, use the generation-contract shape but keep its
evidence and output owned by that repository. Do not turn a target-specific rule into a shared rule
merely by deleting concrete paths; redesign it around genuinely stable cross-repository policy or
keep it local.

## Evidence

Read the complete owned rule family and collect evidence appropriate to its class.

Common evidence:

- the user's requested outcome, examples, constraints, technical choices, thresholds, and
  compatibility requirements;
- the existing rule, broader and more-specific rules, wrappers, indexes, mirrors, manifests,
  catalogs, validators, tests, and real usage artifacts;
- applicable precedence, numbering, source-of-truth, distribution, and platform-loading policy.

Class-specific evidence:

- For a project-local rule, inspect current project rules, code, configuration, schemas, APIs,
  commands, lints, services, generated-file ownership, module boundaries, and verification
  behavior. Prefer these facts over generic best practices.
- For a shared rule, identify the minimum policy that remains correct across supported repositories
  and platforms. Treat facts from one repository as examples, not defaults.
- For a shared rule-generation contract, inspect the target evidence categories its generated rule
  must consume and test the contract against materially different representative repositories.

Separate stable behavioral requirements from implementation history, prior edits, personal taste,
and multi-step procedures that belong in skills.

## Path and Ownership Rules

- Never hardcode an absolute filesystem path in a tracked rule or wrapper. Do not embed drive
  letters, user-home paths, checkout locations, or machine-specific temporary directories.
- In a project-local rule, use repository-root-relative paths and record concrete APIs, commands,
  modules, services, and lints only when current project evidence proves them.
- In a shared rule, use semantic project targets and stable protocol-owned paths. Keep a concrete
  path only when the shared protocol owns and standardizes it across supported targets.
- In a shared rule-generation contract, describe target files semantically unless a path belongs to
  the shared generation protocol itself. Require the generated project rule to resolve its concrete
  paths and policy from target evidence.
- Keep universal rule-authoring constraints in `write-rule`. Keep target facts and behavioral
  policy in the target repository's project-local rules, and reference them instead of duplicating
  them.
- Keep stable always-on constraints in rules. Keep reusable multi-step procedures in skills and
  runtime facts in their owning configuration or tooling surface.
- Determine the natural owner before honoring a named destination. A user-named file identifies the
  requested surface, but does not prove that the policy belongs there. When intent is clear,
  implement the policy in its natural owner and report the named-destination conflict; ask only when
  moving it would materially change the requested behavior or exceed current authority.
- Keep one source of truth for each instruction. A wrapper contains only platform metadata or a
  source reference unless its platform requires additional runtime fields.

## Required Format and Contract Shape

Give every rule:

1. One H1 title that names the owned policy.
2. A `Strength` declaration using the target rule system's supported vocabulary and precedence.
3. A one-sentence `Scope` that names the owned responsibility and its meaningful boundary.
4. A number, filename, glob, or applicability declaration consistent with the target's discovery
   system.
5. Imperative instructions, explicit ownership, evidence-backed exceptions, validation, and a
   defined relationship to broader and more-specific rules.

When the target uses this repository's rule format, preserve this opening shape:

```markdown
# Rule Title

Strength: `Mandatory|Default|Advisory`

Scope: One precise sentence naming the rule's owned behavior.
```

Choose the contract shape after classification. Add or omit a section only when the responsibility
proves it necessary; do not combine complete templates.

| Contract shape | Required section order | Additional constraint |
| --- | --- | --- |
| Project-local direct rule | H1; Strength; Scope; responsibility-ordered policy sections; Boundaries or Exceptions when needed | Use verified target facts, target numbering, and target normative vocabulary |
| Shared direct rule | H1; Strength; Scope; responsibility-ordered policy sections; Boundaries or Precedence when needed | Preserve only cross-repository policy and leave target overrides to project-local rules |
| Shared rule-generation contract | Generation Contract; Evidence; Content; Boundaries | Produce a complete target-owned candidate; never mix authoring instructions with final target policy |

## Workflow

1. Classify the artifact as a project-local rule, shared rule, or shared rule-generation contract.
   Record the evidence for that decision before drafting.
2. Define the complete policy the rule must own and the responsibilities it must exclude. Infer
   clear details from evidence; ask only when unresolved ambiguity would materially change behavior.
3. Inventory every existing claim and discovery surface. Classify each as retained, rewritten,
   removed, added, or moved to its actual owner.
4. State the rule's distribution, ownership, `Strength`, `Scope`, precedence, invariants,
   exceptions, and cross-rule boundaries from scratch before reusing current headings or sentences.
5. Select the contract shape and outline the complete candidate in the required order.
6. Write the opening metadata for precise applicability and precedence. Preserve the target's
   numbering and normative vocabulary unless current evidence requires a deliberate change.
7. Write the body as one coherent policy contract. Integrate retained facts into their natural
   sections instead of preserving the old document order.
8. Update every owned wrapper, index, language mirror, manifest, catalog, and contract test in the
   same coherent change. Preserve unrelated project-owned files and existing Git state.
9. Resolve conflicts by precedence, specificity, enforced constraints, current evidence, and
   explicit user intent. Never leave conflicting versions in different sections.
10. Read the complete candidate without the diff and apply the anti-degradation and validation
    gates. Rewrite again when any gate fails.

## Content and Boundaries

- Include only stable policy, ownership constraints, and evidence-backed decisions another capable
  agent needs to implement or review the target correctly.
- Design one coherent responsibility. Split unrelated policy into its natural owner, but do not
  fragment one invariant across rules that must always be read together.
- Match specificity to ownership: use concrete repository facts in project-local rules, stable
  cross-repository policy in shared rules, and semantic evidence categories in generation
  contracts.
- Write one obligation per bullet. Include the trigger, required behavior, and exception together
  when scope is not obvious.
- Use concrete, verifiable language and the target's normative vocabulary. Avoid unsupported best
  practices, slogans, personal taste, and rationale that adds no enforceable meaning.
- Use concise examples only when they disambiguate behavior. Do not let an example introduce policy
  absent from the normative text.
- Keep wrappers thin and update discovery surfaces only when applicability, distribution, or
  validation requires it.
- Preserve paths, commands, identifiers, code blocks, classification, `Strength`, and behavioral
  meaning in language mirrors.

## Anti-Degradation Gate

Reject and rewrite the candidate when any condition is true:

- the latest request appears as an appended note instead of changing the governing policy;
- one obligation is repeated across sections or conflicts with an older exception;
- project-local facts leak into a shared contract, or a local rule is weakened into vague generic
  advice in the name of portability;
- a shared rule-generation contract contains final target policy, or a shared rule contains
  authoring instructions for a different rule;
- a broad rule duplicates a more-specific rule or overrides it accidentally;
- a rule contains a reusable multi-step workflow that belongs in a skill;
- obsolete names, paths, assumptions, placeholders, wrappers, or abandoned policy remain;
- the document grew without adding a distinct responsibility or necessary evidence;
- the old section order survives only to minimize the diff;
- content describes change history, review discussion, or what was recently fixed.

Before acceptance, answer yes to all of these questions:

- Would this be the rule written today if no previous version existed?
- Is its project-local or shared ownership explicit and supported by the catalog or repository?
- If shared, is it unambiguously a shared rule or a shared rule-generation contract?
- Does every paragraph own unique, current, enforceable information?
- Can an agent identify applicability, precedence, obligations, overrides, exceptions, and handoff?
- Are established direction, technical choices, thresholds, `Strength`, and valid exceptions
  preserved unless the request intentionally changes them?
- Did the rewrite reduce or hold complexity unless the responsibility genuinely expanded?

## Validation and Handoff

1. Run the current rule validators and all project contract tests covering numbering, metadata,
   wrappers, mirrors, manifests, catalogs, synchronization, and ownership.
2. For a project-local rule, verify its concrete paths, commands, APIs, lints, schemas, services, and
   module claims against the target repository's real configuration and enforcement surfaces.
3. For a shared rule, forward-test the applied policy in representative contexts that exercise
   project-rule precedence, local overrides, and applicability.
4. For a shared rule-generation contract, generate or simulate at least one complete target
   candidate and verify that target facts come from evidence rather than the generator. Use
   materially different targets when the contract claims broad portability.
5. Compare language mirrors structurally and preserve commands, relative paths, identifiers, code
   blocks, classification, `Strength`, and behavioral meaning.
6. Run repository formatting and diff-integrity checks, then inspect the complete final rule and its
   discovery surfaces once more rather than reviewing only changed lines.
7. Do not report success while placeholders, absolute path literals, unsupported claims, stale
   discovery surfaces, failed checks, or unresolved ownership conflicts remain.

## Result

Report whether the artifact is a project-local rule, shared rule, or shared rule-generation
contract; then report the selected contract shape, preserved direction, globally rewritten
responsibilities, removed duplication or stale content, owned discovery surfaces, synchronized
mirrors, and exact validation results.
