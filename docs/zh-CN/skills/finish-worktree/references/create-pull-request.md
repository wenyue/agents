# 创建 Pull Request

发布已验证的任务分支且不改写历史，并保留其本地 worktree 供后续处理。

1. 确定准确的 remote、base 分支、head 分支、pull-request 标题、正文和 draft 状态。仓库证据和已接受
   请求都无法确定的值必须询问用户。
2. 再次确认任务 worktree 干净且验证仍然有效。如果仓库策略要求使用最新 base，只通过该策略更新
   未发布分支并重新运行受影响的验证；不得 force-update 已发布历史，遇到这种情况应停止。
3. 不使用 force 推送准确的任务分支，然后通过可用的宿主原生或仓库授权接口创建 pull request。
4. 验证远程分支提交、pull-request base 和 head、draft 状态，以及返回的 URL。
5. 保留本地任务分支和 worktree 以处理审查更新。只有后续单独授权了完成结果，才能移除任一项。

用户选择此结果即授权解析出的分支推送和 pull-request 创建。它不授权无关推送、删除远程分支、合并
pull request 或本地清理。
