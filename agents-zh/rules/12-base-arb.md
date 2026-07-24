# ARB 指引

强度：`Mandatory`

适用范围：ARB 源文件归属、本地化键语法、元数据、排序和生成规则。

## 源文件

- 将 Flutter `gen-l10n` 配置的模板 ARB 作为键和元数据的事实源。
- 缺少翻译时，遵循应用配置的 locale resolution 和 fallback 行为；不要假设某个固定的
  fallback ARB。
- 源文件中的每个键都必须有对应的 `@key` 元数据条目。
- 仓库有自有的本地化流程时，用它排序键；否则按字母顺序排列每个键及其紧邻的 `@key`
  元数据条目。
- 不要编辑生成的本地化产物。

## 键语法

使用 `${module}_${filename?}_${name}{index?}`。

## 键的组成部分

- 除非项目配置声明了共享 module，否则从负责该字符串的应用模块推导 `module`。
- 各组成部分使用小驼峰命名；可选的 filename 部分从负责该字符串的 Dart 文件推导。
- 只有同一位置附近有多个用途相同的重复字符串时，才追加数字。

## 元数据契约

- 元数据 description 使用英语，并遵循
  `[Module] > Location > purpose. ~min–max chars.`。
- `Module` 使用 PascalCase。把负责该字符串的 Dart 文件名转换成一个易读的页面或组件名称作为
  `Location`；`purpose` 使用明确角色，例如 `button`、`label`、`tooltip`、`error`、`success`、
  `title` 或 `description`。
- `~min–max chars.` 的范围应根据调用点的组件布局推断，不要根据当前字符串长度估算。
  拉丁字符按 1 计数，CJK 字符按 2 计数。
- 每个 placeholder 都要记录类型和有代表性的示例。

例如：

```json
{
  "album_itemCount": "{count} albums",
  "@album_itemCount": {
    "description": "[Album] > Album Page > label. ~4–12 chars.",
    "placeholders": {
      "count": {
        "type": "int",
        "example": "5"
      }
    }
  }
}
```
