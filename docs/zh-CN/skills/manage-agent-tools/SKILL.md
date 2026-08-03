---
name: manage-agent-tools
description: 当需要诊断或在用户批准后升级 Codex、Cursor、Copilot、Superpowers、CodeGraph 或 Tokscale 时使用。
---

# 管理智能体工具

这个共享的操作型 Skill 用于诊断当前平台的推荐工具策略，只在用户明确批准后执行维护。它先进行只读诊断；新的检查报告剩余问题后结束。项目 Hook 可以诊断，但绝不安装或升级任何工具。

## 归属与策略

- 插件在 `config/recommended-tools/` 中维护权威策略。
- 项目快照在 `references/recommended-tools/` 中维护其复制的策略；检查器优先使用这些文件，因此 Hook 检查的是安装它的快照。
- `setup-project-agents` 负责项目快照和显式 Hook 启用。本 Skill 不修改项目配置、插件缓存或 Hook 信任。

## 诊断

1. 确定当前平台为 `codex`、`cursor` 或 `copilot`。无法确定时询问用户并停止。
2. 将当前 `SKILL.md` 所在目录解析为 `MANAGE_AGENT_TOOLS_ROOT`。
3. 在 POSIX 上运行 `sh "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.sh" check --platform PLATFORM`；在 Windows 上运行 `& "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.ps1" check --platform PLATFORM`。
4. 将此命令视为只读：退出码 `0` 表示策略已满足，`1` 表示发现问题，`2` 表示诊断失败并停止维护。
5. 报告选用的策略路径，并将每项发现归类为缺失、版本不可读、版本过旧、必需值不匹配或检测器失败。

## 经批准的升级

1. 提出命令前，确定每个受影响工具的安装来源。
2. 展示确切命令、受影响工具和预期效果。请求批准，并在执行任何命令前结束本轮。
3. 获得批准后，只通过原生管理器执行已批准的命令：
   - Copilot 插件使用 `copilot plugin update`。
   - Codex 插件刷新已配置的市场，并使用可用的 Codex 原生安装或更新流程；执行前报告确切的受支持命令。
   - Cursor 插件在没有稳定的非交互更新命令时，引导用户使用 Cursor 官方扩展 UI。
   - CodeGraph 或 Tokscale 的包管理器或安装来源不明确时停止，报告候选来源并请求决定。
4. 不要用其他管理器替代已知的原始管理器。不要编辑插件缓存、平台信任存储或编辑器信任数据。
5. 再次运行诊断，并报告执行过的命令、结果及未解决问题。

## Hook 边界

作为 SessionStart Hook 调用时，检查器可以使用每日缓存、锁、超时和平台原生输出。它只能诊断并渲染发现项；不得调用安装或升级执行器、修改配置，或请求隐式批准。

## 停止条件

- 未获得对确切命令的批准时，在修改前停止。
- 诊断失败或 CodeGraph、Tokscale 的来源不明确时，不进行修改。
- 同一已批准升级命令失败两次后停止；报告两次失败和下一项安全的手动操作。

## 验证与结果

- [ ] 每次经批准的修改后运行诊断；确认退出状态和剩余发现项。
- [ ] 确认每条执行过的命令与获批命令完全一致。
- [ ] Hook 运行时，确认它只产生诊断输出。

报告平台、策略路径、修改前后的发现项、获批命令、命令结果及未完成工作。
