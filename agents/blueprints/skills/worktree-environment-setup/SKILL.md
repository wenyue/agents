---
name: worktree-environment-setup
description: Use when creating or revising a target repository's environment setup skill for an already-created linked Git worktree.
---

# Worktree Environment Setup

Author a complete target-owned skill that prepares an already-created linked Git worktree and stops
when the repository is ready for implementation. This generation contract does not perform setup or
own the worktree lifecycle.

## Evidence

Inspect the target repository's `Project Tools` rule, manifests, lock files, toolchain pins, setup
and generation entry points, CI workflows, generated-source policy, required assets, environment
variables, credentials, local services, and readiness checks. Establish:

- how to identify the repository root, its common Git directory, and an already-created linked
  worktree before any mutation;
- the minimum preparation every new worktree requires, plus optional task-specific branches;
- the narrowest repository-owned commands that install locked dependencies, initialize required
  inputs, generate required outputs, or start required services;
- the supported host platforms, script runtime already established by the project, rerun behavior,
  failure behavior, and observable readiness result; and
- responsibilities owned by worktree creation, machine provisioning, baseline verification,
  implementation, synchronization, integration, or cleanup instead of environment setup.

Do not invent a cross-platform promise, command, prerequisite, or readiness check that target
evidence does not support.

## Authoring Workflow

1. Define the generated skill's trigger, prerequisites, ready state, stop conditions, and excluded
   lifecycle responsibilities from the evidence above.
2. Reuse the narrowest repository-owned setup entry point. Add a skill-owned script only when the
   target lacks a reliable owner for repeated deterministic orchestration.
3. If a skill-owned script is required, choose either the target project's established language and
   runtime or paired `scripts/setup.ps1` and `scripts/setup.sh` entry points. For paired entry points,
   require the same supported outcome while allowing verified host differences.
4. Keep deterministic command sequences in scripts and keep invocation, prerequisites, optional
   branches, readiness, failure recovery, and result reporting in `SKILL.md`.
5. Read the complete generated directory without relying on the old target skill or its diff, then
   revise it until every instruction and resource has one clear owner and execution meaning.

## Generated Skill Contract

- Discovery metadata must trigger only for preparing an already-created linked worktree in the
  target repository. The body must state the environment result and the point at which setup ends.
- Detect and reject the primary checkout before installing dependencies, generating files,
  changing services, or performing any other setup mutation. Resolve paths from the discovered
  repository or skill root, never from the caller's current directory.
- Execute only evidence-backed, locked, and repository-owned preparation. Keep expensive, optional,
  platform-specific, or task-specific branches out of the default path unless every new worktree
  requires them.
- Make every owned command sequence stop on failure and safe to rerun after partial completion.
  Do not silently substitute an unverified command or degraded result.
- Verify readiness through real project configuration, required outputs, and tool or service
  behavior. Version probes alone are insufficient when functional readiness can be checked.
- Include `## Failure Recovery`. Report the failed step, exact command or condition, exit status
  when available, relevant output, and smallest corrective action. Review any candidate script
  change before retrying it.
- Report the linked worktree root, completed preparation, selected optional branches, verified ready
  state, and any task-relevant preparation intentionally left to another owner.
- Stop at environment readiness. Exclude worktree selection or creation, machine provisioning,
  baseline or completed-change verification, business implementation, Git history, integration,
  cleanup, and agent synchronization. Hand later completed-change verification to
  `change-set-verification`.

## Review Gate

Review the complete generated directory before execution. Confirm every command, prerequisite,
mutation, platform claim, optional branch, readiness check, and boundary against target evidence.
Review skill-owned scripts for deterministic ordering, path resolution, failure propagation,
rerun safety, and consistency with `SKILL.md`. A stale or unsupported instruction fails review.

## Acceptance Gate

After review passes, exercise the complete generated skill in a representative already-created
linked worktree for the target repository. Invoke the actual candidate, prove that the primary
checkout guard runs before mutation, complete the default preparation path, and verify the declared
ready state. Exercise an optional branch only when the target contract declares it part of the
accepted capability.

Validate a project-matched script with the project's established runtime. For paired entry points,
run only the current host's entry point and do not claim the other host was executed. Record exact
commands, observed mutations, readiness evidence, stop-path evidence, and anything not run. Any
unexpected mutation, unsupported prerequisite, or unverified ready state fails acceptance.

## Handoff

Only after both gates pass, give `setup-project-agents` the complete accepted directory, supporting
repository evidence, review decision, acceptance evidence, and unresolved or not-run platform and
optional branches. If either gate fails, stop and report the blocker instead of handing off the
candidate as accepted.
