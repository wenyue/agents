# 工作流配置

强度：`Mandatory`

适用范围：子 Agent 委派、Superpowers 启用条件、工作树工作流归属和 Git 安全。

## 委派

- 自动授权 Agent 根据任务需要使用 Subagent。

## Superpowers

- 将 `superpowers:using-superpowers` 视为已禁用。其他 `superpowers:*` Skill 根据各自的触发条件和
  适用的更高优先级规则直接判断。
- 编写 Skill 时使用 `write-skill`，编写 Rule 时使用 `write-rule`。仅在用户明确要求对抗性行为评测
  或压力测试时使用 `superpowers:writing-skills`。
- 仅在用户明确要求 brainstorming 时使用 `superpowers:brainstorming`。

## 工作树工作流

- 在遵守上述 Superpowers 策略的前提下，工作树的创建时机、检测、授权、位置选择和创建过程，
  均由 `superpowers:using-git-worktrees` 负责。
- 创建工作树后，如果目标仓库提供 `worktree-environment-setup` Skill，应先使用它，再执行
  `superpowers:using-git-worktrees` 要求的基线验证。
- 具名关联 worktree 中的实现完成并通过验证时，先提供四种选择，再执行操作：在本地合并到已记录的
  基准分支；推送并创建 pull request；保留任务分支和 worktree；或集成到当前 checkout。
- 按用户选择的结果直接执行，不再重复询问：集成到当前 checkout 使用 `worktree-integrate`；
  本地合并、pull request、保留分支或用户明确要求的丢弃使用
  `superpowers:finishing-a-development-branch`。
- 即使当前 checkout 位于已记录的基准分支，也要将本地合并和集成到当前 checkout 视为不同结果。
  本地合并会推进基准分支；`worktree-integrate` 的 review mode 保持当前 `HEAD` 和 index 不变，
  将任务改动作为 unstaged 或 untracked 内容交回，并保留无关本地改动。
- 只有用户明确要求整合后创建本地提交时，才使用 `worktree-integrate` 的提交模式，并将所有业务改动放在
  一个提交中。

## Git 安全

- 保留已有本地改动。某项操作会覆盖、stash、reset、clean 或丢弃这些改动时，停止并改用无损方案，
  或请求用户决定。
- 同一文件存在改动重叠并不必然构成阻塞。置信度高且结果可验证时可以合并；否则停止并询问用户。
- 只有用户明确要求远程操作后，才能推送或创建拉取请求。
