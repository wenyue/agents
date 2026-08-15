# 04 — Project stdio MCP and Platform Differences

Category: enhancement
Status: resolved
Blocked by: 03 — Complete Project HTTP MCP Management

## What to build

Use Flutter Inspector as a tracer bullet so Project MCP supports one canonical stdio declaration
while constrained host overrides express unavoidable executable-path differences across the three
hosts.

- [x] The stdio command, arguments, working directory, and environment-variable name references are
  strictly validated.
- [x] Environment variables are passed by name only; generated files and the ownership lock contain
  no secret values.
- [x] An override can modify only typed fields supported by the current transport and can apply only
  to enabled hosts.
- [x] Codex, Cursor, and Copilot adapters preserve their respective type, environment-variable, and
  working-directory representations.
- [x] Command arguments permit valid duplicates, while environment-variable names and host lists
  remain unique.
- [x] Mixed HTTP and stdio fields, unknown hosts, and unknown fields fail before any write.
- [x] stdio adoption, conflict, update, removal, and user-configuration preservation behavior
  matches HTTP behavior.

## Comments

- This ticket enters the frontier only after ticket 03 is complete.
- 2026-08-10: Implemented three-host stdio adapters, name-based environment passing, and constrained
  platform overrides; added tests for duplicate arguments, unique platform/environment lists,
  cross-platform migration, and preservation of user entries.
- 2026-08-10: `python3 -m unittest tests.test_setup_catalog tests.test_setup_renderer` passed
  (41 tests).
