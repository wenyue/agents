---
name: report-session-usage
description: 需要报告 Tokscale 支持的一个稳定 Agent Session 的 Token 消耗或 API 等价估算费用时使用。
---

# 报告 Agent Session 消耗

任务完成后只运行一次命令，并返回精简的消耗报告。本工作流不创建任务凭据，不统计耗时、模型活动或
工具活动，也不要求 Agent 维护 Worktree 生命周期记录。

## 工作流

1. 确定 Tokscale client 和稳定 Session ID。任何受支持的 client 都可以显式传入这两个值；Codex
   存在 `CODEX_THREAD_ID` 时可以省略。稳定 ID 未知时不得猜测最新 Session。
2. 在当前平台运行一次 wrapper：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/report-session-usage/scripts/task-metrics.ps1 usage --client <client> --session-id <id>
```

POSIX 平台使用：

```sh
sh .agents/skills/report-session-usage/scripts/task-metrics.sh usage --client <client> --session-id <id>
```

两个 wrapper 都会调用 Python 3.11+ 的确定性核心 `scripts/timing.py`。

3. 在交接回复中原样引用 wrapper 输出。不得计算时间、重建任务边界、聚合其他 Session、重新排版数值，
   也不要再写第二份指标摘要。

## 消耗恢复

脚本按指定 client 和 Session ID 的精确后缀筛选 Tokscale
`--json --group-by client,session,model` 输出。Codex 日志日期可用时据此限制扫描范围；其他 client
不限制日期，避免漏掉较早的 Session。结果代表整个 Session 的消耗，不代表单个任务。

如果 Codex 的 Tokscale 查询失败，脚本只读取匹配 Codex Session 中最新的累计 `token_count` 事件，
返回其中的 Token 分类，来源标为 `codex-log`，API 等价估算费用标为不可用。其他 client 没有本 Skill
提供的日志回退路径，应明确返回不可用。如果失败由沙箱权限引起且可以申请授权，只在沙箱外重试同一
wrapper 一次；不得反复执行冷扫描。

## 指标契约

- input、cached input、cache write、output、reasoning 和 total Token 都使用精确整数。
- 费用必须标为 Tokscale `API 等价估算费用`，不得称为实际账单。
- 日志缺失和费用不可用必须作为问题明确说明；某项不可用时仍要保留已经取得的 Token 证据。
- 不得报告实际耗时、任务时长、模型活动、工具活动、任务凭据、Session 登记或归因缺口。

## 输出

wrapper 固定生成以下可直接回复的格式：

```text
### Usage Metrics
- Scope: whole session
- Tokens: <exact categories | unavailable>
- Estimated API-equivalent cost: <amount | unavailable>
- Problems: <concise evidence or recovery explanation>
```

Token 和费用证据完整时省略 `Problems`。

## 停止条件

- client 或稳定 Session ID 不可用时，应向用户索取两者，不得猜测。
- Tokscale 不支持传入的 client 时，应报告原始错误，不得擅自替换 client。
- Tokscale 和适用的 client 专属回退路径都无法提供消耗证据时，返回脚本生成的不可用结果，不得编造数值。
