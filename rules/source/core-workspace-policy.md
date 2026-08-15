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
  through the repository's normal commit hooks without separate authorization.
- When implementation and its initial review are complete, apply `finish-worktree`. Let it own
  target synchronization, final review, consolidation into one Task Commit, outcome selection,
  exact authorization, execution, verification, recovery, and lifecycle cleanup.

## Remote Actions

- Commit authorization in either workspace does not authorize a push or pull request. Perform each
  remote action only when the user explicitly requests that outcome.
