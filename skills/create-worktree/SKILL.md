---
name: create-worktree
description: Use when state-changing repository work requires an isolated linked Git worktree for parallel execution, host or workflow isolation, or protection of the current checkout.
---

# Create Worktree

Create or reuse one named linked Git worktree and leave it ready for implementation without changing
the base checkout. This Skill owns worktree selection, creation, validation, and preparation
handoff; it does not own business implementation, completed-change integration, or cleanup.

## Preconditions

1. Inspect `git worktree list --porcelain`, the current branch and `HEAD`, the Git common directory,
   and the base checkout's staged, unstaged, and untracked state. Identify one intended base branch
   and commit; stop when the base is detached or ambiguous.
2. Choose a lowercase hyphenated task slug and a named task branch. Follow a verified repository
   branch convention; otherwise use `worktree/<task-slug>`. Stop when the branch or intended path
   already exists rather than attaching or overwriting it implicitly.
3. Record the base branch, base commit, existing worktrees, existing local branches, and base
   checkout status before any mutation.

## Select the Worktree

- Reuse the current worktree when the host already created a linked, named worktree for this task.
  Verify its branch and base before continuing.
- Otherwise select `<base-root>/.worktrees/<task-slug>` and use the host's native worktree creation
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
   selected path and branch remain absent.
2. For a Git fallback, create the named branch and linked worktree from the recorded base commit
   with `git -C <base-root> worktree add -b <task-branch> <worktree-path> <base-commit>`.
3. Verify through `git worktree list --porcelain` that the resulting path, branch, and `HEAD` match
   the selected values. Confirm the base checkout's `HEAD`, index tree, and pre-existing local state
   still match the recorded snapshot; allow only the recorded `.worktrees/` `.gitignore` addition.
4. If creation fails, inspect both Git worktree metadata and the selected path before retrying.
   Remove only incomplete artifacts proven to have been created by this attempt and containing no
   user work; otherwise retain them and report the exact recovery required.

## Prepare for Implementation

1. Continue inside the selected worktree. When the target repository provides
   `worktree-environment-setup`, apply it to prepare dependencies, generated inputs, and required
   services.
2. Run the repository's declared baseline verification after environment preparation. Treat a
   failing baseline as pre-existing evidence and stop before implementation unless the user accepts
   that baseline explicitly.
3. Report the ready worktree only after its environment and baseline satisfy the target repository's
   contracts. Retain a failed worktree for diagnosis rather than discarding evidence automatically.

## Result

Report the base checkout and commit, task branch, worktree path, whether `.gitignore` changed,
creation owner, environment setup, baseline result, preserved base state, and the owner responsible
for later integration or cleanup.
