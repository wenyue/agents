# Workspace Policy

Strength: `Mandatory`

Scope: Workspace selection, local Git state, commit authority, and remote action authorization.

## Current Workspace

- Use the current workspace when the user, Harness, and applicable Skills do not require isolation,
  parallel work does not need separate state, and existing checkout state can be preserved in place.
- Preserve all pre-existing staged, unstaged, and untracked work while implementing and reviewing
  the accepted task.
- Choose a non-destructive path when a task operation would overwrite, stash, reset, clean, or
  discard that state; request direction when no such path is available.
- A file containing both pre-existing and task changes is not automatically a blocker. Continue
  when the two can be distinguished and the result is verified to preserve the pre-existing
  changes; otherwise stop and request direction.
- Leave task changes uncommitted unless the user separately authorizes a commit. This requirement
  also governs `implement`; an unqualified linked worktree follows the same boundary.

## Task Worktree

- Apply `create-worktree` when the user requests isolation, the Harness or an applicable Skill
  requires it, parallel work needs separate state, or isolation is needed to protect existing
  checkout state. Let it own linked-worktree selection, readiness, and Task Worktree qualification.
- In a qualified Task Worktree, the implementation workflow may create task-only Checkpoint Commits
  through the repository's normal commit hooks without separate authorization. In a qualified Batch
  Worktree, each ticket worker may append exactly its ticket's Task Commit, and the controller may
  create batch-review Checkpoint Commits through the same hooks.
- When an implementation workflow is ready to consolidate or deliver, apply `finish-worktree`.
  Let the implementation workflow own formal review and let `finish-worktree` verify that its
  evidence matches the exact fixed point, reviewed tree, and acceptance sources, records successful
  verification for that same reviewed tree, and contains no blocking finding before delivery.
  For one task, let `finish-worktree` own target synchronization, consolidation into one Task
  Commit, outcome selection, exact authorization, execution, verification, recovery, and lifecycle
  cleanup. For an accepted Ticket Batch, each worker owns its Ticket Task Worktree lifecycle; the
  controller owns Batch Worktree creation, whole-batch review and delivery, and every tracker
  transition. Target synchronization that changes reviewed
  content returns to the implementation workflow for review instead of being delivered.

## Remote Actions

- Commit authorization in either workspace does not authorize a push or pull request. Perform each
  remote action only when the user explicitly requests that outcome.
