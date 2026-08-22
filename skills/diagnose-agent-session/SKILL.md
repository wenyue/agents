---
name: diagnose-agent-session
description: Diagnose suspected abnormal token or API-equivalent cost consumption, model or tool activity, subagent coordination, waits, or incomplete calls in one stable agent session.
---

# Diagnose Agent Session

Diagnose the current turn and complete stable session after the fact, without retaining a task
receipt. The public-wrapper call and its controlled sandbox retry are the only fixed procedure;
interpretation follows the judgment frame.

## Judgment frame

Treat the wrapper report as the evidence record. Compare it with the task's expected work and
applicable concurrency limits. Explicit findings, failed or incomplete evidence, and behavior that
does not fit that context can support an abnormal conclusion; raw Token or call volume alone is
descriptive.

Preserve every reported problem and unavailable surface. Never fill an evidence gap by inferring a
task boundary, call result, Token count, cost, or normal verdict. One unavailable surface does not
invalidate the evidence that remains available.

## Capture evidence

Resolve the Tokscale client and stable session ID as one pair. For Codex, omit both only when
`CODEX_THREAD_ID` is available. If exactly one is supplied or neither can be resolved, request both
rather than selecting the newest log.

Use `--scope both` unless the request explicitly selects only `turn` or `session`. Run the one branch
supported by the current platform:

- POSIX:

  ```sh
  sh .agents/skills/diagnose-agent-session/scripts/task-metrics.sh diagnose --scope both --client <client> --session-id <id>
  ```

- Windows with PowerShell:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .agents/skills/diagnose-agent-session/scripts/task-metrics.ps1 diagnose --scope both --client <client> --session-id <id>
  ```

Both wrappers require Python 3.10+. Run the selected wrapper once. When sandbox access caused a
Tokscale failure and approval is available, retry the same wrapper once outside the sandbox. Then
return to the judgment frame with the complete, partial, or unavailable report.

## Evidence contract

Use the wrapper report's Tokscale whole-session usage and `estimated API-equivalent cost`; for Codex,
also use its current-turn and local tool and coordination evidence. Summed model and tool durations
can overlap elapsed span; lifecycle counts are lower bounds, and child-session Token consumption
requires a stable mapping. Read transcripts transiently and persist no prompts, responses, tool
inputs, or tool outputs.

## Exits

Complete with the wrapper report and a concise health conclusion grounded in the judgment frame. If
evidence remains incomplete after the permitted attempt or retry, the partial or unavailable report
is the final result. Missing identifiers or an unsupported platform stops before the wrapper;
report an unsupported Tokscale client error without substituting another client.
