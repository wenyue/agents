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
generated-file ownership as evidence. Do not copy commands from this contract or from a deleted
`project-development-workflow`.

## What Belongs Here

- Instructions for generating the target-owned environment setup skill.
- Dependency installation or restoration required inside an already-created Git worktree.
- Project-specific setup for linters, checkers, formatters, compilers, and generators.
- Proto and other generated files required for imports, runtime startup, or test collection.
- Required environment variables, local data, services, and command working directories.
- Failure reporting for missing dependencies, credentials, services, or generated assets.

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
2. Run the repository-supported dependency, generated-file, and required-service setup commands.
3. Check every command result and report the exact blocker without inventing a degraded path.
4. Stop after the environment is ready; leave baseline tests, implementation, and Git integration
   to their owning workflows.

## Verification Expectations

When `setup-project-agents` creates or materially changes the generated target skill, it must test
the exact candidate in a real temporary worktree before accepting it. If the candidate or relevant
tooling rule is not committed, copy byte-identical content into the acceptance worktree and verify
the copy before invocation.

Acceptance must prove that dependency setup, required generated files, services, and the real
project configuration for each linter, checker, and formatter work. A version command alone is not
functional verification. Use non-writing formatter modes such as `--check` or `--dry-run`; use the
smallest reliable project check, or the repository's full read-only check when no focused mode
exists.

Do not repeat this acceptance during ordinary use. Ordinary use runs the documented environment
commands, checks their exit status, reports failures, and stops when the existing worktree is ready.
