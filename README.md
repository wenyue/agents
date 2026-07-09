# wenyue/agents

Shared agent configuration for projects that use `.agents/` rules, skills, and subagents.

This repository provides public rules, reusable skills, reusable subagents, an `AGENTS.md` entry
template, and the `update-project-rules` sync workflow.

## New Project Setup

Run these steps from the target project root.

1. Provide `wenyue/agents` as repository reference or attached workspace context. The coding agent
   only needs read access to the public source files.
2. Ask the coding agent to use:

```text
wenyue/agents/.agents/skills/update-project-rules/SKILL.md
```

The workflow syncs public assets, creates or refreshes local project rules and local project
skills, then regenerates thin platform wrappers and `AGENTS.md`. Detailed generation requirements
live in the relevant placeholders, such as `.agents/rules/20-project-tools.md` and
`.agents/skills/project-development-workflow/SKILL.md`.

## Updating Existing Projects

Provide the latest `wenyue/agents` source to the coding agent, then run `update-project-rules` so
public sources, local project assets, wrappers, and `AGENTS.md` stay aligned.

## Third-Party Skills

Use skillshare only for third-party skills that should remain independently upgradable, such as
skills installed from other repositories:

```bash
skillshare update --all -p
skillshare sync -p
```

Do not use skillshare to install or sync the public rules, skills, or subagents from
`wenyue/agents`. `update-project-rules` owns that copy step.

## Boundaries

- Do not put project-specific facts into `wenyue/agents`.
- Do not rewrite public rules or public skills to fit one project.
- Keep wrappers thin and source files authoritative.
- Use `.skillshare/` only for third-party, independently upgradable skills.
