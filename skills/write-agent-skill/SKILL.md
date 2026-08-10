---
name: write-agent-skill
description: Use when creating, rewriting, or materially updating an Agent Skill, including project-local Skills, shared Skills, Skill-generation contracts, Skill-owned scripts, or Skill discovery and distribution surfaces.
---

# Write Agent Skill

Apply `writing-for-agents` first for general Agent-document structure, context pointers, information
hierarchy, relevance, pruning, and Skill invocation mechanics. This Skill owns Skill classification,
job boundaries, discovery, distribution, scripts, resources, and generation gates.

Produce one coherent, discoverable, executable, evidence-backed Skill that another Agent can use
without hidden context. Rebuild the complete job inside its approved scope instead of preserving the
shape of earlier edits.

## Authoring Standard

Clarity, executability, and one unambiguous interpretation are acceptance conditions. After they
pass, make the Skill as concise as possible without hiding, merging, or removing information that
changes its behavior. Make the actor, trigger, inputs, conditions, actions, stop and completion
conditions, failure behavior, and result explicit wherever they affect execution. Do not broaden,
narrow, weaken, strengthen, or otherwise reinterpret an instruction without current evidence or
explicit user approval.

## Classify

Choose one class from distribution, ownership, and the requested output before authoring.

| Condition | Class |
| --- | --- |
| One repository owns and executes the complete job | Project-local Skill |
| A distributed Skill executes the same stable workflow across repositories | Shared Skill |
| A distributed artifact authors a complete target-owned Skill | Shared Skill-generation contract |

Removing local details does not make a Skill shared. Use the shared class only when its workflow is
stable across repositories and target-specific facts can be discovered at runtime.

A project-local or shared Skill may be operational, diagnostic, or an orchestrator. Record that
distinction only when it changes ownership, execution, gates, or completion.

## Evidence

Collect only evidence that can change the job, ownership, applicability, distribution, or validation:

- define the outcome, trigger, inputs, constraints, start, completion, stop and failure behavior,
  and excluded responsibilities;
- inspect the owning Skill directory, resources, scripts, mirrors, tests, real usage, callers,
  wrappers, indexes, manifests, and other discovery or distribution entries;
- for a project-local Skill, verify every repository fact and command needed to execute it;
- for a shared Skill, inspect representative repositories and platforms plus every target fact that
  must be discovered at runtime; and
- for a Skill-generation contract, inspect a representative target plus the authoring, review,
  acceptance, and handoff surfaces.

Use an existing Skill only as evidence and an omission check. Keep project policy in Rules, runtime
facts in their owning configuration, and change history outside the final job.

### Owned Surfaces

Modify only the Skill and the owned resources, wrappers, indexes, manifests, mirrors, and contract
tests required to execute or distribute it. When another owner must change, report the dependency
and obtain approval before expanding the scope.

Tracked Skills use repository-relative, Skill-root-relative, or stable protocol-owned paths. Derive
runtime absolute paths from a discovered root or task input. Refer to another Rule or Skill by its
canonical name unless its path is part of the runtime contract.

## Author

1. Select the class and define the complete job, owner, outcome, boundaries, start, completion, stop,
   and failure behavior. This step is complete when each field has one explicit value or a verified
   reason that it does not apply.
2. Synthesize the full candidate from current user intent and verified evidence. Preserve intended
   outcomes, supported decisions, and safety boundaries; remove stale, duplicated, contradictory,
   transitional, or misplaced content and resources. Organize it as a Skill authored today rather
   than appended notes or edits shaped around a smaller diff. This step is complete when every
   current requirement and supported decision is represented once.
3. Put each requirement in the narrowest Skill section or owned resource that owns it. Modify another
   owner only when it is already within the requested scope; otherwise report the dependency and
   request approval. This step is complete when every requirement has one owner.
4. Modify only the Skill and the owned resources, wrappers, indexes, manifests, mirrors, and contract
   tests required to execute or distribute it. This step is complete when required surfaces agree
   and no unrelated owner changed.
5. Write the steady-state job from current inputs, conditions, actions, and outcomes. Keep migration
   behavior only while a current input can trigger it, with an explicit trigger and retirement
   condition. This step is complete when no history-only behavior remains.
