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

Set up or sync public agent assets first. Then refresh project-local rules and skills from current
repository evidence before regenerating entry files and wrappers.

## Core Rules

- Public assets mirrored from `wenyue/agents` stay public; do not locally adapt them in target
  repositories.
- Local project rules and local project skills are target-owned facts. Refresh them from current
  target repository evidence on every invocation.
- Run `scripts/sync_public_agent_assets.py` before manually editing project-owned assets.
- The sync script is limited to public assets, thin wrappers, entry files, and legacy cleanup. It
  must not generate project-local rule or workflow content from hardcoded scaffolds.
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
4. Refresh local project rules from current repository evidence every time, including
   `.agents/rules/20-project-tools.md`, `.agents/rules/21-project-rules.md`,
   `.agents/rules/22-project-structure.md`, and any project-owned module or domain rules.
5. Refresh local project skills from the same evidence every time, including
   `.agents/skills/project-development-workflow/SKILL.md` and any project-owned workflow skills.
6. Run the public sync script again so wrappers and entry files reflect the refreshed sources.
7. Run validation and report only final changed files, preserved files, refresh work, and
   verification results.

## Skill Resources

- `scripts/`: executable sync and validation tools.
- `references/`: JSON manifests that describe the `wenyue/agents` public base catalog.
- `assets/templates/`: wrapper and entry-file templates copied or rendered by the sync script.

## Local Refresh Evidence

Use concrete target-repository evidence when refreshing local assets:

- Tooling and runtime facts: MCP configs, shell scripts, package manifests, watcher configuration,
  test and generation commands, runtime ports, and project skill handoffs.
- Project conventions: language and framework usage, localization paths, route APIs,
  generated-file ownership, lint behavior, persistence models, and public project APIs.
- Structure facts: actual directories, module boundaries, analysis options, plugins, tests, shared
  locations, and dependency enforcement.
- Workflow facts: the current tooling rule, real bootstrap and verification commands, worktree
  handling, review checkpoints, merge-back behavior, and any unverified steps or blockers.
- `project-development-workflow` is a worktree execution prompt for Superpowers-style development.
  Do not include agent configuration setup as part of the ordinary development workflow.

Do not persist intermediate diagnostic state, template versions, or refresh reports. Temporary
notes are only for deciding the final edits and final user-facing output.

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
