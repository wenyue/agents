# wenyue/agents

Shared agent configuration for projects that use `.agents/` rules, skills, and subagents.

This repository provides:

- public rules under `.agents/rules/`
- reusable skills under `.agents/skills/`
- reusable subagents under `.agents/agents/`
- `AGENTS.md` as a project entry template
- `update-project-rules` as the sync workflow
- `project-development-workflow` as a placeholder contract for generated per-project worktree
  workflows

## New Project Setup

Run these steps from the target project root.

### 1. Provide this repo to the coding agent

Provide `wenyue/agents` as a repository reference or attached workspace context. The coding agent
only needs read access to the public source files; this README does not require a specific download
or install command.

### 2. Ask the LLM to update project rules

Ask the coding agent to use:

```text
wenyue/agents/.agents/skills/update-project-rules/SKILL.md
```

The skill syncs public rules, public skills, and public subagents from `wenyue/agents`, then creates
or refreshes the target project's local rules. After it runs, the runtime copy should exist in the
target project at `.agents/skills/update-project-rules/SKILL.md`.

### 3. Generate project workflow skills when needed

`project-development-workflow` in this repository is not a final workflow for target projects. It is
a public contract that tells `update-project-rules` what a generated project workflow must cover.

When a target project needs isolated worktree development, the coding agent should generate
`.agents/skills/project-development-workflow/` from that project's repository evidence. The
generated workflow must document concrete bootstrap, verification, agent-instruction availability,
review, and merge-back behavior. It must be accepted only after a real git worktree run proves the
full flow works in that target project.

## Local Rule Authoring Guide

Public rules are the base. Project facts belong in `20+` local rules.

### `20-project-tools.md`

Write stable tooling facts:

- package manager and scripts
- test, build, lint, format, and code-generation commands
- MCP servers, runtime services, ports, health checks, and watcher markers
- recommended verification order
- task-specific skill handoffs

Do not write general code style here.

### `21-project-rules.md`

Write project API and convention facts:

- project hooks, services, routes, state management, theme, logging, and storage APIs
- generated-file and hand-written-file boundaries
- custom lint interpretation
- domain terms, naming prefixes, lifecycle constraints, and async rules

Do not copy the directory map here.

### `22-project-structure.md`

Write structure facts:

- top-level modules and responsibilities
- feature/module internal layout
- dependency direction and forbidden dependencies
- shared locations and configuration ownership

If module order is enforced by a real config file, link to that file as the source of truth instead
of duplicating the complete configuration.

## Updating Existing Projects

Provide the latest `wenyue/agents` source to the LLM, then ask it to run `update-project-rules` so
wrappers, `AGENTS.md`, local `20+` rules, and public sources stay aligned.

If the project uses a generated `project-development-workflow`, refresh it from current repository
evidence during the same update. Do not copy the public placeholder as the target workflow.

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
- Do not rewrite public rules to fit one project.
- Keep wrappers thin and source files authoritative.
- Use `.skillshare/` only for third-party, independently upgradable skills.
