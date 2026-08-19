---
name: finish-worktree
description: Finish a standalone Task Worktree or an accepted Ticket Batch. Verify formal-review evidence, consolidate checkpoints into Task Commits, stage per-ticket commits on a Batch Worktree, and deliver or retain the exact reviewed history safely.
---

# Finish Worktree

Complete a standalone Task Worktree or Ticket Batch lifecycle while preserving checkpoint recovery
and pre-existing base state. Own review-evidence validation, Task Commit consolidation, batch
staging, outcome selection, authorization, delivery, verification, recovery, and lifecycle cleanup;
leave implementation, formal review, and initial worktree setup to their owning workflows.

## Establish Completion Context

1. Require worktrees qualified by `create-worktree`, each on one named branch with a non-detached
   `HEAD`. Select exactly one accepted mode: finish one standalone task, stage one completed ticket
   on its Batch Worktree, or finish one fully staged Ticket Batch.
2. Require every selected worktree to be clean and its work entirely represented by commits. A
   standalone task or staged ticket supplies Checkpoint Commits; a finished batch supplies an
   ordered per-ticket Task Commit range and any batch-review checkpoints. Stop when a path or commit
   has ambiguous ownership.
3. Discover the intended base checkout and branch, Git common directory, every creation owner, and
   the exact target for the selected mode. Record the worktree `HEAD`, merge base, complete commit
   range and paths, target state, upstream state, ticket mapping, and publication state. Record the
   owning implementation workflow's supplied review and verification evidence, including its claimed
   fixed point, commit, tree, acceptance sources, result, and findings. Ticket staging supplies
   self-review evidence instead because it does not deliver accepted behavior.
4. Stop before rewriting when a selected Checkpoint Commit is already published. Preserve published
   history and route later review fixes through the repository's pull-request update workflow. A
   Ticket Batch may contain unpublished staged Task Commits but no published batch commit.
5. Snapshot every affected checkout's branch, `HEAD`, index tree, staged changes, unstaged changes,
   and untracked paths before offering or executing a result.

Completion criterion: the selected standalone or batch mode, its complete owned history, every
applicable target, supplied review evidence, and unchanged unrelated checkout state are identified
from current evidence.

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
An accepted `implement-tickets` run selects one of two internal batch outcomes instead of the four
standalone outcomes. **Stage ticket in batch** appends one self-reviewed Task Commit to the Batch
Worktree without delivering the ticket. **Finish ticket batch** locally delivers the reviewed
ordered range while preserving every per-ticket Task Commit. These outcomes authorize no remote
action.

The selected outcome determines the exact delivery target. Resolve it before finalization, then
read only the matching procedure for outcome-specific execution:

- merge locally: [`references/merge-local.md`](references/merge-local.md)
- create a pull request: [`references/create-pull-request.md`](references/create-pull-request.md)
- keep for later: [`references/keep-for-later.md`](references/keep-for-later.md)
- return for review: [`references/return-for-review.md`](references/return-for-review.md)
- explicit discard: [`references/discard.md`](references/discard.md)

## Finalize Reviewed History

1. Refresh the selected target and record its exact commit. For a standalone task, detect **Already
   Delivered** through ancestry or equivalent-change evidence plus required verification. For ticket
   staging, require the Batch Worktree `HEAD` to equal the ticket's recorded base. For batch finish,
   require the delivery target to equal the immutable batch base; target movement stops the batch.
2. A standalone task may merge a moved target into its task branch as a Checkpoint Commit, but that
   mutation invalidates its review evidence. Stop after synchronization and return the changed task
   to its implementation workflow for verification and formal review. Batch staging and finish
   permit no target merge or rebase: their recorded batch ancestry must remain linear so local
   delivery can preserve the ordered per-ticket Task Commits by fast-forward.
3. On an allowed standalone conflict, inspect the accepted source, target changes, and conflicting
   paths before choosing a resolver. Invoke `resolving-merge-conflicts` only when evidence permits
   one behavior; otherwise abort, restore the pre-merge task state, and ask the user to decide.
   After a resolved conflict, retain the synchronization checkpoint and return to the implementation
   workflow for verification and formal review. A batch conflict or ancestry mismatch stops with
   all batch evidence retained.
