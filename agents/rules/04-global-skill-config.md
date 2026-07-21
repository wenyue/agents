# Workflow Configuration

Strength: `Mandatory`

Scope: Subagent delegation, Superpowers activation and execution-plan language, worktree workflow
ownership and timing, and Git safety.

## Delegation

- Automatically authorize the agent to use subagents when needed.

## Superpowers

- `superpowers:using-superpowers` is disabled and must not be invoked. Evaluate other
  `superpowers:*` skills directly under their own trigger conditions and applicable higher-priority
  rules.
- Invoke `superpowers:brainstorming` only when the user explicitly requests brainstorming.
- Use English for concrete Superpowers execution plans. This exception applies to step-by-step
  implementation plans, not design documents.

## Worktree Workflow

- Use `track-worktree-time` for every task that creates or reuses a linked Git worktree for code
  changes. Create one task receipt before worktree preparation, attach every attributable
  participating agent session, record attribution gaps for participants without stable session IDs,
  and include its reconciled post-hoc metrics report in the final handoff.
- Subject to the Superpowers policy above, let `superpowers:using-git-worktrees` own worktree
  creation timing, detection, consent, location, and creation.
- After creating a worktree, use the target repository's `worktree-environment-setup` skill when it
  exists, then run the baseline verification required by `superpowers:using-git-worktrees`.
- When implementation is complete, use `worktree-integrate`. Its default review mode returns changes
  to the current checkout as unstaged or untracked work while preserving the current `HEAD`, index,
  and unrelated local changes.
- Use `worktree-integrate` commit mode only when the user explicitly requests local integration with
  a commit, and keep all business changes in one commit.
- Use `superpowers:finishing-a-development-branch` for pull-request, keep-branch, or discard
  outcomes.

## Git Safety

- Do not overwrite, stash, reset, clean, or silently discard pre-existing local changes.
- A same-file overlap is not automatically a blocker. Merge it when confidence is high and the
  result can be verified; otherwise stop and ask.
- Do not push or create a pull request unless the user explicitly requests that remote action.
