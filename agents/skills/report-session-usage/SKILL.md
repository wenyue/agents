---
name: report-session-usage
description: Use when token usage or API-equivalent cost must be reported for one stable agent session supported by Tokscale.
---

# Report Agent Session Usage

Run one post-hoc command after the task and return its compact consumption report. This workflow does
not create task receipts, track elapsed time, measure model or tool activity, or require worktree
lifecycle bookkeeping.

## Workflow

1. Resolve the Tokscale client and stable session ID. Pass both explicitly for any supported client.
   Codex may omit them when `CODEX_THREAD_ID` is available. Never infer the newest session when the
   stable ID is unknown.
2. Run the platform wrapper once:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/report-session-usage/scripts/task-metrics.ps1 usage --client <client> --session-id <id>
```

On POSIX, use:

```sh
sh .agents/skills/report-session-usage/scripts/task-metrics.sh usage --client <client> --session-id <id>
```

Both wrappers invoke the deterministic Python 3.11+ `scripts/timing.py` core.

3. Include the wrapper output verbatim in the handoff. Do not calculate time, reconstruct task
   boundaries, aggregate other sessions, reformat the values, or add a second metrics summary.

## Consumption Recovery

The script filters Tokscale `--json --group-by client,session,model` output by the selected client and
exact session-ID suffix. It bounds Codex scans to matching log dates when those dates are available;
other clients use an unbounded scan so older sessions are not silently excluded. The result is
whole-session consumption, not task-specific consumption.

If Tokscale fails for Codex, the script reads only the latest cumulative `token_count` event from the
matching Codex session. It reports those Token categories with source `codex-log` and marks estimated
cost unavailable. Other clients have no skill-owned log fallback and return an explicit unavailable
result. When sandbox access caused the failure and approval is available, retry the same wrapper once
outside the sandbox; do not repeat cold scans.

## Metric Contract

- Report input, cached input, cache write, output, reasoning, and total Token counts as exact integers.
- Label money as Tokscale `estimated API-equivalent cost`, never billed cost.
- Missing logs and unavailable cost remain explicit problems; one unavailable value does not hide
  available Token evidence.
- Do not report elapsed time, task duration, model activity, tool activity, task receipts, session
  attachment, or attribution gaps.

## Output

The wrapper emits this ready-to-use format:

```text
### Usage Metrics
- Scope: whole session
- Tokens: <exact categories | unavailable>
- Estimated API-equivalent cost: <amount | unavailable>
- Problems: <concise evidence or recovery explanation>
```

The `Problems` line is omitted when Token and cost evidence are complete.

## Stop Conditions

- If the client or stable session ID is unavailable, request both instead of guessing.
- If Tokscale does not support the supplied client, report its error instead of substituting a client.
- If Tokscale and any client-specific fallback provide no consumption evidence, report the generated
  unavailable result without inventing values.
