# 03 — Complete Project HTTP MCP Management

Category: enhancement
Status: resolved
Blocked by: None

## What to build

Use Sentry HTTP MCP as a tracer bullet so a project can generate native configuration for all three
hosts from one strict canonical declaration through the public setup workflow, then precisely manage
its own entries with the Managed MCP Entry lock.

- [x] Project MCP is an optional server array in the existing version 1 project configuration, and
  every entry has a stable ID.
- [x] HTTP transport, URL, host scope, and typed overrides are strictly validated.
- [x] The setup request fully preserves and validates the Project MCP selection, with no second read path.
- [x] Codex, Cursor, and Copilot generate HTTP MCP entries conforming to their respective schemas.
- [x] The ownership lock records only managed native paths and keys, never secrets or service
  artifact information.
- [x] The first run can adopt a semantically equal existing entry and rejects a non-equivalent user entry.
- [x] Removing a canonical server deletes only entries recorded by the lock and preserves all
  unrelated user MCP configuration.
- [x] Setup apply/check transaction, rollback, and request round-trip tests pass.

## Comments

- When this ticket was published, the worktree already contained a partially implemented but
  unaccepted version of this slice; this ticket remains the source of its acceptance criteria.
- 2026-08-10: Added the version 1 `mcp.servers[]` HTTP contract, three-host adapters, precise
  `project-mcp.lock.json` ownership, and prepare/apply/check round-trip coverage.
- 2026-08-10: Focused HTTP tracer-bullet and catalog/renderer tests passed (41 tests).
