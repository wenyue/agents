---
name: create-worktree
description: 当会改变仓库状态的工作因并行执行、宿主或工作流隔离，或保护当前 checkout 而需要关联 Git worktree 时使用。
---

# 创建 Worktree

创建或复用一个具名关联 Git worktree，使其在不改变基准 checkout 的情况下达到可实施状态。本 Skill
负责 worktree 的选择、创建、验证和准备交接；不负责业务实现、完成后的改动集成或清理。

## 前提条件

1. 检查 `git worktree list --porcelain`、当前分支和 `HEAD`、Git 公共目录，以及基准 checkout 的
   staged、unstaged 和 untracked 状态。确定唯一的预期基准分支和提交；基准处于 detached 状态或存在
   歧义时停止。
2. 选择一个小写、连字符分隔的任务 slug 和具名任务分支。遵循已验证的仓库分支约定；否则使用
   `worktree/<task-slug>`。分支或预期路径已经存在时停止，不得隐式附加或覆盖。
3. 在任何变更前，记录基准分支、基准提交、现有 worktree、现有本地分支和基准 checkout 状态。

## 选择 Worktree

- 宿主已经为本任务创建具名关联 worktree 时，复用当前 worktree。继续前验证其分支和基准。
- 否则选择 `<base-root>/.worktrees/<task-slug>`，并在宿主提供原生 worktree 创建能力时使用该能力；
  记录负责其生命周期的创建者。
- 确保根 `.gitignore` 包含仓库相对条目 `.worktrees/`。缺少该条目时，在保留现有内容的前提下只
  追加这一条，并将该编辑记录为有意的项目自有变更。`.gitignore` 由工具生成、只读或归属不明时停止。
- 在 `.worktrees` 下创建前，必须用 `git check-ignore` 证明所选路径已被忽略。全局 exclude 或
  `.git/info/exclude` 不能代替仓库 `.gitignore` 条目。
- 取得创建所选目录需要的权限。该权限只授权这一精确路径和 worktree，不授权无关的 Git 或文件系统
  变更。

## 创建并验证

1. 创建前立即确认已记录的基准分支和 `HEAD` 尚未移动，并且所选路径和分支仍不存在。
2. 使用 Git fallback 时，通过
   `git -C <base-root> worktree add -b <task-branch> <worktree-path> <base-commit>` 从已记录的基准提交
   创建具名分支和关联 worktree。
3. 通过 `git worktree list --porcelain` 验证结果中的路径、分支和 `HEAD` 与所选值一致。确认基准
   checkout 的 `HEAD`、index tree 和既有本地状态仍与已记录快照一致；只允许已经记录的
   `.worktrees/` `.gitignore` 新增项。
4. 创建失败时，重试前检查 Git worktree 元数据和所选路径。只删除已证明由本次尝试创建且不包含用户
   工作的不完整产物；否则保留产物并报告准确的恢复要求。

## 准备实施

1. 在所选 worktree 中继续。当目标仓库提供 `worktree-environment-setup` 时，应用它来准备依赖、生成
   输入和所需服务。
2. 环境准备后，运行仓库声明的基线验证。将失败基线视为既有证据，并在实施前停止，除非用户明确接受
   该基线。
3. 只有环境和基线满足目标仓库契约后，才报告 worktree 已就绪。失败的 worktree 应保留用于诊断，不得
   自动丢弃证据。

## 结果

报告基准 checkout 和提交、任务分支、worktree 路径、`.gitignore` 是否改变、创建者、环境准备、
基线结果、保留的基准状态，以及负责后续集成或清理的所有者。
