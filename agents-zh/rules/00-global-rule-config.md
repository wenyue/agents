# 规则配置

强度：`Mandatory`

适用范围：规则强度、优先级、事实源、包装文件卫生和规则源卫生。

## 强度等级

- `Mandatory`：除非更高优先级的指令覆盖，否则必须遵守。
- `Default`：除非任务本身或更具体的规则提供充分理由，否则遵守。
- `Advisory`：仅作为指导，可按任务上下文调整。

## 优先级

按以下顺序解决冲突：

1. system、developer 和用户的直接指令覆盖仓库规则。
2. 更具体的规则（`globs` 或适用范围更窄）覆盖更一般的规则。
3. 具体程度相同时：`Mandatory` > `Default` > `Advisory`。
4. 当建议性规则（例如结构布局）与 `Mandatory` 项目规则或强制 lint 冲突时，遵守强制约束。

## 事实源

每类资产只保留一个事实源。所有平台专用文件都应是引用该事实源的薄包装。

| 资产 | 事实源 |
| --- | --- |
| 项目规则 | `.agents/rules/<nn>-<name>.md` |
| Agent 提示词 | `.agents/agents/<name>.md` |
| 项目 skill | `.agents/skills/<skill>/SKILL.md` |
| 第三方 skill | `.skillshare/skills/<skill>/SKILL.md` |
| Copilot 指引 | `.github/instructions/*.instructions.md` |

核心要求：

- tracked 配置使用仓库根目录相对路径，不得使用绝对文件系统路径。
- 如果相同内容出现在两个包装文件中，应将内容移回事实源并缩减包装文件。
- 薄包装只能包含平台专用元数据或运行时字段，以及一行指向事实源的引用。

## 包装文件风格

规则源的平台包装文件只保留引用：

- Cursor：`.cursor/rules/<same-name>.mdc`
- Copilot：`.github/instructions/<same-name>.instructions.md`

包装文件正文使用以下格式：

```text
Apply @.agents/rules/<nn>-<name>.md
```

新增规则时：

1. 在 `.agents/rules/<nn>-<name>.md` 编写事实源。
2. 当平台应加载该规则时，为 Cursor 和 Copilot 添加包装文件。
3. 如果规则改变了适用路径或工作流，更新 `AGENTS.md`。

新增 subagent 时：

1. 在 `.agents/agents/<name>.md` 编写共享提示词。
2. 当平台应公开该 subagent 时，为 Cursor、Codex 和 Copilot 添加薄包装。
3. 仓库级 Copilot 指引保留在 `.github/instructions/*.instructions.md`；subagent 提示词不得重复它。

## 编号约定

| 范围 | 作用域 |
| --- | --- |
| `00–09` | 全局规则：强度、人格、响应格式、skill。 |
| `10–19` | 基础规则：语言约定和其他共享默认值。 |
| `20–29` | 项目规则：工具、约定、结构、实用程序。 |
| `30–39` | 模块规则：功能、页面或有边界的子系统。 |
| `40–49` | 领域规则：测试及其他横切关注点。 |
| `50–59` | 插件、第三方插件或 package 专用规则。 |

必须先读完适用的 `00–09` 全局规则，再决定后续编号规则是否适用。

## MCP 配置

各平台的 server 命名和意图必须保持一致。具体项目 server 名称、端口、二进制文件和服务依赖应放在项目工具规则或配置所有者文档中，而不是全局规则中。优先使用相对路径或基于命令的配置，避免机器专用路径。

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| Cursor | `.cursor/mcp.json` | 共享意图。 |
| Codex | `.codex/config.toml` | 运行时 MCP 条目。 |
| Copilot CLI | `.vscode/mcp.json` | 顶层 key 为 `servers`。 |

## Skill 布局

- Skill 是可移植单元，不要在 `SKILL.md` 中硬编码仓库专用路径。
- 在 `SKILL.md` 内，使用相对于 skill 目录的路径引用 skill 自有文件。
- `.agents/skills/` 是运行时 skill 位置，可以包含项目自有 skill、来自 `wenyue/agents` 的公共 skill，以及由 `.skillshare/skills/` 单独管理的第三方 skill。
- 用语义描述项目目标，让 agent 在运行时解析具体路径。
- 仓库专用政策属于 `.agents/rules/`；可复用于其他仓库的工作流属于 skill。
