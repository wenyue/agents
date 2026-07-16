---
name: track-worktree-time
description: Use when a task creates or reuses a linked Git worktree for code changes.
---

# Track Worktree Time

Track one code-changing worktree task from initiation through integration and final handoff. Keep
one persistent wall-clock ledger whose accumulated phases reconcile with the complete task time.

## Preconditions

- Let the main agent own one ledger and task ID for the complete worktree task.
- Start the ledger before worktree creation or environment preparation.
- Store runtime state under the host operating system's resolved temporary directory through
  `scripts/timing.py`.
- Keep timing active through final integration and handoff, including repeated implementation,
  review, verification, and testing rounds.

## Workflow

1. Start with `python .agents/skills/track-worktree-time/scripts/timing.py start --task "<summary>"
   --repository "<repository>" --phase environment` and retain the returned task ID.
2. At each phase boundary, run `python .agents/skills/track-worktree-time/scripts/timing.py
   transition <task-id> <phase>`. Repeated phases accumulate in the same ledger.
3. Before user, approval, service, or external-state waits, run `pause <task-id>`. Continue with
   `resume <task-id> <phase>` when active work resumes.
4. Use `report <task-id>` for an in-progress snapshot.
5. After integration or the selected completion outcome, run `finish <task-id>` and include its
   reconciled Markdown report in the final handoff.

## Phases

| Phase | Ownership |
| --- | --- |
| `environment` | Worktree creation, environment setup, dependency preparation, and baseline readiness |
| `code-generation` | Code authoring, generated outputs, implementation edits, and review-driven fixes |
| `review` | Diff inspection, code review, feedback analysis, and review rounds |
| `verification` | Formatting, approved fixers, lint, analysis, builds, and static checks |
| `testing` | Unit, integration, end-to-end, regression, and other test execution |
| `integration` | Consolidation, rebase, conflict resolution, transfer, merge, and worktree cleanup |
| `waiting` | User input, approvals, external services, and blocked coordination time |
| `other` | Remaining task activity needed for complete wall-clock reconciliation |

Track the main task's active wall-clock phase. Describe parallel agent activity in the final prose
while keeping total time equal to elapsed wall-clock time rather than summed agent effort. A phase
with multiple intervals reports their accumulated duration.

## Failure Recovery

If a timing command fails, retain the last valid ledger, capture the current UTC timestamp, restore
the ledger from its JSON state, and account for the recovery interval under `other`. Complete the
task after `report` confirms that every recorded interval reconciles with total wall-clock time.

## Validation

- Confirm the task ID resolves to one JSON ledger in the system temporary directory.
- Confirm every phase transition closes the previous interval at the same timestamp.
- Confirm accumulated phase durations equal the complete task duration.
- Confirm unused phases render as `not applicable`.

## Result

Report the task start and completion timestamps, every phase duration, complete wall-clock time,
parallel activity, and any timing recovery. Preserve the phase values produced by `finish` when
localizing the surrounding final response.
