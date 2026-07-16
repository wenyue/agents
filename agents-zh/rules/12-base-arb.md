# ARB 指引

强度：`Mandatory`

适用范围：ARB 源文件归属、本地化键语法、元数据、排序和生成规则。

## 源文件

- 将 `zh.arb` 用作 Flutter `gen-l10n` 模板，以及键和元数据的事实源。
- 缺少翻译时，运行时回退到 `en.arb`。
- `zh.arb` 中的每个键都必须有对应的 `@key` 元数据条目。
- 每个 ARB 文件内的所有键都按字母顺序排列。

## 键语法

键采用以下形式：

```text
${module}_${filename?}_${name}{index?}
```

```text
GOOD: album_title, album_detailBase_button, global_cancelButton, album_tip2
BAD:  title, Album_Title, _album_title, album_detail_base_button
```

## 键的组成部分

- `module` 为必填项，使用小驼峰命名。对于 Dart 文件使用的键，从 `lib/` 下的第一级目录推导，
  并将 snake case 转换为小驼峰。跨模块共享键的 module 应在目标项目的 analyzer、lint 或本地化配置中设置。
- `filename` 为可选项。将 Dart 文件名主体转换为驼峰形式，例如将 `detail_base` 转为 `detailBase`。
- `name` 为必填项，使用驼峰形式说明用途，例如 `title`、`button`、`tip`、`error` 或 `success`。
- `index` 为可选项。同一位置附近有多个用途相同的重复字符串时，在 `name` 后追加数字。

## 元数据契约

元数据采用以下形式：

```json
"album_title": "专辑标题",
"@album_title": {
  "description": "[Album] > Album Page > title. ~4–12 chars.",
  "placeholders": { "count": { "type": "int", "example": "5" } }
}
```

- 元数据使用英语。只有翻译值使用目标区域设置的语言。
- 方括号中的 module 首字母大写，例如 `[Album]` 或 `[Filter]`。
- 位置只保留一个易读的文件名层级，例如将 `albumDetailBase` 写成 `Album Detail Page`。
- 用 button、label、tooltip、error、success、title 或 description 表明用途。
- `~min–max chars.` 的范围应根据调用点的组件布局推断，不要根据当前字符串长度估算。
  拉丁字符按 1 计数，CJK 字符按 2 计数。
- 记录每一个 placeholder。

## 禁止形式

- 不要遗漏对应的 `@key` 元数据。
- 元数据 description 必须遵守 `[Module] > ...` 形式。
- 不要根据当前字符串长度估算字符数范围。
- 键不得缺少 module 前缀，也不得使用不一致的大小写。
- 元数据不得使用英语以外的语言。
