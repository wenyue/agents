# ADR 0001: Deliver Skills as snapshots and MCP as configuration

Status: Accepted

Date: 2026-08-10

## Context

SmartKit supports Codex, Cursor, and GitHub Copilot. Those hosts discover Skills from plugin-local
or project-local files, but they register MCP servers through host-native configuration. Treating
both capabilities as remotely resolved dependencies would make Skill behavior vary after a plugin
release. Treating MCP servers as copied repository assets would duplicate implementations owned by
npm packages, remote services, or target applications.

Project MCP configuration shares native files with user-owned servers. Rules, Skills, Agents,
wrappers, and seeded documents also have different ownership semantics. Separate feature locks and
catalog lists of historical names made those boundaries harder to reason about.

## Decision

- Third-party Plugin Skills are reviewed, license-checked, hash-locked snapshots published inside
  SmartKit. Project external Skills use compact `source`/`ref`/`include` declarations and are
  resolved and snapshotted by `setup-project-agents`; setup discovers their root license.
- Plugin MCP is a Configured MCP. `mcp/registry.json` is canonical and generated adapters preserve
  each host's native schema. SmartKit does not vendor the external server implementation.
- Project MCP is a compact array in `.agents/config.json`; `url` implies HTTP and `command` implies
  stdio. Setup renders host-native fields while preserving unrelated entries.
- `.agents/smartkit.lock.json` is the sole project ownership manifest. It records source resolution
  metadata plus digest-bearing `file`, `tree`, and `field` assets with descriptive roles. Seeded
  human-owned documents are recorded separately without update or deletion authority.
- First setup adopts only missing or equal assets. Later setup verifies the previous digest before
  updating or deleting an asset. Removed assets are derived only from the previous/current manifest
  difference; old lock formats and historical catalog names are not read.
- Plugin MCP readiness remains declarative in the plugin registry. Project MCP readiness is inferred
  from bare commands, workspace-relative commands, and named environment variables. The daily
  runner does not contact remote endpoints or authenticate.

## Consequences

Skill updates require a reviewed SmartKit release or project setup run and remain reproducible.
Package-backed MCP servers may resolve a newer package when a host starts them, as Playwright does
with `@latest`; that runtime lifecycle is explicit and separate from plugin installation.

Every new host requires an MCP adapter, and adapter drift is rejected by synchronization tests.
Project removal is safe because setup deletes only manifest-owned assets. A manually modified owned
asset fails before writes instead of being overwritten. Secrets remain outside canonical
declarations, generated adapters, and the ownership manifest.
