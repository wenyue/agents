# Ordinary Artifact

An Ordinary Artifact is a Rule or Skill used directly as policy or as a triggered job. This
reference owns its lifecycle classification, runtime boundary, and representative application.

## Classify the owner boundary

| Evidence | Class | Contract |
| --- | --- | --- |
| One repository owns and directly uses the complete policy or job | Project-local | State the final behavior from verified repository facts and keep it in the narrowest project owner. |
| The same stable policy or job applies across repositories | Shared | Keep only cross-project behavior; discover project facts at runtime and leave narrower decisions local. |

Removing project details does not make an artifact Shared. Support a Shared claim with traceable
evidence that its policy or job does not depend on one project's facts. Use actual Rules,
configuration, schemas, entry points, or existing project evidence; do not invent full projects
merely to claim portability.

A Project-local claim needs the current repository evidence that affects behavior. Use a small
self-contained project only when local Rules, configuration, files, or commands must be exercised
outside the working repository.

## Prove behavior-shaping need

When a proposed instruction exists only to change default Agent behavior and no observed failure
establishes that need, run one isolated Behavior Control before writing. Use the previously accepted
artifact for a rewrite or no candidate for a new artifact, and give a fresh Agent the same task
planned for candidate Acceptance. Preserve the raw result for review.

Do not run a control for policy authority, project facts, reference material, or an already observed
failure. If the control already produces the required behavior, omit the no-op instruction unless
separate accepted evidence requires an explicit policy.

## Author the runtime artifact

- State the final policy or job, not the authoring history, semantic ledger, review process, or
  qualification evidence.
- Keep project facts in a Project-local artifact. A Shared artifact names stable protocols and tells
  the Agent how to discover local facts or stop when discovery cannot resolve them.
- Keep each requirement in one owner. Follow more-specific project Rules and supported local
  overrides without copying them into Shared prose.
- Include only schema-required or behavior-changing instructions that cannot be derived from a
  reliably loaded owner.

## Accept representative use

Use the real policy-application seam or public job entry where available. The selected `rule.md` or
`skill.md` supplies the type-specific cases.

Give the selected cases to one isolated Acceptance Runner. Start every case from its declared frozen
input and do not let one case's result become another case's input. Expose the candidate as runtime
would, the representative tasks, and only their required context or tools. Keep expected results,
the semantic ledger, diff, author reasoning, findings, and prior run output reviewer-only. The
Runner must apply the artifact; an academic explanation or the reviewer's paper walkthrough is not
Acceptance evidence.

- For a Project-local artifact, check its repository claims, owner boundary, real entry or
  enforcement point, and relevant local cases.
- For a Shared artifact, use one representative traceable context plus direct evidence that the
  policy or job is independent of project-local facts. Add a second context only when that
  portability claim materially affects acceptance and the direct evidence cannot establish it.
- Run owned deterministic resources through their public entry points. Report supported execution
  that the environment cannot run as untested. A controlled walkthrough may explain an untested
  executable surface but cannot replace isolated application of the Ordinary Artifact.

Run each case once. Repeat an inconclusive or unstable case at most once with a new isolated Runner;
divergent outcomes fail. When Readiness required a Behavior Control, compare its raw result with the
matching candidate run, but do not expose either result to the other Runner.

Acceptance passes only when the artifact keeps one meaning across its claimed scope, produces one
supported result for each selected case, and requires no invented project fact, action, or exit.
