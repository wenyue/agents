---
name: write-comment
description: >-
  编写满足项目格式规则并补充非显而易见信息的注释。添加或编辑注释时使用。
---

# 编写注释

注释必须满足目标项目的格式和 lint 规则。此 skill 还要求每条注释都通过承载代码本身无法表达的信息来证明其存在价值。

## 格式规则

1. 第一个单词大写，以 `.`、`?` 或 `!` 结尾。
2. 只使用英文。
3. `//` 或 `///` 后留一个空格。
4. 声明（类、方法、字段、函数）使用 `///`；行内或函数体使用 `//`。

## 信息密度

注释必须添加读者无法从名称、签名、类型或下一行显而易见的代码中获得的信息。如果只是重述这些内容，就删除它。

- 好：行为、约束、边界情况、失败模式、不变量、意图、理由。
- 差：改述符号名称，或听起来正式但没有信息的装饰性标签。
- 测试：“没有这条注释，读者会遗漏什么？”如果答案是“什么也不会”，就不要写。

## 语气

- 方法文档注释使用**祈使语气**：`Return the cached item for [id], or null if it expired.`
- getter、字段和行为说明使用**第三人称一般现在时**：`Returns null when the cache is stale.` 或 `Cache for the last page fetched from disk.`
- **主动语态优先于被动语态**：使用 `Skips empty segments.`，不要使用 `Empty segments are skipped.`
- 每条注释只表达一个观点。

## 各上下文示例

| 上下文 | 风格 | 示例 |
| --- | --- | --- |
| 文件头 | `///` 说明此文件做什么。 | `/// Widgets that align settings rows.` |
| 类或枚举 | `///` 职责。 | `/// Controller that serializes refresh requests to avoid duplicate fetches.` |
| 构造函数 | `///` 做什么或何时使用。 | `/// Creates a tile that reserves space for the progress label.` |
| 方法 | `///` 祈使语气。 | `/// Return the cached item for [id], or null if it expired.` |
| Getter | `/// "Returns X."` / `"True if X."` | `/// True if the queue still has retryable jobs.` |
| 字段 | `///` 保存什么。 | `/// Cache for the last page fetched from disk.` |
| 行内 | `//` 说明原因而非行为。 | `// Avoid rebuilding when key is unchanged.` |

## 豁免（句子形态规则不适用）

- **标记**：`TODO`、`FIXME`、`NOTE`、`WARNING`、`DEPRECATED`、`HACK`、`XXX`、`BUG`、`NOCOMMIT`、`TEMP`、`TEMPORY`、`ignore:`、`ignore_for_file:`、`cspell:`。
- **URL**：注释包含 `http://`、`https://`、`www.` 或 `ftp://`。
- **类代码内容**：注释读起来像代码，例如 `foo()`、`bar =`、`CONST_NAME`。
- **文档或 API 指令**：注释以 `@` 或 `\` 开头。
- **短行内注释**：注释与代码在同一行，且不超过 16 个字符和 3 个单词。

## 多行注释

- 第一行：独立的摘要句。
- 后续行：详细信息；段落最后一行以 `.`、`?` 或 `!` 结尾。
- 段落之间空一行。参数引用使用 `[paramName]`。

## 句型

- `Returns … when ….` / `Returns … or null if ….`
- `True if ….` / `Checks whether ….`
- `Loads … from ….` / `Parses … while ….`
- `Throws [Exception] if ….`（仅限多行）

避免片段：把 `The user id.` 改为 `The id of the user.`。

只有在这些句型确实添加信息时才使用。位于 `loadConfig()` 上方的 `/// Loads the config.` 仍然是差注释。

## 不应添加注释的情况

- 显而易见的代码，例如在 `i++` 上方写 `// Increment i.`。
- 与名称、完整声明、签名或类型重复。
- 不增加行为、约束、理由或其他非显而易见信息的空洞注释。

## 工作流

1. 声明使用 `///`，行内或函数体使用 `//`。
2. 是否属于豁免？是则保持原样。
3. 否则：写完整句子，首词大写，以 `.`、`?` 或 `!` 结尾。
4. 运行目标项目的 lint 或格式化命令，并修复注释格式报告。
