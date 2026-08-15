# Project Rules

Strength: `Mandatory`

Scope: Plugin and project capability ownership, documentation, target installation, contract
evolution, and test policy.

Keep one canonical owner for every capability and treat generated, delivery, documentation, and
test surfaces according to the boundaries below. `AGENTS.md` owns this Rule's applicability; the
SmartKit Rule configuration owns precedence.

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
- Setup preserves Project Rules it discovers as user-owned canonical inputs under
  `.agents/rules/`. Catalog-generated Rule targets remain setup-managed under Installation
  Ownership.
- Setup preserves Project Skill sources it discovers as user-owned canonical inputs under
  `.agents/skills/` or through external `source`/optional `ref`/`include` declarations, and records
  external provenance in `.agents/smartkit.lock.json`. Catalog-generated and configured external
  installed surfaces remain setup-managed under Installation Ownership.
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
- Treat the corresponding English first-party Rule and Skill sources as canonical. Complete their
  authoring, semantic review, and representative Acceptance before updating `docs/zh-CN/`.
- Keep every Chinese translation one-to-one with its corresponding English source. Preserve the
  source order, Markdown structure, commands, identifiers, code blocks, and behavioral meaning;
  do not add translation-only explanations or omit source content.
- Review translation fidelity independently after the canonical source passes. A translation
  failure blocks adoption but does not invalidate unchanged canonical evidence.
- Treat `.agents/rules/` as the source of truth for this repository's development rules. Keep
  `.agents/` limited to `plugins/` and `rules/`; it is not a generated project snapshot.

## Installation Ownership

- Preserve `.agents/` as the installation root in public setup prompts, templates, manifests,
  scripts, and documentation for target repositories.
- Treat catalog-selected sources, generated outputs, platform wrappers, and configured external
  Skill directories as setup-managed content. Preserve discovered project Rules and Skills,
  configured Agent sources, and non-template structured fields.
- Use `.agents/smartkit.lock.json` as the sole project ownership authority for managed Rules, Skills,
  Agent wrappers, MCP fields, other wrappers, and configuration. Derive removal from the difference
  between the previous manifest and current desired state; do not retain historical names in the
  catalog.
- On first adoption, own only a missing asset or one whose current deterministic digest equals the
  desired digest. On later runs, verify every recorded digest before planning. Never overwrite an
  unowned conflict or a modified owned asset.

## Tests and Evaluation

- Unit tests may assert structured configuration, schemas, formal identifiers, resource and
  registration relationships, generated outputs, filesystem effects, state transitions, exit
  behavior, and documented repository-boundary facts.
- Do not make ordinary natural-language sentences, physical line wrapping, translated wording, or
  complete heading lists into test snapshots. Exact text assertions require the text itself to be a
  structured external protocol value. Review prose, prompts, and Hook wording through whole-artifact
  semantic review and representative Acceptance instead.
- Judge first-party Rule and Skill prose by semantic fidelity, navigability, purposeful Markdown,
  and executable outcomes. Do not require similarity to an external exemplar or use an external
  artifact as the semantic oracle.
- Mark each Ordinary Artifact case for isolated-runner Acceptance and each generation-contract case
  for static walkthrough. Keep structured expected results reviewer-only: an Acceptance Runner may
  receive the frozen candidate, request, selected case input, and required runtime context or tools,
  but not the expected result, semantic ledger, diff, author reasoning, findings, or prior case
  output.
- Keep generation-contract evaluation cases static: provide guidance inputs and supported
  walkthrough cases, not a generated target or fake project. Back a Shared Rule or Shared Skill
  case with one representative traceable context plus direct evidence that its behavior is
  independent of project-local facts; require a second context only when that portability claim is
  material and direct evidence cannot resolve it.

## Contract Evolution

- When changing the SmartKit Rule and Skill Acceptance Standard, qualify the candidate against the
  previously accepted Standard plus the current accepted task specification. Keep
  campaign-specific canaries, scheduling, evidence, and adoption scope in that task specification;
  ADRs remain decision records rather than runtime policy owners.
- Treat a material change to either governing source as invalidating every prior semantic Review or
  Representative Acceptance verdict that depended on the old requirement. Structured proof remains
  valid only when the changed requirement cannot affect what it proves.
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
