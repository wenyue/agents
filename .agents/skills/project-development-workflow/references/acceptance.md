# Project Development Workflow Acceptance

Use this reference when generating or reviewing a target repository's
`project-development-workflow` skill.

Acceptance requires an actual git worktree and the complete generated workflow:

1. Create a temporary worktree from the target repository.
2. Ensure the worktree has the generated workflow skill and any local-only agent assets needed to
   read repository instructions.
3. Run the generated bootstrap script.
4. Run generated in-worktree verification.
5. Make a harmless tracked change and checkpoint it through the generated workflow.
6. Run merge-back into the original workspace.
7. Run authoritative verification in the original workspace.
8. Confirm the original workspace remains usable after merge-back.

Treat skipped runtime services, missing credentials, dependency failures, or generated-file failures
as blockers unless the generated skill explicitly documents a safe degraded path.