4. Never invoke formal `code-review`. For standalone delivery, require review evidence whose fixed
   point equals the selected target, whose reviewed commit and tree equal the clean task `HEAD`,
   whose acceptance sources match the accepted task, and whose report has no blocking finding. For
   ticket staging, require focused and repository verification plus the worker's self-review. For
   batch finish, require full verification and whole-batch review evidence from the immutable batch
   base through batch `HEAD`, using the complete Spec and every frozen ticket, with no blocking
   finding; both results must identify the current batch `HEAD` and tree. Missing, stale, or
   mismatched evidence returns to the owning implementation workflow.
5. Derive each Task Commit message from its accepted source and repository convention. One staged
   ticket uses its ticket; standalone work uses its issue, Spec, Ticket, or conversation; optional
   whole-batch review fixes use the Ticket Batch and findings. Ask only when those sources permit
   materially different meanings.
6. For standalone work or ticket staging, create a unique recovery ref and run
   `scripts/consolidate_task_commit.py` against the exact selected target. During batch finish,
   preserve the ordered per-ticket Task Commits; only review-fix Checkpoint Commits, when present,
   are consolidated into one optional Batch Review Commit on top of that range.
7. Prove every created Task Commit has the expected sole parent, its tree matches the corresponding
   reviewed or self-reviewed checkpoint `HEAD`, commit hooks succeeded, and each worktree is clean.
   Consolidation may replace reviewed checkpoint commit identities only through this byte-identical
   tree proof; the review and verification remain current for the new Task or Batch Review Commit
   because its tree is unchanged. Recheck the immutable batch base and ordered ticket mapping before
   batch delivery.

Completion criterion: standalone work has one Task Commit whose tree matches current formal-review
evidence or Already Delivered proof; ticket staging has one verified per-ticket Task Commit appended
to the Batch Worktree with recovery retained; or batch finish has one ordered range matching current
whole-batch review evidence that preserves every per-ticket Task Commit and contains at most one
Batch Review Commit.

## Complete Already Delivered

Complete this terminal branch without creating a Task Commit:

- Apply the matching standalone procedure's **Already Delivered** exit without manufacturing a
  Task Commit.

Recheck the proven target immediately before completion; a moved target invalidates the proof and
returns to finalization. After the procedure verifies its outcome, delete each workflow-created
recovery ref with an expected-old-value check. A cleanup failure retains the remaining refs and
makes the outcome fail. Then stop without entering Task Commit execution below.

## Execute and Verify

1. For a standalone outcome, execute only its selected procedure and outcome-specific final
   rechecks, mutations, verification, recovery, and handoff.
2. For ticket staging, recheck the finalized commit, base, worktrees, mapping, evidence, and
   recovery ref; fast-forward the Batch Worktree; prove it advanced by exactly the tree-matching
   Task Commit; then perform only owner-authorized ticket cleanup, transfer its recovery ref to the
   batch, return the Task Commit, and leave the ticket claimed.
3. For batch finish, recheck the immutable base, reviewed `HEAD` and tree, mapping, evidence,
   unchanged target, recovery refs, and snapshots. Stop on changed evidence or overlapping
   base-local work; otherwise fast-forward the target without squashing or a merge commit, run full
   target verification, prove the reviewed ordered range and unrelated local state, return the
   ticket list, and perform only owner-authorized cleanup.
4. After standalone or batch delivery succeeds, delete each workflow-created recovery ref with an
   expected-old-value check and perform only authorized cleanup. Ticket staging retains and reports
   its recovery ref; preserve every ref and owned worktree on failure.

Completion criterion: the standalone outcome, ticket staging handoff, or reviewed batch delivery is
proven complete; otherwise all task, batch, tracker, and recovery evidence is retained with the
exact failed operation and next decision reported.

## Safety and Recovery

- Create recovery data before rewriting task history or changing base working files. Restore only
  state owned by a failed operation; retain every Task or Batch Worktree and recovery ref when its
  verification or handoff fails.
- Use no pull, stash, hard reset, clean, force push, rebase, or merge commit on a base or batch
  branch. Rewrite only unpublished checkpoint history through the consolidation workflow; preserve
  staged per-ticket Task Commits while validating and delivering the reviewed batch.
- Delegate cleanup of a host-created worktree to that host. Remove a Git-created ticket or Batch
  Worktree and branch only when its selected procedure permits cleanup and exact ownership is proven.

## Result

Report the applicable fields for the selected mode: outcome and authorization; standalone or
immutable batch base; checkpoint and ordered Task Commit ranges; ticket mapping; formal-review or
self-review evidence and verification; optional Batch Review Commit; conflict decisions; target
mutations; tracker handoff; preserved local state; recovery refs; remote result; and retained or
removed Task and Batch Worktrees and branches.
