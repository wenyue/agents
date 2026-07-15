---
name: worktree-environment-setup
description: 用于为已经创建的 Git worktree 定义或生成目标仓库的环境设置 skill。
---

# Worktree 环境设置

生成一个归目标仓库所有的 skill，依据当前仓库证据准备一个已经创建的关联 Git worktree。

## 编写工作流

1. 阅读 `.agents/rules/20-project-tools.md`、清单文件、锁文件、设置脚本、CI 配置和生成文件所有权。
2. 推导在新关联 worktree 中使依赖、生成文件、本地服务和项目工具可用所需的最小准备工作。
3. 一并生成 `SKILL.md`、`scripts/setup.sh` 和 `scripts/setup.ps1`。把可执行命令序列放在脚本中，`SKILL.md` 只关注何时以及如何调用它们。
4. 复用范围窄的仓库自有设置入口。只添加当前证据证明缺失的准备步骤。
5. 说明前置条件、平台选择、可选分支、就绪检查和失败报告，但不要重复脚本内容。

## 生成契约

- 要求在已经创建的关联 worktree 内执行，并在修改前拒绝主检出目录。
- Windows 使用 `scripts/setup.ps1`，非 Windows 主机使用 `scripts/setup.sh`。要求两者产生相同的核心环境结果，但不要求另一平台的 shell。
- 从 skill 或仓库根目录解析路径；命令失败即停止；在部分设置完成后可安全重跑。
- 除非证据证明每个 worktree 都需要，否则将昂贵或任务特定的准备保留为可选项。
- 在环境就绪处停止。排除 worktree 生命周期、基线验证、业务改动、提交、集成和 agent 同步。
- 将已完成变更的验证交给 `change-set-verification`。不要负责验证触发时机、范围选择或结果策略。

## 失败恢复

由于两个设置入口都是可执行脚本，要求生成的 `SKILL.md` 包含自己的 `## Failure Recovery` 小节。任一脚本失败时，指示 agent 立即停止，报告准确命令和错误，分析原因，并提出具体的候选修改。在提案得到审查前，不得继续设置、隐藏失败或重试已修改脚本。

## 交接

把完整生成目录和辅助证据交给 `setup-project-agents`。候选项审查与验收由该工作流负责。
