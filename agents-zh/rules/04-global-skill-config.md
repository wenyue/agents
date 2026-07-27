# 工作流配置

强度：`Mandatory`

适用范围：子 Agent 委派、Superpowers 启用条件与执行计划语言、工作树工作流归属和 Git 安全。

## 委派

- 自动授权 Agent 根据任务需要使用 Subagent。

## Superpowers

- 将 `superpowers:using-superpowers` 视为已禁用。其他 `superpowers:*` Skill 根据各自的触发条件和
  适用的更高优先级规则直接判断。
- 编写 Skill 时使用 `write-skill`，编写 Rule 时使用 `write-rule`。仅在用户明确要求对抗性行为评测
  或压力测试时使用 `superpowers:writing-skills`。
- 仅在用户明确要求 brainstorming 时使用 `superpowers:brainstorming`。
- 具体的 Superpowers 执行计划使用英语。此例外只适用于分步实现计划，不适用于设计文档。

## 工作树工作流

- 在遵守上述 Superpowers 策略的前提下，工作树的创建时机、检测、授权、位置选择和创建过程，
  均由 `superpowers:using-git-worktrees` 负责。
- 创建工作树后，如果目标仓库提供 `worktree-environment-setup` Skill，应先使用它，再执行
  `superpowers:using-git-worktrees` 要求的基线验证。
- 实现完成后使用 `worktree-integrate`。它的默认审查模式会将改动作为未暂存或未跟踪内容送回当前检出，
  同时保留当前 `HEAD`、索引和无关本地改动。
- 只有用户明确要求整合后创建本地提交时，才使用 `worktree-integrate` 的提交模式，并将所有业务改动放在
  一个提交中。
- 需要创建拉取请求、保留分支或丢弃分支时，使用 `superpowers:finishing-a-development-branch`。

## Git 安全

- 保留已有本地改动。某项操作会覆盖、stash、reset、clean 或丢弃这些改动时，停止并改用无损方案，
  或请求用户决定。
- 同一文件存在改动重叠并不必然构成阻塞。置信度高且结果可验证时可以合并；否则停止并询问用户。
- 只有用户明确要求远程操作后，才能推送或创建拉取请求。
