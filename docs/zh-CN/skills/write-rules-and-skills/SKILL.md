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
决定和安全边界；移除陈旧、重复、矛盾、过渡性或位置错误的内容。每项义务只在最窄的 owner 中
出现一次。除非会改变运行，否则不要把工作证据、来源、验证记录和 reviewer 指令放进运行工件。

**Candidate Revision** 是活动项目或宿主所选工作区内的一份完整当前内容状态。它不是复制出来的
修订目录，也不是强制报告。脱离前一版本和 diff 阅读它。只有在生命周期和语义类型要求都通过，
且另一个 Agent 无需臆造条件、事实、步骤、owner 或出口即可使用该工件时，才能继续。

## 验证并冻结

针对每个已变更 owner，以及受影响的加载、资源、生成或分发表面，运行活动项目要求的检查。机器
验证可以证明 schema、标识符、注册、资源可达性、生成关系、文件系统效果、脚本结果、状态转换和
进程退出。它不能证明自然语言语义；关键词检查、散文快照、完整标题快照、复制的期望值或作者编写的
政策解释器，均不能替代 Semantic Review。

如果必需的机器检查失败，在语义关卡前停止。报告精确命令、最终退出状态、相关输出、未运行关卡和
未验证表面。不要把走查称为机器 PASS。

在有界 Review Packet 中记录成功命令、最终退出状态和未测试表面。如果存在基线，比较行数、词数
和字节数；增长必须对应一项独立且有依据的义务，而不是符合某个数字限额。除非活动 owner 要求，
不要创建持久验证报告。

review 前冻结候选写入。内容变化会创建新的 Candidate Revision，并使所有依赖它的机器验证、
Review 和 Acceptance 结果失效。停止当前 review，而不是自动重启。

## 审查并验收

把以下有界材料交给一个未参与候选编写的 fresh reviewer：

- 已接受结果和语义账本；
- Readiness 要求 Behavior Control 时所选的任务及其原始结果；
- 完整候选工件、自有资源以及加载或分发表面；
- 治理证据和适用 reference；以及
- 精确的机器验证结果和未测试表面。

排除 diff、作者推理、怀疑的缺陷、预期修复和预期结论。每个候选工件都使用自己的 fresh reviewer；
独立候选的 review 可以并行进行，但不得共享证据或结论。

reviewer 按顺序执行两个关卡：

1. **Semantic Review** 完整阅读候选工件，并用两到四个风险最高且有证据支持的反例尝试证伪它。
   返回 `PASS` 或 `FAIL`。
2. **Acceptance** 仅在 Semantic Review 通过后开始。应用所选生命周期和语义类型的 portfolio：
   普通工件 Acceptance 使用一个隔离的 fresh Runner；生成契约 Acceptance 由 reviewer 静态走查，
   不使用 Runner，也不生成目标。它返回单独的 `PASS` 或 `FAIL`。

每个阻塞 finding 都要指出关卡、证据、具体反例，以及以下一种分类：

- `uniquely-forced`——当前证据只允许一种范围内修正，且不引入新政策、权限、行为、范围或副作用；
- `decision-required`——仍存在多种实质修正，或需要新的意图、证据、权限、范围或外部动作。

如果 fresh reviewer 不可用，停止并报告。生成契约与以后编写的真实目标是不同候选工件，默认由不同
fresh reviewer 审查，并且彼此不继承证据或结论。

## 修正一次并交接

出现任何 `decision-required` finding 时，在修正前停止并询问缺失决定。如果所有 finding 都是
`uniquely-forced`，在一次 Correction Pass 中一起修正，重跑所有失效的机器检查，并冻结新的
Candidate Revision。

把修正后的 revision、首轮 finding、治理证据和精确复验结果交给另一个 fresh Closure Reviewer。
它重新执行完整候选的 Semantic Review 和受影响的 Acceptance，并为受影响的普通工件 portfolio
使用一个新的隔离 Runner。`PASS` 结束本轮；`FAIL` 则停止。不要自动开始下一轮修正。用户决定可以
基于结果状态启动之后一次明确的 authoring run。

成功要求机器验证、Semantic Review 和 Acceptance 对同一个 Candidate Revision 全部通过。报告
候选工件的生命周期、语义类型、owner、保留内容与批准变更、受影响表面、大小比较、精确命令和退出
状态、各关卡与修正结论，以及所有未解决或未测试表面。每次停止都要报告 blocker、已完成证据、未运行
关卡和下一个 owner。发布、安装、commit、push 和其他外部动作交给各自 owner。
