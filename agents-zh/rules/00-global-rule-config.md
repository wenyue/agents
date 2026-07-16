# 规则配置

强度：`Mandatory`

适用范围：规则强度、优先级、事实源所有权、wrapper 维护、编号、MCP 配置和 Skill 编写所有权。

## 强度等级

- `Mandatory`：除非更高优先级指令覆盖，否则必须遵守。
- `Default`：除非任务或更具体的规则提供充分理由，否则遵守。
- `Advisory`：在有帮助时根据任务上下文调整。

## 优先级

按以下顺序解决冲突：

1. system、developer 和用户的直接指令覆盖仓库规则。
2. 更具体的规则（包括更窄的 glob 或适用范围）覆盖更一般的规则。
3. 具体程度相同时，`Mandatory` 覆盖 `Default`，`Default` 覆盖 `Advisory`。
4. 强制约束（例如 Mandatory 项目规则或 lint）覆盖建议性指导。

## 事实源

每类资产只保留一个事实源。平台专用文件是引用该事实源的薄 wrapper。

| 资产 | 事实源 |
| --- | --- |
| 项目规则 | `.agents/rules/<nn>-<name>.md` |
| Agent prompt | `.agents/agents/<name>.md` |
| 项目 Skill | `.agents/skills/<skill>/SKILL.md` |
| 第三方 Skill | `.skillshare/skills/<skill>/SKILL.md` |
| Copilot guidance | `.github/instructions/*.instructions.md` |

- tracked 配置使用仓库根目录相对路径；不得使用绝对文件系统路径。
- 当相同内容出现在多个 wrapper 中时，将内容移回事实源并缩减 wrapper。
- 薄 wrapper 只能包含平台元数据或运行时字段，以及一个事实源引用。

## Wrapper 维护

Rule wrapper 使用以下位置：

- Cursor：`.cursor/rules/<same-name>.mdc`
- Copilot：`.github/instructions/<same-name>.instructions.md`

两类 Rule wrapper 都使用以下正文：

```text
Apply @.agents/rules/<nn>-<name>.md
```

新增 Rule 时：

1. 在 `.agents/rules/<nn>-<name>.md` 编写事实源。
2. 为应加载该 Rule 的每个平台添加 Cursor 和 Copilot wrapper。
3. 当 Rule 改变适用路径或工作流时更新 `AGENTS.md`。

新增 subagent 时：

1. 在 `.agents/agents/<name>.md` 编写共享 prompt。
2. 为公开该 subagent 的平台添加薄 Cursor、Codex 和 Copilot wrapper。
3. 仓库级 Copilot guidance 保留在 `.github/instructions/*.instructions.md`；不要在
   subagent prompt 中重复。

## 编号

| 范围 | 适用范围 |
| --- | --- |
| `00–09` | 全局规则：强度、人格、响应格式和 Skill。 |
| `10–19` | 基础规则：语言和共享默认值。 |
| `20–29` | 项目规则：工具、约定、结构和实用程序。 |
| `30–39` | 模块规则：功能、页面和有边界的子系统。 |
| `40–49` | 领域规则：测试及其他横切关注点。 |
| `50–59` | Plugin、第三方 plugin 和 package 专用规则。 |

必须先读完所有适用的 `00–09` 全局规则，再决定后续规则是否适用。

## MCP 配置

各平台的 server 名称和意图保持一致。将项目专用 server 名称、端口、二进制文件和服务依赖放入
项目工具规则或拥有它的配置。优先使用相对路径或基于命令的配置，避免机器专用路径。

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| Cursor | `.cursor/mcp.json` | 共享意图。 |
| Codex | `.codex/config.toml` | 运行时 MCP 条目。 |
| Copilot CLI | `.vscode/mcp.json` | 顶层 key 为 `servers`。 |
