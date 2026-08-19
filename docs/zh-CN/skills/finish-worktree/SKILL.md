---
name: finish-worktree
description: 完成一个 standalone Task Worktree 或已接受的 Ticket Batch。验证 formal-review evidence，将 checkpoints 收束为 Task Commits，在 Batch Worktree 上暂存 per-ticket commits，并安全交付或保留准确的已 review 历史。
---

# 完成 Worktree

在保留 checkpoint 恢复能力和 base 既有状态的前提下，完成 standalone Task Worktree 或 Ticket Batch
生命周期。负责 review-evidence validation、Task Commit 收束、batch staging、结果选择、授权、交付、
验证、恢复和生命周期清理；implementation、formal review 和初始 worktree 设置仍由对应工作流负责。

## 建立完成上下文

1. 要求使用由 `create-worktree` 认定的 worktrees，每个 worktree 上只有一个具名分支，且 `HEAD` 不
   处于 detached 状态。准确选择一个已接受模式：完成一个 standalone task、在其 Batch Worktree 上
   暂存一个已完成 ticket，或者完成一个全部 staged 的 Ticket Batch。
2. 要求每个所选 worktree 干净，且其工作完全由 commits 表示。standalone task 或 staged ticket
   提供 Checkpoint Commits；finished batch 提供有序的 per-ticket Task Commit range 和任何
   batch-review checkpoints。任一路径或 commit 所有权含义不明确时停止。
3. 找出预期 base checkout 和分支、Git common directory、每个 creation owner，以及所选模式的精确
   target。记录 worktree `HEAD`、merge base、完整 commit range 和 paths、target state、upstream
   state、ticket mapping 和 publication state。记录 owning implementation workflow 提供的 review
   和 verification evidence，包括其声称的 fixed point、commit、tree、acceptance sources、result
   和 findings。ticket staging 不交付 accepted behavior，因此改为提供 self-review evidence。
4. 所选 Checkpoint Commit 已发布时，在改写前停止。保留已发布历史，并通过仓库的 pull-request
   update workflow 处理后续 review fixes。Ticket Batch 可以包含未发布的 staged Task Commits，但
   不能包含已发布的 batch commit。
5. 在提供或执行结果前，快照每个受影响 checkout 的 branch、`HEAD`、index tree、staged changes、
   unstaged changes 和 untracked paths。

完成条件：根据当前证据识别所选 standalone 或 batch 模式、其完整 owned history、每个适用 target、
已提供的 review evidence，以及未改变的无关 checkout state。

## 选择一个结果

- **本地合并：** 将已记录本地 base 分支推进到 Task Commit，并在创建方允许时清理 linked worktree。
- **创建 pull request：** 推送 Task Commit、创建 pull request，并保留本地 task state 供后续处理。
- **保留备用：** 保留已收束的 task branch 和 worktree。
- **返回审查：** 将 Task Commit 的净结果写入 base working tree，同时保持其 `HEAD`、index 和无关
  local changes 不变。

已接受指令已经准确选择一个结果时直接使用；否则展示这四个结果，并在改变 task、base 或 remote
state 前等待选择。丢弃是只有用户明确请求时才可使用的特殊破坏性结果；直接执行其流程，不进行收束。
对于丢弃，只读取并执行 `references/discard.md`、验证其结果并报告完成；跳过下方的 target
finalization 和 Task Commit checks。丢弃验证成功后，使用 expected-old-value 检查删除本工作流创建
的每个 recovery ref。清理失败时保留剩余 refs，并将该结果视为失败。
已接受的 `implement-tickets` 运行选择两个内部 batch outcomes 之一，而不是四个 standalone
outcomes。**Stage ticket in batch** 将一个 self-reviewed Task Commit 追加到 Batch Worktree，但不
交付该 ticket。**Finish ticket batch** 在本地交付已 review 的 ordered range，同时保留每个
per-ticket Task Commit。这些 outcomes 不授权任何 remote action。

所选结果决定准确 delivery target。在 finalization 前解析该 target，随后只读取匹配流程来执行结果
专属步骤：

- 本地合并：[`references/merge-local.md`](references/merge-local.md)
- 创建 pull request：[`references/create-pull-request.md`](references/create-pull-request.md)
- 保留备用：[`references/keep-for-later.md`](references/keep-for-later.md)
- 返回审查：[`references/return-for-review.md`](references/return-for-review.md)
- 明确丢弃：[`references/discard.md`](references/discard.md)

## 最终化已 Review 历史

1. 刷新所选 target 并记录其精确 commit。对于 standalone task，通过 ancestry 或 equivalent-change
   evidence 加上所需 verification 来检测 **Already Delivered**。对于 ticket staging，要求 Batch
   Worktree `HEAD` 等于该 ticket 已记录的 base。对于 batch finish，要求 delivery target 等于
   immutable batch base；target movement 会停止该批次。
2. standalone task 可以将已移动 target 合并到其 task branch 并形成 Checkpoint Commit，但该
   mutation 会使其 review evidence 失效。synchronization 后停止，并将已改变的 task 交回其
   implementation workflow 执行 verification 和 formal review。batch staging 和 finish 不允许
   target merge 或 rebase：它们记录的 batch ancestry 必须保持线性，以便 local delivery 能够通过
   fast-forward 保留有序的 per-ticket Task Commits。
3. 对于允许的 standalone conflict，在选择 resolver 前检查 accepted source、target changes 和
   conflicting paths。仅当证据允许一种行为时才调用 `resolving-merge-conflicts`；否则 abort、
   恢复 pre-merge task state，并请求用户决定。conflict 解决后，保留 synchronization checkpoint，
   并交回 implementation workflow 执行 verification 和 formal review。batch conflict 或 ancestry
   mismatch 会停止，并保留所有 batch evidence。
