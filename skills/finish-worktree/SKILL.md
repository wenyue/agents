---
name: finish-worktree
description: Finalize a standalone Task Worktree, stage one ticket into a Batch Worktree, or deliver a reviewed Ticket Batch through a closed Git contract with verified history, recovery, and cleanup.
---

# Finish Worktree

Finalize one qualified worktree lifecycle while preserving checkpoint recovery and unrelated local
state. This Skill validates evidence, consolidates authorized history, executes one Git protocol,
verifies its result, and performs owned cleanup. Callers retain implementation, formal review,
Ticket dependencies, tracker state, and Issue completion.

## Establish Completion Context

1. Accept one closed Finalization Contract with `mode` exactly `standalone-task`,
   `stage-ticket-into-batch`, or `deliver-ticket-batch`. Every mode supplies `source` worktree,
   branch, exact `head` and `tree`, `creation_owner`, and `scope_owner`; `target` checkout, branch,
   `expected_head`, and `target_policy`; `evidence` fixed point, acceptance sources, review kind and
   result, reviewed head and tree, verification commands and results, and findings;
   `history_policy` and complete owned range; recovery refs and current and next owners; authorized
   cleanup and retained state; and one `authorized_outcome`. Reject unknown modes, cross-mode
   fields, missing values, and implicit remote authority.
2. For `standalone-task`, require `history_policy=consolidate-checkpoints`, the complete unpublished
   checkpoint range, a target policy matching the selected standalone procedure,
   `evidence.review_kind=formal-review`, and `authorized_outcome` exactly `merge-locally`,
   `create-pull-request`, `keep-for-later`, or `return-for-review`. `discard` is outside the
   contract.
3. For `stage-ticket-into-batch`, require the worker-owned Ticket Task Worktree as source, the Batch
   Worktree as target, its exact ticket base as `expected_head`,
   `target_policy=exact-head-fast-forward-only`, worker self-review and required verification,
   `history_policy=consolidate-checkpoints`, controller recovery ownership, and the matching
   authorized outcome.
4. For `deliver-ticket-batch`, require the controller-owned Batch Worktree as source, the final
   local checkout as target, immutable batch base as `expected_head`,
   `target_policy=exact-head-fast-forward-only`, current whole-batch review and full verification,
   `history_policy=preserve-ordered-task-commits` with the ordered Task Commits and optional review
   tail, controller-owned recovery refs, and the matching authorized outcome.
5. Re-derive all named Git identities, clean owned state, ancestry, ranges, publication, evidence,
   recovery, and ownership. Snapshot each affected checkout's branch, `HEAD`, index tree, staged,
   unstaged, and untracked state. Immediately before every mutation, recheck all facts it depends
   on. Stop on stale, ambiguous, published, or unrelated state.

Completion criterion: one complete mode, owned history, exact source and target, current evidence,
authorized recovery and cleanup, and preserved unrelated state are proven.

## Select One Outcome

- **Merge locally:** advance the recorded local base branch to the Task Commit and clean up when
  its creation owner permits.
- **Create a pull request:** push the Task Commit, create the pull request, and retain local task
  state.
- **Keep for later:** preserve the consolidated task branch and worktree.
- **Return for review:** materialize the Task Commit's net result in the base working tree while
  preserving its `HEAD`, index, and unrelated changes.

For `standalone-task`, use the contract's already-authorized outcome. Execute discard only after a
separate explicit destructive instruction, without accepting a contract or consolidating history;
verify it and delete only owned recovery refs through expected-old-value checks. The batch modes
authorize only their matching local Git outcome and no remote or tracker action.

The selected standalone outcome determines the target. Read only its matching procedure:

- merge locally: [`references/merge-local.md`](references/merge-local.md)
- create a pull request: [`references/create-pull-request.md`](references/create-pull-request.md)
- keep for later: [`references/keep-for-later.md`](references/keep-for-later.md)
- return for review: [`references/return-for-review.md`](references/return-for-review.md)
- explicit discard: [`references/discard.md`](references/discard.md)

## Finalize Reviewed History

