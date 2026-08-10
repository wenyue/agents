# Project Agent Entry

## Project rules

Read every project Rule whose `Read when` condition matches the current task.

| Read when | Rule | Strength |
| --- | --- | --- |
| Project tooling, MCP, runtime, or verification | `.agents/rules/00-project-tools.md` | `Mandatory` |
| Plugin assets, documentation, generated files, ownership, or contract evolution | `.agents/rules/01-project-rules.md` | `Mandatory` |
| Making structure, module, or dependency-boundary decisions | `.agents/rules/02-project-structure.md` | `Advisory` |

Apply SmartKit plugin Rules for shared strength and precedence. Keep project Rule policy in the
files listed above.

## Agent skills

Load the context required by the current task or Skill.

| Read when | Context |
| --- | --- |
| Working with tracked work, specifications, tickets, or repository navigation | `docs/agents/issue-tracker.md` |
| Assigning or interpreting Matt triage roles | `docs/agents/triage-labels.md` |
| Using domain language or recording architecture decisions | `docs/agents/domain.md` |
