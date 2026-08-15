---
name: finish-worktree
description: Use when implementation checkpoints in a Task Worktree are ready for final review, consolidation into one Task Commit, and a local, pull-request, retained, review, or discard outcome.
---

# Finish Worktree

Complete one Task Worktree lifecycle while preserving checkpoint recovery and pre-existing base
state. Own target synchronization, final review, Task Commit consolidation, outcome selection,
authorization, execution, verification, recovery, and lifecycle cleanup; leave implementation and
initial worktree setup to their owning workflows.

## Establish Completion Context

1. Require a Task Worktree qualified by `create-worktree`, on one named task branch with a
   non-detached `HEAD`. Confirm implementation, its initial review, and relevant verification are
   complete.
2. Require a clean worktree whose task work is entirely represented by Checkpoint Commits. Return
   staged, unstaged, or untracked task work to implementation; stop when any path has ambiguous
   ownership.
3. Discover the intended base checkout and branch, Git common directory, creation owner, and the
   candidate delivery target for each permitted outcome. Record the task `HEAD`, merge base, complete
   checkpoint range and paths, target state, upstream state, and publication state.
4. Stop before consolidation when any Checkpoint Commit is already published. Preserve published
   history and route later review fixes through the repository's pull-request update workflow.
5. Snapshot the base branch, `HEAD`, index tree, staged changes, unstaged changes, and untracked
   paths before offering an outcome.

Completion criterion: one unpublished, clean Task Worktree, its complete checkpoint history, every
applicable outcome target, and one unchanged base checkout are proven from current evidence.

## Select One Outcome

- **Merge locally:** Advance the recorded local base branch to the Task Commit and clean up the
  linked worktree when its creation owner permits it.
- **Create a pull request:** Push the Task Commit, create the pull request, and retain local task
  state for follow-up.
- **Keep for later:** Preserve the consolidated task branch and worktree.
- **Return for review:** Materialize the Task Commit's net result in the base working tree while
  keeping its `HEAD`, index, and unrelated local changes unchanged.

If an accepted instruction already selects exactly one outcome, use it. Otherwise present these
four outcomes and wait before mutating task, base, or remote state. Treat discard as a special
destructive outcome only when explicitly requested; execute its procedure without consolidating.
For discard, read and execute only `references/discard.md`, verify its result, and report completion;
skip target finalization and Task Commit checks below. After discard verification succeeds, delete
each workflow-created recovery ref with an expected-old-value check. A cleanup failure retains the
remaining refs and makes the outcome fail.

The selected outcome determines the exact delivery target. Resolve it before finalization, then
read only the matching procedure for outcome-specific execution:

- merge locally: [`references/merge-local.md`](references/merge-local.md)
- create a pull request: [`references/create-pull-request.md`](references/create-pull-request.md)
- keep for later: [`references/keep-for-later.md`](references/keep-for-later.md)
- return for review: [`references/return-for-review.md`](references/return-for-review.md)
- explicit discard: [`references/discard.md`](references/discard.md)

## Finalize One Task Commit

1. Refresh the selected target through the repository's authorized policy and record its exact
   commit. Before changing the task branch, test whether the target already contains the complete
   accepted task result through current ancestry or equivalent-change evidence plus the task's
   required verification. When that proof passes, enter **Already Delivered** and skip target
   synchronization, final consolidation, and Task Commit creation. An empty or inconclusive diff is
   not proof; continue this workflow unless the accepted behavior is verified on the target.
2. When the target is not an ancestor of the task `HEAD`, merge it into the task branch as a
   Checkpoint Commit so each conflict is resolved once against the task's net result.
3. On conflict, inspect the accepted task source, target changes, and conflicting paths before
   choosing a resolver. When the evidence permits one behavior, invoke `resolving-merge-conflicts`
   to resolve and complete the merge. When multiple behaviors remain reasonable, abort the merge,
   restore the pre-merge task state, and ask the user to decide.
