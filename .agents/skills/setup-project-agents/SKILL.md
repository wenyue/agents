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

Sync public assets, then regenerate project-owned rules, environment setup, and verification from
current target-repository evidence.

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
4. Dispatch a subagent to regenerate project rules from current target-repository evidence and the
   public generator contracts, including `.agents/rules/20-project-tools.md`,
   `.agents/rules/21-project-rules.md`, and `.agents/rules/22-project-structure.md`.
5. Have the same subagent generate the complete `.agents/skills/worktree-environment-setup/` and
   `.agents/skills/project-verification/` directories from their public generator contracts and the
   same evidence.
6. Review the complete candidate rules, skills, references, and scripts using the review gate
   below. Do not invoke the candidate or run actual setup or acceptance tests during this review.
7. Resolve every review finding, repeat the review, and apply the complete candidate files only
   after the review passes.
8. Run environment-skill acceptance when `worktree-environment-setup` was created or materially
   changed. Run verification-skill acceptance after the temporary worktree environment is ready
   when `project-verification` was created or materially changed. The ordinary use of an unchanged
   generated skill does not repeat its acceptance.
9. Run the public sync script again so wrappers and entry files reflect the refreshed sources.
10. Run validation and report final changed files, deletion/regeneration work, review results,
     acceptance results, and blockers.

## Review

Review complete candidate files before invoking them. Confirm that:

- project-owned rules and skills are written in English and match current repository evidence;
- claims about commands, generated files, services, and ownership are backed by concrete files;
- `20-project-tools.md` records tool capabilities and invocation constraints without absorbing
  environment or verification workflow policy;
- the environment skill contains `SKILL.md`, `scripts/setup.sh`, and `scripts/setup.ps1` and follows
  its public generator contract;
- both setup entry points prepare the same core environment, guard the primary checkout, surface
  failures, and are safe to rerun;
- the environment skill stops at readiness and hands completed-change verification to
  `project-verification` instead of embedding verification selection policy;
- the verification skill's trigger, task scope, verification matrix, command scopes, cost claims,
  broadening rules, and path-scoped safe fixes match current repository evidence;
- verification excludes unrelated dirty files, does not require unconditional full-suite runs,
  deduplicates already-covered surfaces, and permits mutation only after an observed in-scope
  diagnostic;
- the candidate does not absorb tests, business implementation, worktree lifecycle, Git
  integration, or agent sync work owned by other workflows.

Resolve all findings and repeat the review. Do not start environment-skill acceptance or
verification-skill acceptance while any review finding remains unresolved. Report a review blocker
instead of treating later test results as a substitute for review.

## Acceptance

Run only after review passes, and only for acceptance phases required by created or materially
changed generated skills. When both phases apply, keep one temporary linked worktree and run them
in the order below.

### Environment Skill

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
7. Mark the environment candidate accepted only after every required check passes. Keep the ready
   worktree when verification-skill acceptance follows; otherwise remove it safely.

### Verification Skill

Run this phase only after the temporary linked worktree environment is ready. If the environment
skill was unchanged, use its accepted host entry point to prepare the worktree without treating
ordinary setup as a repeated environment-skill acceptance.

1. Validate the complete generated verification skill and load its verification matrix when one
   exists.
2. Make the exact candidate and relevant project rules available in the temporary worktree. Verify
   byte equality for uncommitted candidate files before using them.
3. Exercise a narrow representative change set and confirm that the skill selects the minimum
   supported checks once, excludes unrelated dirty files, and records scope and rationale.
4. When the project exposes a documented formatter or safe fixer, create an isolated in-scope
   diagnostic, confirm check-before-fix behavior, apply one path-scoped safe fix, and repeat the
   affected checks. Confirm no unrelated file changed.
5. Confirm that a failed prerequisite or focused preflight prevents dependent expensive checks,
   and that a representative high-risk change selects the documented broader or full verification
   surface.
6. Confirm output distinguishes `passed`, `failed`, `inconclusive`, and `not applicable`, including
   commands, scopes, selection reasons, fixes, and gaps.
7. Do not run an expensive full suite only to accept the skill. Run it during acceptance only when
   repository evidence proves it is inexpensive and required for every coherent code change.
8. Inspect repository and worktree state, mark the verification candidate accepted only after every
   applicable scenario passes, and remove the temporary worktree safely.

### Failure Recovery

If any generated script fails, stop immediately and keep every affected candidate unaccepted.
Report the exact failing command and blocker. Do not patch the temporary acceptance worktree, skip
the failure, or resume from the failing step. Fix the complete candidate on the target repository's
current branch, repeat the complete review, copy the revised candidate byte-for-byte, and restart
acceptance from its first step. Preserve unrelated current-branch changes throughout recovery.

For non-script acceptance failures, keep the affected candidate unaccepted, fix it in the current
branch, repeat review, and restart that acceptance phase from its first step. Do not restore
`project-development-workflow`.

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
- Report the shared candidate review result before any acceptance result.
- Report environment-skill and verification-skill acceptance separately and only when each ran.
- Report validation commands and blockers exactly; do not describe skipped checks as passed.
