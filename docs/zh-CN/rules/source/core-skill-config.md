# 工作流配置

强度：`Mandatory`

适用范围：Subagent 委派、Skill 优先级、worktree 工作流归属和 Git 安全。

## 委派

- 自动授权 Agent 根据任务需要使用 Subagent。
- 按任务选择每个 Subagent 的模型和推理强度：范围明确的辅助工作优先使用更快、成本更低的选项；
  存在歧义、跨模块或高风险的工作使用能力更强的选项。
- 保留用户、适用 Rule 或 Skill、选中的具名 Agent 要求的设置；否则按任务主动选择，不要默认继承
  父 Agent 的设置。
- 使用其他模型时，不继承父对话或只继承最少必要内容，并提供自包含的任务说明。只有任务需要完整
  父对话时，才使用会继承父模型的完整历史 fork。
- 没有合适的其他模型时，只有隔离上下文或独立执行仍有价值才委派；否则由父 Agent 完成。

## Skill 优先级

- 根据 Skill 声明的用户和模型调用元数据使用它。在职责重叠的范围内，项目本地 Skill 和更具体的
  项目 Rule 优先于内置 Skill。

## Worktree 工作流

- 对于会改变状态的实现工作，当用户要求隔离、宿主或适用 Skill 要求隔离，或者必须通过隔离保护
  checkout 中原有状态时，使用关联 worktree。不得为只读工作创建 worktree，也不得仅因任务涉及仓库
  就创建 worktree。
- 选择使用关联 worktree 时，如果宿主已经提供，应复用它；否则使用宿主的原生 worktree 能力，或在
  取得所需授权后，使用位置安全且已被忽略的 Git worktree。
- 创建 worktree 后，如果目标仓库提供 `worktree-environment-setup` Skill，应先使用它，再在实现前
  运行仓库的基线验证。
- 具名关联 worktree 中的实现完成并通过验证时，提供四种结果：在本地合并到已记录的基准分支；
  推送并创建 pull request；保留任务分支和 worktree；或集成到当前 checkout。
- 只有集成到当前 checkout 才使用 `worktree-integrate`。父 Agent 根据本 Rule 的 Git 安全约束负责
  本地合并、pull request、保留分支和用户明确要求的丢弃结果。
- 即使当前 checkout 位于已记录的基准分支，也要将本地合并和集成到当前 checkout 视为不同结果。
  本地合并会推进基准分支；`worktree-integrate` 的 review mode 保持当前 `HEAD` 和 index 不变，
  将任务改动作为 unstaged 或 untracked 内容交回，并保留无关本地改动。
- 只有用户明确要求整合后创建本地提交时，才使用 `worktree-integrate` 的 commit mode，并将所有
  业务改动放在一个提交中。

## Git 安全

- 保留已有本地改动。某项操作会覆盖、stash、reset、clean 或丢弃这些改动时，停止并改用无损方案，
  或请求用户决定。
- 同一文件存在改动重叠并不必然构成阻塞。置信度高且结果可验证时可以合并；否则停止并询问用户。
- 只有用户明确要求远程操作后，才能推送或创建 pull request。
