# Review ticket batches once while retaining per-ticket Task Commits

For a dependency-ordered Ticket Batch, SmartKit stages one Task Commit per ticket on an isolated
Batch Worktree. The `implement-tickets` controller then performs one formal `code-review` over the
complete Spec and frozen ticket set before giving the reviewed range to `finish-worktree` for local
delivery. This places the review seam at the behavior users will receive while retaining per-ticket
history, instead of paying for substantially overlapping review subagents before and during every
ticket finalization or hiding review inside the delivery transaction.

## Consequences

The delivery target must remain at the batch's recorded base commit; target movement stops the batch
rather than rebasing or introducing a merge commit. Staged tickets remain claimed until batch review
and delivery succeed. Review fixes are consolidated into one optional Batch Review Commit after the
per-ticket Task Commits, so the original ticket history is preserved without rewriting reviewed or
downstream commits.
