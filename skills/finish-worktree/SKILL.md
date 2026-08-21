---
name: finish-worktree
description: Finalize a standalone Task Worktree, stage one ticket into a Batch Worktree, or deliver a reviewed Ticket Batch through a closed Git contract with verified history, recovery, and cleanup.
---

# Finish Worktree

This Procedure-led Skill finalizes one qualified worktree lifecycle while preserving checkpoint
recovery and unrelated local state. It validates evidence, consolidates authorized history,
executes one Git protocol, verifies its result, and performs owned cleanup. Callers retain
implementation, formal review, Ticket dependencies, tracker state, and Issue completion.

## Route Explicit Discard

Only after a separate explicit destructive instruction, read and execute
[`references/discard.md`](references/discard.md) without accepting a Finalization Contract or
consolidating history. Do not enter a mode path.

## Establish Completion Context

Read and apply [`references/finalization-contract.md`](references/finalization-contract.md).
Continue only when the common contract and current-state proof pass.

## Run One Mode

Read and execute only the reference selected by `mode`:

| Mode | Read completely |
| --- | --- |
| `standalone-task` | [`references/standalone-task.md`](references/standalone-task.md) |
| `stage-ticket-into-batch` | [`references/stage-ticket-into-batch.md`](references/stage-ticket-into-batch.md) |
| `deliver-ticket-batch` | [`references/deliver-ticket-batch.md`](references/deliver-ticket-batch.md) |

## Safety and Recovery

- Create recovery data before rewriting history or changing target working state. Restore only
  state owned by the failed mutation; preserve every state item whose ownership is unproven.
- Use no pull, stash, hard reset, clean, force push, rebase, or merge commit on a base or batch
  branch. Rewrite only unpublished checkpoints and preserve staged per-ticket Task Commits.
- Delegate host-created worktree cleanup to its host; remove a Git-created worktree or branch only
  with proven creation ownership and contract authority.

## Result

Return `status` (`complete`, `stopped`, or `failed`), `mode`, source and target identities before
and after, evidence and verification for the final tree, retained/transferred/deleted recovery refs,
retained/removed worktrees and branches, `next_owner`, and exact next action. A non-complete result
also includes the failed phase, mismatch or error, and preserved recovery state. The selected mode
reference supplies its history and handoff fields.
