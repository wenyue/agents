# 05 — Unified MCP Readiness Check

Category: enhancement
Status: resolved
Blocked by: 01 — Plugin Playwright MCP Delivery Across Three Hosts; 02 — Daily Project Check Gate; 04 — Project stdio MCP and Platform Differences

## What to build

After the Daily Project Check Gate allows execution, use one runner to aggregate existing
recommended tools, required values, the Plugin MCP Readiness Profile, and the Project MCP Readiness
Profile, then deliver one actionable diagnostic to the user.

- [x] A readiness profile and its corresponding MCP declaration share a lifecycle.
- [x] Support checks for command availability, allowlisted runtime minimums, workspace files, and
  environment-variable presence.
- [x] Runtime version checks are selected through a trusted profile; projects cannot inject
  arbitrary commands or shell scripts.
- [x] Playwright checks the minimum Node version and `npx` without inspecting the npm cache or
  starting MCP.
- [x] Flutter Inspector checks only the project executable and does not require a live debug session.
- [x] Sentry and OtakuRoom HTTP MCP perform no network, OAuth, port, or service-health probes.
- [x] All findings are aggregated into one host-native prompt and preserve the existing consent boundary.
- [x] Invalid readiness produces a non-blocking diagnostic and is not retried automatically that day.
- [x] Every detector type, platform filter, and safety boundary has external behavior tests.

## Comments

- This ticket enters the frontier only after all blockers are complete.
- 2026-08-10: The daily runner aggregates tool/required-value, Plugin MCP, and Project MCP checks;
  readiness supports only four static check types: command, Node minimum, workspace path, and
  environment-variable name.
- 2026-08-10: Added platform filtering, rejection of shell and non-allowlisted runtimes,
  aggregation, and once-per-day gate tests;
  `python3 -m unittest tests.test_recommended_tools tests.test_sync_mcp_adapters` passed (38 tests).
