# 07 — SmartKit 1.1.0 Release Contract and Cross-Repository Acceptance

Category: enhancement
Status: resolved
Blocked by: 01 — Plugin Playwright MCP Delivery Across Three Hosts; 02 — Daily Project Check Gate; 03 — Complete Project HTTP MCP Management; 04 — Project stdio MCP and Platform Differences; 05 — Unified MCP Readiness Check; 06 — OtakuRoom Skills and Project MCP Integration

## What to build

Consolidate the completed Plugin MCP, Project MCP, Daily Project Check Gate, and OtakuRoom adoption
into SmartKit 1.1.0's complete releasable contract and provide cross-repository verification evidence.

- [x] The root version, three-host manifests, marketplaces, and setup catalog are synchronized to 1.1.0.
- [x] English and Simplified-Chinese public documentation describes Plugin MCP, Project MCP,
  readiness, and third-party Skill boundaries.
- [x] An ADR records the choices and host-adapter tradeoffs for Skill snapshot delivery and MCP
  configuration delivery.
- [x] Project Rules, structural boundaries, and the setup Skill describe only the current contract,
  retaining no former throttle or bridge behavior.
- [x] The Plugin MCP adapter check, version check, Codex MCP companion validator, and complete
  SmartKit unit suite pass.
- [x] Existing incompatibility diagnostics from the complete legacy plugin-creator validator are
  reproduced and recorded, without deleting Hooks or changing the Matt Skill invocation contract
  to avoid them.
- [x] SmartKit and OtakuRoom both pass diff whitespace and conflict-marker checks.
- [x] OtakuRoom completes risk-proportionate configuration analysis and focused tests with its
  pinned Flutter/Dart environment.
- [x] The final diff contains no secrets, cache files, session files, or unauthorized user
  configuration changes.
- [x] Every ticket acceptance criterion maps to final evidence, with no unexplained omissions.

## Comments

- This ticket enters the frontier only after all blockers are complete.
- 2026-08-10: `sync_mcp_adapters.py --check`, `sync_plugin_version.py --check`, the Codex MCP
  companion validator, and the complete SmartKit unit suite passed (211 tests, 1 skipped).
- 2026-08-10: The built-in complete legacy plugin-creator validator still reports SmartKit's
  existing Copilot Hooks and 14 user-invoked Matt Skills. These are not MCP companion errors, so the
  existing contract remains unchanged.
- 2026-08-10: SmartKit and OtakuRoom passed `git diff --check`, conflict-marker checks, and
  secret/cache/session audits; OtakuRoom official setup reported `finish/check=clean`, and the
  pinned Flutter focused tests passed (15 tests).
