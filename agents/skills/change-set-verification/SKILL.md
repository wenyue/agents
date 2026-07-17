---
name: change-set-verification
description: Use when creating or revising a target repository's skill for normalizing and verifying a coherent completed change set before handoff.
---

# Change-Set Verification

Author a complete target-owned skill that normalizes and verifies one coherent completed change set
before handoff. This generation contract defines the verifier; it does not verify the current
change set or implement semantic repairs.

## Evidence

Inspect the target repository's `Project Tools` rule, broader and more-specific rules, tool
configuration, manifests, package boundaries, test layout, CI workflows, generated-source policy,
and repository-owned verification selectors. Establish:

- formatter, fixer, analyzer, linter, test, build, runtime, and diff-integrity surfaces actually
  supported by the repository;
- the working directory, prerequisites, scope selectors, mutation behavior, output, relative cost,
  and overlap of every candidate command;
- direct test ownership, generated-source owners, dependency boundaries, and evidence-backed
  change-to-check mappings;
- risks and tool limitations that require broader verification, plus any trustworthy way to
  distinguish a selected failure from the target baseline; and
- files and diagnostics the verifier may repair mechanically versus semantic work that must return
  to the implementation owner.

Do not invent commands, ownership mappings, or scope support that the evidence does not prove.

## Authoring Workflow

1. Define the generated skill's trigger, completed-checkpoint precondition, selected-change-set
   model, completion conditions, result states, stop conditions, and excluded implementation work.
2. Map each supported change class to the minimum sufficient repository-owned checks. Define
   broadening conditions from dependencies, shared contracts, generated interfaces, tool mutation,
   ownership gaps, and risk.
3. Order normalization, non-mutating static checks, directly owned tests, broader checks, and result
   classification so each distinct surface runs only when its evidence is still needed.
4. Prefer repository-owned selectors. Add a skill-owned script only when repeated deterministic
   selection cannot be expressed reliably through existing tools; follow the target skill's own
   project-local script runtime policy.
5. Keep the core decisions in `SKILL.md`. Add `references/verification-matrix.md` only when multiple
   packages, languages, or risk mappings would otherwise obscure the executable workflow.
6. Read the complete generated directory without relying on the previous target skill or its diff,
   then revise it until every instruction, command, scope decision, and result has one clear meaning.

## Generated Skill Contract

### Trigger and Scope

- Run at a completed implementation checkpoint, before handoff. Do not interrupt active editing,
  debugging, or an incomplete fix cycle.
- Identify the coherent intended change set from task context and repository state. Preserve the
  existing `HEAD`, index, unrelated staged or unstaged work, and untracked files.
- Resolve production code, tests, configuration, generated-source owners, and supporting files that
  belong to that change set.
- Start with the minimum sufficient scope. Broaden only when dependencies, shared contracts,
  generated interfaces, fixer mutations, tool limitations, or unknown ownership make the narrower
  result unreliable.
- Treat missing test ownership as a gap to resolve or a reason to broaden, never as proof that tests
  are unnecessary.
- Never edit generated output, third-party code, or files outside the selected project-owned scope.

### Normalization and Repair

1. When the project supports it, format the selected project-owned source scope.
2. Run each approved automatic fixer at most once on its minimum supported selected scope. Do not
   duplicate analyzer or lint work when one tool already owns the same surface. Accept mechanical
   repairs within that selected scope, but do not broaden solely to discover or repair older issues.
3. Add every formatter- or fixer-modified file to the selected change set. Stop if a tool changes
   generated, third-party, unrelated, or otherwise non-owned files.
4. Reformat fixer-modified source when required, then run the minimum supported non-mutating static
   checks.
5. Return remaining semantic diagnostics to the implementation owner with exact locations and
   messages. Do not author semantic fixes inside the verifier.
6. If the implementation owner changes files, treat the result as a new completed checkpoint and
   restart the workflow from current repository state.

### Verification and Results

- Run directly owned tests after static checks pass. Include tests for components added to scope by
  formatter, fixer, or implementation-owner changes.
- Run broader tests, builds, runtime checks, or integration surfaces only when the evidence-defined
  risk or ownership boundary requires them.
- Run each unique verification surface once per completed checkpoint unless a mutation requires a
  documented repeat.
- Classify every selected surface as `passed`, `failed`, `inconclusive`, or `not applicable`.
  Report the command, scope, selection reason, result, and remaining gap.
- Report every modified file, formatter and fixer invocation, repeated check, remaining diagnostic,
  and verification gap.
- Return one overall result: `passed`, `semantic_fix_required`, `failed`, or `inconclusive`.
- Do not report `passed` while any required surface failed or remains inconclusive.
- When an out-of-scope failure may predate the change, compare only that failing surface with a
  trustworthy baseline. Do not run a full baseline suite solely for classification.

### Stop and Failure Behavior

- Stop when prerequisites are missing, selected ownership cannot be resolved safely, an automatic
  tool changes forbidden scope, repository state cannot be accounted for, or a required result is
  not trustworthy. Preserve the evidence and report the affected surface as `inconclusive` or
  `failed` as appropriate.
- A generated skill with executable scripts must include `## Failure Recovery`: report the exact
  failed command and error, analyze the cause, and propose a complete candidate script change before
  modifying or retrying it.
- Exclude business implementation, semantic repair, worktree creation or integration, dependency
  installation, agent synchronization, and destructive cleanup unless the target repository
  explicitly makes one of them part of a selected verification surface.

## Review Gate

Review the complete generated directory before executing it. Confirm every command, scope mapping,
mutation, deduplication rule, broadening condition, result state, baseline rule, and handoff against
target evidence. Verify that repository rules remain the policy source, optional resources are
necessary and reachable, and the verifier owns neither semantic implementation nor worktree
lifecycle. Any unsupported or ambiguous mapping fails review.

## Acceptance Gate

After review passes, exercise the complete generated skill on a representative coherent change set
in the target repository. Invoke the actual candidate through normal completion and verify selected
scope, normalization behavior, directly owned checks, broadening when applicable, per-surface
classification, overall result, and preservation of unrelated repository state.

Also exercise a safe relevant stop or failure path, such as a remaining semantic diagnostic,
missing prerequisite, forbidden mutation, or inconclusive ownership. Record exact commands,
candidate-caused file changes, initial and final repository state, diagnostics, classifications,
and anything not run. If acceptance cannot safely exercise the candidate or cannot account for its
mutations, it fails.

## Handoff

Only after both gates pass, give `setup-project-agents` the complete accepted directory, supporting
repository evidence, review decision, acceptance evidence, and unresolved or not-run surfaces. If
either gate fails, stop and report the blocker instead of handing off the candidate as accepted.
