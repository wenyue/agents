# wenyue/agents

Shared agent configuration for projects that use `.agents/` rules, skills, and subagents.

This repository provides:

- public rules under `.agents/rules/`
- reusable skills under `.agents/skills/`
- reusable subagents under `.agents/agents/`
- `AGENTS.md` as a project entry template
- `update-project-rules` as the sync workflow
- project-local placeholders for repository rules and generated workflow skills

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
or refreshes the target project's local rules and local project skills. After it runs, the runtime
copy should exist in the target project at `.agents/skills/update-project-rules/SKILL.md`.

### 3. Generate local project skills when needed

`project-development-workflow` in this repository is not a final workflow for target projects. It is
a public local-skill placeholder that tells `update-project-rules` what a generated project workflow
must cover.

When a target project needs isolated worktree development, the coding agent should generate
`.agents/skills/project-development-workflow/` from that project's repository evidence. The
generated workflow must document concrete bootstrap, verification, agent-instruction availability,
review, and merge-back behavior. It must be accepted only after a real git worktree run proves the
full flow works in that target project.

## Local Project Rule Authoring Guide

Public rules are the base. Project facts and constraints belong in `20+` local project rules.
Executable project workflows belong in local project skills.

### `20-project-tools.md`

Record stable tooling facts and verification requirements. Do not write the full execution
workflow here; put procedural worktree, bootstrap, verification, review, and merge-back steps in
`project-development-workflow`.

- package manager, language/runtime versions, and workspace layout
- test, build, lint, format, and code-generation commands
- MCP servers, runtime services, ports, health checks, and watcher markers
- generated assets or files required by tools
- verification requirements and links to procedural local skills

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

## Local Project Skill Authoring Guide

Public skills provide reusable techniques or workflows. Local project skills contain executable
workflows generated from the target repository's own facts.

### `project-development-workflow`

Treat this as the procedural counterpart to `20-project-tools.md`.

- `20-project-tools.md` records tooling facts, commands, generated-file requirements, and
  verification requirements.
- `project-development-workflow` turns those facts into an executable worktree workflow:
  bootstrap, verification, review checkpoints, and merge-back.
- The generated skill must stay consistent with `20-project-tools.md` and current repository
  evidence.
- Do not copy the public placeholder as the target workflow, and do not invent commands that are
  not supported by target repository evidence.

## Updating Existing Projects

Provide the latest `wenyue/agents` source to the LLM, then ask it to run `update-project-rules` so
wrappers, `AGENTS.md`, local project rules, local project skills, and public sources stay aligned.

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
