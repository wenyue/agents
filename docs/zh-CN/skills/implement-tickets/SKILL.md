---
name: implement-tickets
description: 将配置 tracker 中剩余的 agent-ready tickets 作为一个无人值守的串行 Ticket Batch 实施。每个 ticket 使用一个 fresh worker 和一个 Task Worktree，在 Batch Worktree 上保留每个 ticket 各自的 Task Commit，然后在本地交付前对完整 Spec 和冻结的 ticket 集合统一 review 一次。
---

# 实施 Tickets

将一个冻结的 Ticket Batch 作为按依赖排序的流水线实施。controller 负责 ticket 选择、委派、batch
staging、whole-batch review、delivery handoff 和 tracker transitions。每个 worker 在自己的 Task
Worktree 中仅负责一个 ticket 的实施和 self-review。

## 建立运行

1. 读取配置的 issue-tracker 指令、引用的 Spec 或父级来源，以及所请求 effort 中的每个 ticket。
   如果 effort 未明确给出，仅当当前上下文恰好标识一个 ticket 集合时才推断；否则询问 effort。
2. 快照本次运行的 ticket 标识符、顺序、状态、blocking edges 和 acceptance criteria。仅将配置
   tracker 的 agent-ready 状态视为未实施工作。排除已完成、已拒绝、由人负责、因信息阻塞或已
   claimed 的 tickets。
3. 验证每个 blocker 都解析为一个 ticket 或一个已完成的外部依赖，并且冻结的图无环。当多个
   tickets 同时 ready 时，保留发布顺序作为平局规则。
4. 标识将接收完整 Ticket Batch 的命名本地目标分支和 checkout。要求已有接受的指令为该批次选择
   **merge locally**。如果目标或 outcome 尚不明确，在改变 tracker 或 Git 状态前只询问一次。
5. 检查目标 checkout 和现有 worktrees，然后调用 `create-worktree`，从目标的精确 `HEAD` 创建一个
   qualified Batch Worktree 和具名 batch branch。将该 commit 记录为 immutable batch base，并保留
   所有预先存在的本地状态。

当一个冻结的 ticket 图、一个未改变的本地目标、一个 qualified Batch Worktree、一个 merge-local
outcome 和第一个 dependency-ready ticket 都已确定时，运行准备就绪。如果仍有未完成 tickets 但没有
ready ticket，报告其未解决的 edges，并在不 claim ticket 的情况下停止。

## 处理一个 Ticket

每次严格为一个 dependency-ready ticket 重复本节。当这个 controller 已在 Batch Worktree 上为每个
冻结 blocker 暂存 Task Commit 时，该 ticket 即为 ready；tracker status 本身不能覆盖这项批次内证明。

### Claim 并隔离

1. 在 claim 前立即重新读取 ticket 及其 blockers。如果它的状态、要求或 blocking edges 在运行
   快照后发生实质变化，停止并报告已变化的来源。
2. 使用配置 tracker 记录的 Ticket Batch claim operation，包括 staged blocker proof 和
   compare-and-set guard。记录先前状态和 claim；当 tracker 指令未定义 transition 时，绝不虚构一个
   transition。
3. 从当前 Batch Worktree `HEAD` 调用 `create-worktree`，使用 ticket 专属的 task slug 和分支。
   delivery target 在整个运行期间保持在 immutable batch base。
4. 仅当 `create-worktree` 报告 qualified Task Worktree，以及通过或被明确接受的 baseline 时才继续。
   失败时保留其证据；仅当 tracker 记录了安全的 conditional transition 时恢复 ticket 的先前状态，
   然后停止运行。

### 派发一个 Worker

为该 ticket 启动一个 fresh write-capable worker Agent。仅向其提供完成工作所需的上下文：

- 完整的 ticket 及其 acceptance source；
- Task Worktree 路径和 task branch；
- `create-worktree` 记录的目标分支和精确 base commit；
- 适用的仓库指令和 verification commands；以及
- 以下边界。

worker 必须：

1. 只在分配的 Task Worktree 内工作，并且只实施所分配的 ticket。
2. 在编辑前建立当前机制和受影响 seams，然后在行为存在可测试 seam 时使用 `tdd`。
3. 实施期间运行 focused verification，并在结束时运行仓库要求的每项检查。
4. 通过仓库正常的 commit workflow 创建可恢复的 Checkpoint Commits。
5. 对照 acceptance criteria self-review 完整的 ticket diff，并纠正观察到的每个 mismatch。不得调用
   正式的 `code-review`；所有 tickets 暂存完成后，由 controller 负责该 review。
