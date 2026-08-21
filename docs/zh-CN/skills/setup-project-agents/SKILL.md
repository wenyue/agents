---
name: setup-project-agents
description: 当需要跨 Codex、Cursor 和 Copilot 初始化或对齐仓库的 Rules、Skills、Agents 或 MCP 时使用。
---

# 设置项目 Agents

本 Hybrid Skill 对齐一个仓库的 Rules、Skills、Agents 和 MCP。Agent 决定已接受的能力意图；公开
工作流负责确定性的发现、渲染、验证、事务和清理。

## Judgment Frame

将四类能力视为平级。在 `start` 前检查其 canonical inputs，并且只有用户要求变更时才修改。

| 能力 | Canonical project input | Setup 职责 |
| --- | --- | --- |
| Rules | `.agents/rules/` 下的项目自有 source，以及请求生成的 Rule target | 保留项目 Rules，并向各宿主交付 setup 受管的 Rules。 |
| Skills | `.agents/skills/` 下的项目自有目录、请求生成的 Skill target，以及 `.agents/config.json` 的 `skills` 声明 | 保留项目 Skills，并安装请求生成或外部来源的 Skills。 |
| Agents | `.agents/agents/` 下的项目自有 source，以及 `.agents/config.json` 的 `agents` 声明 | 保留 Agent source，生成声明的宿主 adapter，并安装 catalog 声明的 Codex Plugin Agent 默认项。 |
| MCP | `.agents/config.json` 的 `mcp` 声明 | 生成声明的宿主原生 MCP 条目，不存储 secret 值。 |

使用随插件发布的 `.agents/config.json` schema。配置的 Agent source 是与 ID 匹配的
`.agents/agents/<id>.md`；每个 MCP 条目只声明 `url` 或 `command` 之一。按顺序执行的 `when`/`set`
override 可选择 Harness 和 Platform；可选的 MCP readiness 可限定或替换推断出的静态检查。

项目自有 canonical input 始终是可编辑的项目内容。Setup 生成的文件和结构化字段由 setup 拥有。
Plugin Rules、Skills、MCP，以及原生 Cursor 和 Copilot Plugin Agents 不属于此项目工作流。Setup
只把 catalog 声明的 Codex Plugin Agent 默认项安装为受管资产；它们绝不会成为 Project Agent 声明。

Matt repository context 是独立的项目自有前置条件。本工作流既不生成也不拥有
`docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md`、`docs/agents/domain.md`，或指向
这些文件的 `## Agent skills` 区块。

## 事务工作流

1. 从目标仓库根目录验证 Matt repository setup 已完成：三个 `docs/agents/` context 文件均存在，且
   `AGENTS.md` 或 `CLAUDE.md` 包含匹配的 `## Agent skills` 区块。任何部分缺失时，在 `start` 前停止，
   并告诉用户在该仓库中显式调用 `setup-matt-pocock-skills`。不要代替该 Skill 重复提问或选择 issue
   tracker。只有 Matt setup 报告完成后，才再次调用 `setup-project-agents` 继续。

2. 确定 Rules、Skills、Agents 和 MCP 各自表达已接受的项目意图。

3. 将已加载 Skill 的目录识别为 `SETUP_PROJECT_AGENTS_ROOT`，然后启动公开工作流：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" start \
     --target "$PWD"
   ```

   在 Windows 上使用相同参数调用 `setup_project_agents.ps1`。返回非零时停止。将返回的 `session`
   记录为 `SESSION`，将 `generated` 记录为 `GENERATED`，并记录 `request` 与 `source_root` 路径。
   只有一个私有 session 存在且 target 保持不变时才继续。

4. 读取 request，确认它已捕获接受的 Rules、Skills、Agents 和 MCP 意图。任何选择不正确时，取消
   session，修正 canonical project input，再重新 start。Start 后保持 request 不变。

5. 在 `GENERATED/<target>` 下完成每个 `generation_requests` 条目，并保留完整 target 路径。从
   `source_root` 解析每项 blueprint，并使用匹配的编写契约：

   - 对 Rule target 应用 `write-rules-and-skills` 的 Rule 分支；
   - 对 Skill target 应用 `write-rules-and-skills` 的 Skill 分支。

   Request 恰好包含五个 generated target：

   - `.agents/rules/00-project-tools.md`
   - `.agents/rules/01-project-rules.md`
   - `.agents/rules/02-project-structure.md`
   - `.agents/skills/change-set-verification/SKILL.md`
   - `.agents/skills/worktree-environment-setup/SKILL.md`

   Matt context 永远不会成为 generation request。

   使用当前仓库证据；除非用户要求重新配置，否则保留完整的项目自有内容。只有 `GENERATED` 恰好
   包含全部请求 target 且没有未声明路径时才继续。

6. Review Gate 通过后，恰好完成同一个 session 一次：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   在 Windows 上调用 `setup_project_agents.ps1`。完成条件是退出码为零，且 JSON 包含
   `phase: finish` 和 `check: clean`。

7. 如果工作必须在 `start` 后、`finish` 前停止，取消 session：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" cancel \
     --session "$SESSION"
   ```

   `finish` 后不要调用 cancel；无论成功或失败，清理由 finish 负责。

## Review Gate

- [ ] Rules、Skills、Agents 和 MCP 都符合已接受的项目意图。
- [ ] Matt repository setup 在 `start` 前已完成，并保持为项目自有内容。
- [ ] 每个已配置的 Agent 都指向完整且匹配的项目自有 source。
- [ ] 每个生成的 Rule 和 Skill 都遵循其编写契约和当前仓库证据。
- [ ] Request 未被修改，每个请求 target 都存在于 generated root 下。
- [ ] 生成的项目内容不包含 credential 或 secret。

## 停止与恢复

`start`、`finish` 或 `cancel` 失败时停止并原样报告错误。`finish` 失败后丢弃该 session，解决原因后
重新开始。能力声明、所有权冲突或生成输出仍未解决时，在 `finish` 前停止。
只使用 `start`、`finish` 和 `cancel`；其实现负责 selection、rendering、deletion、validation、
transaction、checking 和 session cleanup。

## 结果

报告 finish 结果：固定的 source commit、启用的宿主、changed paths、external Skills、保留的项目
自有路径和 clean check 状态。要求维护者审查并提交报告的项目快照；其他开发者通过 clone 或 pull
获取该快照。
