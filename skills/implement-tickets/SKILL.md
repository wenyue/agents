---
name: implement-tickets
description: Implement the remaining agent-ready tickets from the configured tracker as one unattended sequential Ticket Batch. Use one fresh worker and Task Worktree per ticket, preserve one Task Commit per ticket on a Batch Worktree, then review the complete Spec and frozen ticket set once before local delivery.
---

# Implement Tickets

Implement one frozen Ticket Batch as a dependency-ordered pipeline. The controller owns ticket
selection, delegation, batch staging, whole-batch review, delivery handoff, and tracker transitions.
Each worker owns exactly one ticket's implementation and self-review inside its Task Worktree.

## Establish the Run

1. Read the configured issue-tracker instructions, the referenced Spec or parent source, and every
   ticket in the requested effort. If the effort is not explicit, infer it only when the current
   context identifies exactly one ticket set; otherwise ask for the effort.
2. Snapshot the ticket identifiers, order, statuses, blocking edges, and acceptance criteria for
   this run. Treat only the configured tracker's agent-ready state as unimplemented work. Exclude
   completed, rejected, human-owned, information-blocked, or already-claimed tickets.
3. Validate that every blocker resolves to a ticket or an already-completed external dependency and
   that the frozen graph is acyclic. Preserve the published order as the tie-breaker when multiple
   tickets are simultaneously ready.
4. Identify the named local target branch and checkout that will receive the complete Ticket Batch.
   Require an accepted instruction selecting **merge locally** for the batch. If the target or
   outcome is not already unambiguous, ask once before changing tracker or Git state.
5. Inspect the target checkout and existing worktrees, then invoke `create-worktree` to create one
   qualified Batch Worktree and named batch branch from the exact target `HEAD`. Record that commit
   as the immutable batch base and preserve all pre-existing local state.

The run is ready when one frozen ticket graph, one unchanged local target, one qualified Batch
Worktree, one merge-local outcome, and the first dependency-ready ticket are established. If
unfinished tickets remain but none is ready, report their unresolved edges and stop without
claiming one.

## Process One Ticket

Repeat this section for exactly one dependency-ready ticket at a time. A ticket becomes ready for
this controller when each frozen blocker has a staged Task Commit on the Batch Worktree; tracker
status alone does not override that batch-local proof.

### Claim and Isolate

1. Re-read the ticket and its blockers immediately before claiming it. If its status, requirements,
   or blocking edges changed materially after the run snapshot, stop and report the changed source.
2. Use the configured tracker's documented Ticket Batch claim operation, including its staged
   blocker proof and compare-and-set guard. Record the prior state and the claim; never invent a
   tracker transition when its instructions do not define one.
3. Invoke `create-worktree` from the current Batch Worktree `HEAD`, using a ticket-specific task
   slug and branch. The delivery target remains at the immutable batch base throughout the run.
4. Continue only when `create-worktree` reports a qualified Task Worktree and a passing or explicitly
   accepted baseline. On failure, retain its evidence, restore the ticket's prior state only when
   the tracker documents a safe conditional transition, and stop the run.

### Dispatch One Worker

Start one fresh write-capable worker Agent for the ticket. Give it only the context needed to do the
job:

- the complete ticket and its acceptance source;
- the Task Worktree path and task branch;
- the target branch and exact base commit recorded by `create-worktree`;
- applicable repository instructions and verification commands; and
- the boundaries below.

The worker must:

1. Work only inside the assigned Task Worktree and implement only the assigned ticket.
2. Establish the current mechanism and affected seams before editing, then use `tdd` where the
   behavior has a testable seam.
3. Run focused verification during implementation and every repository-required check at the end.
4. Create recoverable Checkpoint Commits through the repository's normal commit workflow.
5. Self-review the complete ticket diff against its acceptance criteria and correct every observed
   mismatch. Do not invoke the formal `code-review`; the controller owns that review after every
   ticket is staged.
