# Consolidate task-worktree checkpoints into one delivery commit

SmartKit permits an Agent to create recoverable Checkpoint Commits only in a Task Worktree whose
isolation and task ownership were proven by `create-worktree`; other checkouts still require
separate commit authorization. After implementation and review fixes, `finish-worktree` first
synchronizes the delivery target, resolves only evidence-determined conflicts, and repeats
verification and review before consolidating the entire unpublished checkpoint history into one
hook-validated Task Commit with an identical tree. This deliberately separates recoverable internal
history from concise delivery history without force-rewriting published review commits. When the
selected target is proven to contain the complete accepted task result, the lifecycle instead ends
as Already Delivered and creates no empty Task Commit.

## Consequences

Checkpoint Commits may include clearly marked work-in-progress recovery points but never bypass
commit hooks. Consolidation retains explicit recovery refs until the selected finish outcome is
verified. Pull-request fixes published after the initial Task Commit remain visible review history;
the repository's pull-request policy owns any final platform squash. An empty diff alone cannot
establish Already Delivered; current ancestry or equivalent-change evidence and the task's required
verification must prove the accepted result on the selected target.
