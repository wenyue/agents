# Review ticket batches once while retaining per-ticket Task Commits

For a dependency-ordered Ticket Batch, SmartKit stages one Task Commit per ticket on an isolated
Batch Worktree. One fresh worker owns each ticket's Task Worktree lifecycle: it invokes
`create-worktree`, implements and self-reviews the ticket, then invokes `finish-worktree` to stage
the resulting Task Commit. The `implement-tickets` controller retains the frozen dependency graph,
performs one formal `code-review` over the complete Spec and frozen ticket set, and invokes
`finish-worktree` to deliver the reviewed range. A closed finalization mode tells the finalizer
which Git protocol to enforce without exposing tracker claims, dependency ordering, or Issue
completion. This places the review seam at the behavior users will receive while retaining
per-ticket history and keeps orchestration outside the Git finalizer.

## Consequences

The delivery target must remain at the batch's recorded base commit; target movement stops the batch
rather than rebasing or introducing a merge commit. Staged tickets remain claimed until batch review
and delivery succeed. Only the controller completes tracker transitions after delivery proof.
Review fixes are consolidated into one optional Batch Review Commit after the per-ticket Task
Commits, so the original ticket history is preserved without rewriting reviewed or downstream
commits.
