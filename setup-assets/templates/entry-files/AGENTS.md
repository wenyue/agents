# Project Agent Entry

## Project rules

Read every project Rule whose `Read when` condition matches the current task.

| Read when | Rule | Strength |
| --- | --- | --- |
{{project_rule_rows}}

Apply SmartKit plugin Rules for shared strength and precedence. Keep project Rule policy in the
files listed above.

## Agent skills

Load the context required by the current task or Skill.

| Read when | Context |
| --- | --- |
| Working with tracked work, specifications, tickets, or repository navigation | `docs/agents/issue-tracker.md` |
| Assigning or interpreting Matt triage roles | `docs/agents/triage-labels.md` |
| Using domain language or recording architecture decisions | `docs/agents/domain.md` |