6. 仅当 Task Worktree 干净，并已报告其 implementation、verification、self-review 和 checkpoint
   range 时才返回。worker 不得暂存、交付、发布、清理 worktree、改变另一个 ticket，或将自己的
   ticket 标记为完成。

如果 implementation、verification、self-review 或所需决定无法完成，worker 必须原样保留 branch、
worktree、commits 和 failure evidence，并报告准确 blocker。controller 停止运行；不会替换 worker
或继续另一个 ticket。

### 完成并集成

1. 根据当前证据验证 worker 报告的 branch、干净的 Task Worktree、checkpoint range、tests 和
   self-review。将 worker report 视为需要检查的证据，而不是证明本身。
2. 以已接受的 **stage ticket in batch** 路径调用 `finish-worktree`。由它将该 ticket 的 checkpoints
   收束为一个 Task Commit、fast-forward Batch Worktree、保留 recovery evidence，并只清理已完成的
   ticket worktree。
3. 仅当 `finish-worktree` 证明 Batch Worktree 恰好推进了该 ticket 的一个 Task Commit，且所需
   verification 通过时才继续。对于任何其他 exit，保留所有 batch、worktree、branch、commit 和
   recovery evidence，然后进入 **停止与恢复**；由该节根据 delivery evidence 和 compare-and-set
   results 决定 tracker transition。
4. 保持 ticket 为 claimed，并在冻结图中记录其 staged Task Commit。staged ticket 足以在这个
   exclusive run 内解锁其 dependants，但尚未完成或交付。
5. 重新读取冻结的 ticket contracts。选择 frozen blockers 均已 staged 且最早发布的 ticket，并从
   **Claim 并隔离** 重复；任何 material contract change 都会停止运行。

## 完成运行

每个 included ticket 都 staged 后，运行 full verification，并对
`git diff <batch-base>...HEAD` 执行一次正式 `code-review`，以 immutable batch base 作为 fixed
point，并以完整 Spec 和每个 frozen ticket 作为 acceptance sources。将 blocking findings 作为
Batch Worktree 上的 review-fix Checkpoint Commits 处理；每轮修复后重新运行 full verification 和
同一次 whole-batch review。只有两者都针对同一个最终 batch `HEAD` 和 tree 通过时才继续。随后以
已接受的 **finish ticket batch** 路径调用 `finish-worktree`。向其提供 immutable batch base、
完整 Spec、每个 frozen ticket、有序的 per-ticket Task Commits、针对该最终 tree 的精确 review 和
verification evidence、tracker claims 和 recovery refs。由它验证该 evidence，将所有 review-fix
checkpoints 收束为至多一个 tree 相同的可选 Batch Review Commit，然后在不 squash per-ticket Task
Commits 的情况下，将未改变的本地目标 fast-forward 到已 review 的 batch `HEAD`。交付验证成功后，
使用配置 tracker 记录的 completion operation，按依赖顺序完成每个 included ticket。transition
失败时停止 reconciliation，但不回滚已交付 commits，也不改变另一个 ticket。仅当目标包含已 review
的有序 range、每个 included ticket 均已完成、不再有 run claim，且已授权的 worktree、branch 和
recovery cleanup 得到证明时才完成。

报告冻结的 ticket 集合与顺序、immutable batch base、target 和 batch branches、每个 ticket 的
worker、Task Worktree 和 Task Commit、whole-batch review 与 verification、可选 Batch Review
Commit、tracker transitions、cleanup，以及每个 excluded ticket。不要将运行扩展到快照后发布的
tickets；为它们提议一次新运行。

## 停止与恢复

在首次出现含义不明确的要求、已变化的 ticket contract、无效 dependency graph、claim conflict、
baseline failure、worker failure、staging failure、未解决的 blocking review finding、target
movement、delivery 或 post-delivery verification failure，或者 tracker mismatch 时停止整个运行。

保留有用的部分状态。报告 immutable batch base、未改变或已交付的 target、当前 claims、staged Task
Commits、准确的 failed operation、保留的 batch 和 ticket worktrees、branches、checkpoints、
recovery refs，以及安全恢复或开始新运行所需的决定或操作。当 delivery target 不包含任何 run-owned
Task Commit 或 equivalent accepted result 时，对每个 run-owned claim 按逆依赖顺序使用配置 tracker
记录的 release operation，同时保留所有 Git 和 recovery evidence；compare-and-set 失败时停止
release，并报告剩余 claims。delivery 已发生时，保留 unresolved claims，并改为交接配置 tracker
记录的 completion operation。除非用户另行授权，否则不执行 push、pull request、force operation、
rebase、rollback、discard，或配置的 claim、release 和 completion transitions 之外的 remote
tracker action。
