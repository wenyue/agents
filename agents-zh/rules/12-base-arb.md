# ARB 指南

强度：`Mandatory`

适用范围：ARB 事实源所有权、本地化 key grammar、metadata、排序和生成规则。

## 源文件

- 使用 `zh.arb` 作为 Flutter `gen-l10n` template 和 key、metadata 的事实源。
- 翻译缺失时，使用 `en.arb` 作为运行时 fallback。
- 为 `zh.arb` 中每个 key 添加对应的 `@key` metadata 条目。
- 每个 ARB 文件内的所有 key 按字母顺序排序。

## Key Grammar

使用以下 key 形状：

```text
${module}_${filename?}_${name}{index?}
```

```text
GOOD: album_title, album_detailBase_button, global_cancelButton, album_tip2
BAD:  title, Album_Title, _album_title, album_detail_base_button
```

## Key 组成部分

- `module` 为必需项，使用 lower camel case。Dart 文件使用的 key 从 `lib/` 下第一层目录派生，
  并将 snake case 转换为 lower camel case。在目标项目的 analyzer、lint 或 localization 配置中
  声明跨 module 共享 key 使用的 module。
- `filename` 为可选项。将 Dart 文件名 stem 转换为 camel case，例如 `detail_base` 转换为
  `detailBase`。
- `name` 为必需项，使用 camel case 说明用途，例如 `title`、`button`、`tip`、`error`
  或 `success`。
- `index` 为可选项。对于用途相同且位置邻近的重复字符串，在 `name` 后附加数字。

## Metadata 契约

使用以下 metadata 形状：

```json
"album_title": "专辑标题",
"@album_title": {
  "description": "[Album] > Album Page > title. ~4–12 chars.",
  "placeholders": { "count": { "type": "int", "example": "5" } }
}
```

- Metadata 使用英文。只有翻译值使用目标 locale 语言。
- 方括号中的 module 首字母大写，例如 `[Album]` 或 `[Filter]`。
- Location 使用一层可读文件名，例如 `albumDetailBase` 转换为 `Album Detail Page`。
- Purpose 使用 button、label、tooltip、error、success、title 或 description。
- 根据调用点的 widget 布局推断 `~min–max chars.` 边界，不根据当前字符串长度推断。Latin 字符计
  1，CJK 字符计 2。
- 记录每个 placeholder。

## 禁止形式

- 不得缺少对应的 `@key` metadata。
- 不得使用不符合 `[Module] > ...` 形状的 metadata description。
- 不得根据当前字符串长度估算字符边界。
- 不得使用缺少 module 前缀或大小写不一致的 key。
- Metadata 不得使用英文以外的语言。
