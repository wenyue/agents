---
name: write-rules-and-skills
description: 在创建、重写或实质更新 SmartKit Rule、Agent Skill 或 Rule/Skill 生成契约时使用，包括项目级或共享工件、自有资源以及发现或分发表面。
---

# 编写 Rule 和 Skill

根据已接受意图和已验证证据，编写最小而完整的工件。先应用 `writing-for-agents`，处理信息层级、
有目的的 Markdown 和 Skill 调用机制。本 Skill 负责共享工作流；所选 reference 负责生命周期和
语义类型要求。

## 路由候选工件

写入前，对两个相互独立的属性进行分类：

1. **生命周期**——普通工件（Ordinary Artifact）被直接使用；生成契约（Generation Contract）
   指导另一个 Agent 编写未来目标。
2. **语义类型**——Rule 表示一项持续生效的政策；Skill 表示一项触发式工作。

生成契约是独立的指导工件。决定语义类型 reference 的是其未来目标，而不是契约的文件扩展名或
包装方式。

| 候选工件 | 完整读取 |
| --- | --- |
| 普通 Rule | [`references/ordinary-artifact.md`](references/ordinary-artifact.md) 和 [`references/rule.md`](references/rule.md) |
| 普通 Skill | [`references/ordinary-artifact.md`](references/ordinary-artifact.md) 和 [`references/skill.md`](references/skill.md) |
| Rule 生成契约 | [`references/generation-contract.md`](references/generation-contract.md) 和 [`references/rule.md`](references/rule.md) |
| Skill 生成契约 | [`references/generation-contract.md`](references/generation-contract.md) 和 [`references/skill.md`](references/skill.md) |

当一个请求同时包含持久政策和可执行工作时，创建分别拥有 owner 的 Rule 与 Skill 候选工件。
当每个候选工件都有一个生命周期、一个语义类型、一个 owner，且两个 reference 均已加载时，
路由才算完成。

## 达到写入就绪状态

首次写入候选工件前，根据已接受意图和当前证据确定：

- 请求的结果、必须保留的语义、已批准的变更、非目标和安全边界；
- 工件 owner、允许的写入、上层与下层 owner，以及受影响的加载、资源、生成和分发表面；以及
- 当前行为、适用的项目 Rule 与宿主机制、验证接缝，以及任何可能改变政策、动作、目标或出口的
  环境事实。

写入前，应用所选生命周期 reference 要求的任何 Behavior Control，并保留其选定任务和原始结果，
供 review 使用。

只有在现有证据仍允许实质不同的行为、所有权、写入目标、权限、副作用或出口时才提问。否则，
记录唯一受支持的事实并继续。把项目事实保留在其当前 owner 中；可复用 Skill 应发现这些事实，
而不是缓存它们。

当所有选定 reference 都能在不存在实质未知项的情况下应用时，写入准备才算通过。

## 构建一个 Candidate Revision

写入前，为每项可独立变化的义务记录一行：

| 义务 | 证据 | Owner | 处置 | 候选位置 |
| --- | --- | --- | --- | --- |

仅当谓词、例外、owner、动作、恢复或出口可以独立变化时才拆行。不要拆分保持相同行为的措辞选择。
每一行只能有一个 owner，以及一个 `preserve`、`change`、`add`、`move` 或 `retire` 处置。
当一项未解决义务仍允许实质不同的结果时停止。

根据账本综合生成完整候选工件。将现有工件用作遗漏检查的证据，而不是新结构的大纲。保留受支持的
决定和安全边界。每项义务只在最窄的 owner 中出现一次。除非会改变运行，否则不要把工作证据、
来源、验证记录和 reviewer 指令放进运行工件。

**Candidate Revision** 是活动项目或宿主所选工作区内的一份完整当前内容状态。它不是复制出来的
修订目录，也不是强制报告。脱离前一版本和 diff 阅读它。只有在生命周期和语义类型要求都通过，
且另一个 Agent 无需臆造条件、事实、步骤、owner 或出口即可使用该工件时，才能继续。

## 对阻塞 finding 分类

在 Pruning、Review 和修正中统一使用以下分类：

