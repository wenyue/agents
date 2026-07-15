# 项目验证 Skill 生成设计

## 目标

在 `wenyue/agents` 中新增 `project-verification` 项目 Skill 生成契约。目标项目重新运行
`setup-project-agents` 后，从当前仓库证据生成稳定的验证流程；公共目录不保存任何目标项目的
具体命令或路径。

## 职责边界

`20-project-tools.md` 只记录工具事实，包括用途、命令、工作目录、范围能力、修改属性、
safe-fix 能力、前置条件、外部依赖、输出和成本。验证触发、执行顺序、去重、风险升级、基线
处理和结果汇报属于生成后的 `project-verification`。

公共 Skill 必须保持跨项目可移植。项目生成 Skill 可以记录由当前目标仓库证据支持的具体路径、
命令和约束，不得把这些项目事实反向写入 `wenyue/agents`。

生成的 `worktree-environment-setup` 只负责把环境准备到可实现、可验证状态，随后把完整变更集
验证交给 `project-verification`，不再内嵌验证触发或范围选择流程。

## 生成契约

生成后的 `project-verification` 在一个完整代码变更集准备交付时触发，活跃实现、调试和连续
编辑期间不触发。它必须排除无关 dirty files，根据测试归属、依赖关系、项目映射和已有选择器
选取最小充分验证，并且每个独立验证面只执行一次。

依赖、测试基础设施、共享契约、生成接口或未知影响使范围无法可靠封闭时，Skill 自动升级到
子系统或全量验证。找不到测试映射不能自动解释为“不需要测试”。昂贵验证可以由廉价聚焦检查
做前置失败筛选。

Skill 先执行非修改检查。只有实际范围内诊断出现，且 Project Tools 明确标记工具支持路径级
safe-fix 时，才允许执行一次自动格式化或安全修复。unsafe fix、无范围 fixer、行为性重写和
无关 cleanup 一律禁止；修复后必须重跑受影响检查并报告所有修改。

每个验证面使用 `passed`、`failed`、`inconclusive` 或 `not applicable`，同时报告命令、范围、
选择理由、修复和缺口。疑似历史失败只按需比较同一个失败项，不运行基线全量套件。

默认只生成 `SKILL.md`。多语言、多包或特殊映射较多时增加
`references/verification-matrix.md`。优先引用仓库已有选择器，只有确定性重复逻辑无法可靠复用
时才生成 Skill 自有脚本。

## Review 与 Acceptance

`setup-project-agents` 使用同一个子代理生成项目规则、`worktree-environment-setup` 和
`project-verification`。完整候选必须先通过 Review，确认工具事实、验证矩阵、风险升级和
safe-fix 均有仓库证据，且没有无条件全量验证或无意义重复。

环境 Skill 先在真实临时 linked worktree 中验收。环境就绪后验收验证 Skill 的聚焦选择、无关
文件排除、条件 safe-fix、失败阻止昂贵后续检查、高风险升级和状态报告。Acceptance 不为证明
命令存在而运行昂贵全量套件；只有目标仓库证明全量检查廉价且每次变更必需时例外。

任何生成脚本报错都立即停止。不得在临时 acceptance worktree 中热修或跳过失败；必须回到目标
项目 current branch 修复完整候选、重新 Review、复制字节一致内容，并从 Acceptance 第一步
重新执行。通过前候选保持未接受状态。
