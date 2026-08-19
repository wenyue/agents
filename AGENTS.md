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

### Issue tracker

Issues and specifications are tracked in this repository's GitHub Issues. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the five default canonical triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain documentation layout. See `docs/agents/domain.md`.
