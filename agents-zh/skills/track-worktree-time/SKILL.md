---
name: track-worktree-time
description: 当任务创建或复用链接 Git Worktree 来修改代码时使用。
---

# 记录 Worktree 时间

从任务启动开始，持续记录一个修改代码的 Worktree 任务，直至集成和最终交接。维护一份持久的 wall-clock
账本，使累计阶段时间与完整任务耗时保持一致。

## 前置条件

- 由主 Agent 为完整 Worktree 任务持有一份账本和一个任务 ID。
- 在创建 Worktree 或准备环境之前启动账本。
- 通过 `scripts/timing.py` 将运行时状态存入主机操作系统解析出的临时目录。
- 持续计时直到最终集成和交接，并累计反复发生的实现、Review、验证和测试阶段。

## 工作流

1. 运行 `python .agents/skills/track-worktree-time/scripts/timing.py start --task "<summary>"
   --repository "<repository>" --phase environment`，并保存返回的任务 ID。
2. 每次阶段切换时运行 `python .agents/skills/track-worktree-time/scripts/timing.py transition
   <task-id> <phase>`。同一阶段的多次进入会累计到一份账本中。
3. 等待用户、审批、服务或外部状态前运行 `pause <task-id>`，恢复活动后运行 `resume <task-id>
   <phase>`。
4. 使用 `report <task-id>` 获取进行中的快照。
5. 完成集成或所选结束方式后运行 `finish <task-id>`，并在最终交接中包含它生成的已对账 Markdown
   报告。

## 阶段

| 阶段 | 归属内容 |
| --- | --- |
| `environment` | Worktree 创建、环境设置、依赖准备和基线就绪 |
| `code-generation` | 代码编写、生成产物、实现修改和 Review 驱动的修订 |
| `review` | Diff 检查、代码 Review、反馈分析和多轮 Review |
| `verification` | 格式化、获准的 Fixer、Lint、分析、构建和静态检查 |
| `testing` | 单元、集成、端到端、回归和其他测试执行 |
| `integration` | 整理提交、Rebase、冲突处理、传回、合并和 Worktree 清理 |
| `waiting` | 用户输入、审批、外部服务和阻塞协调时间 |
| `other` | 用于完整 wall-clock 对账的其余任务活动 |

在主账本中记录主任务当前的 wall-clock 阶段。在最终说明中描述并行 Agent 活动，同时让完整任务耗时保持为
实际经过时间，而不是多个 Agent 工时之和。同一阶段包含多个区间时，报告其累计耗时。

## 故障恢复

计时命令失败时，保留最后一份有效账本，记录当前 UTC 时间戳，根据 JSON 状态恢复账本，并把恢复区间计入
`other`。`report` 确认所有已记录区间与完整 wall-clock 时间完成对账后，再结束任务。

## 验证

- 确认任务 ID 在系统临时目录中对应一份 JSON 账本。
- 确认每次阶段切换都在同一时间戳结束前一阶段并开始后一阶段。
- 确认累计阶段耗时等于完整任务耗时。
- 确认未使用的阶段显示为 `not applicable`。

## 结果

报告任务开始和完成时间、每个阶段的耗时、完整任务耗时、并行活动和所有计时恢复情况。对最终回复进行本地化
时，保留 `finish` 生成的阶段数值。
