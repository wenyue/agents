---
name: worktree-environment-setup
description: 创建或修订目标仓库的环境准备 skill，用于已经创建的 linked Git worktree 时使用。
---

# Worktree 环境准备

生成目标自有 skill，用于准备已经创建的 linked Git worktree，并在项目环境可供实现时停止。

## 证据

读取 `.agents/rules/20-project-tools.md`、manifest、lock file、setup script、CI workflow、生成文件所有权、必需本地服务和 readiness check。识别 Windows 与非 Windows 主机所需的最小可重复准备。

## 编写工作流

1. 确定生成 skill 如何识别 linked worktree，并在任何修改前拒绝 primary checkout。
2. 复用最窄的仓库自有 setup 入口，只添加当前证据表明确实缺失的准备。
3. 同时生成 `SKILL.md`、`scripts/setup.ps1` 和 `scripts/setup.sh`。把可执行命令序列放在脚本中；让 `SKILL.md` 只负责调用方式、前置条件、可选分支和 readiness。
4. 让两个脚本都在命令失败时停止，并能在部分 setup 后安全重跑。
5. 按下述契约审查完整目录。

## 生成 Skill 契约

- 要求在已经创建的 linked worktree 中执行。在安装依赖、生成文件、改变服务或其他修改前拒绝 primary checkout。
- Windows 使用 `scripts/setup.ps1`，非 Windows 主机使用 `scripts/setup.sh`。要求相同的核心环境结果，同时允许有证据支持的平台差异。
- 从 skill 或仓库根目录解析路径；绝不依赖调用者的当前目录。
- 将昂贵、可选或任务特定的准备排除在默认路径之外，除非每个新 worktree 都需要它。
- 使用真实项目配置和必需工具或服务行为验证 readiness，不要只检查版本。
- 在环境就绪时停止。排除 worktree 创建或删除、baseline 验证、业务变更、commit、integration 和 agent 同步。
- 将已完成变更验证交给 `change-set-verification`。
- 不负责验证触发时机、范围选择或结果策略。

## 失败恢复

要求生成的 `SKILL.md` 包含自己的 `## Failure Recovery`。任一主机脚本失败时立即停止，报告准确命令和错误，分析原因，并提出具体脚本或环境变更。候选变更通过审查前，不要继续 setup 或重试修改后的脚本。

## 审查和交付

确认脚本内部一致、按主机选择、可重跑，并且只负责环境准备。将完整生成目录和支持证据交给 `setup-project-agents` 进行候选审查和验收。
