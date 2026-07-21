---
name: track-worktree-time
description: Use when a task creates or reuses a linked Git worktree for code changes.
---

# Track Worktree Task Metrics

Create one minimal task receipt, then derive wall-clock, token, estimated cost, and observed tool
activity from registered session logs after completion. Do not maintain manual phase transitions.

## Workflow

1. Before worktree preparation, run `start --task "<summary>" --repository "<repository>"
   --worktree "<intended-worktree>"` and retain the task ID. Codex uses `CODEX_THREAD_ID`; its
   latest user-message timestamp sets the boundary without storing message content. Otherwise pass
   stable `--client` and `--session-id` values together.
2. Run `attach <task-id>` once for every additional attributable session. Use `--entire-session`
   only when that session was created for this task after `start`; otherwise capture its baseline.
3. When a participant has no stable session ID, run `gap <task-id> --label "<participant>"
   --reason "<reason>"`. This makes whole-task attribution partial; never guess by workspace or date.
4. Use `report <task-id>` only for a non-mutating snapshot. After integration or the selected
   completion outcome, run `finish <task-id>` and include its post-hoc Markdown report in the final
   handoff. `finish` closes the boundary, so final-response generation is excluded.

On POSIX, prefix commands with `sh .agents/skills/track-worktree-time/scripts/task-metrics.sh`.
On Windows, use `powershell -File .agents/skills/track-worktree-time/scripts/task-metrics.ps1`.
Both invoke the deterministic Python 3.11+ `scripts/timing.py` core.

## Metric Contract

- `wall-clock` is receipt start-to-finish elapsed time.
- Tokscale token, cost, and model activity are finish-minus-baseline deltas for explicitly registered
  client/session/model rows. Match rollout-prefixed IDs only by stable session-ID suffix.
- `model activity` is summed processing time; `tool activity` classifies completed Codex tool-call
  intervals post-hoc. They may overlap and are not wall-clock phases. Do not calculate a separate
  parallel-duration metric.
- Missing logs, incomplete calls, gaps, and unreconciled snapshots produce concrete unavailable or
  partial diagnostics. Never infer that an unobserved category did not occur.
- Label money as Tokscale `estimated API-equivalent cost`, not billed cost.

## Privacy and Failure Boundaries

- Use raw Tokscale `--json --group-by client,session,model`. Never invoke summarizers,
  `tokscale report` task grouping, `tokscale submit`, or network publication.
- Read transcripts transiently. Persist only counts, durations, identifiers, and diagnostics—never
  prompts, responses, commands, or tool output.
- Tokscale is optional enrichment; failures must not prevent wall-clock completion.
- `scripts/timing.py` may finish legacy schema-1 ledgers, whose token and cost remain unavailable.

## Validation and Result

Confirm one receipt exists, included sessions were explicitly registered, counters never decrease,
and partial/unavailable metrics explain why. Report timestamps, wall-clock, registered sessions,
attribution gaps, token categories, summed model activity, Tokscale version and estimated cost when
available, observed tool activity, diagnostics, and any recovery.
