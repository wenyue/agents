# Workflow Configuration

Strength: `Mandatory`

Scope: Agent invocation, planning and decision artifacts, current-workspace and Task Worktree
modes, and remote action authorization.

## Agent Invocation Strategy

- Automatically authorize the Agent to use Subagents when needed.
- Choose each Subagent's model and reasoning effort for its task: prefer faster, lower-cost options
  for bounded supporting work and stronger options for ambiguous, cross-cutting, or high-risk work.
- Preserve settings required by the user, an applicable Rule or Skill, or the selected named Agent;
  otherwise choose task-appropriate settings instead of inheriting the parent's by default.
- When using a different model, inherit no history or only the smallest sufficient history and give
  the Subagent a self-contained brief. Use a full-history fork, which inherits the parent model,
  only when the task requires the complete parent conversation.
- If no suitable alternate model is available, delegate only when isolation or independent
  execution still helps; otherwise keep the work in the parent Agent.

## Planning and Decision Artifacts

- Write every file under `.scratch/` and `docs/adr/` in English.
- Before state-changing implementation, determine whether the accepted conversation, issue, Spec,
  or other source already defines stable scope, decisions, and acceptance criteria.
- Recommend that the user invoke `to-spec` when material behavior, contracts, testing seams, or
  scope decisions remain implicit or need a durable reviewable source of truth.
- Recommend that the user invoke `to-tickets` when the accepted work contains multiple independently
  verifiable slices, blocking relationships, parallel work, or more work than one fresh
  implementation context should own. Tickets may start from an accepted Spec or the current
  conversation.
- Proceed without a Spec or Tickets when one accepted source already makes a single-scope task
  implementable and verifiable.
- Use `implement` to execute accepted implementation work from the conversation, an issue, a Spec,
  or Tickets. It owns implementation, verification, and code review within the selected workspace
  mode.

## Current Workspace Mode

- Use the current workspace when the user, host, and applicable Skills do not require isolation,
  parallel work does not need separate state, and existing checkout state can be preserved in place.
- Preserve all pre-existing staged, unstaged, and untracked work while implementing and reviewing
  the accepted task.
- Choose a non-destructive path when a task operation would overwrite, stash, reset, clean, or
  discard that state; request direction when no such path is available.
- A file containing both pre-existing and task changes is not automatically a blocker. Continue
  when the two can be distinguished and the result is verified to preserve the pre-existing
  changes; otherwise stop and request direction.
- Leave task changes uncommitted unless the user separately authorizes a commit. This boundary also
  governs work performed through `implement`; its commit step requires that authorization in this
  mode. A linked worktree that has not qualified as a Task Worktree follows the same boundary.

## Task Worktree Mode

- Apply `create-worktree` when the user requests isolation, the host or an applicable Skill requires
  it, parallel work needs separate state, or isolation is needed to protect existing checkout state.
  Let it own linked-worktree selection, readiness, and Task Worktree qualification.
- In a qualified Task Worktree, the implementation workflow may create task-only Checkpoint Commits
  through the repository's normal commit hooks without separate authorization.
- When implementation and its initial review are complete, apply `finish-worktree`. Let it own
  target synchronization, final review, consolidation into one Task Commit, outcome selection,
  exact authorization, execution, verification, recovery, and lifecycle cleanup.

## Remote Actions

- Authorization to create commits in either workspace mode does not authorize pushing or creating
  a pull request. Perform either remote action only when the user explicitly requests its
  corresponding remote outcome.
