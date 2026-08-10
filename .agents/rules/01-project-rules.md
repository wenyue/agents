# Project Rules

Strength: `Mandatory`

Scope: Plugin asset ownership, documentation boundaries, target-installation contracts, contract
evolution, and test contracts for this repository.

## Plugin Ownership

- Treat custom entries in `skills/registry.json` as SmartKit-owned plugin Skills and external
  entries as read-only snapshots owned by `scripts/update_external_skills.py`.
- Treat `mcp/registry.json` as the canonical Plugin MCP source and `.mcp.json`,
  `mcp/cursor.json`, and `mcp/copilot.json` as generated host adapters owned by
  `scripts/sync_mcp_adapters.py`. MCP configuration does not make an external MCP implementation
  a vendored repository asset.
- Treat `rules/registry.json` and `rules/source/` as plugin Rule ownership. Cursor wrappers under
  `rules/cursor/` and command Hooks are delivery adapters, not policy owners.
- Treat project `skills` as GitHub `source`/optional `ref`/`include` declarations fetched once per
  source. Setup infers Skill names and source URLs and records resolved source and license metadata
  in `.agents/smartkit.lock.json`.
- Treat project `mcp` as typed configuration rendered into host-native entries. Infer HTTP versus
  stdio from `url` versus `command`, and infer static project readiness from command paths and named
  environment variables. The unified manifest owns only rendered leaf fields, never sibling user
  MCP entries or secret values.
- Keep recommended-tool Hook executables in `runtime/recommended-tools/` without a `SKILL.md`, and
  keep their authoritative tool declarations in `policies/recommended-tools/`. MCP readiness stays
  beside its Plugin or Project MCP declaration and is interpreted by the same runtime only after
  the project/host/local-day gate passes. These assets remain plugin-private and setup must not copy
  them into target repositories.
- Keep shared blueprints and host templates under `setup-assets/`. Treat
  `setup-assets/catalog/assets.json` as the owner of target asset inclusion, Rule and Skill
  blueprints, wrapper routing, renderer metadata, and managed root-configuration declarations.
- Keep deterministic setup, source validation, rendering, planning, and transactional application
  in `skills/setup-project-agents/scripts/`. Target-specific policy belongs to the target
  repository's generated or user-owned content.
- Treat `vendor/external-skills.lock.json` as the source of truth for every plugin external source,
  resolved commit, selected Skill, license, and file hash.

## Documentation and Local Rules

- Treat `README.md` and `docs/zh-CN/README.md` as public end-user documentation. Include only
  information users need to install, configure, use, or troubleshoot the plugin; keep contributor
  release, generation, repository-maintenance, and internal implementation instructions in their
  owning project rules or tooling.
- Treat `docs/zh-CN/` as Simplified-Chinese documentation. It is not a runtime source, plugin
  entry point, setup input, or target-installation asset.
- Keep every Chinese translation one-to-one with its corresponding English source. Preserve the
  source order, Markdown structure, commands, identifiers, code blocks, and behavioral meaning;
  do not add translation-only explanations or omit source content.
- Treat `.agents/rules/` as the source of truth for this repository's development rules. Keep
  `.agents/skills/write-agent-rule/` and `.agents/skills/write-agent-skill/` as local discovery
  wrappers that apply their corresponding English sources under `skills/`. Keep `.agents/` limited
  to `plugins/`, `rules/`, and those Skill wrappers; it is not a generated project snapshot.

## Installation and Tests

- Preserve `.agents/` as the installation root in public setup prompts, templates, manifests,
  scripts, and documentation for target repositories.
- Treat catalog-selected sources, generated outputs, platform wrappers, and configured external
  Skill directories as setup-managed content. Treat automatically discovered project-owned Rules
  and Skills as preserved target content, and keep non-template structured fields unchanged.
- Use `.agents/smartkit.lock.json` as the sole project ownership authority for managed Rules, Skills,
  Agents, MCP fields, wrappers, and configuration. Derive removal from the difference between the
  previous manifest and current desired state; do not retain historical names in the catalog.
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
