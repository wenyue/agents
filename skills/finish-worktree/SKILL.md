---
name: finish-worktree
description: Use when verified implementation in a named linked Git worktree is ready to be merged locally, published as a pull request, kept for later, returned to the base checkout for review, or explicitly discarded.
---

# Finish Worktree

Complete one linked-worktree lifecycle while preserving task work and pre-existing base state. Own
outcome selection, authorization, execution, verification, recovery, and lifecycle cleanup after
implementation; leave implementation and initial worktree setup to their owning workflows.

## Establish Completion Context

1. Require a linked worktree on a named task branch with a non-detached `HEAD`. Confirm the task's
   implementation, review, and relevant verification are complete.
2. Require a clean task worktree. If it contains staged, unstaged, or untracked task work, return it
   to the repository's implementation and commit workflow before finishing. Stop when ownership of
   any dirty path is ambiguous.
3. Discover the intended base checkout, base branch, Git common directory, and worktree creation
   owner from current Git evidence and the `create-worktree` result when available. Stop when one
   intended base cannot be proven.
4. Record the task `HEAD`, merge base, complete task commit range and paths, upstream state, and
   whether any task commit is already published. Preserve the complete commit history; do not
   squash it merely to finish the worktree.
5. Snapshot the base branch, `HEAD`, index tree, staged changes, unstaged changes, and untracked
   paths before offering an outcome.

Completion criterion: one clean, verified task branch and one unchanged base checkout are fully
identified, with the task range, local state, publication state, and lifecycle owner recorded.

## Select One Outcome

- **Merge locally:** Advance the recorded base branch to the verified task history and clean up the
  linked worktree when its creation owner permits it.
- **Create a pull request:** Push the task branch without rewriting published history, create the
  pull request, and retain local task state for follow-up.
- **Keep for later:** Preserve the branch and worktree exactly as they are.
- **Return for review:** Materialize the task's net result in the base working tree as unstaged or
  untracked content while keeping its `HEAD`, index, and unrelated local changes unchanged.

If an accepted user instruction already chooses exactly one outcome, use it. Otherwise present
these four outcomes and wait for the user's selection before mutating local or remote state. Treat
discard as a special destructive outcome only when the user explicitly requests it; do not include
it in the normal choices.

After selection, read only the matching procedure:

- merge locally: [`references/merge-local.md`](references/merge-local.md)
- create a pull request: [`references/create-pull-request.md`](references/create-pull-request.md)
- keep for later: [`references/keep-for-later.md`](references/keep-for-later.md)
- return for review: [`references/return-for-review.md`](references/return-for-review.md)
- explicit discard: [`references/discard.md`](references/discard.md)

## Execute and Verify

1. Immediately before the selected procedure mutates state, recheck the task `HEAD`, base branch,
   base `HEAD`, and relevant local-state snapshot. Refresh the analysis when they moved; request
   direction when the selected outcome is no longer safe or unambiguous.
2. Execute only the selected procedure and its required verification. Treat the selection as
   authorization for that outcome's named operations and exact resolved targets, not for broader
   repository, filesystem, or remote changes.
3. Verify the resulting branch, worktree, checkout, index, local-change, and remote state against
   both the selected outcome and the original snapshots.

Completion criterion: the selected outcome is proven complete, or all recoverable evidence is
retained with the exact failed operation and next decision reported.

## Safety and Recovery

- Preserve all pre-existing base-local changes. A shared pathname is not automatically a conflict;
  merge only when the result is unambiguous, task-scoped, and verifiable.
- Create recovery data outside the repository before changing base working files. Restore only
  paths touched by a failed transfer, and retain the task branch, worktree, and recovery data when
  post-operation verification fails.
- Use no pull, stash, reset, clean, force push, or merge commit. Rewrite an unpublished task branch
  only where the selected procedure permits it; stop before rewriting published history.
- Delegate cleanup of a host-created worktree to that host. Remove a Git-created worktree or task
  branch only when the selected procedure permits cleanup and exact ownership is proven.

## Result

Report the selected outcome and authorization, task range, base target, mutations, overlap or
conflict decisions, verification, preserved local state, recovery data, remote result, and every
retained or removed worktree and branch.
