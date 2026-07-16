---
name: worktree-integrate
description: named linked Git worktree 中已验证的实现需要返回当前 checkout 供人工审查，或用户明确要求本地提交时使用。
---

# Worktree 集成

在不丢失本地变更的情况下返回已验证任务工作。默认使用 review mode；只有用户明确要求已提交的本地集成时才使用 commit mode。

## 模式选择

- **Review mode：** 将任务结果具体化为 unstaged 或 untracked 工作，同时保留 base HEAD、index 和无关本地变更。
- **Commit mode：** 只有明确请求且任务路径不与 base 本地变更重叠时，才 fast-forward base 分支。

绝不把含糊请求解释为 commit mode。

## 任务分支准备

1. 要求 linked、named 任务分支和非 detached HEAD。
2. 确认任务验证已通过。分类任务 worktree 中 staged、unstaged 和 untracked 变更；包含确认属于任务的工作，并在所有权含糊时停止。
3. 使用 `git worktree list --porcelain` 和 Git common directory 发现 base checkout 和分支。不要假设 `main` 或 `master`；预期 base 含糊时停止。
4. 将任务相对 merge base 的工作整理为恰好一个 business commit。
5. 将该 commit rebase 到当前 base HEAD。只自动解决任务范围内、无歧义且可验证的冲突；否则 abort rebase 并请求方向。
6. 要求任务 worktree 干净，并在整理或 rebase 改变内容时重新运行受影响检查。

## Base Snapshot 和恢复数据

1. 记录 base 分支、HEAD、index tree、staged 变更、unstaged 变更和 untracked 文件。
2. 计算最终任务路径并在仓库外备份。在 manifest 中记录文件类型和原本不存在的路径。不要 stash。
3. 传输前立即将 base 分支和 HEAD 与 snapshot 比较。任一移动时，再次 rebase 任务 commit，并刷新 snapshot、受影响路径和备份。

## Review Mode

1. 保持 base HEAD 和 index 不变。
2. 对没有 base 本地变更的任务路径，先检查传输，再只更新 working tree。不要使用会写 index 的 checkout、apply 或 restore 模式。
3. 对重叠文本路径，在临时文件中三方合并任务 commit parent、当前 base working file 和任务结果。共享 pathname 本身不是冲突。
4. 只有结果无歧义、限于任务范围且可验证时才自主解决。
5. 遇到 delete/modify 冲突、复杂 rename、二进制冲突、互斥行为、含糊生成输出或任何无法验证的合并时停止。项目提供确定性 generator 时，从事实源重新生成文件。
6. 在 base checkout 中只运行已知非修改型检查。没有充分检查时报告限制，不要运行 formatter、generator 或 fixer。
7. 证明记录的 HEAD 和 index tree 未改变、原 staged 状态已保留、合并文件同时包含本地与任务工作，并且返回的任务变更保持 unstaged 或 untracked。

成功完成 review-mode 传输后保留任务分支、worktree 和外部备份。报告其位置，便于用户独立检查和恢复来源。

## Commit Mode

1. 任何任务路径存在 staged、unstaged 或 untracked base 本地工作时，报告重叠并改用 review mode；已请求 commit mode 时明确降级到 review mode。
2. 再次确认任务分支包含一个已 rebase 的 business commit，并在集成前立即复查 base 分支和 HEAD。
3. 从 base 分支运行 `git merge --ff-only`。
4. fast-forward 被拒绝时停止，并保持 base 及其本地变更不动。
5. 重新运行相关验证，并证明无关 base 本地状态未改变。
6. 验证通过后按创建所有权清理：将平台创建的 worktree 委托给该平台；只从 base checkout 删除 Git fallback worktree，然后安全删除已集成任务分支。

## 验证和恢复

- 完整结果形成前传输或自动合并失败时，只从外部备份恢复触碰路径。
- 传输后验证失败时，保留返回的 working-tree 结果、任务分支、worktree 和备份。报告准确失败命令供人工审查。
- 在用户接受 review 结果前保留恢复数据。

## 禁止操作

此 skill 绝不执行 push、pull、force-update、stash、reset、clean 或创建 merge commit。对于 PR、保留分支或丢弃结果，交给 `superpowers:finishing-a-development-branch`。

## 结果

报告所选模式、任务 commit、传输或集成路径、重叠决策、验证、保留的 base 状态、恢复数据以及任何保留的 worktree 或分支。
