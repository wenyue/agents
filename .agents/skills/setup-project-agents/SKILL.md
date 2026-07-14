---
name: setup-project-agents
description: >-
  Set up or sync repository agent assets from the wenyue/agents public catalog. Use when Codex must
  initialize .agents rules, public skills, shared subagents, AGENTS.md, and thin
  Cursor/GitHub/Codex wrappers; refresh project-owned rules or project skills from current
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
3. Review created, updated, and deleted paths. Delete
   `.agents/skills/project-development-workflow/` when the public catalog retires it; do not use it
   as generation evidence.
4. Dispatch a subagent to regenerate project rules from current target repository evidence and the
   public generator contracts, including `.agents/rules/20-project-tools.md`,
   `.agents/rules/21-project-rules.md`, and `.agents/rules/22-project-structure.md`.
5. Have the same subagent generate the complete `.agents/skills/worktree-environment-setup/`
   directory from its public generator contract and current repository evidence.
6. Review the complete candidate rules, skill, and scripts using the review gate
   below. Do not invoke the candidate or run actual setup or acceptance tests during this review.
7. Resolve every review finding, repeat the review, and apply the complete candidate files only
   after the review passes.
8. If `worktree-environment-setup` was created or materially changed, run the acceptance workflow
   below. The ordinary use of an unchanged generated skill does not repeat acceptance.
9. Run the public sync script again so wrappers and entry files reflect the refreshed sources.
10. Run validation and report final changed files, deletion/regeneration work, review results,
     acceptance results, and blockers.

## Review

Review complete candidate files before invoking them. Confirm that:

- project-owned rules and skills are written in English and match current repository evidence;
- claims about commands, generated files, services, and ownership are backed by concrete files;
- the environment skill contains `SKILL.md`, `scripts/setup.sh`, and `scripts/setup.ps1` and follows
  its public generator contract;
- both setup entry points prepare the same core environment, guard the primary checkout, surface
  failures, and are safe to rerun;
- the candidate does not absorb tests, business implementation, worktree lifecycle, Git
  integration, or agent sync work owned by other workflows.

Resolve all findings and repeat the review. Do not start environment-skill acceptance while any
review finding remains unresolved. Report a review blocker instead of treating later test results
as a substitute for review.

## Acceptance

Run this workflow only after review passes and when the candidate was created or materially
changed:

1. Validate the generated skill and parse only the setup script for the acceptance host with its
   native shell tooling: Bash on Linux and macOS for `scripts/setup.sh`, and PowerShell on Windows
   for `scripts/setup.ps1`. Do not parse or invoke the other platform's setup script during
   acceptance.
2. Create a real temporary linked worktree outside the generated environment skill.
3. Make the exact candidate skill and relevant tooling rules available there. When they are not
   committed, copy byte-identical content and verify equality before invoking the candidate.
4. Invoke the same host-specific setup entry point from the temporary worktree.
5. Verify required dependencies, generated files, services, working directories, linters, checkers,
   and formatters with real project configuration rather than version-only probes.
6. Inspect repository and worktree state to confirm setup stayed within its contract.
7. Mark the candidate accepted only after every required check passes, then remove the acceptance
   worktree safely.

If acceptance fails, keep the new candidate marked unaccepted, report the exact failing command and
blocker, and do not restore `project-development-workflow`.

## Wrapper Maps

- Rule source `.agents/rules/<name>.md` maps to Cursor and GitHub thin wrappers.
- Agent source `.agents/agents/<name>.md` maps to Cursor, Codex, and GitHub thin wrappers.
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
