---
name: project-development-workflow
description: Use when defining, generating, or validating a repository-specific agent development workflow skill that coordinates isolated worktrees, project bootstrap, verification, review checkpoints, and merge-back behavior.
---

# Project Development Workflow

This public skill is a placeholder and generation contract. Do not use this file as the final
workflow inside a target repository.

`update-project-rules` must generate a project-specific copy from repository facts, then keep that
copy refreshed the same way it refreshes project-owned `20-*` rules.

## Generation Contract

Generate the target repository skill at `.agents/skills/project-development-workflow/`.

The generated skill must describe:

- How to create or enter an isolated development worktree.
- How to copy ignored local agent assets that the worktree needs, such as `AGENTS.md`, `.agents/`,
  `.codex/`, `.cursor/`, `.claude/`, and `.github/instructions/` when those paths are local-only.
- How to bootstrap the project environment from concrete repository evidence.
- Which verification commands to run inside the worktree and after merge-back.
- Which git operations are allowed in the worktree, and which operations remain forbidden.
- How to merge the finished work back to the original workspace without overwriting unrelated user
  changes.

Prefer generated scripts for deterministic operations. Put scripts under
`.agents/skills/project-development-workflow/scripts/` and make the generated skill call them
instead of re-describing fragile shell sequences.

## Required Scripts

Generate these scripts when the target repository has enough evidence for them:

- `bootstrap_worktree.sh`: install dependencies, generate required sources, and prepare the
  worktree for linting/tests.
- `copy_agent_assets.sh`: copy local-only agent instructions into the worktree when those assets are
  ignored or absent from git.
- `merge_back_workspace.sh`: integrate the completed worktree result back into the original
  workspace while refusing to overwrite unrelated local changes.

When a script cannot be generated safely, the generated skill must state the missing evidence and
require the agent to stop before running that part of the workflow.

## Acceptance

The generated target-repository skill is not accepted until it passes a real end-to-end workflow
test. Simulation or static inspection is insufficient.

Acceptance must include:

1. Create a real git worktree from the target repository.
2. Copy the generated `project-development-workflow` skill and any required local agent assets into
   that worktree.
3. Run the generated worktree bootstrap script to completion.
4. Run the generated worktree verification commands that are expected to pass in a clean prepared
   worktree.
5. Make a harmless test change in the worktree, checkpoint it with the generated workflow, and
   exercise the merge-back path.
6. After merge-back, run the target repository's authoritative verification commands in the
   original workspace.
7. Confirm the original workspace remains usable after the full flow: project imports resolve,
   generated files required by tooling exist, and the documented lint/test commands can run.

If any acceptance step is blocked by missing dependencies, credentials, services, or generated
assets, the updater must report the exact blocker and leave the generated skill marked as
unverified. Do not claim the workflow is ready.

## Update Rules

When `update-project-rules` refreshes this skill in a target repository:

- Use current repository evidence, not this placeholder's examples, for concrete commands.
- Keep public constraints in rules and procedural execution in this skill.
- Preserve target-specific facts unless the repository evidence proves they are stale.
- Regenerate scripts and references together with `SKILL.md`; do not leave mixed-version workflow
  assets.
