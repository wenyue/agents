# Stage Ticket into Batch

Require the worker-owned Ticket Task Worktree as source, the Batch Worktree as target, its exact
ticket base as `expected_head`, `target_policy=exact-head-fast-forward-only`, worker self-review and
required focused and repository verification, `history_policy=consolidate-checkpoints`, controller
recovery ownership, and the matching authorized outcome. This mode authorizes no remote or tracker
action.

## Finalize and Stage

1. Require the Batch Worktree `HEAD` and tree to equal the exact ticket base. Movement, conflict,
   or ancestry mismatch stops with evidence retained; do not merge or rebase.
2. Require worker self-review and focused and repository verification for the exact source head and
   tree, with no blocking finding.
3. Derive the commit message from the accepted source and repository convention. Ask only when
   those sources permit materially different meanings.
4. Create a unique recovery ref and run `scripts/consolidate_task_commit.py` against the exact
   target. Prove the Task Commit has the expected sole parent, a tree byte-identical to the
   self-reviewed source, successful hooks, and a clean worktree.
5. Fast-forward the Batch Worktree by exactly that Task Commit, prove the resulting identity and
   ancestry, transfer recovery to the controller, and perform only authorized Ticket Task Worktree
   cleanup. Retain and transfer recovery refs; preserve all owned state on failure unless the exact
   attempted mutation has a proven owned rollback.

Completion requires exactly one Task Commit appended to the Batch Worktree with recovery
transferred. Return the common result plus the checkpoint range, staged Task Commit, resulting Batch
Worktree identity, and staging proof.
