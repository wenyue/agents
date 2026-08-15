# 工作区政策

强度：`Mandatory`

适用范围：工作区选择、本地 Git 状态、commit 权限和远程操作授权。

## 当前工作区

- 当用户、Harness 和适用 Skill 都不要求隔离，并行工作不需要独立状态，且 checkout 既有状态可以
  原地保留时，使用当前工作区。
- 在实施和 review 已接受任务时，保留所有既有 staged、unstaged 和 untracked 工作。
- 某项任务操作会覆盖、stash、reset、clean 或丢弃这些状态时，改用无损方案；没有无损方案时请求用户
  决定。
- 同一文件同时包含既有改动和任务改动并不自动构成阻塞；能够区分两者并验证结果完整保留既有改动时
  继续，否则停止并请求用户决定。
- 除非用户另行授权 commit，否则保留未提交的任务改动。该要求也适用于 `implement`；未取得资格的
  linked worktree 遵循相同边界。

## Task Worktree

- 当用户要求隔离、Harness 或适用 Skill 要求隔离、并行工作需要独立状态，或必须通过隔离保护
  checkout 既有状态时，应用 `create-worktree`。由其负责 linked-worktree 的选择、就绪和 Task
  Worktree 资格认定。
- 在合格的 Task Worktree 中，实施工作流可以无需单独授权，通过仓库正常 commit hook 创建仅含任务
  改动的 Checkpoint Commit。
- 实施及其初次 review 完成时，应用 `finish-worktree`。由其负责目标同步、最终 review、收束为一个
  Task Commit、结果选择、准确授权、执行、验证、恢复和生命周期清理。

## 远程操作

- 任一工作区中的 commit 授权都不包含 push 或 pull request。只有用户明确要求相应结果时，才执行
  对应远程操作。
