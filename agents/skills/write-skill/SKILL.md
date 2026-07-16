---
name: write-skill
description: Use when creating, rewriting, or materially updating any agent skill, including project-local skills, shared skills, and shared skill-generation contracts. Rebuilds the complete skill from current evidence, assigns the correct ownership and contract shape, prevents patch-style accumulation, and validates the full skill before handoff.
---

# Write Skill

Create one coherent skill contract that another agent can execute without hidden context. Classify
its distribution and contract role before writing, then own the quality of the whole skill on every
invocation even when the request names only one defect.

## Whole-Skill Rewrite Invariant

- Treat every creation or update as a fresh synthesis from the skill's complete current purpose.
- Treat the existing skill and its resources as evidence and an omission checklist, not as an
  immutable scaffold or preferred outline.
- Reconstruct the trigger, outcome, distribution, ownership, boundaries, workflow, failure
  behavior, validation, and resources before deciding which existing wording still belongs.
- Produce a complete candidate and replace the owned artifact coherently. The diff is only a
  delivery mechanism; never optimize the skill for the smallest textual patch.
- Integrate each valid requirement at its natural owner. Remove superseded, duplicated,
  contradictory, misplaced, and change-history content.
- Do not append a new exception, note, addendum, or trailing section merely to address the latest
  request. Rewrite the governing sections and then review the entire skill again.
- Preserve the skill's established direction when current intent and evidence still support it, but
  do not preserve weak structure or stale wording solely because it already exists.

## Classify Before Authoring

Determine the ownership scope first. A shared artifact is either a shared skill, which performs its
workflow directly, or a shared skill-generation contract, which authors a complete target-owned
skill. Use manifests, catalogs, sync ownership, installation scope, and the requested output as
evidence.

| Class | Purpose and evidence | Allowed specificity | Required boundary |
| --- | --- | --- | --- |
| Project-local skill | Serves one target repository and is owned by that repository, whether handwritten or generated | Current repository-relative paths, real commands, services, modules, and project rules | Optimize for target accuracy; do not publish or generalize unsupported facts |
| Shared skill | Is distributed across repositories and performs its workflow directly | Cross-repository invariants, skill-owned relative resources, and stable protocol-owned paths | Resolve project facts at runtime and defer target-specific policy to target rules |
| Shared skill-generation contract | Is distributed across repositories to author a complete target-owned skill from target evidence | Semantic evidence categories and stable protocol-owned paths only | Describe authoring and the generated contract; do not act like the final target skill |

A project-local skill normally contains the final executable project procedure. If a project-local
skill-generation contract is explicitly required, use the generation-contract shape but keep its
evidence and output owned by that repository. Do not turn a target-specific skill into a shared skill
merely by deleting concrete paths; redesign it around a genuinely stable cross-repository contract
or keep it local.

## Evidence

Read the complete owned skill directory and collect evidence appropriate to its class.

Common evidence:

- the user's requested outcome, examples, constraints, and compatibility requirements;
- the existing `SKILL.md`, scripts, references, assets, mirrors, tests, and real usage artifacts;
- applicable ownership rules, manifests, validators, wrappers, catalogs, and authoritative
  specifications.

Class-specific evidence:

- For a project-local skill, inspect current project rules, code, configuration, commands,
  generated-file ownership, services, and verification behavior. Prefer these facts over generic
  best practices.
- For a shared skill, identify the minimum behavior that remains correct across supported
  repositories and platforms. Treat facts from one repository as examples, not defaults.
- For a shared skill-generation contract, inspect the target evidence categories its generated
  skill must consume and test the contract against materially different representative repositories.

Separate stable execution requirements from implementation history, prior edits, personal taste,
and explanations that belong in project documentation.

## Path and Ownership Rules

- Never hardcode an absolute filesystem path in a tracked skill or resource. Do not embed drive
  letters, user-home paths, checkout locations, or machine-specific temporary directories.
- When a tool requires an absolute path at runtime, derive it from the skill root, repository root,
  task input, or another discovered owner. Never persist the resolved machine path as authored
  skill content.
- Reference skill-owned scripts, references, and assets with paths relative to the skill root. Keep
  references one level deep and state exactly when to load them.
- In a project-local skill, use repository-root-relative paths for project files and record concrete
  commands only when current project evidence proves them.
- In a shared skill, use semantic project targets and runtime discovery. Keep a concrete path only
  when the shared protocol owns and standardizes it across supported targets.
- In a shared skill-generation contract, describe target files semantically unless a path belongs
  to the shared generation protocol itself. Require the generated project skill to resolve its
  concrete paths from target evidence.
- Keep universal skill-authoring constraints in `write-skill`. Keep target facts and behavioral
  policy in the target repository's rules, and reference them instead of duplicating them.
- Keep one source of truth for each instruction. A wrapper contains only platform metadata or a
  source reference unless its platform requires additional runtime fields.

## Required Format and Contract Shape

Give every skill:

1. YAML frontmatter containing only `name` and `description` under this project's convention.
2. A lowercase hyphenated name no longer than 64 characters and matching its directory.
3. A description that states what the skill does and the concrete situations that trigger it. Put
   all trigger information here because the body loads only after activation.
4. One H1 title followed by a short outcome-and-boundary paragraph.
5. Imperative instructions, explicit ownership, evidence-backed decisions, validation, and a
   defined result or handoff.

Choose the contract shape after classification. Add or omit a section only when the responsibility
proves it necessary; do not combine complete templates.

