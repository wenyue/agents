# Skill 编写

一个 Skill 拥有**一项完整任务**。其 trigger 开始任务；completion、stop 和 failure 条件定义每种
出口。本分支负责 Skill 分类、任务边界、发现、分发、脚本、资源和生成 gate。

## 固定任务

固定 actor、trigger、inputs、preconditions、start、actions、outcome、owner、boundaries、completion、
stop、failure、validation 和 handoff。每个适用字段必须有一个明确值；缺失字段必须有经过验证的
不适用理由。

选择一种 class：

| 条件 | Class | 契约 |
| --- | --- | --- |
| 一个仓库拥有并执行完整任务 | Project-local Skill | 编码已验证的仓库事实，对自有脚本使用项目既有 runtime，并在仓库请求的结果处完成。 |
| 一个分发的 Skill 跨仓库执行同一稳定工作流 | Shared Skill | 在 runtime 发现 target fact，使用稳定协议路径和明确 stop，并在代表性上下文中保持一个支持的结果。 |
| 一个分发的产物编写完整的 target-owned Skill | Shared Skill-generation contract | 将编写工作流与生成的 runtime 任务分离，然后要求不同的 Review、Acceptance 和 handoff gate。 |

删除本地细节不会使 Skill 变成共享 Skill。只有其任务跨仓库稳定且可在 runtime 发现 target-specific
fact 时才使用共享 class。只有 operational、diagnostic 或 orchestrator 的区别会改变所有权、执行、
gate 或完成条件时，才记录该区别。

当每个契约字段都有一种有依据的解释，且每个出口都明确时，任务固定完成。

## 扩展证据

除共同证据外，还要收集：

- 请求的 trigger、inputs、start、completion、stop、failure、handoff 和排除的任务职责；
- 所属 Skill 目录、caller、resource、script、index 和每个 discovery entry；
- 对于 project-local Skill，执行它所需的每项仓库事实和命令；
- 对于 shared Skill，代表性仓库和平台，以及必须在 runtime 发现的每项 target fact；以及
- 对于生成契约，一个代表性 target 及其编写、审查、验收和交接表面。

只有每个任务分支、命令、仓库或平台声明，以及可能影响执行的自有表面都有依据，证据才充分。将项目
政策保留在 Rules 中。

## 编写任务

- 保持主路径可见。将每个条件分支放在其 trigger 旁边，并为每个有序步骤提供可观察出口。将仅分支
  参考移到主路径之后或 context pointer 后。
- 使用具体祈使句和精确对比。将可复用过程保留在 Skill 中。
- 对重复、确定性或脆弱工作使用脚本。陈述其依赖、失败、恢复和安全的代表性测试。
- 当 Skill 创建或更新长期 Rule 时，也选择 Rule 分支；只有 Rule 通过其独立 gate 后，该工作才完成。

对于 Skill，heading 表示任务阶段或真实条件分支。Numbered list 表示顺序会影响正确性或安全性的
有序动作。Checklist 要明确每项独立验证、验收或交接的动作、对象和可观察结果。

## 构造 Skill

使用 `writing-for-agents` 定义的 discovery metadata 和 invocation choice。Skill name 使用小写连字符，
不超过 64 个字符，并与目录匹配。在一个 H1 后用简短段落陈述结果和边界。保持所有权、start、
completion、stop、failure、validation 和 handoff 可发现。

- 只引用一层自有资源，并说明何时需要每项资源。只有 Skill 会在输出中消费 asset 时才添加它。
- 将 wrapper 限制为平台 metadata 和一个 source reference。除非外部分发契约要求，否则不添加
  README、changelog、installation guide 或 quick reference。
- 为每个共享脚本工作流提供配对的 `.sh` 和 `.ps1` 入口。两者面向同一结果，同时允许已验证的平台
  差异。在不支持的平台上明确停止。
- 对于生成契约，定义 target 证据和要求的生成结果，不虚构 target fact。将编写过程与生成 Skill 的
  runtime 过程分离。在 Review Gate 审查完整候选，在代表性 target 的 Acceptance Gate 中实际执行，
  两者通过后才交接。保留候选、证据、两个决定，以及每个未解决或未测试表面。

## 完整 Skill Gate

除完整产物 Gate 外，Skill 只有满足以下条件才通过：

- 其 class、所有者、discovery metadata、actor、trigger、inputs、preconditions、start、actions、
  outcome、boundaries、resources、scripts、validation 和 handoff 均明确或可验证地不适用；
- completion、stop、failure 和 handoff 覆盖每个出口；并且
- 另一个 Agent 无需虚构步骤或出口就能发现并执行完整任务。

## 证明 Skill

- 测试变更任务及其自有资源的正常完成，以及每个相关 stop、failure、明确错误和恢复路径。
- 使用项目 runtime 验证 project-local script。对于配对的共享入口，运行当前平台入口，并将另一个
  报告为未运行。
- 在声称广泛可移植性时，于实质不同的 target 上执行 shared Skill。
- 对于生成契约，分别保留完整候选通过 Review，以及其真实工作流在代表性 target 中通过 Acceptance
  的证据。

## 审查 Skill

在共享独立审查步骤中，针对以下检查尝试证伪完整 Skill：

- 将 class、所有者、actor、trigger、inputs、preconditions、start、actions、outcome、boundaries、
  completion、stop、failure、validation 和 handoff 重建为字段到值到证据的矩阵。任何隐含值或缺少
  依据的不适用声明均判定失败。
- 为主路径、每个条件路径和每个相关的同时发生失败构建分支到出口矩阵。任何没有出口、存在多个未
  定优先级出口、出口不可达，或绕过必要 validation、cleanup 或 preservation 的完成声明均判定失败。
- 从 trigger 到 handoff 检查 discovery metadata、context pointer、script、resource、wrapper 和平台
  分支。任何缺少可执行所有者的重复确定性或脆弱动作，或必须虚构 command、dependency、failure、
  recovery 或 output 的步骤均判定失败。
- 走查正常完成和有代表性的 stop、failure、recovery 与 handoff 情况。当结果基数或所有权改变结果
  时，覆盖零个、一个和多个结果，以及已知和无法发现的所有者。对于生成契约，分别检查生成 Skill
  的 runtime job、Review、Acceptance 和 handoff。
- 只要另一个 Agent 能根据相同的有依据事实采取不同动作或出口，就返回 `FAIL`，并提供准确段落、
  违反的 gate 和反例。
