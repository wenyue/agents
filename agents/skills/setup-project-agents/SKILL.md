---
name: setup-project-agents
description: Use when initializing or updating a repository's agent configuration from the wenyue/agents public catalog, including shared assets, project-owned rules and skills, wrappers, runtime values, and native platform configuration.
---

# Setup Project Agents

Set up or update the target repository's agent configuration through one idempotent workflow. Finish
with current public assets, evidence-backed project configuration, preserved local ownership, and no
unresolved managed drift.

## Outcome

- Fetch `https://github.com/wenyue/agents/archive/refs/heads/master.zip` on every run. Do not use a
  local checkout, cache, or stale snapshot as the public source.
- Mirror catalog-listed public assets and declared retirements exactly.
- Preserve target-owned assets outside the public, generated, and retired sets. Stop and report an
  ownership collision instead of resolving it silently.
- Generate project-owned configuration from current target evidence. Previous content may be used
  as reference during generation, but it is not a source of truth.

## Managed Configuration

Reconcile all applicable configuration in one change set:

- public rules, skills, agent prompts, wrappers, entry files, and declared retirements;
- `.agents/rules/20-project-tools.md`;
- `.agents/rules/21-project-rules.md`;
- `.agents/rules/22-project-structure.md`;
- `.agents/skills/worktree-environment-setup/` when the target has a real preparation step;
- `.agents/skills/change-set-verification/`;
- target-owned runtime values in native agent wrappers; and
- native configuration for every installed or explicitly targeted agent platform.

Write generated or refreshed project-owned rules and skills in English. Produce complete files and
directories, follow their generation contracts, and treat accepted candidates as the target
repository's runtime sources of truth.

## Workflow

1. Read `AGENTS.md` and all applicable `00-*` through `09-*` rules in the target repository.
2. Run:

   ```bash
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py
   ```

3. Review every reported creation, update, deletion, retirement, wrapper change, entry-file change,
   and root-configuration change. Confirm unrelated local assets remain untouched.
4. Discover installed and explicitly targeted agent platforms. Collect current evidence for tools,
   runtimes, services, generated files, APIs, conventions, modules, dependencies, wrappers, and
   platform configuration.
5. Revalidate every retained project claim and runtime value against that evidence.
6. Resolve target-owned runtime values required by each installed or targeted platform.
7. Generate complete candidates for all managed project rules and skills from one shared evidence
   set. Use one subagent for the generation task; if subagents are unavailable, report a blocker.
8. Review each complete candidate and resolve every finding before replacing its target file.
9. Apply accepted candidates, then rerun the synchronization command so wrappers, entry files, and
   deterministic configuration converge on their sources.
10. Validate material changes in dependency order: native platform configuration, project rules,
    environment setup, and change-set verification.
11. Run the synchronization command again and finish with:

    ```bash
    python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check
    ```

## Target-Owned Decisions

- Keep project-specific model, reasoning, permission, service, and platform choices in target-owned
  configuration.
- Treat existing wrapper values as previous target decisions. Retain them only when they remain
  supported and suitable for the wrapper's responsibility.
- Supply every required runtime value explicitly and keep evidence-backed sandbox and permission
  restrictions.
- Change runtime values only when platform support, role responsibility, permissions, observed
  quality, project complexity, or an explicit cost, latency, or quality policy justifies the change.
- Let the synchronization command manage deterministic root configuration and entry files. Review
  its reported changes instead of reconstructing or editing managed values manually.

## Review Gate

Before applying candidates, confirm:

- every change belongs to the managed configuration and preserves unrelated target-owned files;
- every installed or targeted platform has complete, supported wrappers and runtime values;
- generated rules have the correct title, strength, scope, numbering, ownership, and current
  evidence;
- generated skills satisfy their own contracts and contain only resources required by their target
  workflow; and
- wrappers remain thin, reference one source of truth, and are discoverable from `AGENTS.md`.

Do not accept placeholder content, unsupported claims, stale paths, unresolved ownership, missing
references, invalid configuration, or an incomplete required runtime field.

## Acceptance Gate

- Confirm the final synchronization check reports no managed drift.
- Validate changed native configuration with deterministic local checks for syntax, required fields,
  references, permissions, and platform eligibility.
- Validate each changed project rule and skill through its own contract and the target repository's
  supported checks.
- Do not invoke a real model during setup or acceptance. Model availability, response quality,
  latency, and cost are outside this workflow's acceptance boundary.
- Keep any affected asset or platform unaccepted while a required check fails, has no result, or
  leaves an unresolved finding.

## Result

Report the created, updated, deleted, and unchanged managed files. Summarize public synchronization,
project-owned configuration, agent runtime, platform configuration, candidate review, acceptance,
remaining blockers, and any check that did not produce a conclusive result.
