Apply @.agents/skills/change-set-verification/SKILL.md

Verify one coherent completed change set.

- Normalize only the selected project-owned scope and include every tool-modified file in
  verification.
- Return remaining semantic diagnostics to the parent agent instead of authoring semantic repairs.
- Report mechanical changes, static-analysis results, tests, gaps, and the final verdict concisely.
