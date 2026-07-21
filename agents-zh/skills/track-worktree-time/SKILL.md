---
name: track-worktree-time
description: 当任务创建或复用链接 Git Worktree，或需要根据稳定的 Agent Session 报告耗时、Token 消耗、模型活动、工具活动或 API 等价估算费用时使用。
---

# 记录 Worktree 任务指标

准备链接 Worktree 前创建一份任务凭据，任务完成后报告耗时和可归因的消耗。耗时、Token/费用和工具
活动是彼此独立的证据；某一项拿不到，不等于其他可用指标也拿不到。不要维护人工阶段切换；各项指标
应在任务结束后事后分析。

## 快速决策

| 现有证据 | 操作 |
| --- | --- |
| 新建链接 Worktree 的任务 | 准备前运行 `start` 并保存任务 ID。 |
| 还有一个可归因的 Session | 运行 `attach`；只有该 Session 在 `start` 后专为本任务创建时才使用 `--entire-session`。 |
| 活跃的 schema-2 凭据 | 用 `report` 查看快照，或在选定的完成节点运行一次 `finish`。 |
| 凭据缺失、已关闭或为 schema-1 | 如实保留耗时限制，再用稳定 Session ID 运行 `usage`。 |
| Tokscale 不可用或超时 | 立即返回 Codex 日志中的 Token 总量，并把费用标为不可用。 |

## 工作流

1. 准备 Worktree 前运行 `start --task "<summary>" --repository "<repository>"
   --worktree "<intended-worktree>"`。Codex 会优先使用 `CODEX_THREAD_ID`；若环境变量为空，则同时传入
   `--client codex --session-id <id>`。两者都没有时，应索取稳定 Session ID，不得猜测最新日志。
2. 每个额外且可归因的 Session 运行一次 `attach <task-id>`。参与者没有稳定 ID 时，运行
   `gap <task-id> --label "<participant>" --reason "<reason>"`。
3. 集成或选定的完成节点结束后运行 `finish <task-id>`，并在交接中附上 Markdown 报告。`finish` 会关闭
   统计边界，因此最终回复的生成不会计入报告。
4. 无法可靠恢复耗时时，不要事后补建凭据。改用不依赖凭据的消耗统计路径：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/track-worktree-time/scripts/task-metrics.ps1 usage --client codex --session-id <id>
```

在 POSIX 上将包装脚本换成
`sh .agents/skills/track-worktree-time/scripts/task-metrics.sh`。两个包装脚本都会调用 Python 3.11+
的确定性核心 `scripts/timing.py`。

## 消耗恢复

`usage` 根据 Codex Session 日志的起止日期限制 Tokscale 扫描范围，并从原始
`--json --group-by client,session,model` 结果中按 Session ID 的精确后缀筛选。它不需要任务凭据，
也绝不能把整个 Session 的消耗说成任务耗时。

如果 Tokscale 失败，`usage` 只读取该 Codex Session 最新一条累计 `token_count` 事件。返回这些
Token 分类，来源标为 `codex-log`，API 等价估算费用标为不可用，原有耗时结论保持不变。如果失败与
沙箱有关且可以申请权限，应在沙箱外用同一个包装命令重试一次以恢复 Tokscale 费用；不要反复冷扫描。

## 指标契约

- `wall-clock` 是凭据起止之间的实际耗时。
- schema-2 的 Token、费用和模型活动，是已显式登记 Session 的结束值减基线值。单独运行 `usage`
  得到的是整个 Session 的消耗，必须明确标注。
- `model activity` 和 `tool activity` 都是累计时长，可能与 wall-clock 重叠。
- 日志缺失、调用未闭合、归因缺口和无法对账的快照必须明确保留。
- 费用必须标为 Tokscale `API 等价估算费用`，不得称为实际账单。

## 隐私与输出

Transcript 只能临时读取。仅保存计数、时长、标识符和诊断；不得保存 Prompt、Response、Command 或
工具输出。不得运行 Tokscale Summarizer、任务聚类、提交或网络发布功能。

耗时、消耗和工具活动必须分开报告。脚本保留精确整数；面向用户展示 Token 时，中文用“万”为单位，
英文用“k”为单位。始终说明 Token 来源、费用是否可用、已登记 Session、归因缺口、诊断和采用的恢复路径。

## 常见错误

| 错误判断 | 正确处理 |
| --- | --- |
| “匹配到的是旧凭据，所以消耗不可用。” | 报告旧凭据能提供的耗时，并独立运行 `usage`。 |
| “`CODEX_THREAD_ID` 为空，所以稳定 Session 不存在。” | 索取或接受显式的 `--client` 与 `--session-id`。 |
| “现在补建凭据就能恢复之前的耗时。” | 不得伪造边界；耗时标为不可用，同时恢复消耗。 |
| “Tokscale 费用失败，所以 Token 也拿不到。” | 返回 Codex 日志中的 Token，只把费用标为不可用。 |

出现以下任一情况时，不得直接宣布指标不可用，必须先纠正处理路径：

- 只是缺少 `CODEX_THREAD_ID`；用户仍可能提供稳定 Session ID。
- 耗时不可用，但稳定 Session ID 仍可用于恢复消耗。
- Tokscale 失败，但匹配的 Codex 日志仍包含累计 Token 事件。
- 正在考虑为已经发生的工作补建凭据。