4. 绝不调用正式 `code-review`。对于 standalone delivery，要求 review evidence 的 fixed point
   等于 selected target，reviewed commit 和 tree 等于干净的 task `HEAD`，acceptance sources 与
   accepted task 匹配，并且报告不含 blocking finding。对于 ticket staging，要求 focused 和
   repository verification 以及 worker self-review。对于 batch finish，要求从 immutable batch base
   到 batch `HEAD` 的 full verification 和 whole-batch review evidence，使用完整 Spec 和每个
   frozen ticket，并且不含 blocking finding；两个结果必须同时标识当前 batch `HEAD` 和 tree。
   evidence 缺失、过期或不匹配时，交回 owning implementation workflow。
5. 从 accepted source 和 repository convention 推导每个 Task Commit message。一个 staged ticket
   使用其 ticket；standalone work 使用其 issue、Spec、Ticket 或 conversation；可选的 whole-batch
   review fixes 使用 Ticket Batch 和 findings。只有这些来源允许实质不同含义时才询问用户。
6. 对于 standalone work 或 ticket staging，创建唯一 recovery ref，并针对精确 selected target
   运行 `scripts/consolidate_task_commit.py`。在 batch finish 期间保留有序的 per-ticket Task
   Commits；只有存在 review-fix Checkpoint Commits 时，才将其收束为位于该 range 顶端的一个可选
   Batch Review Commit。
7. 证明每个已创建 Task Commit 都以预期 commit 为唯一 parent，其 tree 与对应的已 review 或
   self-reviewed checkpoint `HEAD` 一致，commit hooks 成功，且每个 worktree 干净。consolidation
   只能通过这个 byte-identical tree proof 替换已 review checkpoint 的 commit identities；由于
   tree 未改变，review 和 verification 对新的 Task 或 Batch Review Commit 仍为 current。在 batch
   delivery 前重新检查 immutable batch base 和 ordered ticket mapping。

完成条件：standalone work 具有一个 tree 与 current formal-review evidence 匹配的 Task Commit，或
Already Delivered proof；ticket staging 已将一个 verified per-ticket Task Commit 追加到 Batch
Worktree 并保留 recovery；或者 batch finish 具有一个与 current whole-batch review evidence 匹配的
ordered range，保留每个 per-ticket Task Commit，且至多包含一个 Batch Review Commit。

## 完成 Already Delivered

在不创建 Task Commit 的情况下完成这个 terminal branch：

- 应用匹配 standalone procedure 的 **Already Delivered** exit，不创建 Task Commit。

完成前立即重新检查已证明 target；target 移动会使 proof 失效，并返回 finalization。procedure 验证
其 outcome 后，使用 expected-old-value 检查删除本工作流创建的每个 recovery ref。清理失败时保留
剩余 refs，并将该 outcome 视为失败。随后停止，不进入下方 Task Commit execution。

## 执行并验证

1. 对于 standalone outcome，只执行所选 procedure 及其 outcome-specific final rechecks、mutations、
   verification、recovery 和 handoff。
2. 对于 ticket staging，重新检查已 finalized 的 commit、base、worktrees、mapping、evidence 和
   recovery ref；fast-forward Batch Worktree；证明它准确推进到 tree-matching Task Commit；然后只
   执行 owner-authorized ticket cleanup，将其 recovery ref 转移给 batch，返回 Task Commit，并保持
   ticket claimed。
3. 对于 batch finish，重新检查 immutable base、已 review 的 `HEAD` 和 tree、mapping、evidence、
   unchanged target、recovery refs 和 snapshots。evidence 改变或存在 overlapping base-local work 时
   停止；否则 fast-forward target，不 squash 或创建 merge commit，运行 full target verification，
   证明 reviewed ordered range 和 unrelated local state，返回 ticket list，并只执行 owner-authorized
   cleanup。
4. standalone 或 batch delivery 成功后，使用 expected-old-value 检查删除每个 workflow-created
   recovery ref，并只执行已授权 cleanup。ticket staging 保留并报告其 recovery ref；失败时保留
   每个 ref 和 owned worktree。

完成条件：standalone outcome、ticket staging handoff 或 reviewed batch delivery 已被证明完成；否则
保留所有 task、batch、tracker 和 recovery evidence，并报告准确 failed operation 和下一项决定。

## 安全与恢复

- 改写 task history 或改变 base working files 前创建 recovery data。只恢复 failed operation 拥有的
  state；其 verification 或 handoff 失败时，保留每个 Task 或 Batch Worktree 和 recovery ref。
- 不在 base 或 batch branch 使用 pull、stash、hard reset、clean、force push、rebase 或 merge
  commit。只通过 consolidation workflow 改写未发布的 checkpoint history；在验证和交付已 review
  batch 时保留 staged per-ticket Task Commits。
- 由 host 创建的 worktree 交给该 host 清理。只有所选流程允许 cleanup 且已证明准确 ownership 时，
  才移除 Git 创建的 ticket 或 Batch Worktree 和 branch。

## 结果

报告所选 mode 的适用字段：outcome 和 authorization；standalone 或 immutable batch base；
checkpoint 和 ordered Task Commit ranges；ticket mapping；formal-review 或 self-review evidence 与
verification；可选 Batch Review Commit；conflict decisions；target mutations；tracker handoff；
保留的 local state；recovery refs；remote result；以及保留或移除的 Task 和 Batch Worktrees 与
branches。
