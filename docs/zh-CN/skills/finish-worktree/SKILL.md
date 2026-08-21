---
name: finish-worktree
description: 通过闭合 Git contract 和已验证的历史、恢复及清理来完成 standalone Task Worktree、将一个 ticket 暂存到 Batch Worktree，或交付已 review 的 Ticket Batch。
---

# 完成 Worktree

本 Procedure-led Skill 在保留 checkpoint recovery 和无关本地状态的情况下完成一个 qualified
worktree 生命周期。它验证 evidence、收束 authorized history、执行一种 Git protocol、验证结果并
执行 owned cleanup。调用方保留 implementation、formal review、Ticket dependencies、tracker state
和 Issue completion。

## 路由明确丢弃

只有在另行收到明确 destructive instruction 后，才读取并执行
[`references/discard.md`](references/discard.md)，不接受 Finalization Contract，也不收束 history。
不要进入任何 mode path。

## 建立完成上下文

读取并应用 [`references/finalization-contract.md`](references/finalization-contract.md)。只有其
公共契约和 current-state proof 通过时才继续。

## 运行一种模式

只读取并执行由 `mode` 选择的 reference：

| 模式 | 完整读取 |
| --- | --- |
| `standalone-task` | [`references/standalone-task.md`](references/standalone-task.md) |
| `stage-ticket-into-batch` | [`references/stage-ticket-into-batch.md`](references/stage-ticket-into-batch.md) |
| `deliver-ticket-batch` | [`references/deliver-ticket-batch.md`](references/deliver-ticket-batch.md) |

## 安全与恢复

- 改写 history 或改变 target working state 前创建 recovery data。只恢复 failed mutation 拥有的
  state；保留所有 ownership 未证明的 state item。
- 不在 base 或 batch branch 使用 pull、stash、hard reset、clean、force push、rebase 或 merge
  commit。只改写 unpublished checkpoints，并保留 staged per-ticket Task Commits。
- 由 host 创建的 worktree 交给该 host 清理；只有 creation ownership 和 contract authority 已证明时，
  才移除 Git-created worktree 或 branch。

## 结果

返回 `status`（`complete`、`stopped` 或 `failed`）、`mode`、操作前后的 source 和 target identities、
final tree 的 evidence 和 verification、retained/transferred/deleted recovery refs、
retained/removed worktrees 和 branches、`next_owner` 及准确 next action。non-complete result 还包括
failed phase、mismatch 或 error，以及 preserved recovery state。所选 mode reference 提供对应的
history 和 handoff 字段。
