# Workflow Configuration

Strength: `Mandatory`

Scope: Subagent delegation, bundled Skill precedence, repository context, worktree workflow
ownership, and Git safety.

## Delegation

- Automatically authorize the agent to use subagents when needed.
- Choose each subagent's model and reasoning effort for its task: prefer faster, lower-cost options
  for bounded supporting work and stronger options for ambiguous, cross-cutting, or high-risk work.
- Preserve settings required by the user, an applicable Rule or Skill, or the selected named Agent;
  otherwise choose task-appropriate settings instead of inheriting the parent's by default.
- When using a different model, inherit no history or only the smallest sufficient history and give
  the subagent a self-contained brief. Use a full-history fork, which inherits the parent model,
  only when the task requires the complete parent conversation.
- If no suitable alternate model is available, delegate only when isolation or independent
  execution still helps; otherwise keep the work in the parent Agent.

## Bundled Skills

- Matt Skills are bundled with the SmartKit plugin. Apply each Skill according to its declared user
  and model invocation metadata; do not maintain a second installed copy or a fixed Rule-side list
  of Skill names.
- When a Skill requires repository context under `docs/agents/`, stop if the referenced files are
  missing or incomplete and use `setup-project-agents` to repair the complete project snapshot. Use
  `setup-matt-pocock-skills` separately only when the user explicitly requests a tracker, triage
  label, or domain-layout reconfiguration; do not guess those project facts.
- Project-local Skills and more-specific project Rules take precedence within their owned scope.
  In particular, use `write-rule`, `write-skill`, `change-set-verification`,
  `worktree-environment-setup`, and other project-specific workflows when their triggers match.

## Worktree Workflow

- Create isolated work with the host's native worktree capability when available, or use a safely
  located and ignored Git worktree after obtaining any required consent.
- After creating a worktree, use the target repository's `worktree-environment-setup` Skill when it
  exists, then run the repository's baseline verification before implementation.
- When implementation in a named linked worktree is complete and verified, present four outcomes:
  merge locally into the recorded base branch; push and create a pull request; keep the task branch
  and worktree; or integrate into the current checkout.
- Use `worktree-integrate` only for current-checkout integration. The parent Agent owns local merge,
  pull-request, keep-branch, and explicitly requested discard outcomes under this Rule's Git Safety
  constraints.
- Treat local merge and current-checkout integration as different outcomes even when the current
  checkout is on the recorded base branch. Local merge advances the base branch;
  `worktree-integrate` review mode keeps the current `HEAD` and index unchanged and returns task
  changes as unstaged or untracked while preserving unrelated local changes.
- Use `worktree-integrate` commit mode only when the user explicitly requests local integration with
  a commit, and keep all business changes in one commit.

## Git Safety

- Preserve pre-existing local changes. When an operation would overwrite, stash, reset, clean, or
  discard them, stop and choose a non-destructive path or request direction.
- A same-file overlap is not automatically a blocker. Merge it when confidence is high and the
  result can be verified; otherwise stop and ask.
- Push or create a pull request only after the user explicitly requests that remote action.
