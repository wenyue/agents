---
name: setup-project-agents
description: >-
  Set up or sync repository agent assets from the wenyue/agents public catalog. Use when Codex must
  initialize .agents rules, public skills, shared subagents, AGENTS.md, and thin
  Cursor/Claude/GitHub/Codex wrappers; refresh project-owned rules or project skills from current
  repository facts; or reconcile MCP/runtime config that follows the shared agent configuration
  structure.
---

# Setup Project Agents

Set up or sync public agent assets first. Then align every entry file, wrapper, and runtime config
that follows from those sources.

## Core Rules

- Public assets mirrored from `wenyue/agents` stay public; do not locally adapt them in target
  repositories.
- Local project rules and local project skills are generated from their public placeholders, then
  completed from target repository evidence.
- Run `scripts/sync_public_agent_assets.py` before manually editing project-owned assets.
- The sync script should work without the user attaching `wenyue/agents`: use `--source <path>` for
  a local checkout, otherwise let the script fetch the configured GitHub archive and copy only the
  manifest-listed public assets.
- Change public rules, public skills, or placeholder contracts in `wenyue/agents` first, then sync
  target repositories.
- Treat `.agents/rules/<nn>-<name>.md` as the source of truth for project rules.
- Treat `.agents/skills/<project-skill>/SKILL.md` as the source of truth for project workflows.
- Keep wrappers thin: platform metadata plus one `Apply @...` reference.

## Workflow

1. Read `AGENTS.md`, then all applicable `00-*` through `09-*` rules.
2. Run the public sync script:
   `python3 .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`.
   Use `--source <path>` only when testing local `wenyue/agents` changes or a fork.
3. Review the script report for created, updated, deleted, and unchanged files.
4. Complete or refresh local project rules from current repository evidence, following each
   placeholder rule's contract.
5. Complete or refresh local project skills from the same evidence, following each placeholder
   skill's contract.

## Skill Resources

- `scripts/`: executable sync and validation tools.
- `references/`: JSON manifests that describe the `wenyue/agents` public base catalog.
- `assets/templates/`: wrapper and entry-file templates copied or rendered by the sync script.

## Placeholder Routing

Detailed generation requirements belong in the relevant placeholder, not in this orchestration
skill. For example:

- `.agents/rules/20-project-tools.md` defines how to create and fill the local tooling rule.
- `.agents/skills/project-development-workflow/SKILL.md` defines how to create and validate the
  local workflow skill.

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
python3 .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
```

For target repository updates after syncing public assets, run:

```bash
python3 .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check
```

## Output

- List changed files, or state that no edits were required.
- Summarize the public-sync result and any local project rule or local project skill work done
  afterward.
- Report validation commands and whether language build/test commands were skipped.
