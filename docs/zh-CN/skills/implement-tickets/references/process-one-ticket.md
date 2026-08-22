# 处理一个 Ticket

以选定的 dependency-ready frozen ticket、unchanged Batch Worktree 和 controller 当前的 batch
record 进入。这个 path 只有一个 `staged` exit；其他所有结果都进入主 Skill 中的 **停止与恢复**。

## Claim 并隔离

1. 在 claim 前立即重新读取 ticket 及其 blockers。出现 material status、requirement 或 edge change
   时停止。
2. 使用配置 tracker 所记录的 compare-and-set Ticket Batch claim 和 staged-blocker proof。记录 prior
   state 和 claim；没有记录安全的 claim operation 时停止。
3. 记录 Batch Worktree path、branch、精确 `HEAD`、tree 和 immutable base。选择不存在的 ticket
   专属 task slug、path 和 branch。
4. 将这些记录的事实视为 worker 的 isolation request。由 worker 而不是 controller 创建并认定
   Ticket Task Worktree。

## 派发一个 Worker

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
2. 建立当前 mechanism 和 seams，只实施该 ticket，在 behavior 存在可测试 seam 时使用 `tdd`，并通过
   正常 commit workflow 创建可恢复的 Checkpoint Commits。
3. 实施期间运行 focused verification，并在结束时运行仓库要求的每项检查。
4. 对照 acceptance criteria self-review 完整 ticket diff，并纠正每个 observed mismatch。worker
   不调用正式 `code-review`。
5. 使用根据当前证据得出的完整 `stage-ticket-into-batch` Finalization Contract 调用
   `finish-worktree`。
6. 独立重新检查 finalizer result，并将其连同 ticket 和 worker identities 以及 verification 和
   self-review evidence 原样返回。finalizer 负责其 result fields。

在调用 `finish-worktree` 之前的任何 phase 中，non-complete result 或 missing decision 都返回一个
structured Worker Recovery Handoff，其中包含：

- `status`（`stopped` 或 `failed`）、ticket 和 worker identities、`completed_phase` 和
  `failed_phase`；
- Task Worktree path、branch、精确 base、`HEAD`、tree、qualification 和 owned local-state facts；
- 精确 Checkpoint Commit range、trees、publication facts 和 uncommitted state；
- 每个 verification command、result 及其关联的 `HEAD` 和 tree，以及 self-review evidence 和
  unresolved findings；
- 每个 retained worktree、branch、commit、recovery ref 和其他有用的 recovery state；
- exact blocker、mismatch、error 或 missing decision；以及
- `next_owner` 和 exact next action。

保留所有已报告的 Git 和 recovery state。在进入 **停止与恢复** 前，controller 既不替换 worker，
也不处理另一个 ticket。

## 验证 Staging

1. 要求 worker result 为 complete，并独立验证 worker 和 ticket mapping、Task Commit parent 和
   tree、evidence、cleanup、transferred recovery refs，以及 Batch Worktree 是否从 supplied ticket
   base 准确推进一个 returned Task Commit。任何 mismatch 都进入 **停止与恢复**。
2. 保持 ticket 为 claimed，并在 frozen graph 中记录其 Task Commit。Staged Ticket 可以在本次运行内
   解锁 dependants，但既未 delivered，也未 completed。
3. 重新读取 frozen contracts。material contract change 进入 **停止与恢复**；否则向主 Skill 返回
   `staged` exit。
