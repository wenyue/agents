---
name: implement-tickets
description: Implement the remaining agent-ready tickets as one unattended sequential Ticket Batch. Give each fresh worker its complete Task Worktree lifecycle, preserve one Task Commit per ticket, then review and deliver the frozen batch.
---

# Implement Tickets

This Procedure-led Skill runs one frozen Ticket Batch as a dependency-ordered pipeline. The
controller owns the frozen graph, claims, worker handoffs, batch evidence, delivery handoff, and
tracker completion. Each fresh worker owns one ticket's complete Task Worktree lifecycle.

## Establish the Run

1. Read the configured issue-tracker instructions, referenced Spec or parent source, and every
   ticket in the requested effort. Infer an omitted effort only when context identifies exactly one
   ticket set; otherwise ask for it.
2. Snapshot identifiers, published order, statuses, blocking edges, and acceptance criteria. Include
   only agent-ready work; exclude completed, rejected, human-owned, information-blocked, and claimed
   tickets.
3. Require every blocker to resolve to a frozen ticket or completed external dependency and require
   the graph to be acyclic. Use published order to break readiness ties.
4. Identify the named local target checkout and branch. Require accepted local-delivery authority;
   ask once before tracker or Git mutation if the target or outcome remains ambiguous.
5. In the controller's Agent context, invoke `create-worktree` from the exact target `HEAD` to create
   one qualified Batch Worktree and branch. Record that commit and tree as the immutable batch base.

The run is ready only when the frozen graph, unchanged target, qualified Batch Worktree, authorized
local delivery, and first dependency-ready ticket are established. If unfinished tickets remain but
none is ready, report their unresolved edges and enter **Stop and Recovery** without a claim.

## Execute the Frozen Batch

A frozen blocker is satisfied only when its Task Commit is present in the Batch Worktree's recorded
ordered range; tracker status is not proof. Process exactly one dependency-ready ticket at a time.

1. While a frozen ticket remains unstaged, read and execute
   [`references/process-one-ticket.md`](references/process-one-ticket.md) completely. After its
   `staged` exit, select the earliest published ticket whose blockers are staged and repeat.
2. After every frozen ticket is staged, read and execute
   [`references/complete-run.md`](references/complete-run.md) completely.
3. On any non-complete result, missing decision, or failed invariant, read and execute
   [`references/stop-and-recovery.md`](references/stop-and-recovery.md) completely. This exit takes
   precedence over staging another ticket or reporting completion.

Complete only through the completion criterion in `complete-run.md`. Tickets published after the
snapshot are outside this run and require a new one.
