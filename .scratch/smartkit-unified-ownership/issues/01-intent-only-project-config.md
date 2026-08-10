# 01 — Intent-only project Skill and MCP configuration

Category: enhancement
Status: resolved
Blocked by: None

## What to build

Replace redundant project Skill and MCP fields with the current version 1 intent-only contract.

- [x] External Skills use `source`, optional `ref`, and non-empty `include` paths.
- [x] Source URLs, Skill identifiers, and destination names are derived and validated.
- [x] Project MCP uses exactly one of `url` or `command` and defaults to all three hosts.
- [x] Project MCP readiness is inferred from commands, workspace paths, and environment names.
- [x] The schema, session request round trip, daily checker, and tests use only the current contract.

## Comments

- Old project configuration forms are intentionally unsupported; no migration or compatibility
  parser was added.
