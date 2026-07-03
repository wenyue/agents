# Project Agent Entry

The source of truth for project instructions is `.agents/rules/`.
Do not duplicate or reinterpret those rules unless the user explicitly asks.

## How To Apply Rules

Always read the global rules first:

| Read when | Rule | Strength |
| --- | --- | --- |
| Starting any repository task | `.agents/rules/00-global-rule-config.md` | `Mandatory` |
| Starting any repository task | `.agents/rules/01-global-personality.md` | `Default` |
| Starting any repository task | `.agents/rules/02-global-response-format.md` | `Default` |
| Starting any repository task | `.agents/rules/03-global-skill-config.md` | `Mandatory` |

Then read the base rules that apply:

| Read when | Rule | Strength |
| --- | --- | --- |
| Working with code, reviews, or implementation design | `.agents/rules/10-base-code.md` | `Default` |
| Working with Dart or Flutter code | `.agents/rules/11-base-flutter.md` | `Default` |
| Working with C++ files | `.agents/rules/11-base-cpp.md` | `Default` |
| Working with Go code | `.agents/rules/11-base-go.md` | `Default` |
| Working with ARB localization files | `.agents/rules/12-base-arb.md` | `Mandatory` |

Then read the project-local rules that apply:

| Read when | Rule | Strength |
| --- | --- | --- |
| Using Flutter tooling, MCP, shell, or debug commands | `.agents/rules/20-project-tools.md` | `Mandatory` |
| Working with Dart or Flutter code in this app | `.agents/rules/21-project-rules.md` | `Default` |
| Making Dart or Flutter structure decisions | `.agents/rules/22-project-structure.md` | `Advisory` |
| Working with `common/` module utilities, UI helpers, or widgets | `.agents/rules/30-module-common.md` | `Advisory` |
| Working with tests under `test/` or `plugins/**/test/` | `.agents/rules/40-domain-testing.md` | `Default` |
| Working with `plugins/otaku_room_lint/**/*.dart` | `.agents/rules/50-plugin-otaku-room-lint.md` | `Mandatory` |

The meaning of `Mandatory`, `Default`, and `Advisory` is defined in
`.agents/rules/00-global-rule-config.md`.

## Precedence

- Direct system, developer, and user instructions override everything in this file.
- Always finish reading applicable `00-09` global rules before deciding whether any later numbered
  rule applies.
- When multiple referenced rule files apply, prefer the more specific file-type or project-local
  rule over the general rule.
