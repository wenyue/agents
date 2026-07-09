---
name: project-development-workflow
description: Use when defining, generating, or validating a target repository's local project development workflow skill.
---

# Project Development Workflow

This public skill is a local project skill placeholder and generation contract. Do not use this
file as the final workflow inside a target repository.

`update-project-rules` must generate a project-specific copy from repository facts, then keep that
copy refreshed the same way it refreshes local project rules.

The generated target skill is the procedural counterpart to `.agents/rules/20-project-tools.md`.
That rule records tooling facts and verification requirements; this skill turns those facts into an
executable worktree, bootstrap, verification, review, and merge-back workflow.

## Generation Contract

Generate the target repository skill at `.agents/skills/project-development-workflow/`.

The generated skill must describe:

- How to create or enter an isolated development worktree.
- How to detect whether required agent instruction paths are tracked, ignored, generated, or
  absent in the worktree, and how to make only the missing required paths available there.
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
- `copy_agent_assets.sh`: when needed, copy only required agent instruction paths that are
  local-only, ignored, or absent from the worktree. If the required paths are already tracked and
  present, the generated workflow should skip this script or make it a no-op.
- `merge_back_workspace.sh`: integrate the completed worktree result back into the original
  workspace while refusing to overwrite unrelated local changes.

When a script cannot be generated safely, the generated skill must state the missing evidence and
require the agent to stop before running that part of the workflow.

## Acceptance

The generated target-repository skill is not accepted until it passes a real end-to-end workflow
test. Simulation or static inspection is insufficient.

Acceptance must include:

1. Create a real git worktree from the target repository.
2. Ensure the worktree can read the generated `project-development-workflow` skill and any required
   agent instructions. Copy assets only when they are required and missing from the worktree.
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
- Keep the workflow consistent with `.agents/rules/20-project-tools.md`; update the rule facts when
  the workflow exposes stale or missing tooling facts.
- Keep public constraints in rules and procedural execution in this skill.
- Preserve target-specific facts unless the repository evidence proves they are stale.
- Regenerate scripts and references together with `SKILL.md`; do not leave mixed-version workflow
  assets.
