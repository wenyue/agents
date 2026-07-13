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

Sync public assets, then regenerate project-owned rules and environment setup from current target
repository evidence.

## Core Rules

- Public assets mirrored from `wenyue/agents` stay public; do not locally adapt them.
- Project-owned rules and skills are regenerated from current target repository evidence.
- Write every generated or refreshed project-owned rule and skill in English.
- Run `scripts/sync_public_agent_assets.py` before changing project-owned agent assets.
- The sync script mirrors public assets, regenerates thin wrappers and entry files, and deletes
  retired skill directories associated with catalog entries. It does not generate project-owned
  content.
- The sync script always fetches the configured public GitHub archive. Do not use local source
  checkouts, caches, or stale snapshots.
- Treat `.agents/rules/<nn>-<name>.md` and `.agents/skills/<project-skill>/SKILL.md` as sources of
  truth in the target repository.
- Use a subagent to generate project-owned files from generator contracts and current evidence. If
  no subagent capability is available, report a blocker instead of generating them in the main
  agent.
- Review complete candidate file contents, including generated scripts, before applying or testing
  them. Do not request or apply patch fragments for generated project-owned assets.

## Workflow

1. Read `AGENTS.md`, then all applicable `00-*` through `09-*` rules.
2. Run `python3 .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`.
3. Review created, updated, and deleted paths. The public sync must
   delete `.agents/skills/project-development-workflow/` when present.
4. Do not read, copy, or migrate the deleted skill. Do not restore it if later generation or
   validation fails.
5. Dispatch a subagent to regenerate project rules from current target repository evidence and the
   public generator contracts, including `.agents/rules/20-project-tools.md`,
   `.agents/rules/21-project-rules.md`, and `.agents/rules/22-project-structure.md`.
6. Have the same subagent generate the complete `.agents/skills/worktree-environment-setup/`
   directory from current target repository evidence. Generate
   `.agents/skills/worktree-environment-setup/SKILL.md` and any required `scripts/setup.sh`
   together. The generated skill prepares an already-created worktree; it does not create,
   implement, verify a baseline, integrate, or clean up worktrees.
7. Review the complete candidate rules, skill, and scripts using the environment-skill review gate
   below. Do not invoke the candidate or run actual setup or acceptance tests during this review.
8. Resolve every review finding, repeat the review, and apply the complete candidate files only
   after the review passes.
9. If `worktree-environment-setup` was created or materially changed, run the acceptance workflow
   below. The ordinary use of an unchanged generated skill does not repeat acceptance.
10. Run the public sync script again so wrappers and entry files reflect the refreshed sources.
11. Run validation and report final changed files, deletion/regeneration work, review results,
    acceptance results, and blockers.

## Environment Skill Evidence

Generate the environment skill from:

- `.agents/rules/20-project-tools.md`;
- package manifests and lock files;
- build, lint, type-check, format, test, and code-generation configuration;
- project setup scripts and CI workflows;
- generated-file ownership;
- required local services, environment variables, credentials, data, and command working
  directories.

Do not infer commands from the deleted skill or from generic language conventions when the target
repository provides a concrete command.

## Environment Skill Script Selection

Prefer a repository-owned setup script when it is narrow enough for worktree preparation, uses the
correct working directories, guards against primary-checkout mutation, propagates command failures,
and is safe to rerun. Invoke it directly from the generated skill instead of copying its commands
into `SKILL.md`. Do not rewrite a suitable existing script solely to change its language; the Bash
requirement applies to new target-owned scripts.

Reject an existing script when it couples setup to unrelated platform builds, tests, deployment,
machine-level provisioning, user-level configuration, or other task-specific work. If no existing
script is suitable, generate
`.agents/skills/worktree-environment-setup/scripts/setup.sh` as a target-owned Bash script. Require
`#!/usr/bin/env bash`, `set -euo pipefail`, location-independent path resolution, a pre-mutation
linked-worktree guard, quoted arguments, explicit prerequisite checks, rerun safety, and nonzero
failure propagation. Keep optional expensive setup behind explicit script arguments or branches.

The generated `SKILL.md` must identify the selected script as the canonical setup entry point and
must not duplicate the script's command sequence. A child script cannot persist environment
changes in its caller; use an evidenced repository environment helper or document a repeatable
sourcing/wrapper command when later commands need those values.

## Environment Skill Review

Review the finished environment-skill candidate before invoking it or running actual tests. Review
the complete `SKILL.md`, every generated script, and the repository evidence used to select or
reject existing scripts. Confirm that:

- the selected entry point is the narrowest suitable setup path;
- the linked-worktree check happens before any mutation;
- command failures and missing prerequisites stop the script with a nonzero status;
- reruns after partial setup are safe and unrelated local state is preserved;
- core setup is separated from expensive or task-specific branches;
- environment-variable lifetime is represented accurately;
- the candidate does not run tests, implement business changes, manage worktrees, commit, or sync
  agent configuration.

Resolve all findings and repeat the review. Do not start environment-skill acceptance while any
review finding remains unresolved. Report a review blocker instead of treating later test results
as a substitute for review.

## Environment Skill Acceptance

Run this workflow only after the environment-skill review passes and when the candidate was created
or materially changed:

1. Run `bash -n` on every generated Bash script.
2. Create a real temporary worktree outside the generated environment skill.
3. Make the exact candidate skill and relevant tooling rules available there. When they are not
   committed, copy byte-identical content and verify equality before invoking the candidate.
4. Invoke the candidate from the temporary worktree.
5. Verify dependency setup, required generated files, required services, and command working
   directories.
6. Functionally invoke every required linter, checker, and formatter with real project
   configuration. A version command alone is insufficient; formatters use non-writing check or
   dry-run modes.
7. Confirm the candidate did not create or remove worktrees, implement business changes, create
   commits, integrate branches, or modify agent configuration.
8. Mark the candidate accepted only after every required check passes, then remove the acceptance
   worktree safely.

If acceptance fails, keep the new candidate marked unaccepted, report the exact failing command and
blocker, and do not restore `project-development-workflow`.

## Wrapper Maps

- Rule source `.agents/rules/<name>.md` maps to Cursor, Claude, and GitHub thin wrappers.
- Agent source `.agents/agents/<name>.md` maps to Cursor, Claude, Codex, and GitHub thin wrappers.
- Preserve platform metadata and schema differences; reusable wrapper bodies contain only their
  `Apply @...` reference.

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

- List final changed and deleted files.
- Summarize public sync and project-owned regeneration separately.
- Report the environment-skill review result before any acceptance result.
- Report environment-skill acceptance only when it ran.
- Report validation commands and blockers exactly; do not describe skipped checks as passed.
