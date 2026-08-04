---
name: write-skill
description: Use when creating, rewriting, or materially updating agent skills, including project-local skills, shared skills, and skill-generation contracts.
---

# Write Skill

Create one discoverable, executable, evidence-backed skill that another agent can use without hidden
context. Rebuild the complete job within the requested skill's scope instead of preserving the shape
of earlier edits.

## Authoring Priorities

Clarity, executability, and unambiguous meaning are acceptance conditions. After all three pass, make
the skill as concise as possible without weakening them.

Every instruction must have one clear interpretation. Make its actor, trigger, conditions, action,
stop or completion conditions, and expected result explicit wherever they affect execution. Use
observable predicates and direct actions. Reject a shorter version if it hides, merges, or removes
information that can change behavior.

Do not broaden, narrow, weaken, strengthen, or otherwise reinterpret an instruction without new
evidence or explicit user approval.

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

A project-local or shared skill may be operational, diagnostic, or an orchestrator. Record that
distinction only when it changes ownership, execution, gates, or completion.

## Evidence

Collect only evidence that can change behavior, ownership, resources, or validation.

### Task and Failure Evidence

Record the outcome, triggers, inputs, constraints, examples, compatibility, start, completion, stop,
and failure report. Use the existing skill only as evidence and an omission check. Exclude change
history, project policy, personal taste, and explanations owned by project documentation.

### Owned-Surface Evidence

Inspect the owned directory, resources, mirrors, tests, usage, and discovery or distribution
surfaces. For a project-local skill, also verify the repository facts and validation needed to
execute the workflow. Prove concrete claims before using them.

### Portability and Generation Evidence

For a shared skill, inspect representative repositories and platforms, keep the workflow that remains
directly executable, and state what must be discovered at runtime. For a shared skill-generation
contract, define target evidence and inspect a representative target plus the authoring, review,
acceptance, and handoff surfaces.

## Author

1. Define the job's trigger, outcome, start, completion, stop and failure behavior, and exclusions.
2. Synthesize the full candidate from current user intent and verified evidence. Preserve intended
   outcomes, verified decisions, and safety boundaries; remove stale, duplicated, contradictory, or
   misplaced content and resources. Organize the result as the skill you would author today, placing
   each requirement where it belongs instead of appending a note or preserving old order for a
   smaller diff.
3. Put each requirement in the skill section or skill-owned resource responsible for it. If the
   requested skill does not own a requirement, do not add it there. Modify the owning skill only if
   it is already within the user's requested scope; otherwise get explicit user approval first.
4. Modify only skills and the skill-owned resources, wrappers, indexes, manifests, mirrors, and
   contract tests required to execute or distribute them. Report any other required change as out
   of scope.
5. Write persistent instructions from current inputs, decisions, and outcomes. Keep a former
   command, path, name, classifier, or implementation only in an active compatibility or migration
   branch with an explicit trigger and retirement condition. Keep transition steps in that
   executable branch. When the skill creates or updates a durable rule, apply `write-rule` to that
   separate artifact and complete its standalone steady-state review before handoff.
6. Read the complete candidate without the diff. Resolve every gap or conflicting interpretation,
   then remove repetition, history, and non-actionable explanation. Give the implementing agent
   freedom when several approaches are valid; prescribe ordered steps when sequence affects
   correctness or safety. Use a script for repeated deterministic or fragile work.

Include a fact, configuration value, or implementation detail only when the agent needs it to decide
or perform an action, interpret evidence, satisfy a prerequisite, handle a failure, or report the
result. If none of those purposes needs the information, omit it. When awareness of an automatic
behavior matters but its exact configuration does not, state only the behavior.

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

## Instruction Forms

Use these forms to choose the clearest expression for each requirement; do not turn their names or
order into mandatory headings in every skill.

### Steps and Checklists

