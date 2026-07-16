# 工作流配置

强度：`Mandatory`

适用范围：Subagent 委派、Superpowers 启用、worktree 工作流所有权、Git 安全和正文语言。

## 委派

- 当任务明显受益于有边界的并行工作时，用户授权 subagent 委派。无需为每个子任务重复请求授权。
- 委派工作应具体且自包含。代码编辑子任务应具有互不重叠的所有权，避免 agent 写入范围重叠。
- 当委派会拖慢关键路径时，主 agent 保留当前的阻塞任务。
- 最终回复应说明委派内容，以及委派修改是否已集成。

## Superpowers

- 不得主动调用 `superpowers:brainstorming`。
- 只有用户明确要求时才调用 `superpowers:brainstorming`。
- 其他 `superpowers:*` Skill 遵循各自触发条件和更高优先级规则。
- 对 Superpowers 的引用本身不构成启用 `superpowers:brainstorming` 的授权。

## Worktree 工作流

- 在遵守上述 Superpowers 政策的前提下，将 worktree 的时机、检测、同意、位置和创建交给
  `superpowers:using-git-worktrees`。
- 创建 worktree 后，如果目标仓库存在 `worktree-environment-setup` Skill，使用它，然后运行
  `superpowers:using-git-worktrees` 要求的基线验证。
- 实现完成后使用 `worktree-integrate`。其默认 review 模式在保持当前 `HEAD`、index 和无关本地
  修改不变的情况下，将变更作为 unstaged 或 untracked 工作返回当前 checkout。
- 只有用户明确要求提交式本地集成时才使用 `worktree-integrate` commit 模式。业务变更保持为一个
  commit；允许使用单独的基础设施 commit 将缺失的 worktree 目录加入 `.gitignore`。
- PR、保留分支或丢弃结果使用 `superpowers:finishing-a-development-branch`。

## Git 安全

- 不得覆盖、stash、reset、clean 或静默丢弃已有本地修改。
- 同文件重叠不自动构成 blocker：有高把握且结果可验证时合并，否则停止并询问。
- 除非用户明确要求远程操作，否则不要 push 或创建 PR。

## 正文语言

- 普通面向用户的正文、设计文档和其他非代码文本文件使用简体中文。
- 具体 Superpowers 执行计划使用英文。此例外仅适用于逐步实现计划，不适用于设计文档。