1. For `standalone-task`, refresh the target and detect **Already Delivered** only through current
   ancestry or equivalent-change evidence plus required verification. A moved target may be merged
   into the task branch only when accepted evidence determines conflict behavior; synchronization
   invalidates review and returns the changed task to its implementation workflow.
2. For `stage-ticket-into-batch`, require the Batch Worktree `HEAD` and tree to equal the exact
   ticket base. For `deliver-ticket-batch`, require the final target `HEAD` to equal the immutable
   batch base. Batch modes permit no merge or rebase; movement, conflict, or ancestry mismatch
   stops with evidence retained.
3. On an allowed standalone conflict, inspect accepted behavior and both sides before invoking
   `resolving-merge-conflicts`. When evidence permits multiple results, restore pre-merge task state
   and request a decision. A resolved synchronization returns for verification and formal review.
4. Validate mode-specific evidence: standalone formal review covers the accepted task at the exact
   fixed point and source tree; staging covers one ticket through worker self-review and focused and
   repository verification; delivery covers the complete Spec and frozen ticket set through full
   verification and whole-batch review for the exact Batch Worktree head and tree. Require no
   blocking finding.
5. Derive commit messages from the accepted source and repository convention. Ask only when those
   sources permit materially different meanings.
6. For standalone or staging, create a unique recovery ref and run
   `scripts/consolidate_task_commit.py` against the exact target. For batch delivery, preserve every
   ordered per-ticket Task Commit and consolidate only an optional review-fix checkpoint tail into
   at most one Batch Review Commit.
7. Prove each created commit has the expected sole parent, tree equal to the reviewed or
   self-reviewed source tree, successful hooks, and a clean worktree. Byte-identical tree proof is
   required to keep review and verification current after commit identity changes.

Completion criterion: standalone history is one proven Task Commit or Already Delivered; staging
is exactly one Task Commit appended to the Batch Worktree with recovery transferred; delivery
preserves the ordered Task Commits and contains at most one tree-matching Batch Review Commit.

## Complete Already Delivered

Complete this terminal branch without creating a Task Commit:

- Apply the selected standalone procedure's **Already Delivered** exit.

Recheck the target, verify the outcome, and delete only workflow-owned recovery refs through
expected-old-value checks. Cleanup failure retains remaining refs and fails the outcome.

## Execute and Verify

1. For a standalone outcome, execute only its selected procedure and final rechecks, mutations,
   verification, recovery, and handoff.
2. For staging, fast-forward the Batch Worktree by exactly the tree-matching Task Commit, prove its
   resulting identity and ancestry, transfer recovery to the controller, perform only authorized
   Ticket Task Worktree cleanup, and return the staging proof.
3. For delivery, prove the ordered first-parent range, consolidate only an optional review tail,
   fast-forward the unchanged target, run full target verification, prove the reviewed tree and
   unrelated state, and perform only controller-authorized Git cleanup.
4. Delete or retain recovery refs exactly as authorized after successful standalone or batch
   delivery. Staging retains and transfers its refs. Preserve all owned state on failure unless an
   exact attempted mutation has a proven owned rollback.

Completion criterion: the selected standalone outcome, staging handoff, or reviewed batch delivery
and final tree are proven; otherwise return the exact failed phase, preserved state, and next owner.

## Safety and Recovery

- Create recovery data before rewriting history or changing target working state. Restore only
  state owned by the failed mutation; preserve every state item whose ownership is unproven.
- Use no pull, stash, hard reset, clean, force push, rebase, or merge commit on a base or batch
  branch. Rewrite only unpublished checkpoints and preserve staged per-ticket Task Commits.
- Delegate host-created worktree cleanup to its host; remove a Git-created worktree or branch only
  with proven creation ownership and contract authority.

## Result

Return `status` (`complete`, `stopped`, or `failed`), `mode`, source and target identities before
and after, applicable checkpoint and Task Commit ranges, optional Batch Review Commit, evidence and
verification for the final tree, retained/transferred/deleted recovery refs, retained/removed
worktrees and branches, `next_owner`, and exact next action. A non-complete result also includes the
failed phase, mismatch or error, and preserved recovery state. A staging result identifies the
staged Task Commit and resulting Batch Worktree; a delivery result supplies Git delivery proof for
the controller's later tracker completion.
