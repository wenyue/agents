# Skill 配置

强度：`Mandatory`

适用范围：项目对工作流工具、worktree、Git 和文本输出的覆盖规则。

## Subagent 委派

- 当任务明显受益于有边界的并行委派时，用户授权 Codex 创建 subagent，无需每次重复授权。
- 委派内容应具体且自包含。并行编辑代码时分配互不重叠的写入范围。
- 不要委派主 agent 为保持关键路径推进而应直接处理的即时阻塞任务。
- 最终回复应说明 subagent 的用途，以及其修改是否已集成。

## Superpowers

- 不得主动调用 `superpowers:brainstorming`。
- 只有用户明确要求时才使用 `superpowers:brainstorming`。
- 其他 `superpowers:*` skill 遵循各自触发条件和更高优先级规则。
- 其他位置对 Superpowers 的引用不构成自动启用 `superpowers:brainstorming` 的授权。

## Git 与 Worktree

- 在遵守上述 Superpowers 政策的前提下，将 worktree 的时机、检测、同意、位置和创建交给 `superpowers:using-git-worktrees`。
- 创建 worktree 后，如果目标仓库存在 `worktree-environment-setup` skill，先使用它，再运行 `superpowers:using-git-worktrees` 要求的基线验证。
- Worktree 实现完成后使用 `worktree-integrate`。默认 review 模式在保持当前 HEAD、index 和无关本地修改不变的情况下，将修改作为 unstaged 或 untracked 工作返回当前 checkout。
- 只有用户明确要求提交式本地集成时才使用 `worktree-integrate` commit 模式。任务业务修改必须形成一个 commit；允许在当前分支另建一个基础设施 commit，将缺失的 worktree 目录加入 `.gitignore`。
- PR、保留分支或丢弃结果使用 `superpowers:finishing-a-development-branch`。
- 不得覆盖、stash、reset、clean 或静默丢弃已有本地修改。同文件重叠不自动构成 blocker：有高把握且可验证时合并，否则停止并询问。
- 除非用户明确要求远程操作，否则不要 push 或创建 PR。

## 文本输出

- 普通面向用户的文本、设计文档及其他非代码文本文件使用简体中文。
- 具体 Superpowers 执行计划使用英文。此例外仅适用于逐步实现计划，不适用于设计文档。
