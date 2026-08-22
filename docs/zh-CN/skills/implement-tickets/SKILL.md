---
name: implement-tickets
description: 将剩余 agent-ready tickets 作为一个无人值守的串行 Ticket Batch 实施。让每个 fresh worker 负责完整的 Task Worktree 生命周期，为每个 ticket 保留一个 Task Commit，然后 review 并交付冻结的 batch。
---

# 实施 Tickets

这个 Procedure-led Skill 将一个冻结的 Ticket Batch 作为按依赖排序的流水线运行。controller 负责
frozen graph、claims、worker handoffs、batch evidence、delivery handoff 和 tracker completion。
每个 fresh worker 负责一个 ticket 的完整 Task Worktree 生命周期。

## 建立运行

1. 读取配置的 issue-tracker 指令、引用的 Spec 或父级来源，以及所请求 effort 中的每个 ticket。
   仅当上下文恰好标识一个 ticket 集合时才推断省略的 effort；否则询问。
2. 快照 identifiers、published order、statuses、blocking edges 和 acceptance criteria。仅包含
   agent-ready 工作；排除已完成、已拒绝、由人负责、因信息阻塞和已 claimed 的 tickets。
3. 要求每个 blocker 解析为一个 frozen ticket 或已完成的外部依赖，并要求该图无环。使用 published
   order 打破 readiness 平局。
4. 标识具名本地 target checkout 和 branch。要求已有 accepted local-delivery authority；如果 target
   或 outcome 仍有歧义，在 tracker 或 Git mutation 前只询问一次。
5. 在 controller 的 Agent context 中，从精确 target `HEAD` 调用 `create-worktree`，创建一个 qualified
   Batch Worktree 和 branch。将该 commit 和 tree 记录为 immutable batch base。

仅当 frozen graph、unchanged target、qualified Batch Worktree、authorized local delivery 和第一个
dependency-ready ticket 都已确定时，运行才准备就绪。如果仍有未完成 tickets 但没有 ready ticket，
报告其 unresolved edges，并在不 claim 的情况下进入 **停止与恢复**。

## 执行冻结的 Batch

仅当 frozen blocker 的 Task Commit 存在于 Batch Worktree 已记录的 ordered range 时，才视为满足该
blocker；tracker status 不是证明。每次准确处理一个 dependency-ready ticket。

1. 只要仍有 frozen ticket 未 staged，就完整读取并执行
   [`references/process-one-ticket.md`](references/process-one-ticket.md)。在其 `staged` exit 后，选择
   blockers 均已 staged 且最早发布的 ticket，然后重复。
2. 每个 frozen ticket 都 staged 后，完整读取并执行
   [`references/complete-run.md`](references/complete-run.md)。
3. 出现任何 non-complete result、missing decision 或 failed invariant 时，完整读取并执行
   [`references/stop-and-recovery.md`](references/stop-and-recovery.md)。这个 exit 优先于 staging 另一个
   ticket 或报告完成。

只有通过 `complete-run.md` 中的 completion criterion 才能完成。快照后发布的 tickets 不属于本次
运行，需要一次新运行。