6. Return only after the Task Worktree is clean and its implementation, verification, self-review,
   and checkpoint range are reported. The worker must not stage, deliver, publish, clean up the
   worktree, change another ticket, or mark its ticket completed.

If implementation, verification, self-review, or a required decision cannot complete, the worker must
leave the branch, worktree, commits, and failure evidence intact and report the exact blocker. The
controller stops the run; it does not replace the worker or continue with another ticket.

### Finalize and Integrate

1. Verify the worker's reported branch, clean Task Worktree, checkpoint range, tests, and self-review
   from current evidence. Treat a worker report as evidence to inspect, not proof by itself.
2. Invoke `finish-worktree` in its accepted **stage ticket in batch** path. Let it consolidate the
   ticket checkpoints into one Task Commit, fast-forward the Batch Worktree, preserve recovery
   evidence, and clean only the completed ticket worktree.
3. Continue only when `finish-worktree` proves the Batch Worktree advanced by exactly that ticket's
   Task Commit and required verification passes. On any other exit, retain all batch, worktree,
   branch, commit, and recovery evidence, then enter **Stop and Recovery**; let that section determine
   the tracker transition from delivery evidence and compare-and-set results.
4. Keep the ticket claimed and record its staged Task Commit in the frozen graph. A staged ticket is
   sufficient to unlock its dependants inside this exclusive run but is not completed or delivered.
5. Re-read the frozen ticket contracts. Select the earliest published ticket whose frozen blockers
   are staged, and repeat from **Claim and Isolate**; stop on any material contract change.

## Complete the Run

After every included ticket is staged, run full verification and one formal `code-review` over
`git diff <batch-base>...HEAD`, using the immutable batch base as fixed point and the complete Spec
plus every frozen ticket as the acceptance sources. Address blocking findings as review-fix
Checkpoint Commits on the Batch Worktree; after every fix round, rerun full verification and the
same whole-batch review. Continue only when both pass against the same final batch `HEAD` and tree.
Then invoke `finish-worktree` in its accepted **finish ticket batch** path. Give it the immutable
batch base, complete Spec, every frozen ticket, ordered per-ticket Task Commits, exact review and
verification evidence for that final tree, tracker claims, and recovery refs. Let it validate that
evidence, consolidate all review-fix checkpoints into at most one optional Batch Review Commit with
an identical tree, and fast-forward the unchanged local target to the reviewed batch `HEAD` without
squashing the per-ticket Task Commits.
After delivery verification succeeds, use the configured tracker's documented completion operation
for every included ticket in dependency order. A transition failure stops reconciliation without
rolling back delivered commits or changing another ticket. Complete only when the target contains
the reviewed ordered range, every included ticket is completed, no run claim remains, and authorized
worktree, branch, and recovery cleanup is proven.

Report the frozen ticket set and order, immutable batch base, target and batch branches, per-ticket
worker, Task Worktree and Task Commit, whole-batch review and verification, optional Batch Review
Commit, tracker transitions, cleanup, and every excluded ticket. Do not extend the run to tickets
published after its snapshot; offer a new run for them.

## Stop and Recovery

Stop the whole run on the first ambiguous requirement, changed ticket contract, invalid dependency
graph, claim conflict, baseline failure, worker failure, staging failure, unresolved blocking review
finding, target movement, delivery or post-delivery verification failure, or tracker mismatch.

Preserve useful partial state. Report the immutable batch base, unchanged or delivered target,
current claims, staged Task Commits, exact failed operation, retained batch and ticket worktrees,
branches, checkpoints, recovery refs, and the decision or operation required to recover safely or
start a new run. When the delivery target contains no run-owned Task Commit or equivalent accepted
result, use the configured tracker's documented release operation in reverse dependency order for
every run-owned claim, retaining all Git and recovery evidence; a compare-and-set failure stops
release and reports the remaining claims. When delivery already occurred, keep unresolved claims
and hand off the documented completion operation instead. Perform no push, pull request, force
operation, rebase, rollback, discard, or remote tracker action beyond the configured claim, release,
and completion transitions unless the user separately authorizes it.
