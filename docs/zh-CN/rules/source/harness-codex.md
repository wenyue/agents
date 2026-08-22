# Codex Harness 适配

强度：`Default`

适用范围：Codex 专用的 Subagent 工具、`functions.exec` 编排机制，以及存在运行中 Agent 时的
有界等待机制。

## 权限边界

- 由当前 Skill 或任务决定为什么委派 Agent 以及必须产出什么结果；本 Rule 不改变用户授权、Rule
  优先级或完成标准。

## Subagent 工具映射

- 使用 `spawn_agent` 启动一项具体且可独立产生价值的任务。后续 Subagent 工具使用其返回的任务名或
  agent 标识符。
- 使用 `send_message` 补充上下文但不启动新 turn。空闲 Subagent 需要执行新的有界任务时，使用
  `followup_task`。
- 仅在确实应停止当前工作时使用 `interrupt_agent`。仅为有意的状态检查使用 `list_agents`，不得形成
  轮询循环。

## JavaScript 编排

- 在 `functions.exec` 中，对已选定为并发执行的独立调用进行映射：部分结果仍有用时使用
  `Promise.allSettled`，必须获得所有结果时使用 `Promise.all`。当前工具 schema 或适用的
  Skill 禁止并发执行时，保持调用串行。

## 等待 Agent

- 将 `wait_agent` 视为事件订阅，而不是轮询。仍有可推进的父 Agent 工作时继续推进；已完成 Agent 的
  mailbox 更新会在父 Agent 的下一个 turn 到达。
- 确实处于空闲状态且仍有 Agent 在运行时，在当前 Harness 和运行时允许的范围内，以 300000–600000
  毫秒为一个有界区间调用 `wait_agent`。长订阅会在 mailbox 有活动时立即唤醒，延迟与短订阅相同，
  因此更短的轮询只会增加调用次数，不能缩短响应时间。
- `wait_agent` 超时只表示该区间内没有 mailbox 更新。不得仅因上一区间超时而缩短下一个等待区间。
