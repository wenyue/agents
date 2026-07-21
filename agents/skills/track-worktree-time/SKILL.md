---
name: track-worktree-time
description: Use when a task creates or reuses a linked Git worktree, or when its elapsed time, token usage, model activity, tool activity, or API-equivalent cost must be reported from stable agent sessions.
---

# Track Worktree Task Metrics

Create one task receipt before linked-worktree preparation, then report elapsed time and attributed
consumption after completion. Treat timing, token/cost, and tool activity as independent evidence:
one unavailable surface never makes an available surface unavailable. Do not maintain manual phase transitions.
Metric analysis is post-hoc.

## Quick Decision

| Evidence | Action |
| --- | --- |
| New linked-worktree task | Run `start` before preparation and retain the task ID. |
| Additional attributable session | Run `attach`; use `--entire-session` only for a session created for this task after `start`. |
| Active schema-2 receipt | Run `report` for a snapshot or `finish` once after the selected completion outcome. |
| Missing, closed, or schema-1 receipt | Preserve the honest timing limitation, then run `usage` with a stable session ID. |
| Tokscale unavailable or timed out | Return Codex-log token totals immediately; mark cost unavailable. |

## Workflow

1. Before worktree preparation, run `start --task "<summary>" --repository "<repository>"
   --worktree "<intended-worktree>"`. Codex uses `CODEX_THREAD_ID` when available; otherwise pass
   `--client codex --session-id <id>` together. If neither is available, request the stable session
   ID instead of inferring the newest log.
2. Run `attach <task-id>` once for every additional attributable session. For a participant without
   a stable ID, run `gap <task-id> --label "<participant>" --reason "<reason>"`.
3. Run `finish <task-id>` after integration or the selected completion outcome and include its
   Markdown report. `finish` closes the boundary, so final-response generation is excluded.
4. When reliable elapsed time cannot be recovered, do not create a retroactive receipt. Run the
   receipt-independent consumption path instead:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/track-worktree-time/scripts/task-metrics.ps1 usage --client codex --session-id <id>
```

On POSIX, replace the wrapper with
`sh .agents/skills/track-worktree-time/scripts/task-metrics.sh`. Both wrappers invoke the
deterministic Python 3.11+ `scripts/timing.py` core.

## Consumption Recovery

`usage` bounds Tokscale scanning to the Codex session log dates and filters the raw
`--json --group-by client,session,model` result by exact session-ID suffix. It requires no task
receipt and never turns whole-session consumption into task elapsed time.

If Tokscale fails, `usage` reads only the latest cumulative `token_count` event from that Codex
session. Return those token categories with source `codex-log`, mark the API-equivalent cost
unavailable, and keep the elapsed-time result unchanged. When the failure is sandbox-related and
approval is available, retry the same wrapper once outside the sandbox to recover Tokscale cost;
do not repeat cold scans.

## Metric Contract

- `wall-clock` is receipt start-to-finish elapsed time.
- Schema-2 token, cost, and model activity are finish-minus-baseline deltas for explicitly
  registered sessions. Standalone `usage` is whole-session consumption and must be labeled as such.
- `model activity` and `tool activity` are summed durations that may overlap wall-clock time.
- Missing logs, incomplete calls, attribution gaps, and unreconciled snapshots remain explicit.
- Label money as Tokscale `estimated API-equivalent cost`, never billed cost.

## Privacy And Output

Read transcripts transiently. Persist only counts, durations, identifiers, and diagnostics; never
persist prompts, responses, commands, or tool output. Never run Tokscale summarizers, task grouping,
submission, or network publication.

Report timing, consumption, and tool activity separately. Show exact integers from the script, then
format user-facing token counts as `万` in Chinese and `k` in English. Always include token source,
cost availability, registered sessions, attribution gaps, diagnostics, and any recovery used.

## Common Failures

| Failure | Correct handling |
| --- | --- |
| “The matching receipt is legacy, so consumption is unavailable.” | Report legacy timing and run `usage` independently. |
| “`CODEX_THREAD_ID` is empty, so no stable session exists.” | Ask for or accept explicit `--client` and `--session-id`. |
| “Starting a receipt now will recover earlier elapsed time.” | Do not fabricate a boundary; report timing unavailable and recover consumption. |
| “Tokscale cost failed, so token usage also failed.” | Return Codex-log tokens and mark only cost unavailable. |

Stop and correct course before claiming metrics unavailable when any of these is true:

- The only missing value is `CODEX_THREAD_ID`; an explicit stable session ID may still be supplied.
- Elapsed time is unavailable but a stable session ID can still recover consumption.
- Tokscale failed but the matching Codex log still contains cumulative token events.
- A retroactive receipt is being considered for work that already happened.
