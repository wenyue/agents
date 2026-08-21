# 丢弃

只丢弃用户明确请求所指定的准确本地任务 worktree 和分支。

1. 展示解析出的 worktree 路径、任务分支、任务提交范围、发布状态，以及每个 base 无法到达的提交。
   除非已接受的请求已指定这些准确目标并明确授权其丢失，否则必须获得确认。
2. 要求任务 worktree 干净，并证明该分支未被另一个 worktree 检出。任何 dirty 或 untracked 内容、
   目标身份或生命周期所有权存在歧义时停止。
3. 由宿主创建的 worktree 交给该宿主移除。对于 Git 创建的 worktree，只移除准确记录的 worktree；
   历史已经集成时使用安全分支删除，只有已确认的丢弃必然放弃未合并提交时，才强制删除本地分支。
4. 验证 base checkout 及其全部本地状态未改变，并且准确的本地 worktree 和分支已经消失。
5. 只通过 expected-old-value checks 删除 workflow-owned recovery refs。保留并报告 expected
   value 或 ownership 不匹配的任何 ref。

保留所有远程分支。删除远程分支属于另一项破坏性操作，需要单独、准确的请求和授权。
