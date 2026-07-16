# Response Format

Strength: `Default`

Scope: Response language, tag protocol, formatting, and implementation or review reporting.

## Language

- The first assistant message after each user request restates the request in English.
- The first line of every final answer restates the request in English.
- Keep intermediate progress updates concise and in Simplified Chinese; do not repeat the English
  restatement in those updates.
- Use Simplified Chinese for all other user-facing text unless the user explicitly requests another
  language.

## Response Tags

Use these `##` headings for non-trivial replies. Omit empty tags and use plain prose for very small
replies.

| Tag | Purpose |
| --- | --- |
| `🎯` | English restatement of the user's goal. |
| `⚠️` | Material risks, constraints, prerequisites, or assumptions. |
| `✅` | Completed result, changed files, and verification. |
| `❌` | Failure or blocker and what is needed to proceed. |
| `🤖` | One user question or a small set of choices. |

Preferred order:

```text
🎯 → ⚠️ → ✅ or ❌ → 🤖
```

## Tag Rules

- When present, `🎯` comes first and contains only English goal text.
- Use `⚠️` only for meaningful information and keep it to three items or fewer.
- Do not use `✅` and `❌` together in the same result.
- `🤖` is terminal. Stop after asking for input.
- Do not add an analysis or planning section by default. Put only decision-relevant trade-offs under
  `⚠️` or in concise prose.

## Formatting

- Use Markdown features only when they improve scanability.
- Do not use low-information openers such as "Okay", "Got it", or "Sure".
- Prefer short paragraphs over long narrative bullet lists.
- Use inline code for paths, commands, symbols, configuration keys, and literal values.

## Work Reports

- For implementation work, name changed files and verification performed.
- If verification was skipped or blocked, state that plainly.
- For reviews, put findings first in severity order and include file and line references when
  possible.
- For plans and design notes, use Chinese and make material trade-offs explicit.

## Example

```markdown
## 🎯
#### Update the menu owner scope behavior.

## ⚠️
> **Verification limit** — Widget behavior still needs a focused regression test.

## ✅
已更新 `menu_owner_scope.dart`，让 owner 变化时正确刷新菜单状态。

验证：已运行 `flutter test test/common/widgets/menu_owner_scope_test.dart`。
```
