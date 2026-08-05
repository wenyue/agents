---
name: setup-project-agents
description: Use when initializing or updating a repository with the Agents Rules, Skills, and Agents snapshot.
---

# Setup Project Agents

为一个目标仓库运行由脚本支持的 setup 工作流。Agent 选择平台和目标尚未定义的模型、创作请求的
项目专属内容、审查内容并消费结构化结果；脚本负责所有确定性 setup 操作。

## 所有权

不要自行重建来源选择、发现、覆盖、删除、验证、事务、检查、汇总或清理行为。调用公开工作流，
并把它的结果作为权威。宿主信任、插件缓存、插件自带 Hook 和外部工具安装不属于这个工作流。

## 受管资产

Agent 只能编辑这些工作流输入：

- 用户明确修改的模型值，以及返回的 `models.json` 中仍为空的请求模型值；
- 返回的 `generated` 目录下 `generation_requests` 列出的三个 Rule 和两个 Skill 目标。

不要编辑 `request.json`，也不要创建另一个 models 或 generated 根目录。

## 前置条件

- 从目标仓库根目录开始，并把已加载 Skill 的目录识别为 `SETUP_PROJECT_AGENTS_ROOT`。
- 只询问一次要启用的平台。存在 `.agents/config.json` 时，除非用户修改，否则使用其中的平台；
  不存在时默认使用 Codex、Cursor 和 Copilot。

## 协调工作流

1. 使用 `start`、目标路径和每个所选平台调用平台 wrapper：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" start \
     --target "$PWD" --platform codex --platform cursor --platform copilot
   ```

   Windows 使用相同参数调用 `setup_project_agents.ps1`。结果非零时停止。从单个 JSON 结果中把
   `session` 记录为 `SESSION`，并使用其中返回的 request、models、generated 和 source 路径。

2. 读取 `SESSION/request.json` 和返回的 `models.json`。start 会保留现有平台 Agent 配置中的
   模型设置。除非用户明确修改，否则保留每个预填值；根据请求的 agent 和 `model_key` 填写仍为空的
   必填 `model`。Codex 可选的 `model_reasoning_effort` 和 `sandbox_mode` 是字符串；Cursor
   可选的 `readonly` 是布尔值。

3. 把返回的 `source_root` 解析为 `SOURCE_ROOT`。读取
   `SOURCE_ROOT/setup-assets/skills/write-rule/SKILL.md` 和
   `SOURCE_ROOT/setup-assets/skills/write-skill/SKILL.md` 中完整的创作契约。应用列出的 Blueprint，
   并在返回的 generated 目录下准确写入五个 `generation_requests` 目标。

4. 审查关口通过后，只使用会话路径和 `finish` 调用同一个 wrapper：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   不要直接调用内部 prepare/apply/check 命令。

5. 成功 start 后，如果工作流无法到达 finish，只使用 `--session "$SESSION"` 调用 `cancel`。

## 停止条件

start、finish 或 cancel 发生任何错误时停止并准确报告。不要修复脚本拥有的状态、逐文件选择覆盖
关系、修改请求、向 finish 传递未请求的路径或手动删除会话；解决报告的原因后重新 start。

## 审查关口

- [ ] 阅读每个完整生成 Rule 和 Skill；确认它遵循创作契约并使用当前目标证据。
- [ ] 阅读填写完成的 models 文件；确认每个请求的 agent/平台都有非空模型。
- [ ] 确认请求未改变，并且 generated 目录准确包含请求的五个文件。

## 验收关口

- [ ] 运行一次 finish；只有其 JSON 报告 `phase: finish` 和 `check: clean` 时才接受 setup。

## 验证与结果

报告 finish 返回的字段：固定来源 commit、所选平台、变更路径、第三方 Skill、保留的项目自有路径
和 check 状态。失败时报告脚本的准确错误；没有干净的 finish 结果时，不要推断 setup 完全或部分
成功。
