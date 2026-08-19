---
name: create-worktree
description: Use when state-changing repository work requires an isolated Task or Batch Worktree for parallel execution, host or workflow isolation, or protection of the current checkout.
---

# Create Worktree

Create or reuse one named linked Git worktree and leave it ready for its owning workflow without changing
the base checkout. This Skill owns worktree selection, creation, validation, Task or Batch Worktree
qualification, and preparation handoff; it does not own business implementation, completed-change
integration, or cleanup.

## Preconditions

1. Inspect `git worktree list --porcelain`, the current branch and `HEAD`, the Git common directory,
   and the base checkout's staged, unstaged, and untracked state. Identify one intended base branch
   and commit; stop when the base is detached or ambiguous.
2. Select exactly one role: a Task Worktree for one accepted task, or a Batch Worktree for one
   frozen Ticket Batch. Choose a lowercase hyphenated slug and a named branch. Follow a verified
   repository branch convention; otherwise use `worktree/<slug>`. A current host-created worktree
   selected for reuse takes precedence over the absence check; when creating instead, stop if the
   branch or intended path already exists rather than attaching or overwriting it implicitly.
3. Record the base branch, base commit, existing worktrees, existing local branches, and base
   checkout status before any mutation.

## Select the Worktree

- Reuse the current worktree when the host already created a linked, named worktree for this task or
  batch. Verify its branch and base before continuing.
- Otherwise select `<base-root>/.worktrees/<slug>` and use the host's native worktree creation
  capability when available; record which lifecycle owner created it.
- Ensure the root `.gitignore` contains the repository-relative entry `.worktrees/`. When it is
  absent, append exactly that entry while preserving existing content and record the edit as an
  intentional project-owned change. Stop instead when `.gitignore` is generated, read-only, or has
  ambiguous ownership.
- Before creating under `.worktrees`, require `git check-ignore` to prove the selected path is
  ignored. A global exclude or `.git/info/exclude` does not replace the repository `.gitignore`
  entry.
- Obtain any permission required to create the selected directory. Treat permission as authorization
  for that exact path and worktree, not for unrelated Git or filesystem changes.

## Create and Validate

1. Immediately before creation, confirm the recorded base branch and `HEAD` have not moved and the
   selected path and branch remain absent. If the base moved, stop without creating anything and
   report the recorded and current commits plus the preserved snapshot to the owning workflow.
2. For a Git fallback, create the named branch and linked worktree from the recorded base commit
   with `git -C <base-root> worktree add -b <task-branch> <worktree-path> <base-commit>`.
3. Verify through `git worktree list --porcelain` that the resulting path, branch, and `HEAD` match
   the selected values. Confirm the base checkout's `HEAD`, index tree, and pre-existing local state
   still match the recorded snapshot; allow only the recorded `.worktrees/` `.gitignore` addition.
4. If creation fails, inspect both Git worktree metadata and the selected path before retrying.
   Remove only incomplete artifacts proven to have been created by this attempt and containing no
   user work; otherwise retain them and report the exact recovery required. After safe removal,
   return to pre-creation validation and retry at most once. A second failure stops with all
   remaining evidence retained.

## Prepare for Implementation

1. Continue inside the selected worktree. When the target repository provides
   `worktree-environment-setup`, apply it to prepare dependencies, generated inputs, and required
   services.
2. Run the repository's declared baseline verification after environment preparation. Treat a
   failing baseline as pre-existing evidence and stop before implementation unless the user accepts
   that baseline explicitly. When the repository declares no baseline verification, stop without
   qualification unless the owning workflow or user explicitly accepts the unavailable baseline for
   this worktree; do not substitute completed-change verification or invent a command.
3. Qualify the selected role only when the worktree has one named branch, its baseline is clean or
   explicitly accepted, and every local path belongs exclusively to that role's accepted scope. A
   Task Worktree belongs to one accepted task. A Batch Worktree belongs to one frozen Ticket Batch,
   records its base as the immutable delivery target, and may contain only that batch's ordered Task
   Commits and batch-review checkpoints. A reused worktree with ambiguously owned local state remains
   a worktree but receives neither qualification and authorizes no autonomous Checkpoint Commit.
4. Report the ready worktree only after its environment and baseline satisfy the target repository's
   contracts. Retain a failed worktree for diagnosis rather than discarding evidence automatically.

## Result

Report the base checkout and commit, selected role and branch, worktree path, whether `.gitignore` changed,
creation owner, environment setup, baseline result, preserved base state, whether Task Worktree
or Batch Worktree qualification passed and why, and the owner responsible for later integration or
cleanup.
