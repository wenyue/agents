# Response Format

Strength: `Default`

Scope: Language, tag protocol, formatting, and work reporting in final responses presented to
human users.

## Applicability

- Apply this Rule only while composing the final response presented to a human user. Internal
  reasoning and all intermediate or non-final work are outside its scope.

## Language

- Use Simplified Chinese for all user-facing text unless the user explicitly requests another
  language.

## Response Tags

Use these `##` headings for non-trivial replies. Omit empty tags and use plain prose for very small
replies.

| Tag | Purpose |
| --- | --- |
| `🎯` | The user's goal. |
| `⚠️` | Material risks, constraints, prerequisites, or assumptions. |
| `✅` | Completed result, main changed files, and brief change summary. |
| `❌` | Failure or blocker and what is needed to proceed. |
| `🤖` | One user question or a small set of choices. |

Preferred order: `🎯 → ⚠️ → ✅ or ❌ → 🤖`.

## Tag Rules

- Each `##` tag heading contains only its icon; tagged content starts on the next line.
- When present, `🎯` comes first and contains only the goal statement.
- Use `⚠️` only for meaningful information and keep it to three items or fewer.
- When reporting a result, choose exactly one of `✅` or `❌`.
- `🤖` is terminal. Stop after asking for input.

## Work Reports

- For implementation work, list the main changed files and summarize the change in one or two
  sentences.
- For reviews, put findings first in severity order and include file and line references when
  possible.
- For plans and design notes, make material trade-offs explicit.
