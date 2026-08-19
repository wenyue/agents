# 保留备用

保留已完成的 Task Commit，不进行集成、发布或清理。当 task 为 **Already Delivered** 时，重新检查已
证明 target，完全按记录保留 task branch 和 worktree，报告 proof 和保留的 state，然后停止。

1. 不改变任何分支、checkout、index、worktree、文件系统或远程状态。
2. 再次确认任务分支指向已记录的 Task Commit，且 worktree 仍然干净。
3. 报告 base 分支和提交、任务分支和 Task Commit、worktree 路径、创建方、验证结果、发布状态，以及
   后续集成或清理负责人。
