---
name: change-set-verification
description: Use when creating or revising a target repository's skill for normalizing and verifying a coherent completed change set before handoff.
---

# Change-Set Verification

Generate a target-owned verification skill from current repository evidence. Keep it focused on one
coherent completed change set and the minimum checks needed to hand that change off reliably.

## Evidence

Read the target repository's agent rules, tool configuration, manifests, test layout, CI workflows,
generated-file ownership, dependency boundaries, and repository-owned verification selectors.
Establish:

- supported formatter, fixer, analyzer, linter, and test scopes;
- direct test ownership and change-to-check mappings;
- mutating behavior, prerequisites, relative cost, and safe automatic repair paths;
- risks that require subsystem or full verification.

Do not invent commands, ownership mappings, or scope support that the evidence does not prove.

## Authoring Workflow

1. Classify the change types the generated skill must handle.
2. Select the narrowest repository-supported checks for each class and define evidence-backed
   broadening conditions.
3. Prefer an existing repository selector. Add a skill-owned script only when repeated
   deterministic selection cannot be expressed reliably with repository-owned tools.
4. Generate `SKILL.md`. Add `references/verification-matrix.md` only when multiple packages,
   languages, or risk mappings would otherwise obscure the core workflow.
5. Review the complete generated directory against the contract below.

## Generated Skill Contract

### Trigger and Scope

- Run at a completed implementation checkpoint, before handoff. Do not interrupt active editing,
  debugging, or an incomplete fix cycle.
- Resolve production code, tests, configuration, generated-output owners, and supporting files from
  task context and repository state.
- Start with the minimum sufficient scope. Broaden only when dependencies, shared contracts,
  generated interfaces, fixer mutations, tool limitations, or unknown ownership make the narrower
  result unreliable.
- Treat missing test ownership as a gap to resolve or a reason to broaden, never as proof that tests
  are unnecessary.
- Preserve unrelated user work. Never edit generated output, third-party code, or files outside the
  selected project-owned scope.

### Normalization and Repair

1. Format the selected project-owned source scope when the project provides a formatter.
2. Run each project-approved automatic fixer at most once on its minimum supported selected scope.
   Do not duplicate analyzer and linter work when one tool owns both surfaces.
   Accept mechanical repairs for diagnostics found inside that scope regardless of whether the
   current change introduced them. Do not widen scope only to discover or repair older violations.
3. Add formatter- and fixer-modified files to the change scope. Stop if a tool changes generated,
   third-party, or otherwise non-owned files.
4. Reformat fixer-modified source, then run the minimum supported non-mutating static checks.
5. Return remaining semantic diagnostics to the parent implementation agent with exact locations
   and messages. Do not author semantic fixes inside the verifier.
6. After parent-agent edits, restart normalization at the next completed checkpoint.

### Verification and Results

- Run directly owned tests after static checks pass. Include tests for components added to scope by
  formatter, fixer, or parent-agent changes.
- Run each unique verification surface once per completed checkpoint unless a mutation requires a
  documented repeat.
- Classify every selected surface as `passed`, `failed`, `inconclusive`, or `not applicable`.
  Report the command, scope, selection reason, result, and remaining gap.
- Return one overall result: `passed`, `semantic_fix_required`, `failed`, or `inconclusive`.
- Do not report `passed` while any required surface failed or remains inconclusive.
- When an out-of-scope failure may predate the change, compare only that failing surface with a
  trustworthy baseline. Do not run a full baseline suite solely for classification.

## Optional Resources

Include an executable script only when repository evidence proves it is necessary. A generated
skill with scripts must include `## Failure Recovery`: stop on script failure, report the exact
command and error, analyze the cause, and propose a candidate change before modifying or retrying
the script.

## Review and Handoff

Confirm that the generated skill matches the target tool rule, owns no implementation or worktree
lifecycle behavior, and contains no unsupported command or mapping. Give `setup-project-agents` the
complete generated directory and its supporting evidence for candidate review and acceptance.
