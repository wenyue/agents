---
name: finish-worktree
description: 当 Task Worktree 中的实施检查点可进入最终 review、收束为一个 Task Commit，并产生本地、pull request、保留、返回审查或丢弃结果时使用。
---

# 完成 Worktree

在保留检查点恢复能力和 base 原有状态的前提下，完成一个 Task Worktree 生命周期。负责目标同步、
最终 review、Task Commit 收束、结果选择、授权、执行、验证、恢复和生命周期清理；实施本身和
worktree 初始设置仍由对应工作流负责。

## 建立完成上下文

1. 要求使用由 `create-worktree` 认定的 Task Worktree，其上只有一个具名任务分支，且 `HEAD` 不处于
   detached 状态。确认实施、初次 review 和相关验证已经完成。
2. 要求 worktree 干净，且任务工作已完全由 Checkpoint Commit 表示。将 staged、unstaged 或 untracked
   的任务工作交回实施流程；任何路径所有权不明确时停止。
3. 找出预期 base checkout 和分支、Git common directory、创建方，以及每个允许结果的候选交付目标。
   记录任务 `HEAD`、merge base、完整检查点范围和路径、目标状态、upstream 状态及发布状态。
4. 任一 Checkpoint Commit 已发布时，在收束前停止。保留已发布历史，并通过仓库的 pull request 更新
   工作流处理后续 review 修复。
5. 在提供结果选择前，快照 base 分支、`HEAD`、index tree、staged 改动、unstaged 改动和 untracked
   路径。

完成条件：从当前证据证明唯一未发布且干净的 Task Worktree、其完整检查点历史、每个适用结果目标和
一个未改变的 base checkout。

## 选择一个结果

- **本地合并：** 将已记录本地 base 分支推进到 Task Commit，并在创建方允许时清理关联 worktree。
- **创建 pull request：** 推送 Task Commit、创建 pull request，并保留本地任务状态供后续处理。
- **保留备用：** 保留已收束的任务分支和 worktree。
- **返回审查：** 将 Task Commit 的净结果写入 base working tree，同时保持其 `HEAD`、index 和无关
  本地改动不变。

已接受指令已经准确选择一个结果时直接使用；否则展示这四个结果，并在改变任务、base 或远程状态前
等待选择。丢弃是只有用户明确请求时才可使用的特殊破坏性结果；直接执行其流程，不进行收束。
对于丢弃，只读取并执行 `references/discard.md`、验证其结果并报告完成；跳过下方的目标最终化、Task
Commit 检查。丢弃验证成功后，使用 expected-old-value 检查删除本工作流创建的每个 recovery ref。
清理失败时保留剩余 ref，并将该结果视为失败。

所选结果决定准确交付目标。在最终化前解析该目标，随后只读取匹配流程来执行结果专属步骤：

- 本地合并：[`references/merge-local.md`](references/merge-local.md)
- 创建 pull request：[`references/create-pull-request.md`](references/create-pull-request.md)
- 保留备用：[`references/keep-for-later.md`](references/keep-for-later.md)
- 返回审查：[`references/return-for-review.md`](references/return-for-review.md)
- 明确丢弃：[`references/discard.md`](references/discard.md)

## 最终化一个 Task Commit

1. 通过仓库已授权策略刷新所选目标，并记录其准确提交。在改变任务分支前，通过当前 ancestry 或
   等价变更证据，加上任务所需验证，检查目标是否已经包含
   完整的已接受任务结果。该证明通过时，进入 **Already Delivered**，跳过目标同步、最终收束和 Task
   Commit 创建。空 diff 或结论不明确的 diff 不是证明；除非已在目标上验证已接受行为，否则继续本
   工作流。
2. 目标不是任务 `HEAD` 的 ancestor 时，将其合并进任务分支并形成 Checkpoint Commit，使每个冲突
   只需针对任务净结果解决一次。
3. 发生冲突时，在选择 resolver 前检查已接受任务来源、目标改动和冲突路径。证据只允许一种行为时，
   调用 `resolving-merge-conflicts` 解决并完成合并；仍有多个合理行为时 abort 合并，恢复合并前任务
   状态，并请求用户决定。
