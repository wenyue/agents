# wenyue/agents

Shared agent configuration for projects that use `.agents/` rules, skills, and subagents.

This repository provides public rules, reusable skills, reusable subagents, an `AGENTS.md` entry
template, and the `setup-project-agents` sync workflow.

## New Project Setup

From the target project root, ask the coding agent to use:

```text
wenyue/agents/.agents/skills/setup-project-agents/SKILL.md
```

The workflow fetches the public source archive when no local `wenyue/agents` checkout is supplied,
syncs only manifest-listed public assets, creates or refreshes local project rules and local
project skills, then regenerates thin platform wrappers and `AGENTS.md`. Detailed generation
requirements live in the relevant placeholders, such as `.agents/rules/20-project-tools.md` and
`.agents/skills/project-development-workflow/SKILL.md`.

## Updating Existing Projects

Run `setup-project-agents` so public sources, local project assets, wrappers, and `AGENTS.md` stay
aligned. Use the workflow's `--source <path>` option only when testing local `wenyue/agents`
changes or a fork.

## Third-Party Skills

Use skillshare only for third-party skills that should remain independently upgradable, such as
skills installed from other repositories:

```bash
skillshare update --all -p
skillshare sync -p
```

Do not use skillshare to install or sync the public rules, skills, or subagents from
`wenyue/agents`. `setup-project-agents` owns that copy step.

## Boundaries

- Do not put project-specific facts into `wenyue/agents`.
- Do not rewrite public rules or public skills to fit one project.
- Keep wrappers thin and source files authoritative.
- Use `.skillshare/` only for third-party, independently upgradable skills.
