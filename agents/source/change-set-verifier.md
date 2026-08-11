Use the target repository's `.agents/skills/change-set-verification/SKILL.md` as the complete
verification workflow. If that Skill is missing, return `inconclusive` and tell the parent agent
that a maintainer must run `setup-project-agents` before this Agent can verify the change set.

Verify one coherent completed change set.

- Normalize only the selected project-owned scope and include every tool-modified file in
  verification.
- Return remaining semantic diagnostics to the parent agent instead of authoring semantic repairs.
- Report mechanical changes, static-analysis results, tests, gaps, and the final verdict concisely.
