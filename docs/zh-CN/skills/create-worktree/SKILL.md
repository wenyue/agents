---
name: create-worktree
description: 当会改变仓库状态的工作因并行执行、宿主或工作流隔离，或保护当前 checkout 而需要隔离的 Task 或 Batch Worktree 时使用。
---

# 创建 Worktree

本 Procedure-led Skill 创建或复用一个具名关联 Git worktree，在保留基准 branch、index 和既有
本地状态的情况下为 owning workflow 准备就绪。它负责 worktree 的选择、创建、验证、Task 或 Batch
Worktree 资格认定，以及机械所有权交接。业务实施、完成后的改动集成、tracker 状态和清理由各自
owner 负责。

## 建立准备契约

1. 准确选择一个 role：用于一个 accepted task 的 Task Worktree，或用于一个 frozen Ticket Batch
   的 Batch Worktree。记录调用方提供的 `scope_owner`、预期路径或小写连字符 slug、具名分支、精确
   base commit、后续 `integration_owner` 和 `cleanup_owner`，以及宿主是否已创建预期 worktree；若已
   创建，则记录调用方提供的 `creation_owner`。
2. 对照调用方提供的精确 base commit，确定唯一的基准 checkout 和具名基准分支。检查当前分支和
   `HEAD`、Git 公共目录及 `git worktree list --porcelain`；预期基准处于 detached 状态或存在歧义，
   或解析结果与所提供的 commit 不同时停止。不得以当前分支 tip 替换它。
3. 在任何变更前，快照记录基准 checkout 的 branch、`HEAD`、commit tree、index tree、staged、
   unstaged 和 untracked 状态，以及全部已注册 worktrees 和本地分支。该快照是 preservation boundary，
   也是 qualification 使用的 accepted base。

## 选择并验证 Worktree

1. 只有宿主为这一准确 task 或 batch 创建当前关联 worktree 时才复用它。要求其具名分支、`HEAD`、
   commit tree 和 local-state ownership 与准备契约匹配；否则停止且不予 qualification。
2. 对于新 worktree，选择 `<base-root>/.worktrees/<slug>`，并遵循已验证的仓库分支约定；没有该约定
   时使用 `worktree/<slug>`。验证分支名称，并要求路径和分支在文件系统、已注册 worktrees 和本地
   分支中均不存在。
3. 对于 `<base-root>/.worktrees/` 下的每个所选路径，无论复用还是新建，都要求根 `.gitignore` 包含
   有效的仓库相对 `.worktrees/` 条目。条目缺失或无效时，只有 `.gitignore` 为项目所有，且编辑能够
   保留并区分全部现有内容和本地状态，才追加 `.worktrees/` 作为可生效的最小修复；将其记录为有意的
   项目自有变更。当文件由工具生成、只读、归属不明，或编辑会与无法区分的本地工作重叠时停止。
4. 使用 `git check-ignore -v` 证明每个所选的仓库相对 `.worktrees/` 路径在任何修复后均由根
   `.gitignore` 忽略；全局 exclude 或 `.git/info/exclude` 不充分。对于新 worktree，取得创建这一
   精确目录和 worktree 所需的权限。该权限不授权无关的 Git 或文件系统变更。

## 创建并核验

1. 创建前立即对照已记录契约重新检查基准分支、`HEAD`、commit tree、路径和分支。任何值发生移动
   或出现时，在创建前停止，并报告 recorded 和 current values 以及保留的 snapshot。
2. 宿主提供原生 worktree 创建能力时，必须使用该能力，并将其具体 lifecycle owner 记录为
   `creation_owner`。只有该能力不可用时，才使用 Git fallback，并将执行
   `git -C <base-root> worktree add -b <task-branch> <worktree-path> <base-commit>` 的具体 Agent
   记录为 `creation_owner`。
3. 使用 `git worktree list --porcelain` 核验 path、branch 和 `HEAD` 等于所选值。重新检查基准
   checkout 的 `HEAD`、commit tree、index tree 和既有本地状态均与快照匹配；只允许已记录的
   `.worktrees/` `.gitignore` 新增项。
4. 创建失败时，检查 Git worktree 元数据和所选路径。只移除已证明由本次尝试创建且不含用户工作的
   不完整产物。无法证明时保留证据，并带准确的 recovery owner 和 action 停止。安全移除后，重复
   pre-creation checks 并重试一次。第二次失败时保留所有剩余证据并停止。

## 准备并认定资格

1. 在所选 worktree 中继续。当目标仓库提供 `worktree-environment-setup` 时，在 baseline
   verification 前应用它。
2. 环境准备后运行仓库声明的 baseline verification。失败基线是既有证据：在实施前停止，除非用户
   为此 worktree 明确接受。仓库未声明 baseline 时，不予 qualification 并停止，除非 owning
   workflow 或用户明确接受 unavailable baseline。不得用 completed-change verification 替代或
   虚构命令。
3. 只有 worktree 使用一个具名分支、其 `HEAD` 和 commit tree 等于 accepted base、baseline 通过
   或已被明确接受，且每个本地路径都只属于 accepted scope 时，才认定所选 role。Task Worktree
   属于一个 accepted task。Batch Worktree 属于一个 frozen Ticket Batch，将其 base 记录为
   immutable delivery target，并且只能包含该 batch 的 ordered Task Commits 和 batch-review
   checkpoints。
4. 存在所有权不明确本地状态的复用 worktree 仍是普通 worktree：它不获得 Task 或 Batch
   qualification，也不授权自主创建 Checkpoint Commit。只有 environment、baseline 和 qualification
   都满足目标仓库契约后，才报告 ready。保留每个失败的 worktree 用于诊断，不得自动丢弃证据。

## 结果

返回一个 preparation handoff，其中包含 `status`；所选 `role`、`worktree`、`branch`、精确 `head`
和 `tree`；base checkout、branch、精确 commit 和 tree，以及保留的本地状态；`scope_owner`、
`creation_owner`、`integration_owner` 和 `cleanup_owner`；预期 path 或 slug、`.gitignore` 结果和
允许的 local-state scope；环境准备和 baseline commands、results 及 accepted failures；qualification
结果和原因；以及在未就绪时保留的 state、failed phase 和 next owner。调用方在实施或 finalization 前
重新检查该 handoff。handoff 不推断 Ticket dependencies 或 tracker semantics，也不授予超出其记录值
的权限。
