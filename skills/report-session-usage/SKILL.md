---
name: report-session-usage
description: Use when token usage or API-equivalent cost must be reported for one stable agent session supported by Tokscale.
---

# Report Agent Session Usage

Run one post-hoc command after the task and return its compact consumption report. This workflow does
not create task receipts, track elapsed time, measure model or tool activity, or require worktree
lifecycle bookkeeping.

## Workflow

1. Resolve the Tokscale client and stable session ID as one pair. Pass both explicitly for any
   supported client. Codex may omit both when `CODEX_THREAD_ID` is available. If exactly one value
   was supplied, request both and do not run the wrapper.
2. Run the matching platform wrapper once. On Windows with PowerShell, use:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/report-session-usage/scripts/task-metrics.ps1 usage --client <client> --session-id <id>
```

On POSIX, use:

```sh
sh .agents/skills/report-session-usage/scripts/task-metrics.sh usage --client <client> --session-id <id>
```

Both wrappers invoke the deterministic Python 3.11+ `scripts/timing.py` core.

On any other platform, stop without running an internal script and report that no public wrapper is
supported.

3. Include the wrapper output verbatim as the only metrics summary in the handoff. Leave time
   calculation, task-boundary reconstruction, other-session aggregation, and value reformatting
   outside this workflow.

## Consumption Recovery

The script filters Tokscale `--json --group-by client,session,model` output by the selected client and
exact session-ID suffix. It bounds Codex scans to matching log dates when those dates are available;
other clients use an unbounded scan so older sessions are not silently excluded. The result is
whole-session consumption, not task-specific consumption.

If Tokscale fails for Codex, the script reads only the latest cumulative `token_count` event from the
matching Codex session. It reports those Token categories with source `codex-log` and marks estimated
cost unavailable. Other clients have no skill-owned log fallback and return an explicit unavailable
result. When sandbox access caused the failure and approval is available, retry the same wrapper once
outside the sandbox.

## Metric Contract

- Report input, cached input, cache write, output, reasoning, and total Token counts as exact integers.
- Label money as Tokscale `estimated API-equivalent cost`.
- Missing logs and unavailable cost remain explicit problems; one unavailable value does not hide
  available Token evidence.
- Limit the report to whole-session token categories, estimated API-equivalent cost, and explicit
  evidence problems.

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

- If the client and stable session ID pair cannot be resolved, request both instead of guessing or
  running with a partial pair.
- If Tokscale does not support the supplied client, report its error instead of substituting a client.
- If Tokscale and any client-specific fallback provide no consumption evidence, report the generated
  unavailable result without inventing values.
