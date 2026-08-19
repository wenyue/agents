# Merge Locally

Advance the recorded local base branch to the single verified Task Commit. When the task is
**Already Delivered**, recheck that the local base still points to the proven
target, treat integration as complete, perform only cleanup authorized by this outcome, report the
proof and preserved state, and stop.

1. Confirm the base checkout is on the recorded base branch. If any task path overlaps staged,
   unstaged, or untracked base-local work in a way the merge could overwrite, leave both checkouts
   unchanged and offer return-for-review instead.
2. Require the recorded base `HEAD` to equal the Task Commit's sole parent. A moved base returns to
   target synchronization, then hands the changed task back to its implementation workflow for
   verification and formal review before consolidation or integration.
3. Recheck the Task Commit, base branch, base `HEAD`, and base-local snapshot immediately before
   integration, then run `git merge --ff-only <task-branch>` from the base checkout.
4. Rerun relevant verification from the base checkout. Prove the base now points to the Task Commit
   and every unrelated base-local change still matches its snapshot.
5. After verification passes, ask the recorded lifecycle owner to remove a host-created worktree.
   For a Git-created worktree, remove that exact clean worktree from the base checkout and delete
   the now-merged task branch with Git's safe branch deletion.

If fast-forward integration or post-merge verification fails, preserve the task branch, worktree,
and recovery refs and report the resulting base state. Do not rewrite or roll back the base
automatically.
