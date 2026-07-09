---
name: project-development-workflow
description: Use when defining, generating, or validating a target repository's local project development workflow skill.
---

# Project Development Workflow

This public skill is a local project skill placeholder and generation contract. Do not use this
file as the final workflow inside a target repository.

## Generation Contract

During setup, `update-project-rules` creates the target repository's
`.agents/skills/project-development-workflow/SKILL.md` when it is missing. The generated target
skill starts as `Status: Unverified` and must stay unverified until a real workflow test proves it.

The generated target skill is the procedural counterpart to `.agents/rules/20-project-tools.md`.
That rule records tooling facts and verification requirements; this skill turns those facts into an
executable workflow.

The generated target skill must describe:

- How to create or enter an isolated development worktree.
- How required agent instruction paths are made available in that worktree.
- How to bootstrap dependencies and generated files from repository evidence.
- Which verification commands run inside the worktree and after merge-back.
- Which review checkpoints are required before merge-back.
- Which git operations are allowed in the worktree and which remain forbidden.
- How to merge back without overwriting unrelated original-workspace changes.

Prefer generated scripts for deterministic operations. Put scripts under
`.agents/skills/project-development-workflow/scripts/` when the target repository has enough
evidence to generate them safely.

## Acceptance

The generated target skill is not accepted until it passes a real end-to-end workflow test.
Simulation or static inspection is insufficient.

Acceptance must include:

1. Create a real git worktree from the target repository.
2. Ensure the worktree can read the generated workflow skill and required agent instructions.
3. Run the documented bootstrap flow to completion.
4. Run the documented verification commands expected to pass in a prepared worktree.
5. Make a harmless test change and exercise the merge-back path.
6. After merge-back, run authoritative verification in the original workspace.
7. Confirm the original workspace remains usable after the full flow.

If any acceptance step is blocked by missing dependencies, credentials, services, or generated
assets, report the exact blocker and keep the generated target skill marked `Status: Unverified`.

## Update Rules

When refreshing the target skill:

- Use current repository evidence, not this placeholder's examples, for concrete commands.
- Keep the workflow consistent with `.agents/rules/20-project-tools.md`.
- Preserve target-specific facts unless repository evidence proves they are stale.
- Regenerate scripts and references together with `SKILL.md`; do not leave mixed-version workflow
  assets.
