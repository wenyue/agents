# Workflow Configuration

Strength: `Mandatory`

Scope: Subagent delegation, Superpowers activation, worktree workflow ownership, Git safety, and
prose language.

## Delegation

- The user authorizes bounded subagent delegation when a task clearly benefits from parallel work.
  Do not require repeated authorization for each subtask.
- Keep delegated work concrete and self-contained. Give code-editing subtasks disjoint ownership so
  agents do not overlap write scopes.
- Keep an immediate blocking task with the main agent when delegation would slow the critical path.
- In the final response, state what was delegated and whether delegated changes were integrated.

## Superpowers

- Do not invoke `superpowers:brainstorming` proactively.
- Invoke `superpowers:brainstorming` only when the user explicitly requests it.
- Apply other `superpowers:*` skills according to their own triggers and higher-priority rules.
- A reference to Superpowers does not by itself authorize `superpowers:brainstorming`.

## Worktree Workflow

- Subject to the Superpowers policy above, let `superpowers:using-git-worktrees` own worktree timing,
  detection, consent, location, and creation.
- After creating a worktree, use the target repository's `worktree-environment-setup` skill when it
  exists, then run the baseline verification required by `superpowers:using-git-worktrees`.
- When implementation is complete, use `worktree-integrate`. Its default review mode returns changes
  to the current checkout as unstaged or untracked work while preserving the current `HEAD`, index,
  and unrelated local changes.
- Use `worktree-integrate` commit mode only when the user explicitly requests committed local
  integration. Keep business changes in one commit; a separate infrastructure commit may add a
  missing worktree directory to `.gitignore`.
- Use `superpowers:finishing-a-development-branch` for pull-request, keep-branch, or discard
  outcomes.

## Git Safety

- Do not overwrite, stash, reset, clean, or silently discard pre-existing local changes.
- A same-file overlap is not automatically a blocker. Merge it when confidence is high and the
  result can be verified; otherwise stop and ask.
- Do not push or create a pull request unless the user explicitly requests that remote action.

## Prose Language

- Use Simplified Chinese for normal user-facing prose, design documents, and other non-code prose
  files.
- Use English for concrete Superpowers execution plans. This exception applies to step-by-step
  implementation plans, not design documents.
