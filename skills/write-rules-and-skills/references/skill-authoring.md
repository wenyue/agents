# Skill authoring

A Skill owns **one complete job**. Its trigger starts the job; its completion, stop, and failure
conditions define every way out. This branch owns Skill classification, job boundaries, discovery,
distribution, scripts, resources, and generation gates.

## Pin the job

Pin the actor, trigger, inputs, preconditions, start, actions, outcome, owner, boundaries, completion,
stop, failure, validation, and handoff. Every applicable field must have one explicit value; a
missing field needs a verified reason that it does not apply.

Choose one class:

| Condition | Class | Contract |
| --- | --- | --- |
| One repository owns and executes the complete job | Project-local Skill | Encode verified repository facts, use the project's established runtime for owned scripts, and finish at the repository's requested outcome. |
| A distributed Skill executes the same stable workflow across repositories | Shared Skill | Discover target facts at runtime, use stable protocol paths and explicit stops, and preserve one supported outcome across representative contexts. |
| A distributed artifact authors a complete target-owned Skill | Shared Skill-generation contract | Separate the authoring workflow from the generated runtime job, then require distinct Review, Acceptance, and handoff gates. |

Removing local details does not make a Skill shared. Use the shared class only when its job is stable
across repositories and target-specific facts can be discovered at runtime. Record whether a Skill
is operational, diagnostic, or an orchestrator only when that distinction changes ownership,
execution, gates, or completion.

The job is pinned when every contract field has one supported interpretation and every exit is
explicit.

## Extend the evidence

In addition to the shared evidence, collect:

- the requested trigger, inputs, start, completion, stop, failure, handoff, and excluded job
  responsibilities;
- the owning Skill directory, callers, resources, scripts, indexes, and every discovery entry;
- for a project-local Skill, every repository fact and command required to execute it;
- for a shared Skill, representative repositories and platforms plus every target fact that must be
  discovered at runtime; and
- for a generation contract, a representative target plus its authoring, review, acceptance, and
  handoff surfaces.

Evidence is sufficient only when every job branch, command, repository or platform claim, and owned
surface that could affect execution has support. Keep project policy in Rules.

## Author the job

- Keep the main path visible. Put each conditional branch beside its trigger, and give every ordered
  step an observable exit. Move branch-only reference below the main path or behind a context
  pointer.
- Use concrete imperatives and exact contrasts. Keep reusable procedure in the Skill.
- Use a script for repeated deterministic or fragile work. State its dependencies, failures,
  recovery, and safe representative tests.
- When the Skill creates or updates a durable Rule, select the Rule branch too; that work completes
  only after the Rule passes its standalone gate.

For a Skill, headings represent job phases or genuine conditional branches. Numbered lists represent
ordered actions whose sequence affects correctness or safety. A checklist names each independent
validation, acceptance, or handoff action, object, and observable result.

## Shape the Skill

Use the discovery metadata and invocation choice defined by `writing-for-agents`. The Skill name is
lowercase hyphenated, no longer than 64 characters, and matches its directory. Follow one H1 with a
short paragraph that states the outcome and boundary. Keep ownership, start, completion, stop,
failure, validation, and handoff discoverable.

- Reference owned resources only one level deep, and state when each is required. Add an asset only
  when the Skill consumes it in an output.
- Keep wrappers to platform metadata and one source reference. Add no README, changelog,
  installation guide, or quick reference unless an external packaging contract requires it.
- Give every shared scripted workflow paired `.sh` and `.ps1` entry points. Both target the same
  outcome while allowing verified platform differences. Stop explicitly on an unsupported platform.
- For a generation contract, define target evidence and the required generated outcome without
  inventing target facts. Keep authoring separate from the generated Skill's runtime procedure.
  Review the complete candidate at a Review Gate, exercise it in a representative target at an
  Acceptance Gate, and hand off only after both pass. Preserve the candidate, evidence, both
  decisions, and every unresolved or untested surface.

## Whole-Skill Gate

In addition to the Whole-Artifact Gate, the Skill passes only when:

- its class, owner, discovery metadata, actor, trigger, inputs, preconditions, start, actions,
  outcome, boundaries, resources, scripts, validation, and handoff are explicit or verifiably
  inapplicable;
- completion, stop, failure, and handoff account for every exit; and
- another Agent can discover and execute the complete job without inventing a step or exit.

## Prove the Skill

- Test normal completion and every relevant stop, failure, explicit error, and recovery path for the
  changed job and its owned resources.
- Validate a project-local script with the project's runtime. For paired shared entry points, run
  the current platform's entry point and report the other as not run.
- Exercise shared Skills in materially different target contexts when claiming broad portability.
- For a generation contract, preserve separate evidence that the complete candidate passed Review
  and that its real workflow passed Acceptance in a representative target.

## Review the Skill

In the shared independent-review step, try to falsify the complete Skill against these checks:

- Reconstruct the class, owner, actor, trigger, inputs, preconditions, start, actions, outcome,
  boundaries, completion, stop, failure, validation, and handoff as a field-to-value-to-evidence
  matrix. Fail any implicit value or unsupported claim of inapplicability.
- Build a branch-to-exit matrix for the main path, every conditional path, and every relevant
  coincident failure. Fail any path with no exit, more than one unprioritized exit, an unreachable
  exit, or a completion claim that bypasses required validation, cleanup, or preservation.
- Check discovery metadata, context pointers, scripts, resources, wrappers, and platform branches
  from trigger through handoff. Fail any repeated deterministic or fragile action that lacks an
  executable owner, or any step whose command, dependency, failure, recovery, or output must be
  invented.
- Walk normal completion and representative stop, failure, recovery, and handoff cases. When result
  cardinality or ownership changes the outcome, include zero, one, and multiple results plus known
  and undiscoverable owners. For a generation contract, separately check the generated Skill's
  runtime job, Review, Acceptance, and handoff.
- Return `FAIL` with the exact passage, violated gate, and counterexample whenever another Agent
  could take a different action or exit from the same supported facts.
