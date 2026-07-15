---
name: worktree-environment-setup
description: Use when defining or generating a target repository's environment setup skill for an already-created Git worktree.
---

# Worktree Environment Setup

Generate a target-owned skill that prepares an already-created linked Git worktree. Build it from
current target repository evidence; do not copy a generic command list into the target skill.

## Authoring Workflow

1. Read `.agents/rules/20-project-tools.md`, package manifests, lock files, setup scripts, CI
   configuration, and generated-file ownership.
2. Identify the minimum preparation required for dependencies, generated files, local services,
   and project tooling to work inside a new linked worktree.
3. Generate these files together:
   - `.agents/skills/worktree-environment-setup/SKILL.md`;
   - `.agents/skills/worktree-environment-setup/scripts/setup.sh`;
   - `.agents/skills/worktree-environment-setup/scripts/setup.ps1`.
4. Reuse narrow repository-owned setup scripts when they already perform the required preparation.
   Implement only the missing setup in the generated scripts.
5. Document when to run the skill, the platform entry point, prerequisites, optional setup branches,
   and actionable failure reporting. Keep the executable command sequence in the scripts.

## Generated Skill Contract

- Run only inside an already-created linked worktree and reject the primary checkout before making
  changes.
- Use `scripts/setup.ps1` on Windows and `scripts/setup.sh` on non-Windows hosts. Both entry points
  must produce the same core environment result without requiring the other shell.
- Resolve paths independently of the caller's working directory, stop on failures, and be safe to
  rerun after partial setup.
- Keep expensive or task-specific preparation optional unless current repository evidence proves it
  is required for every worktree.
- Stop when the environment is ready. Do not create or remove worktrees, run baseline tests,
  implement business changes, create commits, integrate branches, or sync agent configuration.
- Hand completed-change verification to the target-owned `project-verification` skill. Do not embed
  verification trigger timing, scope selection, or result policy in the environment skill.

## Handoff

Give `setup-project-agents` the complete generated skill directory and the repository evidence used
to produce it. That workflow owns review and acceptance.
