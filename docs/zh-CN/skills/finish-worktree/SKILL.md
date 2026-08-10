---
name: finish-worktree
description: 当具名关联 Git worktree 中已通过验证的实现可以在本地合并、发布为 pull request、保留备用、返回 base checkout 供审查，或被明确要求丢弃时使用。
---

# 完成 Worktree

在保留任务工作和 base 原有状态的前提下，完成一个关联 worktree 的生命周期。负责实施完成后的
结果选择、授权、执行、验证、恢复和生命周期清理；实施本身和 worktree 初始设置仍由对应工作流负责。

## 建立完成上下文

1. 必须使用具名任务分支上的关联 worktree，且 `HEAD` 不能处于 detached 状态。确认任务的实施、
   审查和相关验证已经完成。
2. 要求任务 worktree 干净。如果仍有 staged、unstaged 或 untracked 的任务工作，先将它交回仓库的
   实施和提交工作流再结束。任何脏路径的所有权不明确时停止。
3. 从当前 Git 证据以及可用的 `create-worktree` 结果中找出预期 base checkout、base 分支、Git common
   directory 和 worktree 创建方。无法证明唯一预期 base 时停止。
4. 记录任务 `HEAD`、merge base、完整任务提交范围和路径、upstream 状态，以及是否已有任务提交被
   发布。保留完整提交历史；不得仅为结束 worktree 而 squash。
5. 提供结果选项前，记录 base 分支、`HEAD`、index tree、staged 变更、unstaged 变更和 untracked
   路径的快照。

完成标准：已经完整识别一个干净、通过验证的任务分支和一个未改变的 base checkout，并已记录任务
范围、本地状态、发布状态及生命周期负责人。

## 选择一个结果

- **本地合并：** 将已记录的 base 分支推进到已验证的任务历史，并在创建方允许时清理关联
  worktree。
- **创建 pull request：** 在不改写已发布历史的情况下推送任务分支，创建 pull request，并保留
  本地任务状态供后续处理。
- **保留备用：** 保持分支和 worktree 原样不变。
- **返回供审查：** 将任务的净结果作为 unstaged 或 untracked 内容放入 base working tree，同时
  保持其 `HEAD`、index 和无关本地变更不变。

如果已经接受的用户指令明确选择了一个结果，直接使用它。否则先提供这四种结果，等待用户选择后
才能改变本地或远程状态。只有用户明确要求时，才将丢弃视为特殊破坏性结果；不得将其包含在常规
选项中。

选择后，只读取匹配的流程：

- 本地合并：[`references/merge-local.md`](references/merge-local.md)
- 创建 pull request：[`references/create-pull-request.md`](references/create-pull-request.md)
- 保留备用：[`references/keep-for-later.md`](references/keep-for-later.md)
- 返回供审查：[`references/return-for-review.md`](references/return-for-review.md)
- 明确丢弃：[`references/discard.md`](references/discard.md)

## 执行与验证

1. 所选流程改变状态前，立即复查任务 `HEAD`、base 分支、base `HEAD` 及相关本地状态快照。如果发生
   移动，刷新分析；如果所选结果已不再安全或明确，请求用户决定。
2. 只执行所选流程及其要求的验证。将该选择视为对该结果所列操作和解析出的准确目标的授权，不得
   扩展为更广泛的仓库、文件系统或远程变更。
3. 对照所选结果和原始快照，验证最终分支、worktree、checkout、index、本地变更和远程状态。

完成标准：所选结果已被证明完成；或者所有可恢复证据均已保留，并报告准确的失败操作和下一项决策。

## 安全与恢复

- 保留所有预先存在的 base 本地变更。路径相同不自动构成冲突；只有结果无歧义、属于任务范围且
  可以验证时才合并。
- 改变 base working file 前，在仓库外创建恢复数据。只恢复失败传输触碰过的路径；操作后验证失败
  时，保留任务分支、worktree 和恢复数据。
- 不使用 pull、stash、reset、clean、force push 或 merge commit。只有所选流程允许时才改写未发布
  的任务分支；改写已发布历史前必须停止。
- 由宿主创建的 worktree 交给该宿主清理。只有所选流程允许清理且已证明准确所有权时，才移除 Git
  创建的 worktree 或任务分支。

## 结果

报告所选结果及其授权、任务范围、base 目标、变更操作、重叠或冲突决定、验证、保留的本地状态、
恢复数据、远程结果，以及每个保留或移除的 worktree 和分支。
