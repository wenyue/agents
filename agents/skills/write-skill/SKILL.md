---
name: write-skill
description: Use when creating, rewriting, or materially updating agent skills, including project-local skills, shared skills, and skill-generation contracts.
---

# Write Skill

Create one discoverable, executable, evidence-backed skill that another agent can use without hidden
context. Rebuild the complete owned job on every invocation instead of preserving the shape of earlier edits.

## Classify

Use distribution and ownership evidence to select one class before authoring.

| Class | Owns | Specificity |
| --- | --- | --- |
| Project-local skill | A complete job for one repository | Verified repository-relative paths, commands, services, modules, rules, and stop conditions |
| Shared skill | Stable behavior executed across repositories | Cross-repository invariants, skill-owned resources, runtime discovery, and protocol-owned paths |
| Shared skill-generation contract | Authoring of a complete target-owned skill | Target evidence categories and the generated skill's contract, not its final project procedure |

Catalogs, manifests, installation scope, sync ownership, and the requested output are stronger
classification evidence than generic wording. Deleting local details does not make a skill shared;
redesign it around stable behavior and runtime discovery or keep it project-local.

Direct skills may be operational, diagnostic, or orchestration contracts. Use that distinction only
when it changes ownership, execution, review gates, or completion conditions.

## Evidence

Collect only evidence that can change the skill's behavior, ownership, resources, or validation:

- the user's outcome, triggers, constraints, examples, compatibility needs, and failure expectations;
- the complete owned skill directory, scripts, references, assets, mirrors, tests, and real usage;
- applicable project rules, manifests, catalogs, wrappers, validators, and authoritative specifications;
- for project-local skills, current code, configuration, commands, services, generated ownership, and
  verification behavior;
- for shared artifacts, the minimum behavior or evidence categories that remain valid across
  supported repositories and platforms.

Treat the existing skill as evidence and an omission check, not as the preferred outline. Separate
reusable execution knowledge from change history, project policy, personal taste, and explanations
that belong in project documentation.

## Author

1. Define the complete job, trigger, outcome, start condition, completion condition, stop conditions,
   failure behavior, and responsibilities the skill excludes.
2. Synthesize the full candidate from current intent. Preserve supported direction and safety
   boundaries; remove stale, duplicated, contradictory, or misplaced content and resources.
   Organize the result as the skill you would author today, integrating each requirement into its
   owning phase instead of appending a note or preserving old order for a smaller diff.
3. Put each instruction at its natural owner. Keep project policy in rules and reference it from the
   skill instead of copying it.
4. Update owned resources, wrappers, manifests, mirrors, and contract tests when execution or
   distribution requires them.
5. Read the complete candidate without the diff and revise it until every paragraph contributes
   unique, current, executable information.

Prefer the desired outcome, relevant facts, and decision boundaries over procedural narration. Give
the executing agent freedom when context determines the best approach; prescribe ordered steps when
sequence affects correctness or safety; use a script when repeated deterministic behavior is more
reliable than generated instructions.

Tracked skills use repository-relative, skill-root-relative, or stable protocol-owned paths, never
machine-specific absolute paths. When a runtime tool needs an absolute path, derive it from a
discovered root or task input rather than persisting it in the skill.

Refer to another rule or skill by the canonical name declared or recognized by the target system,
never by its filesystem path. Use paths only for owned files or resources whose location is part of
the current contract.

## Skill Contract

Start with discovery metadata:

```markdown
---
name: lowercase-hyphenated-name
description: Use when [concrete triggers and situations].
---
```

Under this repository's convention, frontmatter contains only `name` and `description`; the name is
no longer than 64 characters and matches its directory. The description supports reliable selection
without summarizing the workflow that loads after activation.

Follow the metadata with one H1 and a short outcome-and-boundary paragraph. Make ownership, start,
completion, stop, failure, validation, and handoff discoverable in the body. Add sections because the
job needs them, not to satisfy a universal template.

| Contract shape | Required content | Additional constraint |
| --- | --- | --- |
| Project-local operational or diagnostic | Evidence or Preconditions; Workflow or Phases; Stop Conditions; Validation; Result | Use verified project facts and finish at the requested outcome |
| Project-local orchestrator | Ownership; Managed Assets; Workflow; Review or Acceptance gates; Validation; Output | Coordinate components without absorbing their contracts |
| Shared operational or diagnostic | Evidence or Preconditions; Workflow or Phases; Stop Conditions; Validation; Result | Discover target facts before mutation |
| Shared orchestrator | Ownership; Managed Assets; Reconciliation Workflow; Review Gate; Acceptance Gate; Validation; Output | Keep orchestration, review, and acceptance distinct |
| Shared skill-generation contract | Evidence; Authoring Workflow; Generated Skill Contract; Review and Handoff | Produce a complete target-owned candidate without mixing authoring instructions with its runtime procedure |

Keep core decisions in `SKILL.md`. Move conditional or detailed material to directly referenced
resources only when the body states when to load it; keep references one level deep. Add scripts only
for repeated deterministic or fragile operations, with explicit dependencies, errors, recovery, and
safe representative tests. Add assets only when the skill uses them in an output.

Do not add README, changelog, installation, or quick-reference files unless an external packaging
contract requires them. Keep one source of truth for each instruction and keep wrappers limited to
required platform metadata plus a source reference.

## Validate

- Verify classification, ownership, discovery metadata, outcome, start, completion, stop, failure,
  validation, resources, and handoff by reading the final skill rather than only changed lines.
- For a project-local skill, run its changed workflow and resources against current repository facts.
- For a shared skill, test representative contexts that exercise runtime discovery, project-rule
  precedence, and stop conditions.
- For a generation contract, simulate at least one complete target skill; use materially different
  targets when broad portability is claimed.
- Test changed scripts on safe representative inputs and confirm explicit error and recovery behavior.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, and behavior.
- Run the current validators, contract tests, and diff-integrity checks for every owned resource and
  discovery surface.

Do not report success while evidence is unresolved, resources are stale or unreachable, behavior is
unsupported, or required checks fail or remain unreported.

## Result

Report the artifact class, natural owner, resulting contract shape, preserved decisions, removed or
moved content and resources, updated discovery surfaces and mirrors, and exact validation outcomes.
