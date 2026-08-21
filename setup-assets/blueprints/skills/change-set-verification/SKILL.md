---
name: change-set-verification
description: Use when creating or revising a target repository's skill for normalizing and verifying a coherent completed change set before handoff.
---

# Change-Set Verification

Author a complete target-owned skill that normalizes and verifies one coherent completed change set
before handoff. This generation contract defines the verifier; it does not verify the current
change set or implement semantic repairs.

## Evidence

Inspect the target repository's `Project Tools` rule, broader and more-specific rules, effective
callable tool surface, tool configuration, manifests, package boundaries, test layout, CI
workflows, generated-source policy, and repository-owned verification selectors. Establish:

- formatter, fixer, analyzer, linter, test, build, runtime, and diff-integrity surfaces actually
  supported by the repository;
- the working directory, prerequisites, scope selectors, mutation behavior, output, relative cost,
  and overlap of every candidate command;
- whether a native or MCP tool preserves the required selector and evidence, whether independent
  calls can be submitted together, and which owning timeout applies to long-running calls;
- direct test ownership, generated-source owners, dependency boundaries, and evidence-backed
  change-to-check mappings;
- risks and tool limitations that require broader verification, plus any trustworthy way to
  distinguish a selected failure from the target baseline; and
- files and diagnostics the verifier may repair mechanically versus semantic work that must return
  to the implementation owner.

Require evidence for every command, ownership mapping, and supported scope.

## Generation Frame

The generated artifact is a Hybrid Skill. Its Judgment Frame selects the coherent change set,
minimum sufficient checks, broadening conditions, and effective tools from current repository
evidence. Its bounded verification procedure owns only the order that affects mutation safety and
the trustworthiness of later evidence.

Keep these decisions in `SKILL.md`. Add `references/verification-matrix.md` only when multiple
packages, languages, or risk mappings would otherwise obscure the usable mapping. Add a script only
when repeated deterministic selection cannot be expressed reliably through repository-owned tools;
follow the target skill's project-local script runtime policy.

Choose the generated skill's organization from the target evidence. Do not copy this contract's
headings or evidence order as its outline.

## Target Obligations

### Judgment Frame

- Run only at a completed implementation checkpoint before handoff; active editing, debugging, and
  incomplete fix cycles continue until the next completed checkpoint.
- Identify the coherent intended change set from task context and repository state. Preserve the
  existing `HEAD`, index, unrelated staged or unstaged work, and untracked files.
- Resolve production code, tests, configuration, generated-source owners, and supporting files that
  belong to that change set.
- Start with the minimum sufficient scope. Broaden only when dependencies, shared contracts,
  generated interfaces, fixer mutations, tool limitations, or unknown ownership make the narrower
  result unreliable.
- Treat missing test ownership as a gap to resolve or a reason to broaden.
- Restrict mutation to selected project-owned source files; change generated output through its
  owner and leave third-party or out-of-scope files unchanged.
- Choose repository commands or effective native or MCP tools according to selected-scope fidelity,
  diagnostic quality, mutation boundaries, and configured timeout. Keep repository formatter and
  fixer commands when a callable tool would broaden mutation or discard a required selector.
- Group independent checks when the Harness supports it. Keep mutation-sensitive checks and checks
  that consume generated output sequential.

### Verification Procedure

1. When the project supports it, format the selected project-owned source scope.
2. Run an approved automatic fixer only for a known fixable analyzer or lint diagnostic, a
   framework or API migration, or user-requested mechanical cleanup. Run it at most once on its
   minimum supported selected scope. Accept mechanical repairs within that selected scope, but do
   not broaden solely to discover or repair older issues.
3. Add every formatter- or fixer-modified file to the selected change set.
4. Reformat fixer-modified source when required, then run the minimum supported non-mutating static
   checks.
5. Return remaining semantic diagnostics to the implementation owner with exact locations and
   messages; semantic fixes remain with that owner.
6. If the implementation owner changes files, treat the result as a new completed checkpoint and
   restart the workflow from current repository state.
7. Run directly owned tests after static checks pass, including components added by formatter,
   fixer, or implementation-owner changes.
8. Run broader tests, builds, runtime checks, or integration surfaces only when evidence-defined
   risk or ownership requires them. Run each unique surface once per completed checkpoint unless a
   mutation requires a documented repeat.

### Results

- Classify every selected surface as `passed`, `failed`, `inconclusive`, or `not applicable`.
  Report the command, scope, selection reason, result, and remaining gap.
- Report every modified file, formatter and fixer invocation, repeated check, remaining diagnostic,
  and verification gap.
- Return one overall result: `passed`, `semantic_fix_required`, `failed`, or `inconclusive`.
- Return `passed` only when every required surface passed; `semantic_fix_required` only when
  trustworthy completed checks leave a semantic diagnostic and no safety or evidence-trust stop
  applies; `failed` for a trustworthy required-check failure or confirmed forbidden mutation; and
  `inconclusive` when prerequisites, ownership, repository state, or required evidence cannot be
  established reliably.
- A mutation-safety or evidence-trust stop governs over diagnostic routing when conditions
  coincide.
- When an out-of-scope failure may predate the change, compare only that failing surface with a
  trustworthy baseline, using no broader baseline work than classification requires.

### Stop and Failure Behavior

- Stop when prerequisites are missing, selected ownership cannot be resolved safely, an automatic
  tool changes forbidden scope, repository state cannot be accounted for, or a required result is
  not trustworthy. Preserve the evidence and apply the observable result conditions above.
- For executable-script failures, report the exact failed command and error, analyze the cause, and
  propose a complete candidate script change before modifying or retrying it.
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
