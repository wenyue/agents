# 02 — Daily Project Check Gate

Category: enhancement
Status: resolved
Blocked by: None

## What to build

Run SmartKit's automatic environment check at most once for each canonical project, current host,
and local date. The Daily Project Check Gate must run before any detector while preserving manual
forced reruns and non-blocking failure semantics.

- [x] Resolve the project root in this order: nearest project-agent configuration, nearest Git
  marker, then current directory.
- [x] Project, host, and local date jointly define an independent daily identity.
- [x] The gate records `started` before any detector so an abnormal process exit does not trigger an
  automatic rerun that day.
- [x] `passed`, `notified`, `error`, and `started` all block later automatic checks that day.
- [x] Policy or checker changes do not bypass the daily gate; a manual force can rerun the check.
- [x] Only one concurrent `SessionStart` invocation enters the check pipeline.
- [x] If the cache cannot be written safely, diagnostics are skipped and the original task continues.
- [x] Cursor runs the check only at session start and no longer starts a check process for each prompt.
- [x] Rule delivery remains event-driven and does not enter the daily gate.

## Comments

- When this ticket was published, the worktree already contained a partially implemented but
  unaccepted version of this slice; this ticket remains the source of its acceptance criteria.
- 2026-08-10: Implemented canonical project-root resolution, project/host/date cache identity,
  started-first state, a concurrency lock, `--force`, and a fail-open gate; consolidated the Cursor
  Hook to `sessionStart`.
- 2026-08-10: `python3 -m unittest tests.test_recommended_tools` passed (31 tests).
