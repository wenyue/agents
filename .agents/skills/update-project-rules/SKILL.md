---
name: update-project-rules
description: >-
  Update repository agent rule sources and their platform wrappers. Use when Codex must sync
  shared/base rules with a reference project, refresh project-owned rules from current repository
  facts, update AGENTS.md, align Cursor/Claude/GitHub/Codex rule or agent wrappers, or reconcile
  MCP/runtime config that follows the shared agent configuration structure.
---

# Update Project Rules

Update rule sources first. Then align every entry file, wrapper, and runtime config that follows
from those sources.

## Core Rules

- Public assets mirrored from `wenyue/agents` stay public; do not locally adapt them in target
  repositories.
- Public project-skill placeholders in `wenyue/agents` are generation contracts, not final target
  repository workflow skills. Generate target-specific skills from repository evidence.
- Run `scripts/sync_public_agent_assets.py` before manually editing project-owned rules.
- Change public rules or public skills in `wenyue/agents` first, then sync target repositories.
- Treat `.agents/rules/<nn>-<name>.md` as the source of truth for project rules.
- Treat `.agents/skills/<project-skill>/SKILL.md` as the source of truth for project workflows.
- Keep wrappers thin: platform metadata plus one `Apply @...` reference.

## Rule Ranges

- `00-*` through `09-*`: shared/global rules. When a reference project is supplied, copy or sync
  these from the reference unless the user explicitly says the current project is the source.
- `10-*` through `19-*`: shared/base rules, usually language-level defaults. Use a reference
  project heavily for structure and wording, but still verify the final content against the
  current repository's actual language, tooling, lint, build, and generated-file setup.
- `20-*` through `59-*`: project-owned rules. Update these from the current repository's actual
  tools, languages, modules, domains, packages, and verification workflows. Use a reference project
  only for structure or wording patterns.
- Other numbered ranges: follow the repository's own numbering policy. If none exists, treat them
  as project-owned.

## Workflow

1. Read `AGENTS.md`, then all applicable `00-*` through `09-*` rules.
2. Run the public sync script:
   `python3 .agents/skills/update-project-rules/scripts/sync_public_agent_assets.py`.
   Use `--source <path>` when `../agents` is not the correct source.
3. Review the script report for created, updated, deleted, and unchanged files.
4. Only after public sync, update local project rules from current repository evidence.
5. Then update local project skills from the same evidence, keeping their executable workflows
   aligned with the facts recorded in local project rules.

## Skill Resources

- `scripts/`: executable sync and validation tools.
- `references/`: JSON manifests that describe the `wenyue/agents` public base catalog, not
  target-repository facts.
- `assets/templates/`: wrapper and entry-file templates copied or rendered by the sync script.

## Evidence Sources

Use current repository evidence for every project-owned rule and for any base rule that mentions
language tools or generated files. Prefer concrete files over assumptions, such as package
manifests, build and lint config, test directories, CI or script commands, MCP config, generated
file config, existing wrapper metadata, and the repository directory structure.

Project-local rule and agent wrappers are discovered from the target repository's existing
`.agents/rules/*.md` and `.agents/agents/*.md`. Do not ship target-project local manifests in this
public skill.

## Local Project Assets

Local project rules and local project skills are peers:

- Local project rules, such as `.agents/rules/20-*`, record declarative project facts,
  constraints, commands, generated-file requirements, and verification requirements.
- Local project skills, such as `.agents/skills/<project-skill>/`, record executable workflows that
  use those facts.

Keep both generated from target repository evidence. When a workflow skill depends on tooling or
verification facts, keep it consistent with the corresponding local project rule instead of
duplicating stale assumptions.

## Local Project Skills

Generate project-specific local skills from placeholders only after public assets are synced. The
source placeholder describes the contract; the target skill must contain concrete commands and
scripts derived from the target repository.

Project-skill placeholders are not normal public mirrored skills. Do not add them to
`references/public_assets.json` just to make them available in targets. When a target workflow must
be generated, read the placeholder from the public source repository, then write a target-specific
skill into the target repository.

Do not hard-code target workflow generation in this public skill. Public guidance may define the
required sections, safety constraints, and acceptance criteria, but concrete language, framework,
dependency, code-generation, lint, test, and merge commands must come from target repository
evidence.

For `project-development-workflow`, generate `.agents/skills/project-development-workflow/` as the
procedural counterpart to `.agents/rules/20-project-tools.md`. The rule records tooling and
verification facts; the skill organizes those facts into the repository's isolated-worktree
workflow, bootstrap commands, verification commands, local agent asset handling, review checkpoints,
and merge-back behavior. The generated skill is accepted only after a real end-to-end workflow test
creates a git worktree, runs the complete generated workflow, merges back, and verifies that the
original workspace remains usable.

When generating the target skill:

- Read project-owned rules, package/build manifests, CI files, scripts, generated-file config, and
  existing developer docs before choosing commands.
- Prefer repository-provided scripts or CI commands over inventing new command sequences.
- Generate scripts only for deterministic project-local operations, such as worktree bootstrap,
  local agent asset copying, verification orchestration, or merge-back safety checks.
- If evidence is incomplete, write the missing evidence into the generated target skill and mark
  the workflow unverified.
- Keep the public placeholder generic. Do not add target repository names, stack-specific command
  recipes, or project-specific path assumptions to `wenyue/agents`.

## Wrapper Maps

- Rule source `.agents/rules/<name>.md` maps to:
  - `.cursor/rules/<name>.mdc`
  - `.claude/rules/<name>.md`
  - `.github/instructions/<name>.instructions.md`
- Agent source `.agents/agents/<name>.md` maps to:
  - `.cursor/agents/<name>.md`
  - `.claude/agents/<name>.md`
  - `.codex/agents/<name>.toml`
  - `.github/agents/<name>.agent.md`
- MCP/runtime config uses the repository's shared platform files. Preserve platform schema
  differences and keep server intent aligned across platforms.
- Preserve required wrapper metadata or schema fields. Thin wrappers may keep platform metadata,
  but their reusable instruction body should be only the `Apply @...` reference.

## Validation

For public-source edits in `wenyue/agents`, run:

```bash
python3 .agents/skills/update-project-rules/scripts/test_sync_public_agent_assets.py
```

For target repository updates after syncing public assets, run:

```bash
python3 .agents/skills/update-project-rules/scripts/sync_public_agent_assets.py --check
```

Do not use the target-repository `--check` command as the publication check for `wenyue/agents`
itself; it intentionally reports drift when run outside a prepared target repository.

## Output

- List changed files, or state that no edits were required.
- Summarize the public-sync result and any local project rule or local project skill work done
  afterward.
- Report validation commands and whether language build/test commands were skipped.
