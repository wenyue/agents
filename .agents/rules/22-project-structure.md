# Project Structure

Strength: `Advisory`

Scope: Top-level plugin, documentation, local-rule, and target-installation ownership boundaries.

## Repository Areas

- `skills/` contains only the plugin-visible `setup-project-agents` control plane. `hooks/` contains
  the three host lifecycle entry points.
- `runtime/recommended-tools/` contains private Hook executables and no discoverable Skill.
  `policies/recommended-tools/` contains the declarations shared by that runtime and setup output.
- `setup-assets/rules/`, `setup-assets/skills/`, and `setup-assets/agents/` contain content that
  becomes runtime capability only after setup installs it. `setup-assets/blueprints/` and
  `setup-assets/templates/` contain generation and rendering inputs, while `setup-assets/catalog/`
  owns asset selection and lock/configuration contracts.
- `docs/` contains design material and `docs/zh-CN/` contains Simplified-Chinese documentation.
  Documentation is outside runtime loading and target installation.
- `.agents/rules/` owns this repository's development instructions, `.agents/plugins/` owns its
  local marketplace configuration, and `.agents/skills/` contains only thin discovery wrappers for
  `write-rule` and `write-skill`. No other `.agents/` content belongs in this repository.
- `AGENTS.md` is the entry point for discovering `.agents/rules/`; `README.md` is public plugin
  onboarding and describes the setup boundary.

## Distribution Flow

- Setup reads `setup-assets/catalog/assets.json`, then applies only catalog-selected public sources
  to a target repository. Recommended-tool runtime and policy files remain plugin-private.
- Blueprints guide creation of complete target-owned Rules and Skills; they are not installed as
  runtime content themselves.
- The setup control plane remains in `skills/setup-project-agents/`. Target changes have no reverse
  path into plugin runtime assets or documentation.

## Dependency Direction

- Plugin Hooks depend on `runtime/recommended-tools/`, which depends only on
  `policies/recommended-tools/` and the Python standard library.
- The setup control plane may read `setup-assets/`; plugin Hooks alone read `runtime/` and
  `policies/`. None of those areas may depend on plugin-discovered Skills.
- Repository-local Skill wrappers depend only on their corresponding sources under
  `setup-assets/skills/` and add no workflow behavior.
- Plugin manifests expose only `skills/` and host Hook entry points. They do not expose
  `setup-assets/`, `runtime/`, or `policies/`.

## Script and Test Ownership

- Keep setup implementation under `skills/setup-project-agents/scripts/` and recommended-tool
  executables under `runtime/recommended-tools/`.
- Keep repository contract tests under `tests/`; tests may import support scripts from their owning
  plugin Skill directories.

## Boundaries

- Keep runtime versions and executable commands in `Project Tools`.
- Keep public ownership, documentation, and installation policy in `Project Rules`.
- Describe application modules, package dependencies, or service layers only from direct repository
  evidence, not from the plugin directory structure.
