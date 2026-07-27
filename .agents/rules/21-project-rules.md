# Project Rules

Strength: `Default`

Scope: Public catalog ownership, language-mirror policy, target installation contracts,
repository-local runtime boundaries, and repository test contracts.

## Public Catalog Ownership

- Treat `agents/` as the complete English public catalog and the sole source of truth for public
  rules, skills, agent prompts, templates, references, and scripts.
- Make public catalog changes in `agents/`; treat `.agents/` as local runtime and `agents-zh/` as a
  reading mirror rather than sources for English public assets.
- Treat `agents/skills/setup-project-agents/references/public_assets.json` as the owner of public
  asset inclusion, declared retirements, Rule and Skill blueprints, wrapper templates, and managed
  root-configuration declarations.
- Keep deterministic synchronization and manifest validation in
  `agents/skills/setup-project-agents/scripts/`, while target-specific policy remains in the target
  repository.

## Simplified-Chinese Mirror

- Treat `agents-zh/` as a hand-maintained Simplified-Chinese translation of human-readable Markdown
  under `agents/`, for reading only.
- Translate meaning, not sentence form: use natural, plain Chinese instead of word-for-word
  translation, and rewrite sentences when needed without changing their technical meaning.
- When English Markdown changes materially, update its corresponding Chinese mirror in the same
  coherent change.
- Preserve relative paths, commands, identifiers, code blocks, classification, and behavioral
  meaning across the mirror.
- Mirror only human-readable Markdown into `agents-zh/`; scripts, JSON manifests, platform
  configuration, and other machine-read files remain untranslated.
- Keep `agents-zh/` outside runtime loading, publication, and synchronization.

## Project-Local Runtime

- Treat `.agents/` as this repository's curated local runtime source of truth.
- Let `.agents/` contain only the public assets required by this repository; byte equivalence with
  `agents/` is not a requirement.
- Change `.agents/` when this repository's runtime behavior or project-local policy requires it,
  independently of public catalog edits.
- Keep `.agents/agents/change-set-verifier.md` resolved to
  `.agents/skills/change-set-verification/SKILL.md`.

## Generation and Installation

- Treat `agents/blueprints/rules/` and `agents/blueprints/skills/` as the public sources for
  target-owned Rule and Skill generation, not as directly installable runtime assets.
- Generate complete target-owned rules and skills under `.agents/`; use a blueprint as an authoring
  contract rather than copying it as the final runtime artifact.
- Preserve `.agents/` as the installation root in public prompts, templates, manifests, scripts,
  and documentation.

## Test Contracts

- Unit tests may assert structured configuration, schemas, filesystem effects, state transitions,
  exit behavior, and other observable runtime results.
- Review human-readable Markdown, Rule and Skill prose, prompt and hook wording, and implementation
  source semantically. Limit automated assertions to structured configuration or observable runtime
  behavior rather than substrings, presence, absence, or section order.

## Boundaries

- Keep commands, runtime requirements, and tool mutation behavior in `Project Tools`.
- Keep directory ownership and dependency direction in `Project Structure`.
- Add framework, API, persistence, lifecycle, lint, or generated-file conventions only when
  repository evidence establishes them.
