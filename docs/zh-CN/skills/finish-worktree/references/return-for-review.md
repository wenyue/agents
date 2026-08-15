# 返回供审查

在不推进 base 分支或改变其 index 的情况下，将 Task Commit 的净结果放入 base working tree。

1. 记录 base `HEAD`、index tree、staged 变更、unstaged 变更和 untracked 路径。在仓库外备份每个
   任务路径，并在 manifest 中记录原始文件类型和原本不存在的路径。
2. 从 Task Commit 的唯一 parent 与其 tree 之间的完整 diff 推导任务结果。对于没有 base 本地变更的任务路径，
   先检查待传输内容，再通过不改变 index 的方式只更新 working tree。
3. 对重叠的文本路径，在临时文件中以 merge-base 内容、当前 base working file 和任务结果执行三方
   合并。将相同路径名视为可合并证据，而不是冲突本身。
4. 只解决无歧义、属于任务范围且可验证的合并。遇到 delete/modify 冲突、复杂 rename、二进制冲突、
   互斥行为、归属不明的生成输出或任何无法验证的结果时停止。只有项目提供确定性 generator 且其变更
   已被单独授权时，才从源头重新生成文件。
5. 在 base checkout 中只运行已知不会修改文件的检查。没有足够的检查可用时，报告这一限制，不得
   改为运行 formatter、generator 或 fixer。
6. 证明已记录的 base `HEAD` 和 index tree 未改变、原有 staged 状态得到保留、合并后的文件同时包含
   兼容的本地工作和任务工作，并且返回的任务变更是 unstaged 或 untracked。
7. 保留任务分支、worktree 和外部备份。报告其位置，确保用户接受审查结果前，任务来源和恢复数据
   均可被独立检查。

如果传输在形成完整结果前失败，只从外部备份恢复被触碰的路径。如果传输后验证失败，保留返回的
结果和所有恢复数据供人工审查。
