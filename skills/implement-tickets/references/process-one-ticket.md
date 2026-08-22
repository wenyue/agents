# Process One Ticket

Enter with the selected dependency-ready frozen ticket, an unchanged Batch Worktree, and
the controller's current batch record. This path has one `staged` exit; every other result enters
**Stop and Recovery** in the main Skill.

## Claim and Isolate

1. Re-read the ticket and its blockers immediately before claiming. Stop on a material status,
   requirement, or edge change.
2. Use the configured tracker's documented compare-and-set Ticket Batch claim with staged-blocker
   proof. Record the prior state and claim; stop when no safe claim operation is documented.
3. Record the Batch Worktree path, branch, exact `HEAD`, tree, and immutable base. Select an absent
   ticket-specific task slug, path, and branch.
4. Treat those recorded facts as the worker's isolation request. The worker, not the controller,
   creates and qualifies the Ticket Task Worktree.

## Dispatch One Worker

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
5. Invoke `finish-worktree` with a complete `stage-ticket-into-batch` Finalization Contract derived
   from current evidence.
6. Independently recheck the finalizer result and return it unchanged with the ticket and worker
   identities and the verification and self-review evidence. The finalizer owns its result fields.

At any phase before invoking `finish-worktree`, a non-complete result or missing decision returns one
structured Worker Recovery Handoff containing:

- `status` (`stopped` or `failed`), ticket and worker identities, `completed_phase`, and
  `failed_phase`;
- Task Worktree path, branch, exact base, `HEAD`, tree, qualification, and owned local-state facts;
- the exact Checkpoint Commit range, trees, publication facts, and uncommitted state;
- each verification command, result, and associated `HEAD` and tree, plus self-review evidence and
  unresolved findings;
- every retained worktree, branch, commit, recovery ref, and other useful recovery state;
- the exact blocker, mismatch, error, or missing decision; and
- `next_owner` and the exact next action.

Preserve all reported Git and recovery state. The controller neither replaces the worker nor
touches another ticket before entering **Stop and Recovery**.

## Verify Staging

1. Require a complete worker result and independently verify the worker and ticket mapping, Task
   Commit parent and tree, evidence, cleanup, transferred recovery refs, and that the Batch Worktree
   advanced from the supplied ticket base by exactly the returned Task Commit. Any mismatch enters
   **Stop and Recovery**.
2. Keep the ticket claimed and record its Task Commit in the frozen graph. A Staged Ticket may
   unlock dependants inside this run but is neither delivered nor completed.
3. Re-read the frozen contracts. A material contract change enters **Stop and Recovery**; otherwise
   return the `staged` exit to the main Skill.
