# ADR 0001: Deliver Skills as snapshots and MCP as configuration

Status: Accepted

Date: 2026-08-10

## Context

SmartKit supports Codex, Cursor, and GitHub Copilot. Those hosts discover Skills from plugin-local
or project-local files, but they register MCP servers through host-native configuration. Treating
both capabilities as remotely resolved dependencies would make Skill behavior vary after a plugin
release. Treating MCP servers as copied repository assets would duplicate implementations owned by
npm packages, remote services, or target applications.

Project MCP configuration also shares native files with user-owned servers. SmartKit therefore
needs an ownership boundary narrower than the complete native MCP document.

## Decision

- Third-party Plugin Skills are reviewed, license-checked, hash-locked snapshots published inside
  SmartKit. Project external Skills are resolved and snapshotted by `setup-project-agents` with a
  project lock; setup discovers their root license instead of requiring license metadata in project
  configuration.
- Plugin MCP is a Configured MCP. `mcp/registry.json` is canonical and generated adapters preserve
  each host's native schema. SmartKit does not vendor the external server implementation.
- Project MCP is declared in `.agents/config.json` and rendered by setup. The project MCP lock owns
  only the native path/key pairs generated for each logical server; unrelated entries remain
  user-owned.
- MCP readiness is declarative, static, and colocated with the MCP declaration. One daily runner
  interprets the allowlisted check types after the project/host/local-day gate. It does not start a
  server, contact a remote endpoint, or perform authentication.

## Consequences

Skill updates require a reviewed SmartKit release or project setup run and remain reproducible.
Package-backed MCP servers may resolve a newer package when a host starts them, as Playwright does
with `@latest`; that runtime lifecycle is explicit and separate from plugin installation.

Every new host requires an MCP adapter, and adapter drift is rejected by synchronization tests.
Project removal is safe because setup deletes only lock-owned entries. Secrets remain outside the
canonical declarations, generated adapters, and ownership locks.
