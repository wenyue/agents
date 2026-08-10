# 本地合并

推进已记录的本地 base 分支，同时保留经过验证的任务提交历史。

1. 确认 base checkout 位于已记录的 base 分支。如果任何任务路径与 staged、unstaged 或 untracked
   的 base 本地工作重叠，而且合并可能覆盖它们，保持两个 checkout 不变，并改为提供返回供审查。
2. 要求 base `HEAD` 是任务 `HEAD` 的祖先。如果不是，只将尚未发布的任务分支 rebase 到当前 base；
   遇到未解决冲突时中止，并重新运行受影响的任务验证。任务分支已经发布时停止，不得改写它。
3. 集成前立即复查任务 `HEAD`、base 分支、base `HEAD` 及 base 本地快照，然后从 base checkout
   运行 `git merge --ff-only <task-branch>`。
4. 从 base checkout 重新运行相关验证。证明 base 现在包含完整任务提交范围，并且每个无关的 base
   本地变更仍与快照一致。
5. 验证通过后，请已记录的生命周期负责人移除宿主创建的 worktree。对于 Git 创建的 worktree，
   从 base checkout 移除该准确且干净的 worktree，并使用 Git 的安全分支删除来删除已合并任务分支。

如果 fast-forward 集成或合并后验证失败，保留任务分支和 worktree，并报告最终 base 状态。不得自动
改写或回滚 base。
