# wenyue/agents

Shared `.agents/` rules, skills, subagents, wrappers, and `AGENTS.md` templates.

## New Project Setup

From the target project root, ask the coding agent to use `setup-project-agents`:

```text
wenyue/agents/.agents/skills/setup-project-agents/SKILL.md
```

The skill fetches this public source when needed, syncs only manifest-listed public assets, creates
or refreshes local project placeholders, and regenerates thin wrappers.

## Boundaries

- Keep project-specific facts in the target repository, not here.
- Do not locally adapt public rules or public skills for one project.
- Use skillshare only for third-party skills that should remain independently upgradable:

```bash
skillshare update --all -p
skillshare sync -p
```
