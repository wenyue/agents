# Response Format

Strength: `Default`

Scope: Response language, tag protocol, formatting, and implementation or review reporting.

## Language

- Use Simplified Chinese for all user-facing text unless the user explicitly requests another
  language.

## Brevity and Clarity

- Keep responses concise, retaining only the information the user needs to understand the
  conclusion, make a decision, and take the next action.
- Use natural, plain language and prefer common words; briefly explain necessary technical terms.

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

Preferred order:

```text
🎯 → ⚠️ → ✅ or ❌ → 🤖
```

## Tag Rules

- When present, `🎯` comes first and contains only the goal statement.
- Use `⚠️` only for meaningful information and keep it to three items or fewer.
- Do not use `✅` and `❌` together in the same result.
- `🤖` is terminal. Stop after asking for input.

## Work Reports

- For implementation work, list the main changed files and summarize the change in one or two
  sentences.
- For reviews, put findings first in severity order and include file and line references when
  possible.
- For plans and design notes, use Chinese and make material trade-offs explicit.

## Example

```markdown
## 🎯
#### 更新菜单 owner scope 的行为。

## ✅
主要文件：`menu_owner_scope.dart`

已更新 owner 变化时的刷新逻辑，使菜单状态保持一致。

## 🤖
请选择下一步：

A. 保留当前实现
B. 扩展为通用组件
C. 继续调整交互细节
D. 暂时结束
```
