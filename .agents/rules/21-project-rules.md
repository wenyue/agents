# Project Rules

Strength: `Default`

Scope: Plugin asset ownership, documentation boundaries, target-installation contracts, and test
contracts for this repository.

## Plugin Ownership

- Treat root `rules/`, `skills/`, and `agents/` as the English runtime sources of truth for the
  plugin. Keep shared blueprints in `blueprints/`, host templates in `templates/project/`, and
  recommended-tool policy in `config/`.
- Treat `catalog/project-assets.json` as the owner of target asset inclusion, Rule and Skill
  blueprints, wrapper routing, renderer metadata, and managed root-configuration declarations.
- Keep deterministic setup, source validation, rendering, planning, and transactional application
  in `skills/setup-project-agents/scripts/`. Target-specific policy belongs to the target
  repository's generated or user-owned content.

## Documentation and Local Rules

- Treat `docs/zh-CN/` as Simplified-Chinese documentation. It is not a runtime source, plugin
  entry point, setup input, or target-installation asset.
- Write Chinese documentation naturally and preserve commands, identifiers, code blocks, and
  behavioral meaning when documenting English runtime assets.
- Treat `.agents/rules/` as the source of truth for this repository's development rules. Keep
  `.agents/` limited to `plugins/` and `rules/`; it is not a generated project snapshot.

## Installation and Tests

- Preserve `.agents/` as the installation root in public setup prompts, templates, manifests,
  scripts, and documentation for target repositories.
- Unit tests may assert structured configuration, schemas, filesystem effects, state transitions,
  exit behavior, and documented repository-boundary facts. Review prose, prompts, and Hook wording
  semantically in addition to automated checks.

## Boundaries

- Keep commands, runtime requirements, and tool mutation behavior in `Project Tools`.
- Keep directory ownership and dependency direction in `Project Structure`.
- Add framework, API, persistence, lifecycle, lint, or generated-file conventions only when
  repository evidence establishes them.
