# Complete the Run

Enter only after every frozen ticket has a proven Task Commit in the Batch Worktree's ordered range.

1. Run full verification and invoke `code-review` using the immutable batch base as the fixed point
   and the complete Spec and frozen tickets as acceptance sources.
2. Address blocking findings as batch-review Checkpoint Commits. After every correction, rerun full
   verification and the same whole-batch review. Continue only when both gates pass for the same
   final `HEAD` and tree; an unresolved finding or failed gate enters **Stop and Recovery**.
3. Invoke `finish-worktree` in the controller's Agent context with a complete
   `deliver-ticket-batch` Finalization Contract derived from current evidence and containing no
   tracker data.
4. Independently prove exact Batch Delivery, preserved ordered per-ticket Task Commits, at most one
   Batch Review Commit, and target verification. Any mismatch enters **Stop and Recovery**.
5. Only after delivery proof, complete tracker tickets in dependency order. On one transition
   failure, retain later claims and enter **Stop and Recovery** without rolling back delivery or
   changing a later ticket.

Complete only when Batch Delivery, every Ticket Completion, claim removal, and authorized Git
cleanup are proven. Report the frozen order, immutable base, target and batch branches, workers,
Task Commits, whole-batch review and verification, optional Batch Review Commit, tracker
transitions, cleanup, and exclusions.
