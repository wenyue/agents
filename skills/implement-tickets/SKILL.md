---
name: implement-tickets
description: Implement the remaining agent-ready tickets as one unattended sequential Ticket Batch. Give each fresh worker its complete Task Worktree lifecycle, preserve one Task Commit per ticket, then review and deliver the frozen batch.
---

# Implement Tickets

Run one frozen Ticket Batch as a dependency-ordered pipeline.

## Establish the Run

1. Read the configured issue-tracker instructions, referenced Spec or parent source, and every
   ticket in the requested effort. Infer an omitted effort only when context identifies exactly one
   ticket set; otherwise ask for it.
2. Snapshot identifiers, published order, statuses, blocking edges, and acceptance criteria. Include
   only agent-ready work; exclude completed, rejected, human-owned, information-blocked, and claimed
   tickets.
3. Require every blocker to resolve to a frozen ticket or completed external dependency and the
   graph to be acyclic. Use published order to break readiness ties.
4. Identify the named local target checkout and branch. Require accepted local-delivery authority;
   ask once before tracker or Git mutation if target or outcome remains ambiguous.
5. In the controller's Agent context, invoke `create-worktree` from the exact target `HEAD` to create
   one qualified Batch Worktree and branch. Record that commit and tree as the immutable batch base.

The run is ready when the frozen graph, unchanged target, qualified Batch Worktree, authorized local
delivery, and first dependency-ready ticket are established. If unfinished tickets remain but none
is ready, report unresolved edges and stop without a claim.

## Process One Ticket

Process exactly one dependency-ready ticket at a time. A frozen blocker is satisfied only when its
Task Commit is present in the Batch Worktree's recorded ordered range; tracker status is not proof.

### Claim and Isolate

1. Re-read the ticket and blockers immediately before claiming; stop on a material status,
   requirement, or edge change.
2. Use the configured tracker's compare-and-set Ticket Batch claim with staged-blocker proof.
   Record the prior state and claim; stop when no safe claim operation is documented.
3. Record the Batch Worktree path, branch, exact `HEAD`, tree, and immutable base. Select an absent
   ticket-specific task slug, path, and branch.
4. Treat these recorded facts as the worker's isolation request. The worker, not the controller,
   creates and qualifies the Ticket Task Worktree.

### Dispatch One Worker

Start one fresh write-capable worker Agent and give it one complete handoff:

- `ticket`: identifier, complete contract, acceptance sources, and frozen blocker proof;
- `batch`: worktree, branch, exact `head` and `tree`, immutable base, and controller identity;
- `task_worktree`: intended slug, path, branch, worker as scope owner, controller as integration
  owner, and permitted cleanup owner;
- `verification`: focused and repository-required commands;
- `finalization`: `mode=stage-ticket-into-batch`, the Batch Worktree target,
  `target_policy=exact-head-fast-forward-only`, recovery transfer to the controller, and authorized
  cleanup; and
- `tracker_boundary`: no worker claim, release, completion, or other tracker transition.

The worker performs this complete lifecycle in its existing Agent context:

1. Recheck every supplied Batch and intended task identity, then invoke `create-worktree` from the
   exact supplied Batch Worktree `HEAD`. Continue only with a qualified Task Worktree whose owners,
   base, path, branch, and baseline match the handoff.
2. Establish the current mechanism and seams, implement only the ticket, use `tdd` when behavior has
   a testable seam, and create recoverable Checkpoint Commits through the normal commit workflow.
3. Run focused verification during implementation and every repository-required check at the end.
4. Self-review the complete ticket diff against its acceptance criteria and correct every observed
   mismatch. The worker does not invoke formal `code-review`.
5. Read [`finish-worktree`'s Finalization Contract](../finish-worktree/SKILL.md),
   construct the complete `stage-ticket-into-batch` contract from current evidence, and invoke
   `finish-worktree`.
6. Recheck the finalizer result and return `status`, ticket and worker identities, completed or
   failed phase, Task Worktree and checkpoint facts, verification and self-review evidence, the
   complete finalizer result, staged Task Commit and resulting Batch Worktree identity, cleanup,
   retained recovery state, exact blocker, and next owner.

On failure or a missing decision, preserve useful Git and recovery state and return the non-complete
result. The worker changes no tracker state. The controller does not replace the worker or touch
another ticket and enters **Stop and Recovery**.

### Finalize and Integrate

1. The controller independently verifies the worker, ticket mapping, Task Commit parent and tree,
   Batch Worktree fast-forward, evidence, cleanup, and transferred recovery refs.
2. Continue only when the Batch Worktree advanced from the supplied ticket base by exactly the
   returned Task Commit and the worker result is complete; otherwise enter **Stop and Recovery**.
3. Keep the ticket claimed and record its Task Commit in the frozen graph. A Staged Ticket may
   unlock dependants inside this run but is neither delivered nor completed.
4. Re-read frozen contracts, choose the earliest published ticket whose blockers are staged, and
   repeat from **Claim and Isolate**. Stop on a material contract change.

## Complete the Run

After every ticket is staged, run full verification and one formal `code-review` over
`git diff <batch-base>...HEAD` with the immutable base as fixed point and the complete Spec and
frozen tickets as acceptance sources. Address blocking findings as batch-review Checkpoint Commits,
then rerun both gates for the same final `HEAD` and tree. Read
[`finish-worktree`'s Finalization Contract](../finish-worktree/SKILL.md), build
the complete `deliver-ticket-batch` contract without tracker data, and invoke it in the controller's
Agent context. Independently prove exact delivery, preserved per-ticket commits, at most one Batch
Review Commit, and target verification. Only then complete tracker tickets in dependency order; on
one transition failure, retain later claims and stop without rolling back delivery or changing a
later ticket.

Complete only when delivery, tracker completion, claim removal, and authorized Git cleanup are
proven. Report the frozen order, base, branches, workers, Task Commits, review and verification,
optional Batch Review Commit, tracker transitions, cleanup, and exclusions. Tickets published after
the snapshot require a new run.

## Stop and Recovery

Stop on the first ambiguous requirement, changed contract, invalid graph, claim conflict, worker or
staging failure, blocking review finding, target movement, delivery or verification failure, or
tracker mismatch.

Report all retained batch, target, claim, commit, worktree, branch, and recovery state plus the exact
failed operation and next owner. Before Batch Delivery, use only a documented compare-and-set
release in reverse dependency order; after delivery, retain unresolved claims and hand off the
documented completion operation. Perform no pull, push, pull request, force operation, rebase,
rollback, discard, or unconfigured tracker action without separate authorization.
