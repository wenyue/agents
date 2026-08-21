# Standalone Task

Require `history_policy=consolidate-checkpoints`, the complete unpublished checkpoint range, a
target policy matching the selected procedure, `evidence.review_kind=formal-review`, and
`authorized_outcome` equal to `merge-locally`, `create-pull-request`, `keep-for-later`, or
`return-for-review`.

## Select the Authorized Outcome

Read only the matching procedure:

- merge locally: [`merge-local.md`](merge-local.md)
- create a pull request: [`create-pull-request.md`](create-pull-request.md)
- keep for later: [`keep-for-later.md`](keep-for-later.md)
- return for review: [`return-for-review.md`](return-for-review.md)

## Finalize Reviewed History

1. Refresh the target. Detect **Already Delivered** only through current ancestry or
   equivalent-change evidence plus required verification.
2. A moved target may be merged into the task branch only when accepted evidence determines
   conflict behavior. Inspect accepted behavior and both sides before invoking
   `resolving-merge-conflicts`. When evidence permits multiple results, restore pre-merge task state
   and request a decision. Any synchronization invalidates review and returns the changed task for
   verification and formal review.
3. Require formal review of the accepted task at the exact fixed point and source tree, with no
   blocking finding.
4. Derive the commit message from the accepted source and repository convention. Ask only when
   those sources permit materially different meanings.
5. Create a unique recovery ref and run `scripts/consolidate_task_commit.py` against the exact
   target. Prove the Task Commit has the expected sole parent, a tree byte-identical to the reviewed
   source, successful hooks, and a clean worktree.

Completion requires one proven Task Commit or Already Delivered.

## Execute and Verify

For Already Delivered, apply the selected procedure's matching exit without creating a Task
Commit. Otherwise execute only the selected procedure's final rechecks, mutations, verification,
recovery, and handoff. Recheck the target; for Already Delivered, delete only workflow-owned
recovery refs through expected-old-value checks. Delete or retain other recovery refs exactly as
authorized; cleanup failure retains remaining refs and fails the outcome. Preserve all owned state
on failure unless the exact attempted mutation has a proven owned rollback.

Return the common result plus applicable checkpoint and Task Commit ranges and the selected outcome
proof.
