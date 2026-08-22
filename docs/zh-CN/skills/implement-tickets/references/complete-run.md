# 完成运行

仅在每个 frozen ticket 都有经过证明的 Task Commit 位于 Batch Worktree 的 ordered range 中后进入。

1. 运行 full verification，并以 immutable batch base 作为 fixed point、完整 Spec 和 frozen
   tickets 作为 acceptance sources 调用 `code-review`。
2. 将 blocking findings 作为 batch-review Checkpoint Commits 处理。每次纠正后，重新运行 full
   verification 和同一个 whole-batch review。仅当两个 gates 针对同一个最终 `HEAD` 和 tree 通过时
   才继续；unresolved finding 或 failed gate 进入 **停止与恢复**。
3. 在 controller 的 Agent context 中调用 `finish-worktree`，并提供根据当前证据得出的完整
   `deliver-ticket-batch` Finalization Contract，其中不含 tracker data。
4. 独立证明精确 Batch Delivery、保留的 ordered per-ticket Task Commits、至多一个 Batch Review
   Commit 和 target verification。任何 mismatch 都进入 **停止与恢复**。
5. 只有在 delivery proof 之后，才按依赖顺序完成 tracker tickets。一个 transition 失败时，保留
   later claims 并进入 **停止与恢复**，不回滚 delivery，也不改变后续 ticket。

仅当 Batch Delivery、每项 Ticket Completion、claim removal 和 authorized Git cleanup 均已证明时
才完成。报告 frozen order、immutable base、target 和 batch branches、workers、Task Commits、
whole-batch review 和 verification、可选 Batch Review Commit、tracker transitions、cleanup 和
exclusions。
