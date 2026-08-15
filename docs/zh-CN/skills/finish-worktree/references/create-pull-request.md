# 创建 Pull Request

发布已验证的 Task Commit 且不改写它，并保留其本地 worktree 供后续处理。

1. 确定准确的 remote、base 分支、head 分支、pull-request 标题、正文和 draft 状态。仓库证据和已接受
   请求都无法确定的值必须询问用户。
2. 再次确认 Task Worktree 干净，Task Commit 的唯一 parent 是已解析的 pull request base commit，
   且 review 和验证仍然有效。base 已移动时返回最终化。
3. 不使用 force 推送准确的任务分支，然后通过可用的宿主原生或仓库授权接口创建 pull request。
4. 验证远程分支提交、pull-request base 和 head、draft 状态，以及返回的 URL。
5. 保留本地任务分支和 worktree 以处理审查更新。将后续已发布的 review-fix commit 保留为 review
   历史；最终 squash 行为由仓库 pull request 策略决定。只有后续单独授权了完成结果，才能移除本地
   状态。

用户选择此结果即授权解析出的分支推送和 pull-request 创建。它不授权无关推送、删除远程分支、合并
pull request 或本地清理。
