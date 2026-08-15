# Ordinary Artifact

An Ordinary Artifact is a Rule or Skill used directly as policy or as a triggered job. This
reference owns its lifecycle classification, runtime boundary, and representative application.

## Classify the owner boundary

| Evidence | Class | Contract |
| --- | --- | --- |
| One repository owns and directly uses the complete policy or job | Project-local | State the final behavior from verified repository facts and keep it in the narrowest project owner. |
| The same stable policy or job applies across repositories | Shared | Keep only cross-project behavior; discover project facts at runtime and leave narrower decisions local. |

Removing project details does not make an artifact Shared. A Shared claim needs at least two
independent, traceable evidence contexts in which the policy or job remains the same while relevant
local facts differ. Use actual Rules, configuration, schemas, entry points, or existing project
evidence; do not invent full projects merely to claim portability.

A Project-local claim needs the current repository evidence that affects behavior. Use a small
self-contained project only when local Rules, configuration, files, or commands must be exercised
outside the working repository.

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

- For a Project-local artifact, check its repository claims, owner boundary, real entry or
  enforcement point, and relevant local cases.
- For a Shared artifact, apply the same policy or job in at least two independent traceable
  contexts. Vary the project facts most likely to expose a hidden local assumption.
- Run owned deterministic resources through their public entry points. Report supported execution
  that the environment cannot run as untested; a controlled walkthrough may support semantic
  Acceptance but is not machine PASS.

Acceptance passes only when the artifact keeps one meaning across its claimed scope, produces one
supported result for each selected case, and requires no invented project fact, action, or exit.
