# Stage Ticket into Batch

要求 worker 所有的 Ticket Task Worktree 作为 source、Batch Worktree 作为 target、其精确 ticket
base 作为 `expected_head`、`target_policy=exact-head-fast-forward-only`、worker self-review 和所需
focused 与 repository verification、`history_policy=consolidate-checkpoints`、controller recovery
ownership，以及匹配的获准结果。此模式不授权 remote 或 tracker action。

## 最终化并暂存

1. 要求 Batch Worktree `HEAD` 和 tree 等于精确 ticket base。movement、conflict 或 ancestry
   mismatch 会停止并保留 evidence；不要 merge 或 rebase。
2. 要求针对精确 source head 和 tree 的 worker self-review 以及 focused 和 repository
   verification，且没有 blocking finding。
3. 根据 accepted source 和 repository convention 推导 commit message。只有这些来源允许实质不同
   含义时才询问。
4. 创建唯一 recovery ref，并针对精确 target 运行 `scripts/consolidate_task_commit.py`。证明 Task
   Commit 具有 expected sole parent、tree 与 self-reviewed source 字节完全一致、hooks 成功且
   worktree 干净。
5. 将 Batch Worktree 精确 fast-forward 到该 Task Commit，证明 resulting identity 和 ancestry，
   将 recovery 转移给 controller，并且只执行 authorized Ticket Task Worktree cleanup。保留并转移
   recovery refs；失败时保留所有 owned state，除非 exact attempted mutation 有已证明的 owned
   rollback。

完成要求准确一个 Task Commit 追加到 Batch Worktree 且 recovery 已转移。返回公共结果，加
checkpoint range、staged Task Commit、resulting Batch Worktree identity 和 staging proof。
