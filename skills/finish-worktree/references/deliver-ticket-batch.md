# Deliver Ticket Batch

Require the controller-owned Batch Worktree as source, the final local checkout as target, the
immutable batch base as `expected_head`, `target_policy=exact-head-fast-forward-only`, current
whole-batch review and full verification, `history_policy=preserve-ordered-task-commits` with the
ordered Task Commits and optional review tail, controller-owned recovery refs, and the matching
authorized outcome. This mode authorizes no remote or tracker action.

## Finalize and Deliver

1. Require the final target `HEAD` to equal the immutable batch base. Movement, conflict, or
   ancestry mismatch stops with evidence retained; do not merge or rebase.
2. Require full verification and whole-batch review of the complete Spec and frozen ticket set for
   the exact Batch Worktree head and tree, with no blocking finding.
3. Derive any Batch Review Commit message from the accepted source and repository convention. Ask
   only when those sources permit materially different meanings.
4. Prove the ordered first-parent Task Commit range. Preserve every per-ticket Task Commit and
   consolidate only an optional review-fix checkpoint tail into at most one Batch Review Commit.
5. Prove any created Batch Review Commit has the expected sole parent, a tree byte-identical to the
   reviewed source, successful hooks, and a clean worktree.
6. Fast-forward the unchanged target, run full target verification, prove the reviewed tree and
   unrelated state, and perform only controller-authorized Git cleanup. Delete or retain recovery
   refs exactly as authorized; preserve all owned state on failure unless the exact attempted
   mutation has a proven owned rollback.

Completion preserves the ordered Task Commits and contains at most one tree-matching Batch Review
Commit. Return the common result plus the Task Commit range, optional Batch Review Commit, and Git
delivery proof for the controller's later tracker completion.
