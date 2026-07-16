# 规则配置

强度：`Mandatory`

适用范围：规则强度、优先级、事实源归属、包装文件维护、编号和 MCP 配置。

## 强度等级

- `Mandatory`：必须遵守，除非更高优先级的指令另有要求。
- `Default`：默认遵守；如果任务本身或更具体的规则有充分理由，可以调整。
- `Advisory`：可在有帮助时结合任务实际情况采用。

## 优先级

按以下顺序解决冲突：

1. 系统、开发者和用户的直接指令优先于仓库规则。
2. 更具体的规则（包括匹配范围或适用范围更窄的规则）优先于一般规则。
3. 具体程度相同时，优先级依次为 `Mandatory`、`Default`、`Advisory`。
4. 强制执行的约束（如必遵守的项目规则或 lint）优先于建议性指导。

## 事实源

每类资产只保留一个事实源。各平台专用文件应是引用该事实源的精简包装文件。

| 资产 | 事实源 |
| --- | --- |
| 项目规则 | `.agents/rules/<nn>-<name>.md` |
| Agent 提示词 | `.agents/agents/<name>.md` |
| 项目 Skill | `.agents/skills/<skill>/SKILL.md` |
| 第三方 Skill | `.skillshare/skills/<skill>/SKILL.md` |
| Copilot 指引 | `.github/instructions/*.instructions.md` |

- 受版本控制的配置应使用仓库根目录相对路径，不要使用绝对文件系统路径。
- 同一内容出现在多个包装文件中时，应将内容移到事实源，并精简这些包装文件。
- 精简包装文件只能包含平台元数据或运行时字段，以及一个事实源引用。

## 包装文件维护

规则包装文件位于：

- Cursor：`.cursor/rules/<same-name>.mdc`
- Copilot：`.github/instructions/<same-name>.instructions.md`

两类规则包装文件都使用以下正文：

```text
Apply @.agents/rules/<nn>-<name>.md
```

新增规则时：

1. 在 `.agents/rules/<nn>-<name>.md` 中编写源规则。
2. 为每个会加载该规则的平台添加 Cursor 和 Copilot 包装文件。
3. 如果规则改变了适用路径或工作流，更新 `AGENTS.md`。

新增子 Agent 时：

1. 在 `.agents/agents/<name>.md` 中编写共享提示词。
2. 为公开该子 Agent 的平台添加精简的 Cursor、Codex 和 Copilot 包装文件。
3. 仓库级 Copilot 指引应放在 `.github/instructions/*.instructions.md` 中，不要在子 Agent
   提示词中重复。

## 编号

| 范围 | 适用内容 |
| --- | --- |
| `00–09` | 全局规则：强度、人格、回复格式和 Skill。 |
| `10–19` | 基础规则：语言规范和共享默认约定。 |
| `20–29` | 项目规则：工具、约定、结构和实用工具。 |
| `30–39` | 模块规则：功能、界面和边界明确的子系统。 |
| `40–49` | 领域规则：测试及其他横切关注点。 |
| `50–59` | 插件、第三方插件和包的专用规则。 |

必须先读完所有适用的 `00–09` 全局规则，再判断后续编号的规则是否适用。

## MCP 配置

各平台的服务器名称和用途应保持一致。项目专用的服务器名称、端口、二进制文件和服务依赖，
应放入项目工具规则或其归属配置中。优先使用相对路径或基于命令的配置，避免使用机器专用路径。

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| Cursor | `.cursor/mcp.json` | 共享用途。 |
| Codex | `.codex/config.toml` | 运行时 MCP 条目。 |
| Copilot CLI | `.vscode/mcp.json` | 顶层键为 `servers`。 |
