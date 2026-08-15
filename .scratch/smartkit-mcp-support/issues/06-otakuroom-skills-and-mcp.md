# 06 — OtakuRoom Skills and Project MCP Integration

Category: enhancement
Status: resolved
Blocked by: 03 — Complete Project HTTP MCP Management; 04 — Project stdio MCP and Platform Differences; 05 — Unified MCP Readiness Check

## What to build

Use the official setup workflow to give OtakuRoom three official Flutter Skills and three Project
MCP servers—Sentry, Flutter Inspector, and OtakuRoom—while preserving the application's ownership
of its tests, layout, and runtime.

- [x] Resolve and snapshot the three official Flutter Skills from upstream sources, recording the
  resolved commit and file hashes.
- [x] External Skill snapshots contain no OtakuRoom-local modifications.
- [x] Local test routing separates unit/widget tests from integration tests.
- [x] Layout-fix routing reuses runtime-error and screenshot capabilities.
- [x] Responsive layout remains governed by `RootLayoutWidget` and the project's orientation helpers.
- [x] Sentry uses direct HTTP on all three hosts and no longer uses an npm bridge.
- [x] Flutter Inspector uses a host-appropriate stdio executable path and declares static-file readiness.
- [x] OtakuRoom MCP uses the agreed static default endpoint without runtime port discovery.
- [x] The existing Dart MCP and other user configuration remain unchanged.
- [x] Setup completes through the public start/finish workflow and reports `check: clean`.
- [x] Focused tests for project-configuration parsing, MCP ownership, command exposure, and affected
  owners pass.

## Comments

- This ticket enters the frontier only after all blockers are complete.
- 2026-08-10: The official setup finish returned `check: clean`; Flutter Skills were pinned to
  `flutter/skills@141bccd9a3a9d43d698752272ecf56a32026d174`, and the Sentry Skill was pinned to
  `getsentry/plugin-codex@c900f2f12324920d33338db38f037de251b71349`.
- 2026-08-10: Three-host MCP parity, the ownership lock, and every external Skill hash check passed;
  the pinned Flutter `command_mcp_server_test.dart` passed (15 tests).
- 2026-08-10: Project configuration no longer declares license metadata; official setup
  automatically identified Sentry as MIT and Flutter as BSD-3-Clause from upstream root license
  files, then returned `finish/check=clean` again.
