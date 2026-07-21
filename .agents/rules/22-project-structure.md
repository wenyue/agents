# Project Structure

Strength: `Advisory`

Scope: Top-level catalog, mirror, local-runtime, documentation, and synchronization ownership
boundaries.

## Repository Areas

- `agents/` owns the complete English public catalog:
  - `agents/rules/` contains directly distributed shared rules.
  - `agents/skills/` contains directly distributed operational and orchestration skills.
  - `agents/blueprints/` contains Rule and Skill generation contracts that produce target-owned
    runtime assets.
  - `agents/agents/` contains public agent prompts.
- `agents-zh/` mirrors only the human-readable Markdown structure of `agents/` for Simplified-Chinese
  readers. It owns no runtime, generation, synchronization, or distribution behavior.
- `.agents/` owns this repository's curated local runtime. Its rules, skills, and agent prompts are
  selected for this repository and need not reproduce the public catalog.
- `docs/` owns design and implementation plans; it is not an agent-runtime or public-distribution
  source.
- `AGENTS.md` is the repository entry point for discovering `.agents/rules/`.
- `README.md` owns public catalog onboarding and the high-level boundary between `agents/` and
  `.agents/`.

## Distribution Flow

- Public synchronization reads the manifest and English assets under `agents/`, then installs
  manifest-selected assets into a target repository under `.agents/`.
- Rule and Skill blueprints under `agents/blueprints/` guide creation of complete target-owned
  `.agents/` files; the blueprints themselves are not installed as runtime content.
- Changes do not flow from `.agents/` back into `agents/`.
- Changes do not flow from `agents-zh/` into `agents/`, `.agents/`, manifests, wrappers, or target
  repositories.

## Script and Test Ownership

- Keep the public sync implementation under `agents/skills/setup-project-agents/scripts/` and
  distribute it as part of the operational skill.
- Keep public distribution data under
  `agents/skills/setup-project-agents/references/`.
- Keep repository maintenance and contract tests under `tests/`; do not distribute them as runtime
  skill resources.
- Repository tests may import support scripts from their owning public skill directories without
  moving those scripts out of their runtime owners.

## Local Runtime Dependencies

- Keep `.agents/agents/change-set-verifier.md` dependent on
  `.agents/skills/change-set-verification/SKILL.md`.
- Keep the local verification skill self-contained because this repository declares no package,
  module, service, formatter, linter, fixer, build, or environment-setup boundary.
- Do not add `.agents/skills/worktree-environment-setup/` unless the repository later declares a
  real preparation step.

## Boundaries

- Keep runtime versions and executable commands in `Project Tools`.
- Keep public ownership, mirror maintenance, and installation policy in `Project Rules`.
- Do not infer application modules, package dependencies, or service layers from the catalog
  directory structure.
