# ARB 指南

强度：`Mandatory`

适用范围：ARB 本地化 key 命名、metadata、排序和生成规则。

## 源文件

- `zh.arb` 是 Flutter `gen-l10n` 的 template ARB，也是 key 和 metadata 的事实源。
- 翻译缺失时，`en.arb` 是运行时 fallback。
- `zh.arb` 中每个 key 都有对应的 `@key` metadata 条目。
- 每个 ARB 内的所有 key 按字母顺序排序。

## Key 命名：`${module}_${filename?}_${name}{index?}`

- **module**（必需）：lowerCamelCase module 名称。Dart 文件使用的 key 从 `lib/` 下第一层目录派生，并将 snake_case 转换为 lowerCamelCase。跨 module 共享 key 的 module 应在目标项目 analyzer、lint 或 localization 配置中声明。
- **filename**（可选）：来自 Dart 文件名 stem 的 camelCase，例如 `detail_base` → `detailBase`。
- **name**（必需）：camelCase 用途，例如 title、button、tip、error 或 success。
- **index**（可选）：附加在 `name` 末尾的数字，用于用途相同且位置邻近的重复字符串。

```text
✅ 良好：album_title, album_detailBase_button, global_cancelButton, album_tip2
❌ 不好：title, Album_Title, _album_title, album_detail_base_button
```

## Metadata 格式

```json
"album_title": "专辑标题",
"@album_title": {
  "description": "[Album] > Album Page > title. ~4–12 chars.",
  "placeholders": { "count": { "type": "int", "example": "5" } }
}
```

- **语言**：metadata 始终使用英文；只有翻译值使用目标 locale 语言。
- **Module**：在方括号中大写，例如 `[Album]` 或 `[Filter]`。
- **位置**：使用一层可读文件名，例如 `albumDetailBase` → `Album Detail Page`。
- **用途**：button、label、tooltip、error/success、title 或 description。
- **边界**：根据调用处 widget 布局推断 `~min–max chars.`，不要按当前字符串长度推断。Latin 字符计 1，CJK 字符计 2。

## 避免

- 缺失 `@key` metadata。
- 错误的 `[Module] > ...` metadata 形状。
- 根据字符串长度而不是布局猜测字符边界。
- 未记录 placeholder。
- Key 缺少 module 前缀或大小写不一致。
- 非英文 metadata。
