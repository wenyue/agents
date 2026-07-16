---
name: worktree-integrate
description: Use when verified implementation in a named linked Git worktree must return to the current checkout for manual review or an explicitly requested local commit.
---

# Worktree Integrate

Return verified task work without losing local changes. Use review mode by default; use commit mode
only when the user explicitly requests a committed local integration.

## Mode Selection

- **Review mode:** Materialize the task result as unstaged or untracked work while preserving the
  base HEAD, index, and unrelated local changes.
- **Commit mode:** Fast-forward the base branch only after an explicit request and only when task
  paths do not overlap base-local changes.

Never turn an ambiguous request into commit mode.

## Task Branch Preparation

1. Require a linked, named task branch and a non-detached HEAD.
2. Confirm task verification passed. Classify staged, unstaged, and untracked task-worktree changes;
   include confirmed task-owned work and stop on ambiguous ownership.
3. Discover the base checkout and branch with `git worktree list --porcelain` and the Git common
   directory. Do not assume `main` or `master`; stop when the intended base is ambiguous.
4. Consolidate task work relative to its merge base into exactly one business commit.
5. Rebase that commit onto the current base HEAD. Auto-resolve only task-scoped, unambiguous,
   verifiable conflicts; otherwise abort the rebase and ask for direction.
6. Require a clean task worktree and rerun affected checks when consolidation or rebase changed
   content.

## Base Snapshot and Recovery Data

1. Record the base branch, HEAD, index tree, staged changes, unstaged changes, and untracked files.
2. Compute the final task paths and back them up outside the repository. Record file types and paths
   that were originally absent in a manifest. Do not stash.
3. Immediately before transfer, compare the base branch and HEAD with the snapshot. If either moved,
   rebase the task commit again and refresh the snapshot, affected paths, and backup.

## Review Mode

1. Keep the base HEAD and index unchanged.
2. For task paths without base-local changes, check the transfer first, then update only the working
   tree. Do not use a checkout, apply, or restore mode that writes the index.
3. For overlapping text paths, three-way merge the task commit parent, current base working file,
   and task result in temporary files. A shared pathname alone is not a conflict.
4. Resolve autonomously only when the result is unambiguous, task-scoped, and verifiable.
5. Stop for delete/modify conflicts, complex renames, binary conflicts, mutually exclusive behavior,
   ambiguous generated output, or any merge that cannot be verified. Regenerate generated files
   from their source when the project provides a deterministic generator.
6. Run only known non-mutating checks in the base checkout. If adequate checks are unavailable,
   report the limitation instead of running a formatter, generator, or fixer.
7. Prove the recorded HEAD and index tree are unchanged, original staged state is preserved, merged
   files contain both local and task work, and returned task changes remain unstaged or untracked.

Keep the task branch, worktree, and external backup after a successful review-mode transfer. Report
their locations so the user can inspect and recover the source independently.

## Commit Mode

1. If any task path has staged, unstaged, or untracked base-local work, report the overlap and use
   review mode instead; explicitly downgrade to review mode when commit mode was requested.
2. Reconfirm the task branch contains one rebased business commit and recheck the base branch and
   HEAD immediately before integration.
3. Run `git merge --ff-only` from the base branch.
4. If fast-forward is refused, stop with the base and its local changes untouched.
5. Re-run relevant verification and prove unrelated base-local state is unchanged.
6. After verification passes, clean up according to creation ownership: delegate platform-created
   worktrees to that platform; remove only a Git-fallback worktree from the base checkout, then
   delete its integrated task branch safely.

## Verification and Recovery

- If transfer or automatic merge fails before a complete result exists, restore only touched paths
  from the external backup.
- If post-transfer verification fails, keep the returned working-tree result, task branch,
  worktree, and backup. Report the exact failed command for manual review.
- Retain recovery data until the user accepts the review result.

## Prohibited Operations

Never push, pull, force-update, stash, reset, clean, or create a merge commit as part of this skill.
For PR, keep-branch, or discard outcomes, hand off to
`superpowers:finishing-a-development-branch`.

## Result

Report the selected mode, task commit, transferred or integrated paths, overlap decisions,
verification, preserved base state, recovery data, and any retained worktree or branch.
