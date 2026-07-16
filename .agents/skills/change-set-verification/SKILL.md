---
name: change-set-verification
description: Use after completing a coherent change set in this repository, before handoff, to run the declared public-agent contract tests and diff-integrity check while preserving unrelated work.
---

# Change-Set Verification

Verify one completed repository change set with the two declared non-fixing checks. Report
diagnostics to the parent implementation agent; do not implement repairs or manage worktrees.

## Preconditions

- Run only at a completed implementation checkpoint, not during active editing, debugging, or an
  incomplete repair cycle.
- Work from the repository root with Python 3.11 or newer.
- Read the task context and inspect the current Git state before running checks. Distinguish the
  intended change set from unrelated staged, unstaged, and untracked user work.
- Preserve the existing `HEAD`, index, working tree, and unrelated files.
- Do not run a formatter, automatic fixer, analyzer, linter, generator, build, service, dependency
  installer, or sync command. This repository declares none as part of change-set verification.

## Workflow

1. Record the initial Git status and the files belonging to the completed change set.
2. Run the repository contract suite exactly once:

   ```bash
   python -m unittest discover -s tests -p 'test_*.py'
   ```

3. Run the diff-integrity check exactly once:

   ```bash
   git diff --check
   ```

4. Inspect Git status again. Account for any difference from the initial state.
5. Classify both verification surfaces and return all actionable diagnostics to the parent
   implementation agent.
6. If the parent agent changes files in response, treat the result as a new completed checkpoint and
   restart this workflow.

The contract suite is repository-wide and has no declared narrower selector. Do not replace it with
individual test methods or inferred file-to-test mappings.

## Stop Conditions

- If the repository root, Python 3.11 runtime, test script, or Git worktree is unavailable, stop and
  classify the affected surface as `inconclusive`.
- If a verification command unexpectedly changes repository state, stop, report every observed
  change, and classify the overall result as `inconclusive`. Do not revert or clean the changes.
- Do not edit code, Markdown, manifests, mirrors, scripts, generated assets, or unrelated dirty work
  in response to a diagnostic.
- Do not invoke the mutating public sync workflow to repair a verification failure.
- When a failure may predate the selected change and no trustworthy comparison is already
  available, report the attribution gap instead of manipulating Git state to create a baseline.

## Result Classification

Classify each command as:

- `passed`: the command completed successfully.
- `failed`: the command completed and reported a verification failure.
- `inconclusive`: the command could not produce a trustworthy result because of a missing
  prerequisite, interruption, unexpected mutation, or unresolved attribution.
- `not applicable`: current evidence explicitly proves the surface does not apply. Both declared
  commands normally apply to every completed repository change set.

Return one overall result:

- `passed`: both required commands passed and repository state remained accounted for.
- `semantic_fix_required`: a completed check reported actionable implementation or contract
  diagnostics that must return to the parent agent.
- `failed`: a required check reported a non-semantic integrity failure, including
  `git diff --check` diagnostics.
- `inconclusive`: any required surface is inconclusive or repository-state preservation cannot be
  confirmed.

Never report `passed` while a required surface failed, remains inconclusive, or was skipped.

## Validation Report

Report:

- the completed change-set scope;
- each exact command and why it was selected;
- each command's classification and concise diagnostics;
- initial and final Git-state comparison;
- any remaining diagnostic, attribution gap, or prerequisite gap; and
- the overall result.

The verifier must finish without intentional file changes. Any semantic repair belongs to the
parent implementation agent.
