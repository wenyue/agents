---
name: setup-project-agents
description: 当需要使用 Agents Rules、Skills、Agents 和 Matt 仓库上下文快照初始化或更新仓库时使用。
---

# 设置项目 Agents

为一个目标仓库运行脚本驱动的 setup 工作流。该工作流始终启用 Codex、Cursor 和 Copilot，编写
项目拥有的快照，配置内置 Matt Skills，并在一次已审查事务中应用全部内容。脚本负责确定性 setup
行为；Agent 只负责请求中列出的编写决策。

## 所有权

不要重新实现来源选择、发现、覆盖、删除、验证、事务、检查、摘要或清理行为。调用公开工作流，
并将其结果视为权威。宿主信任、插件缓存、内置 Hooks 和外部工具安装不属于此工作流。

## 受管资源

Agent 只能编辑以下工作流输入：

- 用户明确修改的模型值，以及报告的 `models.json` 中仍为空的值；
- `generation_requests` 列出的八个目标：三个 Rules、两个 Skills，以及
  `docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md` 和
  `docs/agents/domain.md`。

将每个仓库相对 `target` 原样写入报告的 `generated` 目录。例如，
`.agents/rules/00-project-tools.md` 应写入 `GENERATED/.agents/rules/00-project-tools.md`，
`docs/agents/domain.md` 应写入 `GENERATED/docs/agents/domain.md`。不要编辑 `request.json`，也不要
创建另一份 models 或 generated 根目录。

三个 `docs/agents/` 文件和 `AGENTS.md` 指针是团队共享、可由人工编辑的仓库配置。除非用户明确
确认重新配置，否则应保留完整的现有文档；它们不是可丢弃的生成缓存。

## 前置条件

- 从目标仓库根目录开始，并将已加载 Skill 的目录识别为 `SETUP_PROJECT_AGENTS_ROOT`。
- 每次运行都启用 Codex、Cursor 和 Copilot。

## 对齐工作流

1. 使用 `start` 和目标路径调用平台 wrapper：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" start \
     --target "$PWD"
   ```

   在 Windows 上使用相同参数调用 `setup_project_agents.ps1`。非零结果时停止。从单个 JSON 结果中
   将 `session` 记录为 `SESSION`，使用其中报告的 request、models、generated 和 source 路径；
   将报告的 generated 路径记录为 `GENERATED`。

2. 读取 `SESSION/request.json` 和报告的 `models.json`。start 会保留现有平台 Agent 配置中的模型
   设置。除非用户明确修改，否则保留所有预填值；并在请求的 Agent 和 `model_key` 处填写仍为空的
   必填 `model`。Codex 的可选 `model_reasoning_effort` 和 `sandbox_mode` 值为字符串；Cursor 的可选
   `readonly` 值为 Boolean。

3. 将报告的 `source_root` 解析为 `SOURCE_ROOT`。完整读取
   `SOURCE_ROOT/skills/write-rule/SKILL.md`、
   `SOURCE_ROOT/skills/write-skill/SKILL.md` 和
   `SOURCE_ROOT/skills/setup-matt-pocock-skills/SKILL.md` 的编写契约。应用 Rule 和 Skill Blueprints，
   然后在同一 setup 工作流中配置三个 Matt 文档；不要再把 `setup-matt-pocock-skills` 作为第二个
   Skill 调用。选择 issue tracker 时，使用本工作流下述默认值，而不是 vendored Skill 的上游
   默认值。

4. 按 Matt setup 契约探索目标仓库。除非用户要求更改，否则保留任何完整的现有
   `docs/agents/*.md` 文档。否则：

   重新生成前，将任何现有生成式 Rule 或 Skill 目标作为项目证据读取。出现分歧时依次采用：当前
   Blueprint 契约、当前仓库证据、之前生成的内容。始终重新生成请求的目标；不要仅因为旧输出已
   存在就原样复制。

   - 对缺失或不完整的 issue-tracker 配置默认使用 Local Markdown，不受 Git remote 影响。只有用户
     明确要求时才使用 GitHub、GitLab 或其他 tracker；读取对应的同级 seed，或编写已确认的自定义
     工作流。Git remote 是仓库证据，不代表允许使用它的 issue tracker；
   - 存在 triage-label mapping 时沿用；不存在时使用内置的五角色默认值；
   - 没有 monorepo 信号时使用 single-context domain layout；当 workspace 文件或多个源 package
     表明确实存在不同上下文时，展示 single-context 和 multi-context 选择并等待确认。

   将全部八个 `generation_requests` 目标原样写入 `GENERATED/<target>`，保留目标的每一段路径。
   issue-tracker 请求在 catalog 中以 Local Markdown seed 作为 blueprint。用户明确选择 GitHub、
   GitLab 或其他 tracker 时，读取对应的同级 seed 或已确认的自定义工作流，并写入相同的请求目标。

5. Review Gate 通过后，只使用 session 路径调用同一个 wrapper 的 `finish`：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   不要直接调用内部 prepare/apply/check 命令。

6. 如果工作流必须在 start 成功后、调用 finish 前停止，只使用 `--session "$SESSION"` 调用
   `cancel`。finish 返回后不要调用 cancel：无论成功还是失败，session 清理都由 finish 负责。

## 停止条件

任何 start、finish 或 cancel 错误都应立即停止并原样报告。finish 出错后不要调用 cancel，也不要
复用该 session；解决报告的原因后重新 start。显式 tracker 选择或 monorepo layout 选择尚未解决时，
应在 finish 前停止。不要修复脚本拥有的状态、选择逐文件覆盖范围、更改 request、向 finish 传入
未请求路径或手动删除 session。

## Review Gate

- [ ] 完整读取每个生成的 Rule 和 Skill；确认其遵循编写契约并使用目标仓库的当前证据。
- [ ] 读取全部三个 Matt 文档；确认它们符合已选择的 tracker、label 和 domain-layout 决策，并保留
      现有用户拥有的内容。
- [ ] 确认 `AGENTS.md` 将只包含一个指向全部三个文档的 `## Agent skills` 区块。
- [ ] 读取已填写的 models 文件；确认每个请求的 Agent/platform 都有非空 model。
- [ ] 确认 request 未被修改，且 `GENERATED` 恰好包含八个请求目标路径，没有未声明目录。
- [ ] 确认 Git 未忽略任何请求目标，并且生成的项目文件不包含 credential 或 secret。

## Acceptance Gate

- [ ] 只运行一次 finish；仅当 JSON 报告 `phase: finish` 和 `check: clean` 时接受 setup。

## 验证与结果

报告 finish 返回的字段：固定 source commit、启用的平台、changed paths、external Skills、保留的
项目自有路径和 check 状态。要求仓库维护者审查并提交报告的 changed paths；其他开发者通过 clone
或 pull 获得共享快照，无需逐人运行 setup。Session 文件、缓存、日志和凭据留在仓库外。失败时原样
报告脚本错误；没有 clean finish 结果时，不得推断 setup 已成功或部分成功。
