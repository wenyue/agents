# Skill Config

Strength: `Mandatory`

Scope: Project overrides for workflow tools, worktrees, git, and prose outputs.

## Git And Worktree

- Assume `master` is the working branch — do not switch branches or ask to confirm the branch
  unless the user requests it.
- Default to the current workspace for small, direct edits.
- Use an isolated git worktree when the user requests worktree-based development, when a workflow
  skill such as `project-development-workflow` requires it, or when isolation is needed to protect
  unrelated local changes.
- Inside a dedicated workflow worktree, all git operations needed by the workflow are allowed,
  including status, diff, branch creation, commits, rebases, merges, and cleanup.
- Keep the original workspace available for final verification and merge-back. Do not overwrite
  unrelated local changes in the original workspace.
- Outside a dedicated workflow worktree, do not create commits or push unless the user explicitly
  asks for that git operation.
- When a generated workflow documents automatic merge-back, it may create the single merge-back
  commit or PR described by that workflow without asking for a second confirmation.

## Prose Output

- Use Simplified Chinese for normal user-facing prose, design documents, and other non-code prose
  files.
- Use English for concrete Superpowers execution plans. This exception applies to step-by-step
  implementation plans, not design documents.
