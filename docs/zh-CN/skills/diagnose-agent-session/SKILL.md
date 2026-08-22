---
name: diagnose-agent-session
description: 诊断一个稳定 Agent Session 中疑似异常的 Token 或 API 等价估算费用消耗、模型或工具活动、子 Agent 协作、等待或未完成调用。
---

# 诊断 Agent Session

对当前 turn 和完整的稳定 Session 进行事后诊断，不保留任务凭据。公共 wrapper 调用及其受控沙箱重试
是唯一固定流程；按照判断框架进行解读。

## 判断框架

将 wrapper 报告视为证据记录。将其与任务的预期工作量和适用的并发上限进行比较。明确发现、失败或
不完整的证据，以及不符合该上下文的行为可以支持异常结论；原始 Token 或调用量本身只用于描述。

保留每个已报告问题和不可用表面。不得通过推断任务边界、调用结果、Token 计数、费用或正常结论来填补
证据缺口。某个表面不可用并不会使仍然可用的证据失效。

## 获取证据

把 Tokscale client 和稳定 Session ID 作为一对值来确定。对于 Codex，仅当 `CODEX_THREAD_ID` 可用时
才能同时省略两者。如果只提供了其中一个值，或者无法确定两者，则应索取两者，不得选择最新日志。

除非请求明确只选择 `turn` 或 `session`，否则使用 `--scope both`。运行当前平台支持的一个分支：

- POSIX：

  ```sh
  sh .agents/skills/diagnose-agent-session/scripts/task-metrics.sh diagnose --scope both --client <client> --session-id <id>
  ```

- 使用 PowerShell 的 Windows：

  ```powershell
  powershell -ExecutionPolicy Bypass -File .agents/skills/diagnose-agent-session/scripts/task-metrics.ps1 diagnose --scope both --client <client> --session-id <id>
  ```

两个 wrapper 都要求 Python 3.10+。运行一次选定的 wrapper。当沙箱访问导致 Tokscale 失败且可以审批时，
在沙箱外重试同一 wrapper 一次。随后带着完整、部分或不可用报告回到判断框架。

## 证据契约

使用 wrapper 报告中的 Tokscale 整个 Session 用量和 `API 等价估算费用`；对于 Codex，还使用它提供的
当前 turn、本地工具和协作证据。汇总的模型与工具时长可能和经过时间重叠；生命周期计数是下界，子
Agent Token 消耗需要稳定映射。临时读取转录内容，不持久化 prompt、response、工具输入或工具输出。

## 退出条件

以 wrapper 报告和基于判断框架的简洁健康结论完成。如果允许的尝试或重试后证据仍不完整，则部分或
不可用报告就是最终结果。缺少标识符或平台不受支持时，在运行 wrapper 前停止；Tokscale client 不受
支持时报告原始错误，不得替换为其他 client。
