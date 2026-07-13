---
name: worktree-environment-setup
description: Use when defining, generating, or validating a target repository's environment setup skill for an already-created Git worktree.
---

# Worktree Environment Setup

This public skill is a generator contract for a target-owned project skill. Do not use this file as
the target repository's final setup procedure.

## Generation Contract

`setup-project-agents` generates `.agents/skills/worktree-environment-setup/SKILL.md` entirely from
current target repository evidence. The generated skill runs only after another skill or platform
mechanism has created or entered a Git worktree.

Use `.agents/rules/20-project-tools.md`, package manifests, project scripts, CI configuration, and
generated-file ownership as evidence. Prefer a repository-owned setup script that already provides
the required worktree preparation. Do not copy commands from this contract or from a deleted
`project-development-workflow`.

## Script-First Setup

Keep the generated setup procedure stable behind a script entry point instead of asking an agent to
reconstruct a long command sequence on every use.

1. Inspect existing repository scripts before designing the generated skill.
2. Use an existing script directly when it prepares the required environment with the correct
   scope, a pre-mutation linked-worktree guard, working directories, failure propagation, rerun
   behavior, and generated-file ownership.
3. Do not select a script that performs unrelated builds, tests, deployment, machine-level
   provisioning, or user-level configuration merely because it includes setup as one step.
4. If no existing script is suitable, generate
   `.agents/skills/worktree-environment-setup/scripts/setup.sh` with the target-owned skill.
5. Write every newly generated setup script in Bash. The generated `SKILL.md` must invoke that
   script as its canonical setup entry point instead of duplicating its command sequence.

Do not rewrite a suitable existing repository script solely to change its language. The Bash
requirement applies to new scripts generated for the target-owned skill.

The generated Bash script must:

- start with `#!/usr/bin/env bash` and `set -euo pipefail`;
- resolve its own location and repository root without assuming the caller's current directory;
- reject the primary checkout before any mutation and operate only on the current linked worktree;
- quote paths and arguments, check prerequisites, and preserve nonzero command exit status;
- be safe to rerun after partial setup and avoid destructive cleanup of unrelated state;
- keep expensive or task-specific setup behind explicit arguments or separate script branches;
- report the failing command or missing prerequisite without silently continuing;
- avoid business changes, tests, worktree lifecycle operations, commits, and agent configuration.

If environment variables must survive after the script exits, use a repository-owned environment
helper or document a repeatable sourcing/wrapper command. Do not claim that a child process changed
its caller's environment.

## What Belongs Here

- Instructions for generating the target-owned environment setup skill.
- Dependency installation or restoration required inside an already-created Git worktree.
- Project-specific setup for linters, checkers, formatters, compilers, and generators.
- Proto and other generated files required for imports, runtime startup, or test collection.
- Required environment variables, local data, services, and command working directories.
- Failure reporting for missing dependencies, credentials, services, or generated assets.
- The selected repository script or the generated Bash fallback and its supported arguments.

## What Does Not Belong Here

- Deciding whether to use a worktree, obtaining consent, or creating a branch or worktree.
- Business implementation, code review, commit creation, rebase, integration, or cleanup.
- Clean-baseline or task-completion verification owned by other workflows.
- Agent configuration sync, wrapper generation, or public catalog updates.
- Concrete commands or project facts that are not proven by target repository evidence.
- A self-test that creates another worktree during ordinary use.

## Suggested Generated Content

The generated target skill should:

1. Confirm it is running inside an already-created Git worktree and locate the project working
   directory.
2. Select and invoke the narrowest suitable repository setup script, or invoke the generated
   `scripts/setup.sh` fallback when no suitable repository script exists.
3. Check every command result and report the exact blocker without inventing a degraded path.
4. Stop after the environment is ready; leave baseline tests, implementation, and Git integration
   to their owning workflows.

## Verification Expectations

When `setup-project-agents` creates or materially changes the generated target skill, review the
complete generated `SKILL.md` and every generated script before running the candidate or any actual
acceptance test. Review the script-selection evidence, worktree guard, scope, rerun behavior,
failure propagation, environment lifetime, and task-specific branches. Resolve every review
finding before acceptance; unresolved findings block testing.

After review passes, test the exact candidate in a real temporary worktree before accepting it. If
the candidate or relevant tooling rule is not committed, copy byte-identical content into the
acceptance worktree and verify the copy before invocation.

Acceptance must prove that dependency setup, required generated files, services, and the real
project configuration for each linter, checker, and formatter work. A version command alone is not
functional verification. Use non-writing formatter modes such as `--check` or `--dry-run`; use the
smallest reliable project check, or the repository's full read-only check when no focused mode
exists.

Do not repeat this acceptance during ordinary use. Ordinary use runs the documented environment
commands, checks their exit status, reports failures, and stops when the existing worktree is ready.
