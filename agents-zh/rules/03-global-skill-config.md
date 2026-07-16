# 工作流配置

强度：`Mandatory`

适用范围：子 Agent 委派、Superpowers 启用条件、工作树工作流归属与计时、Git 安全和文字语言。

## 委派

- 当任务明显适合并行处理时，用户授权进行范围明确的子 Agent 委派。无需就每个子任务反复征求授权。
- 委派内容应具体且自成一体。代码编辑子任务的归属范围必须互不重叠，避免多个 Agent 修改同一范围。
- 如果委派会拖慢关键路径，主 Agent 应自行保留一个当前阻塞任务。
- 最终回复中应说明委派了哪些内容，以及委派产生的修改是否已整合。

## Superpowers

- 不要主动调用 `superpowers:brainstorming`。
- 仅在用户明确要求时调用 `superpowers:brainstorming`。
- 其他 `superpowers:*` Skill 按各自的触发条件和更高优先级规则使用。
- 仅仅提到 Superpowers，并不构成调用 `superpowers:brainstorming` 的授权。

## 工作树工作流

- 每个创建或复用链接 Git Worktree 进行代码修改的任务都使用 `track-worktree-time`。在创建 Worktree
  或准备环境之前开始计时，跨重复阶段维护一份累计账本，并在最终交接中包含已对账的完整计时报告。
- 在遵守上述 Superpowers 策略的前提下，工作树的创建时机、检测、授权、位置选择和创建过程，
  均由 `superpowers:using-git-worktrees` 负责。
- 创建工作树后，如果目标仓库提供 `worktree-environment-setup` Skill，应先使用它，再执行
  `superpowers:using-git-worktrees` 要求的基线验证。
- 实现完成后使用 `worktree-integrate`。它的默认审查模式会将改动作为未暂存或未跟踪内容送回当前检出，
  同时保留当前 `HEAD`、索引和无关本地改动。
- 只有用户明确要求以本地提交的形式整合时，才使用 `worktree-integrate` 的提交模式。
  业务改动应放在一个提交中；如果需要将缺失的工作树目录加入 `.gitignore`，可另建一个基础设施提交。
- 需要创建拉取请求、保留分支或丢弃分支时，使用 `superpowers:finishing-a-development-branch`。

## Git 安全

- 不要覆盖、stash、reset、clean 或暗中丢弃已有的本地改动。
- 同一文件存在改动重叠并不必然构成阻塞。置信度高且结果可验证时可以合并；否则停止并询问用户。
- 除非用户明确要求远程操作，否则不要推送或创建拉取请求。

## 文字语言

- 面向用户的普通文字、设计文档和其他非代码文字文件使用简体中文。
- 具体的 Superpowers 执行计划使用英语。此例外只适用于分步实现计划，不适用于设计文档。
