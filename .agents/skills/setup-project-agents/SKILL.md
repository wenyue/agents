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
- Write every generated or refreshed project-owned rule and skill in English.
- Run `scripts/sync_public_agent_assets.py` before manually editing project-owned assets.
- The sync script is limited to public assets, thin wrappers, entry files, and legacy cleanup. It
  must not generate project-local rule or workflow content from hardcoded scaffolds.
- The sync script always fetches the configured public GitHub archive. Do not use local source
  checkouts, source caches, or stale public asset snapshots.
- Change public rules, public skills, or placeholder contracts in `wenyue/agents` first, then sync
  target repositories.
- Treat `.agents/rules/<nn>-<name>.md` as the source of truth for project rules.
- Treat `.agents/skills/<project-skill>/SKILL.md` as the source of truth for project workflows.
- Keep wrappers thin: platform metadata plus one `Apply @...` reference.
- After public sync, use a subagent to generate or refresh target-owned local project files from
  the generator contracts. If no subagent capability is available, stop and report the missing
  capability as a blocker instead of silently generating those files in the main agent.

## Workflow

1. Read `AGENTS.md`, then all applicable `00-*` through `09-*` rules.
2. Run the public sync script:
   `python3 .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`.
3. Review the script report for created, updated, deleted, and unchanged files.
4. Dispatch a subagent to refresh local project rules from current repository evidence and the
   generator contracts, including `.agents/rules/20-project-tools.md`,
   `.agents/rules/21-project-rules.md`, `.agents/rules/22-project-structure.md`, and any
   project-owned module or domain rules.
5. Have the same subagent refresh local project skills from the same evidence and generator
   contracts, including `.agents/skills/project-development-workflow/SKILL.md` and any
   project-owned workflow skills.
6. Review the subagent output before applying it. The subagent must return candidate file contents
   or precise patch ranges; the main agent applies only reviewed local project files.
7. Run the public sync script again so wrappers and entry files reflect the refreshed sources.
8. Run validation and report only final changed files, preserved files, refresh work, and
   verification results.

## Skill Resources

- `scripts/`: executable sync and validation tools.
- `references/`: JSON manifests that describe the `wenyue/agents` public base catalog.
- `assets/templates/`: wrapper and entry-file templates copied or rendered by the sync script.

## Local Refresh Evidence

Base every local refresh on evidence from the target repository, not on placeholder text or prior
run notes. Collect evidence by the kind of local asset it will generate:

- Tooling evidence: package manifests, scripts, runtime services, ports, MCP config, generated
  assets, CI workflows, and verification commands.
- Project behavior evidence: APIs, routes, schemas, generated-file ownership, lint behavior,
  persistence models, lifecycle rules, and domain terminology.
- Structure evidence: real directories, module owners, package boundaries, shared locations,
  dependency direction, and enforcement tools.
- Workflow evidence: bootstrap steps, worktree handling, review checkpoints, merge-back behavior,
  post-merge verification, and known blockers.

Keep generated content in the asset that owns it: stable facts in project rules, executable
development procedures in local project skills, and public asset synchronization only in this setup
skill. Do not persist intermediate diagnostic state, template versions, refresh reports, or
one-run status fields.

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
