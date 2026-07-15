---
name: change-set-verification
description: Use when defining or generating a target repository's verification skill for a coherent completed change set.
---

# Change-Set Verification

Generate a target-owned skill that normalizes and verifies one coherent completed change set before
handoff. Derive it from current repository evidence rather than a generic command checklist.

## Authoring Workflow

1. Read `.agents/rules/20-project-tools.md`, package manifests, test layout, generated-file
   ownership, CI configuration, repository-owned selectors, and dependency-boundary evidence.
2. Identify the change categories, minimum supported formatter and static-analysis scopes, directly
   owned tests, project-approved automatic fixers, special verification surfaces, and risks that
   require broader or full verification.
3. Generate `SKILL.md`. Add `references/verification-matrix.md` only for a multi-language or
   multi-package repository, or when change-to-check mappings would otherwise obscure the core
   workflow.
4. Prefer an existing repository-owned selector. Generate a skill-owned script only when current
   evidence proves deterministic repeated logic cannot be expressed reliably with existing tools.
5. Keep commands, paths, scope support, mutation behavior, prerequisites, and cost characteristics
   consistent with `.agents/rules/20-project-tools.md`.

## Generation Contract

- Trigger when a coherent completed change set is ready for handoff. Skip active implementation,
  debugging, and iterative edits; after later edits, verify again at the next completed checkpoint.
- Resolve the change set's production code, tests, configuration, generated-output owners, and
  supporting files from task context and repository state. Select the minimum sufficient scope from
  project evidence instead of defaulting to whole-project checks.
- Use direct test ownership, dependency relationships, project mappings, and available repository
  selectors. Run each unique verification surface once per completed checkpoint.
- Start narrowly. Broaden to a subsystem or full verification only when tool scope limitations,
  dependency impact, test infrastructure, shared contracts, generated interfaces, fixer mutations,
  or unknown impact prevent a reliable smaller scope.
- Do not treat an absent test mapping as proof that tests are unnecessary. Report the gap or broaden
  scope when behavior changed and ownership cannot be resolved.
- Preserve unrelated user changes and never hand-edit generated outputs or third-party code. Do not
  expand the selected scope solely to clean up pre-existing diagnostics elsewhere.
- Classify every selected surface as `passed`, `failed`, `inconclusive`, or `not applicable`.
  Report its command, scope, selection reason, result, and any remaining gap. Do not claim overall
  success while a required surface failed or remains inconclusive.
- If a failure outside the selected scope may predate the change, rerun only that failing surface
  and compare the same surface against a trustworthy baseline when needed. Never run a baseline
  full suite solely to classify one suspected pre-existing failure.

## Normalization And Mechanical Repair

1. Run the project formatter on the selected project-owned source scope when one exists.
2. Run each project-approved automatic fixer at most once on its minimum supported selected scope.
   Analyzer and linter diagnostics may share one tool surface; do not run duplicate checks or fixes.
3. Accept mechanical repairs for every diagnostic discovered inside the selected scope, regardless
   of whether the current change introduced it. Do not widen the scope only to find or repair older
   violations.
4. Add every formatter- or fixer-modified file to the verification scope. Stop and report when a
   tool changes generated, third-party, or otherwise non-owned files.
5. Reformat every fixer-modified source file, then run the minimum supported non-mutating static
   analysis scope.
6. Return remaining semantic diagnostics to the parent implementation agent with exact locations
   and messages. The verifier must not author semantic repairs. After the parent edits code, restart
   this workflow from normalization at the next completed checkpoint.
7. Run directly owned unit tests after static checks pass. Include tests for every component added
   to the scope by formatter, fixer, or parent-agent changes, and broaden when the accumulated impact
   makes a narrower test selection unreliable.
8. Report every modified file, formatter and fixer invocation, repeated check, remaining diagnostic,
   and verification gap.

## Verifier Result

The generated skill must return one overall result:

- `passed`: every required selected surface passed after mechanical repair.
- `semantic_fix_required`: static analysis found diagnostics that require parent-agent judgment.
- `failed`: a required check or test failed without a valid pre-existing-failure classification.
- `inconclusive`: prerequisites, ownership ambiguity, or unavailable evidence prevented a reliable
  result.

## Conditional Script Requirements

Generate an executable script only when current evidence shows that deterministic repeated logic
cannot be expressed reliably with repository-owned tools. If the generated skill includes
executable scripts, require its own `## Failure Recovery` section to instruct the agent to stop
immediately, report the exact command and error, analyze the cause, and propose a concrete candidate
change. Do not continue verification, hide the failure, or retry modified code before the proposal
is reviewed.

## Handoff

Give `setup-project-agents` the complete generated directory and supporting evidence. That workflow
owns candidate review and acceptance.
