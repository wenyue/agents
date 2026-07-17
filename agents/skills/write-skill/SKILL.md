---
name: write-skill
description: Use when creating, rewriting, or materially updating agent skills, including project-local skills, shared skills, and skill-generation contracts.
---

# Write Skill

Create one discoverable, executable, evidence-backed skill that another agent can use without hidden
context. Rebuild the complete job within the skill's scope on every invocation instead of preserving
the shape of earlier edits.

## Classify

Use distribution, ownership, and the requested output to select one class before authoring.

| Condition | Class |
| --- | --- |
| One repository owns and executes the complete job | Project-local skill |
| The distributed skill executes the same stable workflow across repositories | Shared skill |
| The distributed artifact authors a complete target-owned skill | Shared skill-generation contract |

Removing local details does not make a skill shared. Classify it as shared only when the workflow
itself remains stable across repositories and target-specific facts can be discovered at runtime;
otherwise keep it project-local.

A project-local or shared skill may be operational, diagnostic, or an orchestrator. Use that
distinction only when it changes ownership, execution, review gates, or completion conditions.

## Evidence

Collect only evidence that can change the skill's behavior, ownership, resources, or validation.

### Task and Failure Evidence

Capture the user's outcome, triggers, constraints, examples, compatibility needs, and failure
expectations. Define what starts the job, what completes it, when it must stop, and what must be
reported when work cannot finish.

Treat the existing skill as evidence and an omission check, not as the preferred outline. Separate
reusable execution knowledge from change history, project policy, personal taste, and explanations
that belong in project documentation.

### Owned-Surface Evidence

Inspect the complete owned skill directory, scripts, references, assets, mirrors, tests, real usage,
and every discovery or distribution surface that can change with it. For a project-local skill,
also inspect current code, configuration, commands, services, generated ownership, and verification
behavior in the owning repository. Treat concrete claims as facts to prove, not placeholders.

### Portability and Generation Evidence

For a shared skill, inspect representative repositories and platforms to find the minimum directly
executable behavior that remains valid across them, then record what the skill must discover at
runtime. For a shared skill-generation contract, identify the evidence categories every target must
collect, then inspect at least one representative target and the generation, review, acceptance,
and handoff surfaces that own the candidate.

## Author

1. Define the complete job, trigger, outcome, start condition, completion condition, stop conditions,
   failure behavior, and responsibilities the skill excludes.
2. Synthesize the full candidate from current user intent and evidence. Preserve intended outcomes,
   verified decisions, and safety boundaries; remove stale, duplicated, contradictory, or misplaced
   content and resources. Organize the result as the skill you would author today, placing each
   requirement where it belongs instead of appending a note or preserving old order for a smaller
   diff.
3. Put each requirement in the skill section or skill-owned resource responsible for it. If the
   requested skill does not own a requirement, do not add it there. Modify the owning skill only if
   it is already within the user's requested scope; otherwise get explicit user approval first.
4. Modify only skills and the skill-owned resources, wrappers, indexes, manifests, mirrors, and
   contract tests required to execute or distribute them. Report any other required change as out of
   scope.
5. Read the complete candidate without the diff and revise it until every paragraph contributes
   unique, current, executable information.

Every instruction must have one clear interpretation. Make its actor, trigger, conditions, action,
stop or completion conditions, and expected result explicit wherever they affect execution. Do not
broaden, narrow, weaken, strengthen, or otherwise reinterpret it without new evidence or explicit
user approval.

Prefer the desired outcome, relevant facts, and decision boundaries over procedural narration. Give
the implementing agent freedom when several approaches are valid; prescribe ordered steps when
sequence affects correctness or safety. Use a script when repeated deterministic behavior is more
reliable than generated instructions.

Tracked skills use repository-relative, skill-root-relative, or stable protocol-owned paths, never
machine-specific absolute paths. When a runtime tool needs an absolute path, derive it from a
discovered root or task input rather than persisting it in the skill.

Refer to another rule or skill by the canonical name declared or recognized by the target system,
never by its filesystem path. Use paths only for owned files or resources whose location is part of
the current contract.

Use the selected skill class to set its execution and content boundaries:

- for a project-local skill, encode verified project facts and finish at the repository's requested
  outcome while keeping project policy in rules;
- for a shared skill, replace project-specific assumptions with runtime discovery, skill-owned
  resources, stable protocol paths, and explicit stop conditions while preserving one supported
  outcome across target contexts;
- for a shared skill-generation contract, separate authoring, the generated contract, review,
  acceptance, and handoff while keeping the target skill's runtime procedure out of the generator.

## Skill Contract

### Core Document

Start with discovery metadata:

