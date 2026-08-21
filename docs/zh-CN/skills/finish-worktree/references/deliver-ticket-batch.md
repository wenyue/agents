# Deliver Ticket Batch

要求 controller 所有的 Batch Worktree 作为 source、最终本地 checkout 作为 target、不可变 batch
base 作为 `expected_head`、`target_policy=exact-head-fast-forward-only`、当前 whole-batch review 和
完整验证、含有序 Task Commits 与可选 review tail 的
`history_policy=preserve-ordered-task-commits`、controller 所有的 recovery refs，以及匹配的获准
结果。此模式不授权 remote 或 tracker action。

## 最终化并交付

1. 要求最终 target `HEAD` 等于不可变 batch base。movement、conflict 或 ancestry mismatch 会停止
   并保留 evidence；不要 merge 或 rebase。
2. 要求完整 Spec 和 frozen ticket set 针对精确 Batch Worktree head 和 tree 通过 full
   verification 和 whole-batch review，且没有 blocking finding。
3. 根据 accepted source 和 repository convention 推导任何 Batch Review Commit message。只有这些
   来源允许实质不同含义时才询问。
4. 证明有序 first-parent Task Commit range。保留每个 per-ticket Task Commit，并且只将可选
   review-fix checkpoint tail 收束为至多一个 Batch Review Commit。
5. 证明任何新建 Batch Review Commit 都具有 expected sole parent、tree 与 reviewed source 字节
   完全一致、hooks 成功且 worktree 干净。
6. fast-forward unchanged target，运行 full target verification，证明 reviewed tree 和 unrelated
   state，并且只执行 controller-authorized Git cleanup。严格按授权删除或保留 recovery refs；失败
   时保留所有 owned state，除非 exact attempted mutation 有已证明的 owned rollback。

完成时保留有序 Task Commits，并至多包含一个 tree-matching Batch Review Commit。返回公共结果，加
Task Commit range、可选 Batch Review Commit，以及供 controller 后续 tracker completion 使用的 Git
delivery proof。