6. Use observable conditions, actions, and outcomes. Use ordered steps when sequence affects
   correctness or safety, and a script for repeated deterministic or fragile work. This step is
   complete when every instruction can be executed without inventing a missing step.
7. Read the complete candidate without its diff. Proceed to validation only after every trigger,
   action, boundary, stop, failure, completion, validation, and handoff gap is resolved.

When the Skill creates or updates a durable Rule, apply `write-agent-rule` to that separate artifact;
this branch is complete only when its standalone review passes. For a Skill-generation contract,
preserve separate authoring, Review Gate, Acceptance Gate, and handoff evidence; this branch is
complete only when both gates record decisions and the handoff evidence is ready.

## Class Contracts

### Project-local Skill

- Encode verified repository facts and finish at the repository's requested outcome.
- Use the project's established runtime for Skill-owned scripts when one exists.
- Keep reusable procedure in the Skill and policy in project Rules.

### Shared Skill

- Replace project-specific assumptions with runtime discovery, Skill-owned resources, stable
  protocol paths, and explicit stop conditions.
- Preserve one supported outcome across target contexts; do not silently degrade it on an
  unsupported platform.
- Provide paired `.sh` and `.ps1` entry points for every Skill-owned scripted workflow. Both entry
  points must target the same outcome while allowing verified platform differences.

### Shared Skill-generation Contract

- Separate the authoring workflow from the generated Skill's runtime procedure.
- Define the target evidence and required generated outcome without inventing target facts.
- Require a Review Gate for the complete candidate and an Acceptance Gate that exercises the
  candidate in a representative target context.
- Hand off only after both gates pass. Include the candidate, supporting evidence, both decisions,
  and unresolved or untested surfaces.

## Instruction Forms

- Use numbered steps when order affects execution. Use a checklist only for independent validation,
  acceptance, or handoff conditions; each item names the action, object, and observable result.
- Add an example only when it resolves a material ambiguity. Keep it minimal and state every
  requirement in normative text rather than introducing policy through the example.
- Prefer positive requirements with observable conditions and results. Use a negative requirement
  only for a plausible harmful shortcut, paired with the required alternative or enduring
  consequence.

## Skill Contract

Use the discovery metadata and invocation choice defined by `writing-for-agents`. The Skill name is
lowercase hyphenated, no longer than 64 characters, and matches its directory. Follow one H1 with a
short outcome-and-boundary paragraph. Make ownership, start, completion, stop, failure, validation,
and handoff discoverable in the body; add sections only when the job needs them.

## Owned Resources

A Skill may reference owned resources only one level deep, and each reference must state when the
resource is required. Skill-owned scripts require explicit dependencies, failure recovery, and safe
representative tests. Add assets only when the Skill consumes them in an output.

Do not add a README, changelog, installation guide, or quick reference unless an external packaging
contract requires it. Keep wrappers limited to platform metadata and one source reference.

## Validate

### Content and Ownership

- Read the complete Skill rather than only changed lines. Verify its class, owner, discovery
  metadata, outcome, start, completion, stop, failure behavior, owned resources, scripts,
  distribution surfaces, mirrors, validation, handoff, and required gates.
- Confirm the complete candidate satisfies the Authoring Standard and remains complete and
  executable after pruning.
- Confirm every instruction, repository or platform claim, and command is supported by current
  evidence.
- Confirm the change is limited to the Skill's owned surfaces and approved dependencies.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, and behavior.

### Execution and Gates

- Validate a project-local script with the project's runtime. For paired shared entry points, run the
  current platform's entry point and report the other as not run.
- Test normal completion and every relevant stop, failure, explicit error, and recovery path for the
  changed workflow and owned resources.
- Exercise shared Skills in materially different target contexts when broad portability is claimed.
- For a generation contract, review the complete generated candidate first, then exercise its real
  workflow in a representative target and preserve separate review and acceptance evidence.

### Distribution

Run the current validators, contract tests, and diff-integrity checks for every changed owned
resource, discovery surface, or distribution surface. Do not report success while evidence, the job,
ownership, an owned resource, a required gate, or a required surface remains unresolved or
unverified.

## Result

Report the Skill class and owner, final job structure, preserved decisions, removed or moved content
and resources, changed discovery and distribution surfaces, scripts and gates, approved
dependencies, and exact validation outcomes.
