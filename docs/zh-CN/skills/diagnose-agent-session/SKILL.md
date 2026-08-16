---
name: diagnose-agent-session
description: 当一个稳定 Agent Session 的 Token 消耗、模型活动、工具调用、子 Agent 协作、等待行为、未完成调用或 API 等价估算费用可能异常时，用它进行诊断。
---

# 诊断 Agent Session

对当前 turn 和完整的稳定 Session 运行一次事后诊断。使用报告区分异常 Agent 行为与证据缺失。
本工作流不保留任务凭据。

## 运行诊断

1. 把 Tokscale client 和稳定 Session ID 作为一对值来确定。存在 `CODEX_THREAD_ID` 时，Codex
   可以同时省略两者。如果只提供了其中一个值，向用户索取两者。
2. 只运行一次与平台匹配的公共 wrapper。在使用 PowerShell 的 Windows 上，运行：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/diagnose-agent-session/scripts/task-metrics.ps1 diagnose --scope both --client <client> --session-id <id>
```

POSIX 平台使用：

```sh
sh .agents/skills/diagnose-agent-session/scripts/task-metrics.sh diagnose --scope both --client <client> --session-id <id>
```

两个 wrapper 都要求 Python 3.10+。在其他平台上，报告没有受支持的公共 wrapper。当 Tokscale
故障由沙箱访问导致且审批可用时，在沙箱外重试同一 wrapper 一次。
只有请求明确只需要一个边界时，才使用 `--scope turn` 或 `--scope session`。

3. 把 wrapper 输出视为证据记录。解释观察到的消耗、工具调用和协作是否符合任务上下文。根据明确
   发现、失败或不完整证据、适用的并发上限以及任务预期工作判断异常；仅把原始调用量视为描述性信息。

完成要求包含 wrapper 报告和简洁的健康结论。在交接中保留每个已报告问题和不可用表面。

## 证据契约

- 将当前 turn 和整个 Session 的 input、cached input、cache write、output、reasoning 和 total
  Token 计数报告为精确整数。根据 Codex 日志的累计快照推导当前 turn Token；当前 turn 的费用和
  模型活动标记为不可用，不做估算。
- 将整个 Session 的费用标为 Tokscale `API 等价估算费用`。可用时报告 Session 跨度和 Tokscale
  模型活动。汇总的模型和工具时长可能与经过时间重叠。
- 对 Codex，将已记录工具调用与其输出配对，并报告每个工具的开始、完成、失败、未完成调用、汇总
  时长、最长时长和连续相同调用。
- 报告 spawn、wait、list、message、follow-up 和 interrupt 协作调用。根日志提供证据时，重建
  spawn 成功与失败、Agent 终止状态、观察到的 Agent 存活峰值、wait timeout，以及没有观察到存活
  Agent 时的 wait。将观察到的生命周期计数视为下界；没有稳定子 Session 映射时，不推断子 Agent
  Token 消耗。
- 临时读取转录内容。不持久化 prompt、response、工具输入或工具输出。
- 对其他 Tokscale client，报告消耗并将本地工具诊断标记为不可用。
- 日志缺失、Tokscale 故障、未完成调用和费用不可用必须明确说明；某项不可用时仍要保留已经取得的证据。

Tokscale 数据行按 client 和 Session ID 的精确后缀筛选。Codex 日志日期可用时据此限制扫描范围；
其他 client 不限制日期。当前 turn 从最新记录的用户消息边界开始。工具调用统计排除诊断 wrapper
自身的调用。Codex 的 Tokscale 查询失败时，只从匹配日志恢复最新的累计 `token_count` 总数，并把
费用标记为不可用。

## 停止条件

- 无法确定 client 和稳定 Session ID 这一对值时，应向用户索取两者；不得推断最新日志。
- Tokscale 不支持传入的 client 时，应报告原始错误，不得擅自替换 client。
- 证据不完整时返回生成的部分或不可用报告；不得编造正常结论、任务边界、调用结果、Token 计数或费用。
