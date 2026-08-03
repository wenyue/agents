---
name: manage-agent-tools
description: 当需要检查、诊断、安装或升级受支持的智能体平台、Superpowers、CodeGraph 或 Tokscale 时使用。
---

# 管理智能体工具

诊断当前平台声明的工具策略，并通过工具原本的插件管理器或包管理器应用经用户批准的修复。全新无缓存检查不再报告发现项时任务完成；否则报告每个尚未解决的发现项及其原因。

## 归属

- 本 Skill 负责交互式诊断，以及经用户批准的工具维护。
- `references/recommended-tools/<platform>.json` 负责目标版本、检测器以及安装或升级指引。
- 项目 SessionStart Hook 可以用 `hook` 模式调用检查器；它只报告发现项，绝不修改工具。
- `setup-project-agents` 负责项目配置和 Hook 安装，不负责修改第三方工具。

## 工作流

1. 根据当前运行时将活跃平台确定为 `codex`、`cursor` 或 `copilot`。如果无法识别运行时，请用户指定平台，并结束本轮。
2. 将当前活跃 `SKILL.md` 所在目录解析为 `MANAGE_AGENT_TOOLS_ROOT`；不要假设 Skill 位于仓库本地的 `.agents/` 路径。
3. 在 POSIX 上运行 `sh "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.sh" check --platform PLATFORM`；在 Windows 上运行 `& "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.ps1" check --platform PLATFORM`。
4. 如果命令以 `0` 退出，报告声明的策略已满足，然后停止。
5. 如果命令以 `2` 退出，报告诊断失败并包含 stderr；不要尝试安装或升级。
6. 如果命令以 `1` 退出，将每个发现项分类为工具缺失、版本不可读、版本过旧、必需值不匹配或检测器失败。
7. 对每个缺失或过旧的工具，检查它的安装来源。Superpowers 使用活跃平台的插件管理器；CodeGraph 和 Tokscale 使用可执行文件位置及可用的包管理器元数据。
8. 修改前展示确切命令和受影响工具。请用户批准这些命令，并结束本轮。
9. 获得批准后，只执行已批准的命令。已知原始安装来源时，不要改用另一种包管理器。
10. 再次执行无缓存检查。报告已满足的工具、尚未解决的发现项、已执行命令，以及任何失败命令。

## 停止条件

- 未获得用户批准时，在修改前停止。
- 安装来源存在歧义时，不进行修改；报告候选来源并请求用户决定。
- 同一工具的升级命令失败两次后停止；报告两次失败和下一项安全的手动操作。
- 不要编辑平台信任存储。Hook 信任仍然必须由用户执行明确的平台操作。

## 验证

- 确认最终检查器退出状态。
- 确认执行的每条命令都包含在用户批准范围内。
- 确认 SessionStart Hook 模式没有执行安装或升级命令。

## 结果

报告平台、策略路径、修改前后的发现项、已批准命令、命令结果，以及尚未完成的工作。
