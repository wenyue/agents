# Project Structure

Strength: `Advisory`

Scope: Top-level plugin, documentation, local-rule, and target-installation ownership boundaries.

## Repository Areas

- `rules/` contains directly distributed shared Rules; `skills/` contains shared operational and
  orchestration Skills; and `agents/` contains shared agent prompts.
- `blueprints/` contains Rule and Skill generation contracts, while `templates/project/` contains
  host configuration and wrapper templates. Neither is copied as a target runtime asset without
  the catalog and renderer selecting it.
- `catalog/` owns public asset selection and lock/configuration contracts. `config/` owns
  recommended-tool policy.
- `docs/` contains design material and `docs/zh-CN/` contains Simplified-Chinese documentation.
  Documentation is outside runtime loading and target installation.
- `.agents/rules/` owns this repository's development instructions, and `.agents/plugins/` owns its
  local marketplace configuration. No other `.agents/` content belongs in this repository.
- `AGENTS.md` is the entry point for discovering `.agents/rules/`; `README.md` is public plugin
  onboarding and describes the setup boundary.

## Distribution Flow

- Setup reads `catalog/project-assets.json` and English plugin assets at the root, then applies only
  manifest-selected content to a target repository under `.agents/`.
- Blueprints guide creation of complete target-owned Rules and Skills; they are not installed as
  runtime content themselves.
- The setup control plane remains in `skills/setup-project-agents/`. Target changes have no reverse
  path into plugin runtime assets or documentation.

## Script and Test Ownership

- Keep setup implementation under `skills/setup-project-agents/scripts/` and recommended-tool
  checkers under `skills/manage-agent-tools/scripts/`.
- Keep repository contract tests under `tests/`; tests may import support scripts from their owning
  plugin Skill directories.

## Boundaries

- Keep runtime versions and executable commands in `Project Tools`.
- Keep public ownership, documentation, and installation policy in `Project Rules`.
- Describe application modules, package dependencies, or service layers only from direct repository
  evidence, not from the plugin directory structure.
