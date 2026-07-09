---
name: project-development-workflow
description: Use when defining, generating, or validating a target repository's worktree-based project development workflow skill.
---

# Project Development Workflow

This public skill is a local project skill placeholder and generator contract. Do not use this file
as the final workflow inside a target repository.

## Generation Contract

During setup, `setup-project-agents` uses this generator contract to refresh the target
repository's `.agents/skills/project-development-workflow/SKILL.md` from current repository
evidence every time it runs.

The generated target skill is the repository-specific prompt for worktree-based development. It
must consume tooling facts from `.agents/rules/20-project-tools.md` and turn them into an
actionable execution workflow.

The generated target skill must not persist template versions, refresh reports, or status fields
that only describe one agent run. It must not set up or sync agent configuration; public asset sync
belongs to `setup-project-agents` before the local refresh step.

## What Belongs Here

- Instructions for generating a target repository's local
  `.agents/skills/project-development-workflow/SKILL.md`.
- The required workflow topics that the generated target skill must cover.
- The evidence sources that the generator must use, especially `.agents/rules/20-project-tools.md`.
- Acceptance expectations for validating the generated target workflow.
- Boundaries between agent configuration setup and ordinary development workflow execution.

## What Does Not Belong Here

- Concrete commands, ports, dependencies, or project-specific workflow facts from one target
  repository.
- A target repository's final development workflow.
- Agent asset sync, wrapper generation, or public catalog update steps.
- One-run refresh reports, template versions, timestamps, or status fields.
- Helper scripts unless target repository evidence proves they are necessary for a repeatable
  worktree operation.

## Suggested Generated Content

The generated target skill should describe:

- When to use the current workspace and when to use an isolated worktree.
- How to create or enter an isolated development worktree.
- Which existing project instructions to read again inside the worktree.
- How to bootstrap dependencies and generated files from repository evidence.
- Which verification commands run inside the worktree and after merge-back.
- Which review checkpoints are required before merge-back.
- Which git operations are allowed in the worktree and which remain forbidden.
- How to merge back without overwriting unrelated original-workspace changes.

## Verification Expectations

The generated target skill is not accepted until it passes a real end-to-end workflow test.
Simulation or static inspection is insufficient. The test must create a real git worktree, run the
generated workflow by starting from that worktree, invoke the generated skill, run the documented
bootstrap and verification commands, make a harmless tracked change, exercise the merge-back path,
and run authoritative verification in the original workspace.

If invoking the generated skill exposes missing steps, stale commands, unclear checkpoints, or
unsafe merge-back behavior, update the generated target skill and repeat the real worktree test
until the generated workflow succeeds.

If any verification step is blocked by missing dependencies, credentials, services, or generated
assets, report the exact blocker in the final output for that run.
