---
name: project-development-workflow
description: Use when defining, generating, or validating a target repository's worktree-based project development workflow skill.
---

# Project Development Workflow

This public skill is a local project skill placeholder and generation contract. Do not use this
file as the final workflow inside a target repository.

## Generation Contract

During setup, `setup-project-agents` refreshes the target repository's
`.agents/skills/project-development-workflow/SKILL.md` from current repository evidence every time
it runs. The generated target skill must not persist template versions, refresh reports, or status
fields that only describe one agent run.

The generated target skill is the repository-specific prompt for Superpowers-style isolated
development work. It consumes tooling facts from `.agents/rules/20-project-tools.md` and turns them
into a worktree-based execution workflow.

The generated target skill must not set up or sync agent configuration. Agent asset synchronization
belongs to `setup-project-agents` before the local refresh step; ordinary development workflow
assumes tracked project instructions already exist in the repository checkout.

The generated target skill must describe:

- When to use the current workspace and when to use an isolated worktree.
- How to create or enter an isolated development worktree.
- Which existing project instructions to read again inside the worktree.
- How to bootstrap dependencies and generated files from repository evidence.
- Which verification commands run inside the worktree and after merge-back.
- Which review checkpoints are required before merge-back.
- Which git operations are allowed in the worktree and which remain forbidden.
- How to merge back without overwriting unrelated original-workspace changes.

Only create helper scripts when target repository evidence proves they are necessary for a
repeatable worktree operation. Do not create scripts for agent configuration setup.

## Acceptance

The generated target skill is not accepted until it passes a real end-to-end workflow test.
Simulation or static inspection is insufficient.

Acceptance must include:

1. Create a real git worktree from the target repository.
2. Read the generated workflow skill and applicable project instructions from the worktree checkout.
3. Run the documented bootstrap flow to completion.
4. Run the documented verification commands expected to pass in a prepared worktree.
5. Make a harmless test change and exercise the merge-back path.
6. After merge-back, run authoritative verification in the original workspace.
7. Confirm the original workspace remains usable after the full flow.

If any acceptance step is blocked by missing dependencies, credentials, services, or generated
assets, report the exact blocker in the final output for that run.

## Update Rules

When refreshing the target skill:

- Use current repository evidence, not this placeholder's examples, for concrete commands.
- Keep the workflow consistent with `.agents/rules/20-project-tools.md`.
- Preserve target-specific facts unless repository evidence proves they are stale.
- Regenerate scripts and references together with `SKILL.md`; do not leave mixed-version workflow
  assets.