4. Run affected verification and `code-review` against the synchronized target and clean task
   `HEAD`. Commit each review-fix round separately as a Checkpoint Commit associated with its
   findings, without bypassing commit hooks. Repeat verification and review until no blocking
   finding remains. A changed target invalidates this evidence and returns to step 1.
5. Derive the Task Commit message from the accepted issue, Spec, Ticket, or conversation and the
   repository's convention. Ask only when those sources permit materially different meanings.
6. Choose a unique, absent local recovery ref name, then run `scripts/consolidate_task_commit.py`
   with the exact target commit, message file, and recovery ref name. Before rewriting history, the
   script atomically creates that ref at the current checkpoint `HEAD`, uses the repository's normal
   commit workflow, and atomically moves the task branch from its recorded old `HEAD` to one Task
   Commit.
7. Prove the Task Commit has the selected target as its sole parent, its tree is byte-identical to
   the reviewed checkpoint `HEAD`, commit hooks succeeded, and the Task Worktree is clean. A target
   movement before the selected outcome completes returns to step 1 and uses a new recovery ref.

Completion criterion: one clean, reviewed, verified, unpublished Task Commit represents the entire
task and every recovery ref needed to restore its Checkpoint Commits remains available, or the
selected target is proven Already Delivered without creating an empty commit.

## Complete Already Delivered

Use the already-selected outcome without manufacturing a Task Commit:

- **Merge locally:** Verify the local base still points to the proven target, treat integration as
  complete, and perform only cleanup authorized by the merge-local outcome.
- **Create a pull request:** Report that the resolved pull-request base has no task diff, do not push
  or create an empty pull request, and retain the task branch and worktree for follow-up.
- **Keep for later:** Preserve the task branch and worktree exactly as recorded.
- **Return for review:** Report that the base has no task diff, leave its working tree and index
  unchanged, and retain the task branch and worktree as review evidence.

Recheck the proven target immediately before completion. A moved target invalidates Already
Delivered and returns to finalization. Report the proof, skipped mutations, preserved task state,
and any authorized cleanup. After the outcome is verified, delete each workflow-created recovery
ref with an expected-old-value check; a cleanup failure retains the remaining refs and makes the
outcome fail. Then stop without entering Task Commit execution below.

## Execute and Verify

1. Recheck the Task Commit, selected target, base snapshot, and relevant remote state immediately
   before the selected procedure mutates state. Re-finalize when the target moved; request direction
   when the outcome is no longer safe or unambiguous.
2. Execute only the selected procedure and its required verification. The selection authorizes its
   named operations and exact resolved targets, not broader repository, filesystem, or remote work.
3. Verify the resulting branch, worktree, checkout, index, local-change, and remote state against
   both the selected outcome and the original snapshots.
4. After successful outcome verification, delete each workflow-created recovery ref with an
   expected-old-value check. Preserve every recovery ref on failure.

Completion criterion: the selected outcome and recovery cleanup are proven complete, or all task
and recovery evidence is retained with the exact failed operation and next decision reported.

## Safety and Recovery

- Preserve all pre-existing base-local changes. Resolve a shared pathname only when the result is
  unambiguous, task-scoped, and verifiable.
- Create recovery data before rewriting task history or changing base working files. Restore only
  state owned by a failed operation; retain the Task Worktree and recovery data when verification
  fails.
- Use no pull, stash, hard reset, clean, force push, or merge commit on the base branch. Rewrite only
  an unpublished task branch through the consolidation workflow.
- Delegate cleanup of a host-created worktree to that host. Remove a Git-created worktree or task
  branch only when the selected procedure permits cleanup and exact ownership is proven.

## Result

Report the selected outcome and authorization, synchronized target, checkpoint range, review and
verification evidence, Task Commit and message source, conflict decisions, base mutations,
preserved local state, recovery refs, remote result, and every retained or removed worktree and
branch.
