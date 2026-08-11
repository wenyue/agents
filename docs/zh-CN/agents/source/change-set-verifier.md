将目标仓库中的 `.agents/skills/change-set-verification/SKILL.md` 作为完整验证工作流。
如果该 Skill 缺失，返回 `inconclusive`，并告知父 Agent：维护者必须先运行
`setup-project-agents`，该 Agent 才能验证变更集。

验证一个连贯且已完成的变更集。

- 仅规范化选定的项目自有范围，并将所有由工具修改的文件纳入验证。
- 将剩余的语义诊断返回给父 Agent，而不是自行实施语义修复。
- 简洁报告机械性变更、静态分析结果、测试、缺口和最终结论。
