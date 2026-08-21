---
name: implement-tickets
description: 将剩余 agent-ready tickets 作为一个无人值守的串行 Ticket Batch 实施。让每个 fresh worker 负责完整的 Task Worktree 生命周期，为每个 ticket 保留一个 Task Commit，然后 review 并交付冻结的 batch。
---

# 实施 Tickets

将一个冻结的 Ticket Batch 作为按依赖排序的流水线运行。

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

当 frozen graph、unchanged target、qualified Batch Worktree、authorized local delivery 和第一个
dependency-ready ticket 都已确定时，运行准备就绪。如果仍有未完成 tickets 但没有 ready ticket，
报告 unresolved edges，并在不 claim 的情况下停止。

## 处理一个 Ticket

每次准确处理一个 dependency-ready ticket。仅当 frozen blocker 的 Task Commit 存在于 Batch
Worktree 已记录的 ordered range 时，才视为满足该 blocker；tracker status 不是证明。

### Claim 并隔离

1. 在 claim 前立即重新读取 ticket 及其 blockers；出现 material status、requirement 或 edge change
   时停止。
2. 使用配置 tracker 的 compare-and-set Ticket Batch claim 和 staged-blocker proof。记录 prior state
   和 claim；没有记录安全的 claim operation 时停止。
3. 记录 Batch Worktree path、branch、精确 `HEAD`、tree 和 immutable base。选择不存在的 ticket
   专属 task slug、path 和 branch。
4. 将这些记录的事实视为 worker isolation request。由 worker 而不是 controller 创建并认定 Ticket
   Task Worktree。

### 派发一个 Worker

启动一个 fresh write-capable worker Agent，并向其提供一个完整 handoff：

- `ticket`：identifier、完整 contract、acceptance sources 和 frozen blocker proof；
- `batch`：worktree、branch、精确 `head` 和 `tree`、immutable base 和 controller identity；
- `task_worktree`：预期 slug、path、branch，以 worker 为 scope owner、controller 为 integration
  owner，以及获准的 cleanup owner；
- `verification`：focused 和 repository-required commands；
- `finalization`：`mode=stage-ticket-into-batch`、Batch Worktree target、
  `target_policy=exact-head-fast-forward-only`、向 controller 转移 recovery，以及 authorized cleanup；
  和
- `tracker_boundary`：worker 不执行 claim、release、completion 或其他 tracker transition。

worker 在其现有 Agent context 中执行以下完整生命周期：

1. 重新检查每项 supplied Batch 和 intended task identity，然后从精确 supplied Batch Worktree
   `HEAD` 调用 `create-worktree`。仅当 qualified Task Worktree 的 owners、base、path、branch 和
   baseline 与 handoff 匹配时才继续。
2. 建立当前机制和 seams，只实施该 ticket，在行为存在可测试 seam 时使用 `tdd`，并通过正常 commit
   workflow 创建可恢复的 Checkpoint Commits。
3. 实施期间运行 focused verification，并在结束时运行仓库要求的每项检查。
4. 对照 acceptance criteria self-review 完整 ticket diff，并纠正每个 observed mismatch。worker
   不调用正式 `code-review`。
5. 读取 [`finish-worktree` 的 Finalization Contract](../finish-worktree/SKILL.md)，根据当前证据构建完整
   `stage-ticket-into-batch` contract，并调用 `finish-worktree`。
6. 重新检查 finalizer result，并返回 `status`、ticket 和 worker identities、completed 或 failed
   phase、Task Worktree 和 checkpoint facts、verification 和 self-review evidence、完整 finalizer
   result、staged Task Commit 和 resulting Batch Worktree identity、cleanup、retained recovery state、
   exact blocker 和 next owner。

失败或缺少决定时，保留有用的 Git 和 recovery state，并返回 non-complete result。worker 不改变
tracker state。controller 不替换 worker，也不处理另一个 ticket，并进入 **停止与恢复**。

### 完成并集成

1. controller 独立验证 worker、ticket mapping、Task Commit parent 和 tree、Batch Worktree
   fast-forward、evidence、cleanup 和 transferred recovery refs。
2. 仅当 Batch Worktree 从 supplied ticket base 准确推进一个 returned Task Commit 且 worker result
   为 complete 时才继续；否则进入 **停止与恢复**。
3. 保持 ticket 为 claimed，并在 frozen graph 中记录其 Task Commit。Staged Ticket 可以在本次运行内
   解锁 dependants，但尚未 delivered 或 completed。
4. 重新读取 frozen contracts，选择 blockers 均已 staged 且最早发布的 ticket，并从
   **Claim 并隔离** 重复。出现 material contract change 时停止。

## 完成运行

每个 ticket 都 staged 后，运行 full verification，并对 `git diff <batch-base>...HEAD` 执行一次正式
`code-review`，以 immutable base 作为 fixed point，并以完整 Spec 和 frozen tickets 作为 acceptance
sources。将 blocking findings 作为 batch-review Checkpoint Commits 处理，然后针对同一个最终 `HEAD`
和 tree 重新运行两个 gates。读取
[`finish-worktree` 的 Finalization Contract](../finish-worktree/SKILL.md)，构建不含 tracker data 的完整
`deliver-ticket-batch` contract，并在 controller 的 Agent context 中调用它。独立证明 exact delivery、
保留的 per-ticket commits、至多一个 Batch Review Commit 和 target verification。只有随后才按依赖
顺序完成 tracker tickets；一个 transition 失败时，保留 later claims 并停止，不回滚 delivery，也不
改变后续 ticket。

仅当 delivery、tracker completion、claim removal 和 authorized Git cleanup 均已证明时才完成。报告
frozen order、base、branches、workers、Task Commits、review 和 verification、可选 Batch Review
Commit、tracker transitions、cleanup 和 exclusions。快照后发布的 tickets 需要一次新运行。

## 停止与恢复

首次出现 ambiguous requirement、changed contract、invalid graph、claim conflict、worker 或 staging
failure、blocking review finding、target movement、delivery 或 verification failure，或者 tracker
mismatch 时停止。

报告所有 retained batch、target、claim、commit、worktree、branch 和 recovery state，以及准确 failed
operation 和 next owner。Batch Delivery 前只使用记录的 compare-and-set release，并按逆依赖顺序
执行；delivery 后保留 unresolved claims，并交接记录的 completion operation。没有单独授权时，
不执行 pull、push、pull request、force operation、rebase、rollback、discard 或未配置的 tracker
action。
