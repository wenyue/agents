# Project Agent Entry

## Project rules

Read every project Rule whose `Read when` condition matches the current task.

| Read when | Rule | Strength |
| --- | --- | --- |
| Running project tooling or synchronization, or completing a change set | `.agents/rules/00-project-tools.md` | `Mandatory` |
| Changing APIs, capability ownership, installation, documentation, evaluation, contract evolution, distribution, hard dependencies, or exposure | `.agents/rules/01-project-contracts.md` | `Mandatory` |
| Placing repository assets or making architectural-boundary decisions | `.agents/rules/02-project-structure.md` | `Advisory` |

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
