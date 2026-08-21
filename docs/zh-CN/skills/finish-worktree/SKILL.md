---
name: finish-worktree
description: 通过闭合 Git contract 和已验证的历史、恢复及清理来完成 standalone Task Worktree、将一个 ticket 暂存到 Batch Worktree，或交付已 review 的 Ticket Batch。
---

# 完成 Worktree

在保留 checkpoint recovery 和无关本地状态的情况下完成一个 qualified worktree 生命周期。本 Skill
验证 evidence、收束 authorized history、执行一种 Git protocol、验证结果并执行 owned cleanup。
调用方保留 implementation、formal review、Ticket dependencies、tracker state 和 Issue completion。

## 建立完成上下文

1. 接受一个闭合 Finalization Contract，其 `mode` 必须准确为 `standalone-task`、
   `stage-ticket-into-batch` 或 `deliver-ticket-batch`。每种 mode 都提供 `source` worktree、branch、
   精确 `head` 和 `tree`、`creation_owner` 及 `scope_owner`；`target` checkout、branch、
   `expected_head` 和 `target_policy`；`evidence` fixed point、acceptance sources、review kind 和
   result、reviewed head 和 tree、verification commands 和 results 及 findings；`history_policy`
   和完整 owned range；recovery refs 及 current 和 next owners；authorized cleanup 和 retained
   state；以及一个 `authorized_outcome`。拒绝 unknown modes、cross-mode fields、missing values 和
   implicit remote authority。
2. 对于 `standalone-task`，要求 `history_policy=consolidate-checkpoints`、完整 unpublished
   checkpoint range、与 selected standalone procedure 匹配的 target policy、
   `evidence.review_kind=formal-review`，以及 `authorized_outcome` 准确为 `merge-locally`、
   `create-pull-request`、`keep-for-later` 或 `return-for-review`。`discard` 不属于该 contract。
3. 对于 `stage-ticket-into-batch`，要求以 worker-owned Ticket Task Worktree 为 source、Batch
   Worktree 为 target、其精确 ticket base 为 `expected_head`、
   `target_policy=exact-head-fast-forward-only`、worker self-review 和 required verification、
   `history_policy=consolidate-checkpoints`、controller recovery ownership，以及 matching
   authorized outcome。
4. 对于 `deliver-ticket-batch`，要求以 controller-owned Batch Worktree 为 source、final local
   checkout 为 target、immutable batch base 为 `expected_head`、
   `target_policy=exact-head-fast-forward-only`、current whole-batch review 和 full verification、
   `history_policy=preserve-ordered-task-commits` 及 ordered Task Commits 和 optional review tail、
   controller-owned recovery refs，以及 matching authorized outcome。
5. 重新推导所有 named Git identities、clean owned state、ancestry、ranges、publication、evidence、
   recovery 和 ownership。快照每个受影响 checkout 的 branch、`HEAD`、index tree、staged、unstaged
   和 untracked state。每次 mutation 前立即重新检查它依赖的所有事实。遇到 stale、ambiguous、
   published 或 unrelated state 时停止。

完成条件：证明一个完整 mode、owned history、精确 source 和 target、current evidence、authorized
recovery 和 cleanup，以及保留的 unrelated state。

## 选择一个结果

- **本地合并：** 将已记录本地 base branch 推进到 Task Commit，并在 creation owner 允许时清理。
- **创建 pull request：** 推送 Task Commit、创建 pull request，并保留 local task state。
- **保留备用：** 保留已收束的 task branch 和 worktree。
- **返回审查：** 将 Task Commit 的净结果写入 base working tree，同时保留其 `HEAD`、index 和无关
  changes。

对于 `standalone-task`，使用 contract 中已授权的 outcome。只有在另行收到明确 destructive
instruction 后才执行 discard，不接受 contract，也不收束 history；验证结果，并通过
expected-old-value checks 只删除 owned recovery refs。batch modes 只授权各自 matching local Git
outcome，不授权 remote 或 tracker action。

selected standalone outcome 决定 target。只读取匹配的 procedure：

- 本地合并：[`references/merge-local.md`](references/merge-local.md)
- 创建 pull request：[`references/create-pull-request.md`](references/create-pull-request.md)
- 保留备用：[`references/keep-for-later.md`](references/keep-for-later.md)
- 返回审查：[`references/return-for-review.md`](references/return-for-review.md)
- 明确丢弃：[`references/discard.md`](references/discard.md)

## 最终化已 Review 历史

1. 对于 `standalone-task`，刷新 target，并且只通过 current ancestry 或 equivalent-change evidence
   加 required verification 检测 **Already Delivered**。仅当 accepted evidence 决定 conflict
   behavior 时，才可将 moved target 合并到 task branch；synchronization 会使 review 失效，并将
   changed task 交回 implementation workflow。