4. 针对已同步目标和干净任务 `HEAD` 运行受影响验证及 `code-review`。每轮 review 修复分别形成关联其
   finding 的 Checkpoint Commit，且不得绕过 commit hook。重复验证和 review，直至没有阻塞 finding。
   目标改变会使这些证据失效，并返回步骤 1。
5. 根据已接受 issue、Spec、Ticket 或对话及仓库惯例推导 Task Commit message。只有这些来源允许实质
   不同含义时才询问用户。
6. 选择一个唯一且不存在的本地 recovery ref 名称，然后使用准确目标提交、message 文件和 recovery
   ref 名称运行 `scripts/consolidate_task_commit.py`。该脚本在改写历史前将该 ref 原子创建在当前检查点
   `HEAD`，使用仓库正常 commit 工作流，并将任务分支从已记录旧 `HEAD` 原子移动到一个 Task Commit。
7. 证明 Task Commit 以所选目标为唯一 parent，其 tree 与已 review 的检查点 `HEAD` 逐字节相同，
   commit hook 成功，且 Task Worktree 干净。所选结果完成前目标移动时返回步骤 1，并使用新的 recovery
   ref。

完成条件：一个干净、已 review、已验证且未发布的 Task Commit 表示完整任务，恢复其 Checkpoint
Commit 所需的每个 recovery ref 仍然可用；或所选目标已被证明 Already Delivered，且没有创建空提交。

## 完成 Already Delivered

使用已经选择的结果，不制造 Task Commit：

- **本地合并：** 验证本地 base 仍指向已证明目标，将集成视为完成，并且只执行本地合并结果授权的
  清理。
- **创建 pull request：** 报告已解析 pull-request base 没有任务 diff，不推送或创建空 pull request，
  并保留任务分支和 worktree 供后续处理。
- **保留备用：** 完全按已记录状态保留任务分支和 worktree。
- **返回审查：** 报告 base 没有任务 diff，保持其 working tree 和 index 不变，并保留任务分支和
  worktree 作为 review 证据。

完成前重新检查已证明目标。目标移动会使 Already Delivered 失效，并返回最终化。报告证明、跳过的
变更、保留的任务状态及任何已授权清理。结果验证成功后，使用 expected-old-value 检查删除本工作流
创建的每个 recovery ref；清理失败时保留剩余 ref，并将该结果视为失败。随后停止，不进入下方 Task
Commit 执行流程。

## 执行并验证

1. 所选流程改变状态前，重新检查 Task Commit、所选目标、base 快照和相关远程状态。目标移动时重新
   最终化；结果不再安全或明确时请求决定。
2. 只执行所选流程及其所需验证。该选择只授权流程中具名操作及准确目标，不授权更广的仓库、文件系统
   或远程工作。
3. 对照所选结果和原始快照，验证最终分支、worktree、checkout、index、本地改动和远程状态。
4. 结果验证成功后，使用 expected-old-value 检查删除每个工作流创建的 recovery ref。失败时保留所有
   recovery ref。

完成条件：所选结果和恢复清理已被证明完成；否则保留所有任务及恢复证据，并报告准确失败操作和下一项
决定。

## 安全与恢复

- 保留所有 base 原有本地改动。只有结果明确、局限于任务且可验证时才解决共享路径。
- 改写任务历史或改变 base working file 前创建恢复数据。只恢复失败操作所拥有的状态；验证失败时保留
  Task Worktree 和恢复数据。
- 不在 base 分支使用 pull、stash、hard reset、clean、force push 或 merge commit。只通过收束工作流
  改写未发布任务分支。
- 由宿主创建的 worktree 交给该宿主清理。只有所选流程允许清理且已证明准确所有权时，才移除 Git
  创建的 worktree 或任务分支。

## 结果

报告所选结果和授权、已同步目标、检查点范围、review 和验证证据、Task Commit 及 message 来源、冲突
决定、base 变更、保留的本地状态、recovery ref、远程结果，以及每个保留或移除的 worktree 和分支。
