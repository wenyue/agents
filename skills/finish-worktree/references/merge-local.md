# Merge Locally

Advance the recorded local base branch without flattening verified task history.

1. Confirm the base checkout is on the recorded base branch. If any task path overlaps staged,
   unstaged, or untracked base-local work in a way the merge could overwrite, leave both checkouts
   unchanged and offer return-for-review instead.
2. Require the base `HEAD` to be an ancestor of the task `HEAD`. When it is not, rebase only an
   unpublished task branch onto the current base, abort on unresolved conflict, and rerun affected
   task verification. Stop for a published task branch rather than rewriting it.
3. Recheck the task `HEAD`, base branch, base `HEAD`, and base-local snapshot immediately before
   integration, then run `git merge --ff-only <task-branch>` from the base checkout.
4. Rerun relevant verification from the base checkout. Prove the base now contains the complete
   task commit range and every unrelated base-local change still matches its snapshot.
5. After verification passes, ask the recorded lifecycle owner to remove a host-created worktree.
   For a Git-created worktree, remove that exact clean worktree from the base checkout and delete
   the now-merged task branch with Git's safe branch deletion.

If fast-forward integration or post-merge verification fails, preserve the task branch and
worktree and report the resulting base state. Do not rewrite or roll back the base automatically.
