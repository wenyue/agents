# 01 — Plugin Playwright MCP Delivery Across Three Hosts

Category: enhancement
Status: resolved
Blocked by: None

## What to build

Generate native Codex, Cursor, and Copilot adapters from one canonical Plugin MCP registry so all
three hosts can discover and start the latest isolated, headless Playwright MCP after SmartKit is
installed. The plugin delivers only configuration, preserves host tool approval, and does not copy
the Playwright service implementation.

- [x] One strictly validated registry is the sole source for all three host adapters.
- [x] The Codex, Cursor, and Copilot manifests explicitly reference their valid MCP configurations.
- [x] All three adapters express the same Playwright launch intent while preserving required host
  schema differences.
- [x] The Copilot adapter explicitly exposes every tool, and all hosts retain default approval
  behavior.
- [x] A read-only synchronization check detects drift between the registry and generated outputs.
- [x] Unknown fields, unsafe readiness configuration, and dangerous Playwright flags are rejected.
- [x] The Codex MCP companion validator and related contract tests pass.

## Comments

- When this ticket was published, the worktree already contained a partially implemented but
  unaccepted version of this slice; this ticket remains the source of its acceptance criteria.
- The Plugin MCP adapter check, three-host manifest and adapter tests, and Codex MCP companion
  validator passed.
- The complete legacy plugin-creator validator still reports SmartKit's existing Hooks and
  user-invoked Matt Skills. Those baseline diagnostics are outside this ticket's MCP companion
  contract and were not avoided by deleting existing capabilities.
