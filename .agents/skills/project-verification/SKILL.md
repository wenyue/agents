---
name: project-verification
description: Use when defining or generating a target repository's verification skill for a coherent completed change set.
---

# Project Verification

Generate a target-owned skill that verifies one coherent completed change set before handoff. Build
it from current target-repository evidence; do not copy a generic command checklist into the target
skill.

## Authoring Workflow

1. Read `.agents/rules/20-project-tools.md`, package manifests, test layout, generated-file
   ownership, CI configuration, repository-owned selectors, and dependency-boundary evidence.
2. Identify the change categories, directly owned tests, special verification surfaces, safe-fix
   tools, and risks that require broader or full verification.
3. Generate `.agents/skills/project-verification/SKILL.md`. Add
   `references/verification-matrix.md` only for a multi-language or multi-package repository, or
   when project-specific change-to-check mappings would otherwise obscure the core workflow.
4. Prefer an existing repository-owned selector. Generate a skill-owned script only when current
   evidence proves deterministic repeated logic cannot be expressed reliably with existing tools.
5. Keep commands, paths, scope support, mutation behavior, prerequisites, and cost characteristics
   consistent with `.agents/rules/20-project-tools.md`.

## Generated Skill Contract

- Trigger when a coherent completed change set is ready for handoff. Skip active implementation,
  debugging, and iterative edits; after later edits, verify again at the next completed checkpoint.
- Resolve task-owned production code, tests, configuration, generated-output owners, and supporting
  files from task context and repository state. Exclude unrelated dirty files; stop and report an
  ambiguity instead of absorbing them.
- Select the minimum sufficient checks from project evidence. Use direct test ownership,
  dependency relationships, project mappings, and available repository selectors; run each unique
  verification surface once per completed checkpoint.
- Start with narrow, inexpensive checks. Broaden to subsystem or full verification when dependency,
  test-infrastructure, shared-contract, generated-interface, or unknown-impact risk prevents a
  reliable smaller scope. A cheap focused preflight may precede an expensive required suite when it
  can avoid wasting that suite's cost.
- Do not treat an absent test mapping as proof that tests are unnecessary. Report the gap or broaden
  scope when behavior changed and ownership cannot be resolved.
- Keep verification non-destructive except for conditional safe fixes below. Never alter unrelated
  files, generated outputs without their owning generator, or user work outside the change set.
- Classify every selected surface as `passed`, `failed`, `inconclusive`, or `not applicable`.
  Report its command, scope, selection reason, result, and any remaining gap. Do not claim overall
  success while a required surface failed or remains inconclusive.
- If a failure appears outside the affected scope and may predate the change, rerun only that
  failing surface and compare the same surface against a trustworthy baseline when needed. Never
  run a baseline full suite solely to classify one suspected pre-existing failure.

## Conditional Safe Fixes

- Run a non-mutating check first. Invoke a path-scoped formatter or safe fix only for an observed,
  in-scope diagnostic and only when project tooling documents that mutation as safe.
- Do not run unsafe fixes, unscoped fixers, behavior-changing rewrites, or unrelated cleanup.
- Snapshot the task-owned file set before fixing and stop if a tool touches anything outside it. Do
  not silently restore or discard unrelated user changes.
- Apply at most one automatic fix pass for a diagnostic class. Repeat the affected format, static,
  and test checks afterward; if the diagnostic remains, return it to the implementation workflow.
- Report every modified file, fixer invocation, and repeated check.

## Handoff

Give `setup-project-agents` the complete generated skill directory and the repository evidence used
to produce its trigger, verification matrix, tool selection, broadening rules, safe fixes, and
failure policy. That workflow owns review and acceptance.