```markdown
---
name: lowercase-hyphenated-name
description: Use when [concrete triggers and situations].
---
```

Frontmatter contains only `name` and `description`; the name is no longer than 64 characters and
matches its directory. The description supports reliable selection without summarizing the workflow
that loads after activation.

Follow the metadata with one H1 and a short outcome-and-boundary paragraph. Make ownership, start,
completion, stop, failure, validation, and handoff discoverable in the body. Add sections because the
job needs them, not to satisfy a universal template.

Choose the remaining body by responsibility and applicability:

- project-local operational or diagnostic skills include Evidence or Preconditions, Workflow or
  Phases, Stop Conditions, Validation, and Result;
- project-local orchestrators make Ownership, Managed Assets, Workflow, review or acceptance gates,
  Validation, and Output explicit without absorbing component contracts;
- shared operational or diagnostic skills use the direct shape but discover target facts before
  mutation;
- shared orchestrators require Ownership, Managed Assets, Reconciliation Workflow, separate Review
  Gate and Acceptance Gate, Validation, and Output while leaving target policy to project-local rules;
- shared skill-generation contracts require Evidence, Authoring Workflow, Generated Skill Contract,
  Review Gate, Acceptance Gate, and Handoff.

### Resources

Keep core decisions in `SKILL.md`. Move conditional or detailed material to directly referenced
resources only when the body states when to load it; keep references one level deep. Add scripts only
for repeated deterministic or fragile operations, with explicit dependencies, errors, recovery, and
safe representative tests. Add assets only when the skill uses them in an output.

Do not add README, changelog, installation, or quick-reference files unless an external packaging
contract requires them. Keep one source of truth for each instruction and keep wrappers limited to
required platform metadata plus a source reference.

### Review, Acceptance, and Handoff

Keep review and acceptance as separate decisions whenever both apply. For a shared
skill-generation contract:

- the Review Gate reviews the complete candidate first;
- the Acceptance Gate exercises the complete generated skill in a representative target context;
- Handoff follows only after both decisions pass.

Hand off only after review and acceptance pass. Include the accepted candidate, review decision,
acceptance evidence, and unresolved or not-run items. If either gate fails, stop and report instead
of handing the candidate off as accepted.

### Scripted Workflows

For a project-local skill, choose either scripts that match the project's established language and
runtime, such as Python in a Python project or Dart in a Dart project, or paired `.sh` and `.ps1`
entry points.

For any shared skill, including a shared skill-generation contract, require paired `.sh` and `.ps1`
entry points for every skill-owned scripted workflow. Both must target the same supported outcome
while allowing evidence-backed platform differences.

A target-owned project-local skill produced by a generation contract follows the project-local rule
above; its scripts do not become shared merely because its generator is shared.

## Validate

### Content Review

- Verify classification, ownership, discovery metadata, outcome, start, completion, stop, failure,
  validation, resources, and handoff by reading the final skill rather than only changed lines.
- Confirm changes are limited to skills and their owned surfaces.
- Check the final candidate for ambiguity or semantic drift: every instruction must have one clear
  interpretation, and its meaning may change only with new evidence or explicit user approval. If
  either condition fails, reject the candidate.
- Review each subsection by responsibility. Keep requirements that apply to every class in common
  text; state conditional requirements where their subject is owned; never create parallel class
  subsections merely for symmetry.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, and behavior.

### Execution

- For the project-matched option, test the script using the project's established language and runtime
  on safe representative inputs.
- For the paired-entry option, validate only the current platform's entry point: `.ps1` on Windows and
  `.sh` on all other platforms. Do not require validation of the other entry point on the current host.
- Test the changed workflow and owned resources for normal completion, relevant stop or failure
  behavior, explicit errors, and recovery.
- For a shared skill, test representative contexts that exercise runtime discovery, project-rule
  precedence, and stop conditions; use materially different contexts when broad portability is claimed.
- For a shared skill-generation contract, first review the complete candidate, then accept at least
  one complete target skill by exercising its workflow in a representative target context. Validate
  the generated skill's scripts according to that skill's own class.

### Distribution

Run the current validators, contract tests, and diff-integrity checks for every owned resource and
required discovery surface. Confirm applicable wrappers, indexes, manifests, mirrors, and other
distribution surfaces remain aligned.

Do not report success while evidence is unresolved, behavior is unsupported, owned resources or
required discovery surfaces are stale or unreachable, or required checks fail or remain unreported.

## Result

Report the artifact class, owning artifact or repository, final document structure and gates,
preserved decisions, removed or moved content and resources, updated discovery and distribution
surfaces and language mirrors, and exact validation outcomes.
