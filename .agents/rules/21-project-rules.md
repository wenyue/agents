# Project Rules

Strength: `Mandatory`

Scope: Plugin asset ownership, documentation boundaries, target-installation contracts, contract
evolution, and test contracts for this repository.

## Plugin Ownership

- Treat `skills/setup-project-agents/` as the plugin-visible control plane and keep it as the only
  Skill under root `skills/`. Treat `setup-assets/rules/`, `setup-assets/skills/`, and
  `setup-assets/agents/` as the English sources installed into target repositories by setup.
- Keep recommended-tool Hook executables in `runtime/recommended-tools/` without a `SKILL.md`, and
  keep their authoritative declarations in `policies/recommended-tools/`. They remain plugin-private
  and setup must not copy them into target repositories.
- Keep shared blueprints and host templates under `setup-assets/`. Treat
  `setup-assets/catalog/assets.json` as the owner of target asset inclusion, Rule and Skill
  blueprints, wrapper routing, renderer metadata, and managed root-configuration declarations.
- Keep deterministic setup, source validation, rendering, planning, and transactional application
  in `skills/setup-project-agents/scripts/`. Target-specific policy belongs to the target
  repository's generated or user-owned content.

## Documentation and Local Rules

- Treat `docs/zh-CN/` as Simplified-Chinese documentation. It is not a runtime source, plugin
  entry point, setup input, or target-installation asset.
- Keep every Chinese translation one-to-one with its corresponding English source. Preserve the
  source order, Markdown structure, commands, identifiers, code blocks, and behavioral meaning;
  do not add translation-only explanations or omit source content.
- Treat `.agents/rules/` as the source of truth for this repository's development rules. Keep
  `.agents/skills/write-rule/` and `.agents/skills/write-skill/` as local discovery wrappers that
  apply their corresponding English sources under `setup-assets/skills/`. Keep `.agents/` limited
  to `plugins/`, `rules/`, and those Skill wrappers; it is not a generated project snapshot.

## Installation and Tests

- Preserve `.agents/` as the installation root in public setup prompts, templates, manifests,
  scripts, and documentation for target repositories.
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
