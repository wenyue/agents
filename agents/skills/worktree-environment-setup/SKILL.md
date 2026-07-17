---
name: worktree-environment-setup
description: Use when creating or revising a target repository's environment setup skill for an already-created linked Git worktree.
---

# Worktree Environment Setup

Generate a target-owned skill that prepares an already-created linked Git worktree and stops when
the project environment is ready for implementation.

## Evidence

Read the target repository's `Project Tools` rule, manifests, lock files, setup scripts, CI
workflows, generated-file ownership, required local services, and readiness checks. Identify the
minimum repeatable preparation required on Windows and non-Windows hosts.

## Authoring Workflow

1. Establish how the generated skill detects a linked worktree and rejects the primary checkout
   before mutation.
2. Reuse the narrowest repository-owned setup entry points and add only preparation that current
   evidence shows is missing.
3. Generate `SKILL.md`, `scripts/setup.ps1`, and `scripts/setup.sh` together. Put executable command
   sequences in the scripts; keep invocation, prerequisites, optional branches, and readiness in
   `SKILL.md`.
4. Make both scripts stop on command failure and safe to rerun after partial setup.
5. Review the complete directory against the contract below.

## Generated Skill Contract

- Require execution inside an already-created linked worktree. Refuse the primary checkout before
  any dependency install, generation, service change, or other mutation.
- Use `scripts/setup.ps1` on Windows and `scripts/setup.sh` on non-Windows hosts. Require the same
  core environment result while allowing evidence-backed platform differences.
- Resolve paths from the skill or repository root; never depend on the caller's current directory.
- Keep expensive, optional, or task-specific preparation out of the default path unless every new
  worktree requires it.
- Verify readiness using real project configuration and required tool or service behavior, not only
  version probes.
- Stop at environment readiness. Exclude worktree creation or removal, baseline verification,
  business changes, commits, integration, and agent synchronization.
- Hand completed-change verification to `change-set-verification`.
- Do not own verification trigger timing, scope selection, or result policy.

## Failure Recovery

Require the generated `SKILL.md` to include its own `## Failure Recovery`. If either host script
fails, stop immediately, report the exact command and error, analyze the cause, and propose a
concrete script or environment change. Do not continue setup or retry a modified script before the
candidate change is reviewed.

## Review and Handoff

Confirm that the scripts are internally consistent, host-selective, rerunnable, and limited to
environment preparation. Give `setup-project-agents` the complete generated directory and
supporting evidence for candidate review and acceptance.
