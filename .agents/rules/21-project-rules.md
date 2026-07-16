# Project Rules

Strength: `Default`

Scope: Public catalog ownership, language-mirror policy, target installation contracts, and
repository-local runtime boundaries.

## Public Catalog Ownership

- Treat `agents/` as the complete English public catalog and the sole source of truth for public
  rules, skills, agent prompts, templates, references, and scripts.
- Make public catalog changes in `agents/`; do not use `.agents/` or `agents-zh/` as the source for
  an English public asset.
- Treat `agents/skills/setup-project-agents/references/public_assets.json` as the owner of public
  asset inclusion, declared retirements, project-skill generators, wrapper templates, and managed
  root-configuration declarations.
- Keep deterministic synchronization and manifest validation in
  `agents/skills/setup-project-agents/scripts/`. Do not encode target-specific policy in those
  public scripts.

## Simplified-Chinese Mirror

- Treat `agents-zh/` as a hand-maintained Simplified-Chinese reading mirror of human-readable
  Markdown under `agents/`.
- When English Markdown changes materially, update its corresponding Chinese mirror in the same
  coherent change.
- Preserve relative paths, commands, identifiers, code blocks, classification, and behavioral
  meaning across the mirror.
- Do not mirror scripts, JSON manifests, platform configuration, or other machine-read files into
  `agents-zh/`.
- Never load, publish, or synchronize `agents-zh/` as a runtime or public source.

## Project-Local Runtime

- Treat `.agents/` as this repository's curated local runtime source of truth.
- Do not require `.agents/` to contain every public asset or to be byte-equivalent to `agents/`.
- Change `.agents/` only when this repository's own runtime behavior or project-local policy
  requires it; public catalog edits alone do not establish that requirement.
- Keep `.agents/agents/change-set-verifier.md` resolved to
  `.agents/skills/change-set-verification/SKILL.md`.

## Generation and Installation

- Treat `agents/rules/20-project-tools.md`, `agents/rules/21-project-rules.md`, and
  `agents/rules/22-project-structure.md` as public generation contracts, not final target rules.
- Treat `agents/skills/change-set-verification/SKILL.md` as the public generation contract for a
  target-owned operational skill.
- Generate complete target-owned rules and skills under `.agents/`; never copy a generation
  contract into the corresponding target path as the final runtime artifact.
- Preserve `.agents/` as the installation root in public prompts, templates, manifests, scripts,
  and documentation.

## Boundaries

- Keep commands, runtime requirements, and tool mutation behavior in `20-project-tools.md`.
- Keep directory ownership and dependency direction in `22-project-structure.md`.
- Do not introduce framework, API, persistence, lifecycle, lint, or generated-file conventions
  without repository evidence.
