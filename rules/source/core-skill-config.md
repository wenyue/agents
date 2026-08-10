# Workflow Configuration

Strength: `Mandatory`

Scope: Subagent delegation, Skill precedence, planning artifacts, worktree workflow ownership, and
Git safety.

## Delegation

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

## Skill Precedence

- Apply Skills according to their declared user and model invocation metadata. Within overlapping
  scope, project-local Skills and more-specific project Rules take precedence over bundled Skills.

## Planning Artifacts

- Before state-changing implementation, determine whether the accepted conversation, issue, Spec,
  or other source already defines stable scope, decisions, and acceptance criteria.
- Recommend that the user invoke `to-spec` when material behavior, contracts, testing seams, or
  scope decisions remain implicit or need a durable reviewable source of truth.
- Recommend that the user invoke `to-tickets` when the accepted work contains multiple independently
  verifiable slices, blocking relationships, parallel work, or more work than one fresh
  implementation context should own. Tickets may start from an accepted Spec or the current
  conversation.
- Proceed without a Spec or Tickets when one accepted source already makes a single-scope task
  implementable and verifiable. Decide worktree isolation independently from planning artifacts.

## Worktree Workflow

- For state-changing implementation, apply `create-worktree` when the user requests isolation, the
  host or an applicable Skill requires it, parallel work needs separate state, or isolation is
  needed to protect pre-existing checkout state. Do not create a worktree for read-only work or
  solely because a repository task exists.
- Let `create-worktree` own reuse or creation, the ignored `.worktrees` location, environment setup
  handoff, and baseline verification before implementation.
- When implementation in a named linked worktree is complete and verified, apply
  `finish-worktree`. Let it own outcome selection, exact authorization, task and base preparation,
  execution, verification, recovery, and lifecycle cleanup under this Rule's Git Safety policy.

## Git Safety

- Preserve pre-existing local changes. When an operation would overwrite, stash, reset, clean, or
  discard them, stop and choose a non-destructive path or request direction.
- A same-file overlap is not automatically a blocker. Merge it when confidence is high and the
  result can be verified; otherwise stop and ask.
- Push or create a pull request only after the user explicitly requests that remote action.
