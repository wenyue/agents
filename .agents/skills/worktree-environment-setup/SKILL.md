---
name: worktree-environment-setup
description: Use when defining or generating a target repository's environment setup skill for an already-created Git worktree.
---

# Worktree Environment Setup

Generate a target-owned skill that prepares an already-created linked Git worktree from current
repository evidence.

## Authoring Workflow

1. Read `.agents/rules/20-project-tools.md`, manifests, lock files, setup scripts, CI configuration,
   and generated-file ownership.
2. Derive the minimum preparation required for dependencies, generated files, local services, and
   project tooling to work inside a new linked worktree.
3. Generate `SKILL.md`, `scripts/setup.sh`, and `scripts/setup.ps1` together. Keep executable command
   sequences in the scripts and keep `SKILL.md` focused on when and how to invoke them.
4. Reuse narrow repository-owned setup entry points. Add only preparation that current evidence
   shows is missing.
5. Document prerequisites, platform selection, optional branches, readiness checks, and failure
   reporting without duplicating the scripts.

## Generation Contract

- Require execution inside an already-created linked worktree and reject the primary checkout before
  mutation.
- Use `scripts/setup.ps1` on Windows and `scripts/setup.sh` on non-Windows hosts. Require the same
  core environment result without requiring the other platform's shell.
- Resolve paths from the skill or repository root, stop on command failure, and make reruns safe
  after partial setup.
- Keep expensive or task-specific preparation optional unless evidence proves that every worktree
  needs it.
- Stop at environment readiness. Exclude worktree lifecycle, baseline verification, business
  changes, commits, integration, and agent synchronization.
- Hand completed-change verification to `change-set-verification`. Do not own verification trigger
  timing, scope selection, or result policy.

## Failure Recovery

Require the generated `SKILL.md` to include its own `## Failure Recovery` because both setup entry
points are executable scripts. If either script fails, instruct the agent to stop immediately,
report the exact command and error, analyze the cause, and propose a concrete candidate change.
Do not continue setup, hide the failure, or retry a modified script before the proposal is reviewed.

## Handoff

Give `setup-project-agents` the complete generated directory and supporting evidence. That workflow
owns candidate review and acceptance.
