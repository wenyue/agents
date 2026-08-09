# Project Agent Entry

The source of truth for project instructions is `.agents/rules/`.
Do not duplicate or reinterpret those rules unless the user explicitly asks.

## How To Apply Rules

Read the project-local rules that apply. Plugin Rules are delivered by the installed SmartKit
plugin and own the shared strength and precedence protocol.

| Read when | Rule | Strength |
| --- | --- | --- |
{{project_rule_rows}}

## Precedence

- Direct system, developer, and user instructions override everything in this file.
- Apply the plugin-owned precedence contract: strength first, then owner, then specificity.
- At equal strength, project Rules take precedence over plugin Rules.

## Agent skills

### Issue tracker

See `docs/agents/issue-tracker.md`.

### Triage labels

See `docs/agents/triage-labels.md`.

### Domain docs

See `docs/agents/domain.md`.