| Contract shape | Required section order | Additional constraint |
| --- | --- | --- |
| Project-local operational or diagnostic | Preconditions or Evidence; Workflow or Phases; Stop Conditions; Validation; Result | Use verified target facts and finish at the target task outcome |
| Project-local orchestrator | Ownership; Managed Assets; Workflow; Review or Acceptance gates when candidates are handed off; Validation; Output | Coordinate target-owned components without absorbing their implementation contracts |
| Shared operational or diagnostic skill | Preconditions or Evidence; Workflow or Phases; Stop Conditions; Validation; Result | Preserve only cross-repository behavior and resolve local facts before mutation |
| Shared orchestrator skill | Ownership; Managed Assets; Reconciliation Workflow; Review Gate; Acceptance Gate; Validation; Output | Keep orchestration, review, and acceptance distinct from generated or delegated implementation |
| Shared skill-generation contract | Evidence; Authoring Workflow; Generated Skill Contract; Review and Handoff | Produce a complete target-owned candidate; never mix authoring instructions with the generated runtime procedure |

## Workflow

1. Classify the artifact as a project-local skill, shared skill, or shared skill-generation
   contract. Record the evidence for that decision before drafting.
2. Define the complete job the skill must perform and the responsibilities it must exclude. Infer
   clear details from evidence; ask only when unresolved ambiguity would materially change behavior.
3. Inventory every existing claim and resource. Classify each as retained, rewritten, removed, or
   moved to its actual owner.
4. State the skill's invariants, completion condition, stop conditions, and cross-skill boundaries
   from scratch before reusing current headings or sentences.
5. Select the contract shape and outline the complete candidate in the required order.
6. Write the frontmatter for precise triggering. Remove nonstandard metadata unless the target
   runtime explicitly requires and supports it.
7. Write the body as one end-to-end contract. Integrate retained facts into their natural sections
   instead of preserving the old document order.
8. Design resources through progressive disclosure. Keep core decisions in `SKILL.md`; move only
   conditional or detailed material to directly referenced resources.
9. Update every owned resource, language mirror, public manifest, wrapper, and contract test in the
   same coherent change. Preserve unrelated project-owned files and existing Git state.
10. Read the complete candidate without the diff and apply the anti-degradation and validation gates.
    Rewrite again when any gate fails.

## Content and Resources

- Include only non-obvious procedural knowledge, domain constraints, and decisions another capable
  agent needs to perform the task reliably.
- Design one coherent unit of work. Split unrelated responsibilities instead of growing one broad
  skill, but do not fragment a single end-to-end job across skills that must always load together.
- Match specificity to fragility: explain goals and reasons where context varies; use exact ordered
  steps where mutation is risky; use executable scripts where determinism is essential.
- Keep `SKILL.md` concise enough that every instruction deserves attention. Move conditional detail
  to references before the core workflow becomes difficult to scan; keep the main file below 500
  lines unless the target runtime proves a different limit.
- Add a script only for repeated deterministic behavior or fragile operations, and test it on safe
  representative inputs. Give it explicit dependencies, errors, and recovery behavior.
- Add a reference only when the body states the condition for reading it. Add an asset only when the
  skill directly uses it in an output.
- Use concise examples only when they disambiguate behavior. Do not explain concepts the agent
  already knows, narrate obvious actions, or describe the edit that created an instruction.
- Do not create README, changelog, installation, or quick-reference files inside a skill unless an
  external packaging standard explicitly requires one.

## Anti-Degradation Gate

Reject and rewrite the candidate when any condition is true:

- the latest request appears as an appended note instead of changing the governing contract;
- one obligation is repeated across sections or conflicts with an older exception;
- project-local facts leak into a shared contract, or a local skill is weakened into vague generic
  advice in the name of portability;
- a shared skill-generation contract contains the final target procedure, or a shared skill
  contains authoring instructions for a different skill;
- obsolete names, paths, assumptions, placeholders, or abandoned workflow stages remain;
- the document grew without adding a distinct responsibility or necessary evidence;
- the old section order survives only to minimize the diff;
- content describes change history, review discussion, or what was recently fixed;
- a resource duplicates the body or is not reached by an explicit instruction.

Before acceptance, answer yes to all of these questions:

- Would this be the skill written today if no previous version existed?
- Is its project-local or shared ownership explicit and supported by the catalog or repository?
- If shared, is it unambiguously a shared skill or a shared skill-generation contract?
- Does every paragraph own unique, current, executable information?
- Can an agent identify the start condition, completion condition, stop conditions, and handoff?
- Did the rewrite reduce or hold complexity unless the responsibility genuinely expanded?

## Validation and Handoff

1. Run the current skill validator and all project contract tests covering manifests, wrappers,
   mirrors, synchronization, and ownership.
2. For a project-local skill, execute its changed scripts and representative workflow against the
   target repository's real configuration and verification surfaces.
3. For a shared skill, forward-test the actual workflow in representative contexts that exercise
   runtime discovery, target-rule precedence, and stop conditions.
4. For a shared skill-generation contract, generate or simulate at least one complete target
   candidate and verify that target facts come from evidence rather than the generator. Use
   materially different targets when the contract claims broad portability.
5. Compare language mirrors structurally and preserve commands, relative paths, identifiers, code
   blocks, classification, and behavioral meaning.
6. Run repository formatting and diff-integrity checks, then inspect the complete final skill once
   more rather than reviewing only changed lines.
7. Do not report success while placeholders, absolute path literals, unsupported claims, stale
   resources, failed checks, or unresolved ownership conflicts remain.

## Result

Report whether the artifact is a project-local skill, shared skill, or shared skill-generation
contract; then report the selected contract shape, preserved direction, globally rewritten
responsibilities, removed duplication or stale content, owned resources, synchronized surfaces, and
exact validation results.
