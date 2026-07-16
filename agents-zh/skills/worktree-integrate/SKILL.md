---
name: worktree-integrate
description: 当具名关联 Git worktree 中已通过验证的实现需要返回当前检出目录供人工审查，或用户明确要求完成本地提交集成时使用。
---

# Worktree 集成

在不丢失本地变更的前提下交回已验证的任务成果。默认使用 review mode；只有用户明确要求以本地提交完成集成时，才使用 commit mode。

## 模式选择

- **Review mode：** 将任务结果放入工作区，保持为 unstaged 或 untracked，同时保留 base HEAD、index 和无关的本地变更。
- **Commit mode：** 只有用户明确提出要求，且任务路径与 base 上的本地变更没有重叠时，才 fast-forward base 分支。

绝不能将含糊的请求解释为 commit mode。

## 准备任务分支

1. 必须使用具名的关联任务分支，且 HEAD 不能处于 detached 状态。
2. 确认任务验证已通过。分别识别任务 worktree 中 staged、unstaged 和 untracked 的变更；纳入已确认属于任务的内容，所有权不明确时停止。
3. 使用 `git worktree list --porcelain` 和 Git common directory 找出 base 检出目录及其分支。不得假定分支名为 `main` 或 `master`；无法明确目标 base 时停止。
4. 将任务相对于 merge base 的全部工作整理成恰好一个业务提交。
5. 将该提交 rebase 到当前 base HEAD。只有冲突明确属于任务范围、没有歧义且可验证时，才自动解决；否则中止 rebase 并请求用户决定。
6. 确保任务 worktree 干净；如果整理提交或 rebase 改变了内容，重新运行受影响的检查。

## Base 快照与恢复数据

1. 记录 base 分支、HEAD、index tree、staged 变更、unstaged 变更和 untracked 文件。
2. 计算最终任务路径，并将其备份到仓库外部。在 manifest 中记录文件类型，以及原本不存在的路径。不得使用 stash。
3. 临近传输前，再将 base 分支和 HEAD 与快照比较。如果任一发生移动，重新 rebase 任务提交，并更新快照、受影响路径和备份。

## Review Mode

1. 保持 base HEAD 和 index 不变。
2. 对 base 上没有本地变更的任务路径，先检查待传输内容，再只更新 working tree。不得使用会写入 index 的 checkout、apply 或 restore 模式。
3. 对内容重叠的文本路径，在临时文件中以任务提交的 parent、当前 base working file 和任务结果执行三方合并。路径名相同本身不构成冲突。
4. 只有结果无歧义、属于任务范围且可以验证时，才自主解决。
5. 遇到 delete/modify 冲突、复杂 rename、二进制冲突、互斥行为、归属不明的生成输出或任何无法验证的合并时停止。如果项目提供确定性 generator，应从源头重新生成文件。
6. 在 base 检出目录中只运行已知不会修改文件的检查。如果没有足够的检查可用，报告这一限制；不得改为运行 formatter、generator 或 fixer。
7. 证明先前记录的 HEAD 和 index tree 未改变、原有 staged 状态得到保留、合并后的文件同时包含本地工作和任务工作，并且交回的任务变更仍为 unstaged 或 untracked。

成功以 review mode 完成传输后，保留任务分支、worktree 和外部备份。报告它们的位置，让用户能够独立检查任务来源并进行恢复。

## Commit Mode

1. 如果任何任务路径在 base 上存在 staged、unstaged 或 untracked 的本地工作，报告重叠并改用 review mode；用户原本要求 commit mode 时，应明确说明已经降级为 review mode。
2. 再次确认任务分支只包含一个已完成 rebase 的业务提交，并在集成前立即复查 base 分支和 HEAD。
3. 从 base 分支运行 `git merge --ff-only`。
4. 如果 fast-forward 被拒绝，立即停止，不得改动 base 及其本地变更。
5. 重新运行相关验证，并证明无关的 base 本地状态没有变化。
6. 验证通过后，按创建方的所有权进行清理：由平台创建的 worktree 交回对应平台处理；只有通过 Git fallback 创建的 worktree 才从 base 检出目录中移除，然后安全删除已经集成的任务分支。

## 验证与恢复

- 如果传输或自动合并在形成完整结果前失败，只从外部备份恢复被触碰的路径。
- 如果传输后的验证失败，保留已经交回 working tree 的结果、任务分支、worktree 和备份。报告失败的准确命令，供人工审查。
- 在用户接受审查结果前，一直保留恢复数据。

## 禁止的操作

此 skill 绝不能执行 push、pull、force-update、stash、reset、clean，也不能创建 merge commit。PR、保留分支或丢弃结果等后续操作交给
`superpowers:finishing-a-development-branch`。

## 结果

报告所选模式、任务提交、传输或集成的路径、重叠处理决定、验证结果、保留下来的 base 状态、恢复数据，以及任何仍保留的 worktree 或分支。
