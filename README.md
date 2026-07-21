# wenyue/agents

Shared runtime assets live under `agents/rules/`, `agents/skills/`, and `agents/agents/`. Generative
Rule and Skill blueprints live under `agents/blueprints/`. Runtime assets are installed into target
repositories under `.agents/`, while blueprints guide creation of target-owned `.agents/` content;
this repository keeps a curated local runtime configuration in `.agents/` rather than mirroring the
public catalog.

## New Project Setup

From the target project root, ask the coding agent to use `setup-project-agents`:

```text
wenyue/agents/agents/skills/setup-project-agents/SKILL.md
```

The skill fetches this public source when needed, syncs only manifest-listed public assets,
deletes declared legacy project skills, refreshes local project assets from target repository
evidence, and regenerates thin wrappers. It generates `worktree-environment-setup` for an existing
worktree and syncs the public `worktree-integrate` completion workflow.

## Boundaries

- Edit the public catalog under `agents/`; treat `.agents/` as this repository's curated local
  runtime configuration.
- Keep project-specific facts in the target repository, not here.
- Do not locally adapt public rules or public skills for one project.
- Use skillshare only for third-party skills that should remain independently upgradable:

```bash
skillshare update --all -p
skillshare sync -p
```