2. 对于 `stage-ticket-into-batch`，要求 Batch Worktree `HEAD` 和 tree 等于精确 ticket base。对于
   `deliver-ticket-batch`，要求 final target `HEAD` 等于 immutable batch base。batch modes 不允许
   merge 或 rebase；movement、conflict 或 ancestry mismatch 会停止并保留 evidence。
3. 对于允许的 standalone conflict，在调用 `resolving-merge-conflicts` 前检查 accepted behavior 和
   双方。证据允许多个结果时，恢复 pre-merge task state 并请求决定。resolved synchronization 交回
   verification 和 formal review。
4. 验证 mode-specific evidence：standalone formal review 在精确 fixed point 和 source tree 上覆盖
   accepted task；staging 通过 worker self-review 以及 focused 和 repository verification 覆盖一个
   ticket；delivery 通过针对精确 Batch Worktree head 和 tree 的 full verification 和 whole-batch
   review 覆盖完整 Spec 和 frozen ticket set。不得存在 blocking finding。
5. 根据 accepted source 和 repository convention 推导 commit messages。只有这些来源允许实质不同
   含义时才询问。
6. 对于 standalone 或 staging，创建唯一 recovery ref，并针对精确 target 运行
   `scripts/consolidate_task_commit.py`。对于 batch delivery，保留每个 ordered per-ticket Task Commit，
   并且只将 optional review-fix checkpoint tail 收束为至多一个 Batch Review Commit。
7. 证明每个 created commit 都有 expected sole parent，tree 等于 reviewed 或 self-reviewed source
   tree，hooks 成功，且 worktree 干净。commit identity 改变后，必须有 byte-identical tree proof，
   review 和 verification 才能保持 current。

完成条件：standalone history 是一个已证明 Task Commit 或 Already Delivered；staging 是准确一个
Task Commit 追加到 Batch Worktree 且 recovery 已转移；delivery 保留 ordered Task Commits，并且至多
包含一个 tree-matching Batch Review Commit。

## 完成 Already Delivered

在不创建 Task Commit 的情况下完成这个 terminal branch：

- 应用 selected standalone procedure 的 **Already Delivered** exit。

重新检查 target、验证 outcome，并通过 expected-old-value checks 只删除 workflow-owned recovery
refs。cleanup failure 保留剩余 refs，并使 outcome 失败。

## 执行并验证

1. 对于 standalone outcome，只执行 selected procedure 及其 final rechecks、mutations、verification、
   recovery 和 handoff。
2. 对于 staging，将 Batch Worktree 准确 fast-forward 到 tree-matching Task Commit，证明 resulting
   identity 和 ancestry，将 recovery 转移给 controller，只执行 authorized Ticket Task Worktree
   cleanup，并返回 staging proof。
3. 对于 delivery，证明 ordered first-parent range，只收束 optional review tail，fast-forward unchanged
   target，运行 full target verification，证明 reviewed tree 和 unrelated state，并且只执行
   controller-authorized Git cleanup。
4. standalone 或 batch delivery 成功后，严格按授权删除或保留 recovery refs。staging 保留并转移
   refs。失败时保留所有 owned state，除非 attempted mutation 存在已证明且归属明确的精确 rollback。

完成条件：selected standalone outcome、staging handoff 或 reviewed batch delivery 及 final tree 已被
证明；否则返回准确 failed phase、preserved state 和 next owner。

## 安全与恢复

- 改写 history 或改变 target working state 前创建 recovery data。只恢复 failed mutation 拥有的
  state；保留所有 ownership 未证明的 state item。
- 不在 base 或 batch branch 使用 pull、stash、hard reset、clean、force push、rebase 或 merge
  commit。只改写 unpublished checkpoints，并保留 staged per-ticket Task Commits。
- 由 host 创建的 worktree 交给该 host 清理；只有 creation ownership 和 contract authority 已证明时，
  才移除 Git-created worktree 或 branch。

## 结果

返回 `status`（`complete`、`stopped` 或 `failed`）、`mode`、操作前后的 source 和 target identities、
适用 checkpoint 和 Task Commit ranges、可选 Batch Review Commit、final tree 的 evidence 和
verification、retained/transferred/deleted recovery refs、retained/removed worktrees 和 branches、
`next_owner` 及准确 next action。non-complete result 还包括 failed phase、mismatch 或 error，以及
preserved recovery state。staging result 标识 staged Task Commit 和 resulting Batch Worktree；
delivery result 为 controller 后续 tracker completion 提供 Git delivery proof。