- `uniquely-forced`——当前证据确定了一种范围内修正，且不引入新政策、权限、行为、范围或副作用；
- `decision-required`——当前证据仍允许两种或更多种有依据且实质不同的结果，或修正需要新的意图、
  证据、权限、范围或外部动作。

逐条 finding 独立分类。finding 的数量不改变其分类；一起应用当前全部 `uniquely-forced` 修正。
每个 `decision-required` finding 都要指出确切的未决选择、decision owner，
以及每种有依据且实质不同的结果所对应的证据。缺少这些要素时，应将 finding 分类为
`uniquely-forced` 或非阻塞项，而不是请求确认。

## 执行 Pruning Gate

在机器验证前，完整读取 [`references/pruning-agent.md`](references/pruning-agent.md)，并让一个未参与
候选编写的 fresh Pruning Agent 应用它。

在不添加行为的前提下应用 **修正直至稳定**，并在修正期间保持使用同一个 Pruning Agent。将每个
revision 与账本重新对齐，并要求相对于基线的每项增长都映射到一项独立且有依据的义务。

Pruning Agent 不写入候选文件，也不能在之后担任该候选的 Reviewer 或 Acceptance Runner。fresh
Pruning Agent 不可用时停止并报告。

## 验证并冻结

针对每个已变更 owner，以及受影响的加载、资源、生成或分发表面，运行活动项目要求的检查。机器
验证可以证明 schema、标识符、注册、资源可达性、生成关系、文件系统效果、脚本结果、状态转换和
进程退出。它不能证明自然语言语义；关键词检查、散文快照、完整标题快照、复制的期望值或作者编写的
政策解释器，均不能替代 Semantic Review。

如果必需的机器检查失败，在语义关卡前停止。报告精确命令、最终退出状态、相关输出、未运行关卡和
未验证表面。不要把走查称为机器 PASS。

在有界 Review Packet 中记录成功命令、最终退出状态和未测试表面。除非活动 owner 要求，不要创建
持久验证报告。

review 前冻结候选写入。

## 审查并验收

完整读取 [`references/semantic-review.md`](references/semantic-review.md)，并让一个未参与候选编写的
fresh reviewer 应用它。对于普通工件，还要在 reviewer 开始 Acceptance 前完整读取
[`references/acceptance-runner.md`](references/acceptance-runner.md)。

reviewer 先返回 Semantic Review `PASS` 或 `FAIL`。仅当该关卡通过后才开始 Acceptance。应用所选
生命周期和语义类型的 portfolio：普通工件 Acceptance 使用一个隔离的 fresh Runner；生成契约
Acceptance 由 reviewer 静态走查，不使用 Runner，也不生成目标。返回单独的 Acceptance `PASS` 或
`FAIL`。

对每个阻塞结果应用共享 finding 分类。

每个候选工件都使用自己的 fresh reviewer；独立候选的 review 可以并行进行，但不得共享证据或结论。
fresh reviewer 不可用时停止并报告。

## 修正直至稳定

出现任何有效的 `decision-required` finding 时，在修正前停止，并且只询问其确切的缺失决定。当所有
finding 都是 `uniquely-forced` 时，无需请求确认，直接一起应用当前全部修正。内容变化会创建新的
Candidate Revision，并使所有依赖它的机器验证、Review 和 Acceptance 结果失效；按正常顺序重跑这些
关卡。修正后的 revision 接受完整候选 Semantic Review 和受影响的 Acceptance，并为每个受影响的
普通工件 case 使用一个新的隔离 Runner。

持续修正，直至所有关卡通过。当同一个 finding 在修正后原样再次出现，或建议的修正不会改变候选
内容时，以无进展停止。报告该 blocker，不要请求用户授权再次进行相同尝试。

成功要求 Pruning Gate、机器验证、Semantic Review 和 Acceptance 对同一个 Candidate Revision
全部通过。报告候选工件的生命周期、语义类型、owner、保留内容与批准变更、受影响表面、大小比较、
精确命令和退出状态、pruning、review、acceptance 与 correction 结论，以及所有未解决或未测试表面。
每次停止都要报告 blocker、已完成证据、未运行关卡和下一个 owner。发布、安装、commit、push 和
其他外部动作交给各自 owner。
