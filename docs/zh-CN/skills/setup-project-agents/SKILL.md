---
name: setup-project-agents
description: 当需要跨 Codex、Cursor 和 Copilot 初始化或对齐仓库的 Rules、Skills、Agents 或 MCP 时使用。
---

# 设置项目 Agents

通过脚本驱动的 setup 工作流对齐一个仓库的 Rules、Skills、Agents 和 MCP。将四类能力视为平级：
每类都有自己的 canonical project input 和原生交付形式；任何一类都不是另一类的附属说明。

## 能力输入

在 `start` 前建立请求的项目意图。只有用户要求变更时，才修改 canonical input。

| 能力 | Canonical project input | Setup 职责 |
| --- | --- | --- |
| Rules | `.agents/rules/` 下的项目自有 source，以及请求生成的 Rule target | 保留项目 Rules，并向各宿主交付 setup 受管的 Rules。 |
| Skills | `.agents/skills/` 下的项目自有目录、请求生成的 Skill target，以及 `.agents/config.json` 的 `skills` 声明 | 保留项目 Skills，并安装请求生成或外部来源的 Skills。 |
| Agents | `.agents/agents/` 下的项目自有 source，以及 `.agents/config.json` 的 `agents` 声明 | 保留 Agent source，并生成声明的宿主 adapter。 |
| MCP | `.agents/config.json` 的 `mcp` 声明 | 生成声明的宿主原生 MCP 条目，不存储 secret 值。 |

使用 `.agents/config.json` 声明的 version 1 schema。配置的 Agent source 必须是与 ID 匹配的
`.agents/agents/<id>.md`。MCP 条目只能声明 `url` 或 `command` 之一；按顺序执行的 `when`/`set`
override 可选择宿主平台和操作系统。

项目自有 canonical input 始终是可编辑的项目内容。Setup 生成的文件和结构化字段由 setup 拥有。
Plugin Rules、Skills、Agents 和 MCP 随 SmartKit 安装，不属于此项目工作流。

## 工作流

1. 从目标仓库根目录检查四类能力输入。在开始前应用用户要求的 canonical-input 变更。本步骤完成的
   标志是 Rules、Skills、Agents 和 MCP 都表达已接受的项目意图。

2. 将已加载 Skill 的目录识别为 `SETUP_PROJECT_AGENTS_ROOT`，然后启动公开工作流：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" start \
     --target "$PWD"
   ```

   在 Windows 上使用相同参数调用 `setup_project_agents.ps1`。返回非零时停止。将返回的 `session`
   记录为 `SESSION`，将 `generated` 记录为 `GENERATED`，并记录 `request` 与 `source_root` 路径。
   本步骤完成的标志是只存在一个私有 session，且 start 尚未修改目标仓库。

3. 读取 request，确认它已捕获接受的 Rules、Skills、Agents 和 MCP 意图。任何选择不正确时，取消
   session，修正 canonical project input，再重新 start。Start 后保持 request 不变。

4. 在 `GENERATED/<target>` 下完成每个 `generation_requests` 条目，并保留完整 target 路径。从
   `source_root` 解析每项 blueprint，并使用匹配的编写契约：

   - 对 Rule target 应用 `write-agent-rule`；
   - 对 Skill target 应用 `write-agent-skill`；
   - 从 `source_root` 读取 `setup-matt-pocock-skills`，并在本工作流内对请求的 `docs/agents/` target
     执行其契约；不要将它作为独立 Skill 调用。

   使用当前仓库作为证据；除非用户要求重新配置，否则保留完整的项目自有内容。对于 Matt context，
   tracker 缺失时默认使用 Local Markdown，保留现有 triage mapping，并在仓库证据未建立实质不同的
   context 时使用 single domain context。本步骤完成的标志是 generated 目录恰好包含全部请求 target，
   且没有未声明路径。

5. Review Gate 通过后，完成同一个 session：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   在 Windows 上调用 `setup_project_agents.ps1`。只调用一次 `finish`。完成条件是退出码为零，且 JSON
   包含 `phase: finish` 和 `check: clean`。

6. 如果工作必须在 `start` 后、`finish` 前停止，取消 session：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" cancel \
     --session "$SESSION"
   ```

   `finish` 后不要调用 cancel；无论成功或失败，清理由 finish 负责。

## Review Gate

- [ ] Rules、Skills、Agents 和 MCP 都符合已接受的项目意图。
- [ ] 每个已配置的 Agent 都指向完整且匹配的项目自有 source。
- [ ] 每个生成的 Rule 和 Skill 都遵循其编写契约和当前仓库证据。
- [ ] Matt context 符合已接受的 tracker、triage 和 domain 决策。
- [ ] Request 未被修改，每个请求 target 都存在于 generated root 下。
- [ ] 生成的项目内容不包含 credential 或 secret。

## 停止条件

`start`、`finish` 或 `cancel` 失败时停止并原样报告错误。`finish` 失败后丢弃该 session，解决原因后
重新开始。Tracker、domain layout、能力声明、所有权冲突或生成输出仍未解决时，在 `finish` 前停止。
只使用公开的 `start`、`finish` 和 `cancel` 命令；selection、rendering、deletion、validation、
transaction、checking 和 session cleanup 由工作流负责。

## 结果

报告 finish 结果：固定的 source commit、启用的宿主、changed paths、external Skills、保留的项目
自有路径和 clean check 状态。要求维护者审查并提交报告的项目快照；其他开发者通过 clone 或 pull
获取该快照。
