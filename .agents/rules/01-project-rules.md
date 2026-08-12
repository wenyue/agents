# Project Rules

Strength: `Mandatory`

Scope: Plugin asset ownership, documentation boundaries, target-installation contracts, contract
evolution, and test contracts for this repository.

## Capability Ownership

- Plugin Rules are owned by `rules/registry.json` and `rules/source/`; Cursor wrappers and command
  Hooks are delivery adapters, not policy owners.
- Plugin Skills are owned by custom entries in `skills/registry.json`; external entries are
  read-only snapshots owned by `scripts/update_external_skills.py`.
- Plugin Agents are owned by `agents/registry.json` and `agents/source/`; generated adapters under
  `agents/codex/`, `agents/cursor/`, and `agents/copilot/` are owned by
  `scripts/sync_agent_adapters.py`. Cursor and Copilot manifests expose their adapters directly;
  the catalog delivers Codex adapters as setup-managed Plugin Agent defaults without adding a
  Project Agent declaration.
- Plugin MCP is owned by `mcp/registry.json`; `.mcp.json`, `mcp/cursor.json`, and
  `mcp/copilot.json` are generated adapters owned by `scripts/sync_mcp_adapters.py`, not vendored
  MCP implementations.
- Project Rules are project-owned sources under `.agents/rules/`; setup discovers and preserves
  them.
- Project Skills are project-owned directories under `.agents/skills/` or external
  `source`/optional `ref`/`include` declarations; setup preserves project sources and records
  external provenance in `.agents/smartkit.lock.json`.
- Project Agents are project-owned sources under `.agents/agents/` with typed `agents`
  declarations; setup preserves sources and records only generated host adapters.
- Project MCP is typed `mcp` configuration rendered into host-native entries; the ownership
  manifest records only rendered leaf fields, never sibling entries or secret values.
- Keep recommended-tool Hook executables in `runtime/recommended-tools/` without a `SKILL.md`, and
  keep their authoritative tool declarations in `policies/recommended-tools/`. MCP readiness stays
  beside its Plugin or Project MCP declaration and is interpreted by the same runtime only after
  the project/host/local-day gate passes. These assets remain plugin-private and setup must not copy
  them into target repositories.
- Keep shared blueprints and host templates under `setup-assets/`. Treat
  `setup-assets/catalog/assets.json` as the owner of target asset inclusion, Rule and Skill
  blueprints, Codex Plugin Agent default delivery, wrapper routing, renderer metadata, and managed
  root-configuration declarations.
- Keep deterministic setup, source validation, rendering, planning, and transactional application
  in `skills/setup-project-agents/scripts/`. Target-specific policy belongs to the target
  repository's generated or user-owned content.
- Treat `vendor/external-skills.lock.json` as the source of truth for every plugin external source,
  resolved commit, selected Skill, license, and file hash.

## Documentation and Local Rules

- Keep Rule and Skill documents limited to context and instructions that change Agent decisions or
  actions. Leave directly discoverable implementation facts in their owning code, configuration,
  schema, or tests.
- Treat `README.md` and `README.zh-CN.md` as public end-user documentation. Before adding or
  retaining content, require it to help users install, configure, use, or troubleshoot the plugin.
  Keep contributor workflows, release and generation details, repository maintenance, architecture,
  validation internals, and implementation details in their owning project rules or tooling.
- Treat `docs/zh-CN/` as Simplified-Chinese documentation. It is not a runtime source, plugin
  entry point, setup input, or target-installation asset.
- Keep every Chinese translation one-to-one with its corresponding English source. Preserve the
  source order, Markdown structure, commands, identifiers, code blocks, and behavioral meaning;
  do not add translation-only explanations or omit source content.
- Treat `.agents/rules/` as the source of truth for this repository's development rules. Keep
  `.agents/` limited to `plugins/` and `rules/`; it is not a generated project snapshot.

## Installation and Tests

- Preserve `.agents/` as the installation root in public setup prompts, templates, manifests,
  scripts, and documentation for target repositories.
- Treat catalog-selected sources, generated outputs, platform wrappers, and configured external
  Skill directories as setup-managed content. Preserve discovered project Rules and Skills,
  configured Agent sources, and non-template structured fields.
- Use `.agents/smartkit.lock.json` as the sole project ownership authority for managed Rules, Skills,
  Agent wrappers, MCP fields, other wrappers, and configuration. Derive removal from the difference
  between the previous manifest and current desired state; do not retain historical names in the
  catalog.
- On first adoption, own only missing or semantically equal assets. On later runs, verify every
  recorded digest before planning. Never overwrite an unowned conflict or a modified owned asset.
- Unit tests may assert structured configuration, schemas, filesystem effects, state transitions,
  exit behavior, and documented repository-boundary facts. Review prose, prompts, and Hook wording
  semantically in addition to automated checks.

## Contract Evolution

- Implement and validate only the repository's current contract. When a path, identifier, schema,
  command, configuration field, or behavior is removed, remove its implementation, documentation,
  tests, and handling in the same change.
- Do not add compatibility aliases, deprecated branches, migrations, shims, legacy fallbacks,
  dual-read or dual-write behavior, or version translation for retired contracts. Inputs that use a
  former contract are unsupported and may fail current validation.
- Keep tests and documentation focused on the current contract; they must not preserve retired
  names or behaviors as executable or normative surfaces.

## Boundaries

- Keep commands, runtime requirements, and tool mutation behavior in `Project Tools`.
- Keep directory ownership and dependency direction in `Project Structure`.
- Add framework, API, persistence, lifecycle, lint, or generated-file conventions only when
  repository evidence establishes them.
- Treat data-integrity checks, ownership checks, transactional rollback, and safe offline behavior
  as current correctness requirements rather than backward-compatibility mechanisms.
