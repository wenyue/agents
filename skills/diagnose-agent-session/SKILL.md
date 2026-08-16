---
name: diagnose-agent-session
description: Diagnose one stable agent session when token consumption, model activity, tool calls, subagent coordination, wait behavior, incomplete calls, or API-equivalent cost may be abnormal.
---

# Diagnose Agent Session

Run one post-hoc diagnostic over the current turn and complete stable session. Use the report to
distinguish abnormal Agent behavior from missing evidence. This workflow keeps no task receipt.

## Run the diagnostic

1. Resolve the Tokscale client and stable session ID as one pair. Codex may omit both when
   `CODEX_THREAD_ID` is available. If exactly one is supplied, request both.
2. Run the matching public wrapper once. On Windows with PowerShell, use:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/diagnose-agent-session/scripts/task-metrics.ps1 diagnose --scope both --client <client> --session-id <id>
```

On POSIX, use:

```sh
sh .agents/skills/diagnose-agent-session/scripts/task-metrics.sh diagnose --scope both --client <client> --session-id <id>
```

Both wrappers require Python 3.10+. On another platform, report that no public wrapper is supported.
When sandbox access causes Tokscale failure and approval is available, retry the same wrapper once
outside the sandbox.
Use `--scope turn` or `--scope session` only when the request explicitly needs one boundary.

3. Treat the wrapper output as the evidence record. Explain whether the observed consumption,
   tool calls, and coordination fit the task context. Base abnormalities on explicit findings,
   failed or incomplete evidence, applicable concurrency limits, and the task's expected work;
   treat raw call volume alone as descriptive.

Completion requires the wrapper report plus a concise health conclusion. Preserve every reported
problem and unavailable surface in the handoff.

## Evidence contract

- Report current-turn and whole-session input, cached input, cache write, output, reasoning, and total
  Token counts as exact integers. Derive current-turn Tokens from cumulative Codex log snapshots;
  report current-turn cost and model activity unavailable rather than estimating them.
- Label whole-session money as Tokscale `estimated API-equivalent cost`. Report session span and
  Tokscale model activity when available. Summed model and tool durations may overlap elapsed span.
- For Codex, pair logged tool calls with their outputs and report per-tool starts, completions,
  failures, incomplete calls, summed and longest durations, and consecutive identical calls.
- Report coordination calls for spawn, wait, list, message, follow-up, and interrupt. Reconstruct
  successful and failed spawns, terminal Agent statuses, observed peak live Agents, wait timeouts,
  and waits without an observed live Agent when the root log provides the evidence. Treat observed
  lifecycle counts as lower bounds; do not infer child-session Token consumption without a stable
  child-session mapping.
- Read transcripts transiently. Persist no prompts, responses, tool inputs, or tool outputs.
- For other Tokscale clients, report consumption and mark local tool diagnostics unavailable.
- Missing logs, Tokscale failures, incomplete calls, and unavailable cost remain explicit; one
  unavailable surface does not hide available evidence.

Tokscale rows are filtered by client and exact session-ID suffix. Codex scans use matching log
dates when available; other clients use an unbounded scan. The current turn begins at the latest
logged user-message boundary. Exclude the diagnostic wrapper's own tool call from call statistics.
If Tokscale fails for Codex, recover only the latest cumulative `token_count` totals from the
matching log and mark cost unavailable.

## Stop conditions

- Request both client and stable session ID when the pair cannot be resolved; never infer the newest
  log.
- Report unsupported Tokscale clients without substituting another client.
- Return the generated partial or unavailable report when evidence is incomplete; never invent a
  normal verdict, task boundary, call result, Token count, or cost.