Use numbered steps (`1.`) when order affects execution. Use a Markdown task list (`- [ ]`) only for
independent validation, acceptance, or handoff conditions. Each checklist item must name one action,
its object, and the observable result to confirm. Use
`- [ ] <action> <object>; confirm <observable result>.` Start a conditional item with `If` or `When`
plus an observable predicate. Do not use a checklist to repeat the workflow or replace criteria
with phrases such as "ensure quality," "review carefully," or "follow the requirements above."

### Examples

Add an example only when it resolves a material ambiguity. Demonstrate one decisive distinction with
the smallest complete input/output, before/after, or boundary pair. Put bold `**Required**` and
`**Invalid**` labels before a binding contrast; use `**Preferred**` and `**Avoid**` for a default
with valid exceptions. Use a fenced block when exact syntax matters and one-line bullets when only
behavior matters. State every requirement in the normative text; an example must not introduce or
override one.

### Positive Requirements

Prefer a positive requirement. Use
`When <observable condition>, <subject> must <action>; the result must <observable property>.`
Omit the condition only when the requirement is unconditional. Define an output shape with its
required fields, conditional behavior with `If` or `When`, and required content with an explicit
slot or checklist item.

### Negative Requirements

Use a negative requirement only to exclude a plausible harmful shortcut not fully excluded by the
positive contract. Use
`Do not <forbidden action> when <observable trigger>; instead <required alternative>.`
If no alternative exists, state the enduring failure, safety, or compatibility consequence. Do not
use an unscoped prohibition such as "never take shortcuts," "do not be vague," or "avoid unnecessary
work."

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
completion, stop, failure, validation, and handoff discoverable in the body. Add a section only when
the job needs that responsibility.

Choose the remaining body by responsibility and applicability:

- project-local operational or diagnostic skills include Evidence or Preconditions, Workflow or
  Phases, Stop Conditions, Validation, and Result;
- project-local orchestrators make Ownership, Managed Assets, Workflow, review or acceptance gates,
  Validation, and Output explicit without absorbing component contracts;
- shared operational or diagnostic skills use the direct shape but discover target facts before
  mutation;
- shared orchestrators require Ownership, Managed Assets, Reconciliation Workflow, separate Review
  Gate and Acceptance Gate, Validation, and Output while leaving target policy to project-local
  rules;
- shared skill-generation contracts require Evidence, Authoring Workflow, Generated Skill Contract,
  Review Gate, Acceptance Gate, and Handoff.

### Resources

Keep core decisions in `SKILL.md`. Move conditional or detailed material to a directly referenced
resource only when the body states when to load it; keep references one level deep. Add scripts only
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

- Read the final skill, not only changed lines. Verify classification, ownership, discovery metadata,
  outcome, start, completion, stop, failure, validation, resources, and handoff.
- Confirm changes are limited to skills and their owned surfaces.
- Check the final candidate for ambiguity or semantic drift: every instruction must have one clear
  interpretation, and its meaning may change only with new evidence or explicit user approval. If
  either condition fails, reject the candidate.
- Reject instructions that cannot be executed from the stated context or became incomplete through
  compression.
- Read persistent instructions without the diff or prior implementation. Every former alternative
  must have a live trigger and retirement condition. Every negative requirement must identify its
  current trigger and enduring failure, safety, or compatibility consequence; otherwise state the
  current action, decision boundary, or completion condition.
- Review every durable rule produced by the skill as a separate artifact with `write-rule`;
  workflow history and transition steps are evidence for authoring, not final rule content.
- Review each subsection by responsibility. Keep common requirements in common text and conditional
  requirements with the subject that owns them.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, and behavior.

### Execution

- For the project-matched option, test the script using the project's established language and
  runtime on safe representative inputs.
- For the paired-entry option, validate only the current platform's entry point: `.ps1` on Windows
  and `.sh` on all other platforms. Do not require validation of the other entry point on the
  current host.
- Test normal completion, relevant stop or failure behavior, explicit errors, and recovery for the
  changed workflow and owned resources.
- For a shared skill, test representative contexts that exercise runtime discovery, project-rule
  precedence, and stop conditions; use materially different contexts when broad portability is
  claimed.
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
