# Project Structure

Strength: `Advisory`

Scope: Top-level placement, distribution flow, dependency direction, and script/test ownership.

Place repository assets in the areas below and preserve the declared dependency direction.
`AGENTS.md` owns this Rule's applicability; the SmartKit Rule configuration owns precedence.

## Repository Areas

- `rules/source/` owns plugin Rule policy, `rules/registry.json` owns order and activation, and
  `rules/cursor/` contains Cursor-native adapters.
- `skills/` contains registry-declared SmartKit custom Skills and read-only external Skill
  snapshots.
- `agents/registry.json` and `agents/source/` own Plugin Agent intent and shared instructions;
  `agents/codex/`, `agents/cursor/`, and `agents/copilot/` are generated host adapters.
- `mcp/registry.json` owns Plugin MCP intent; the other files under `mcp/` and root `.mcp.json` are
  generated host adapters.
- `hooks/` contains the host lifecycle entry points.
- `runtime/recommended-tools/` contains private Hook executables and no discoverable Skill.
  `policies/recommended-tools/` contains the declarations shared by that runtime and setup output.
- Target projects own Rules under `.agents/rules/`, Skills under `.agents/skills/`, and Agent sources
  under `.agents/agents/`; `.agents/config.json` declares external Skills, Agents, and MCP. Setup
  preserves those canonical inputs and records setup-managed outputs, including Codex Plugin Agent
  defaults, in `.agents/smartkit.lock.json`.
- `setup-assets/blueprints/` and `setup-assets/templates/` contain generation and rendering inputs,
  while `setup-assets/catalog/` owns asset selection and project-configuration contracts.
- `docs/agents/` contains project-owned repository context produced by
  `setup-matt-pocock-skills` and reached from its `AGENTS.md` or `CLAUDE.md` entry block; keep other
  design material under `docs/` and Simplified-Chinese documentation under `docs/zh-CN/`.
- `.agents/rules/` owns this repository's development instructions, and `.agents/plugins/` owns its
  local marketplace configuration. No other `.agents/` content belongs in this repository.
- `AGENTS.md` is the entry point for discovering `.agents/rules/`; `README.md` is public plugin
  onboarding and describes the setup boundary.
- `vendor/external-skills.lock.json` and `licenses/` record all external plugin Skill snapshots;
  the generic updater exclusively owns the lock-declared root Skill directories.
- `tests/fixtures/write-rules-and-skills/` owns six independent authoring-evaluation case inputs:
  Shared Rule, Project-local Rule, Rule-generation contract, Shared Skill, Project-local Skill, and
  Skill-generation contract. A Project-local case may include a small self-contained project.
  Nothing under this fixture root is a plugin runtime source, discovery input, distribution asset,
  generated candidate, or expected prose answer.

## Distribution Flow

- Setup reads `setup-assets/catalog/assets.json`, then force-converges catalog-selected public
  Rules and Skills, external Skill snapshots, Codex Plugin Agent defaults, project-declared Agent
  adapters, and MCP entries while preserving project-owned canonical inputs. Recommended-tool
  runtime and policy files remain plugin-private.
- Blueprints guide creation of complete target-owned Rules and Skills; they are not installed as
  runtime content themselves.
- The setup control plane remains in `skills/setup-project-agents/`; catalog-managed external Skills
  enter targets only through setup. Target changes have no reverse path into plugin runtime assets
  or documentation.

## Dependency Direction

- Plugin Hooks depend on `runtime/recommended-tools/`, which depends only on
  `policies/recommended-tools/`, `mcp/registry.json`, an optional target `.agents/config.json`, and
  the Python standard library.
- The setup control plane may read `setup-assets/`; plugin Hooks alone read `runtime/` and
  `policies/`. None of those areas may depend on plugin-discovered Skills.
- `setup-project-agents` may verify the project-owned Matt repository-context prerequisite. It does
  not read Matt seed templates or author Matt outputs; `setup-matt-pocock-skills` owns that work.
  Plugin Hooks must not depend on vendored Skills, and all vendored Skills remain independent
  read-only plugin capabilities.
- Plugin manifests expose `skills/`, Cursor and Copilot Plugin Agent adapters, Plugin MCP adapters,
  host Hook entry points, and Cursor-native Rule adapters. Codex Plugin Agent adapters enter target
  repositories only through catalog-managed setup. Manifests do not expose `setup-assets/`, private
  runtime implementation, or policies directly.

## Script and Test Ownership

- Keep setup implementation under `skills/setup-project-agents/scripts/` and recommended-tool
  executables under `runtime/recommended-tools/`.
- Keep repository contract tests under `tests/`; tests may import support scripts from their owning
  plugin Skill directories.
- Keep generated candidates, Git state, mutable working files, verdicts, reports, and sandboxes
  outside the `write-rules-and-skills` fixture root. Copy a fixture project only when an executable
  Project-local case needs mutable state.

## Boundaries

- Keep runtime versions and executable commands in `Project Tools`.
- Keep public ownership, documentation, and installation policy in `Project Rules`.
- Describe application modules, package dependencies, or service layers only from direct repository
  evidence, not from the plugin directory structure.
