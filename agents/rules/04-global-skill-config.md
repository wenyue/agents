# Workflow Configuration

Strength: `Mandatory`

Scope: Subagent delegation, Superpowers activation, worktree workflow ownership, and Git safety.

## Delegation

- Automatically authorize the agent to use subagents when needed.

## Superpowers

- Treat `superpowers:using-superpowers` as disabled. Evaluate other `superpowers:*` skills directly
  under their own trigger conditions and applicable higher-priority rules.
- Use `write-skill` for Skill authoring and `write-rule` for Rule authoring. Reserve
  `superpowers:writing-skills` for an explicit user request for adversarial behavioral evaluation or
  pressure testing.
- Reserve `superpowers:brainstorming` for an explicit user request for brainstorming.

## Worktree Workflow

- Subject to the Superpowers policy above, let `superpowers:using-git-worktrees` own worktree
  creation timing, detection, consent, location, and creation.
- After creating a worktree, use the target repository's `worktree-environment-setup` skill when it
  exists, then run the baseline verification required by `superpowers:using-git-worktrees`.
- When implementation in a named linked worktree is complete and verified, present four outcomes
  before acting: merge locally into the recorded base branch; push and create a pull request; keep
  the task branch and worktree; or integrate into the current checkout.
- Execute the selected outcome without asking again: use `worktree-integrate` for current-checkout
  integration and `superpowers:finishing-a-development-branch` for local merge, pull request,
  keep-branch, or explicitly requested discard.
- Treat local merge and current-checkout integration as different outcomes even when the current
  checkout is on the recorded base branch. Local merge advances the base branch;
  `worktree-integrate` review mode keeps the current `HEAD` and index unchanged and returns task
  changes as unstaged or untracked while preserving unrelated local changes.
- Use `worktree-integrate` commit mode only when the user explicitly requests local integration with
  a commit, and keep all business changes in one commit.

## Git Safety

- Preserve pre-existing local changes. When an operation would overwrite, stash, reset, clean, or
  discard them, stop and choose a non-destructive path or request direction.
- A same-file overlap is not automatically a blocker. Merge it when confidence is high and the
  result can be verified; otherwise stop and ask.
- Push or create a pull request only after the user explicitly requests that remote action.
