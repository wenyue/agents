# Owner Gate

Owner Gate 判断已接受的义务应归属于 Rule、Skill、二者，还是均不属于。它在写入 Candidate
Revision 前运行，也为父 Skill 提供只读的 Ownership Review 出口。

## 对义务分类

使用已接受的请求、语义账本、现有工件（如有）、更宽和更窄的 owner，以及可发现的环境事实。
逐项独立分类：

- `rule`——跨触发式工作持续约束决策的政策；
- `skill`——由触发条件启动并产生一个有界结果的工作；
- `environment-owned`——可从代码、配置、schema、工具输出或其他活动 owner 可靠获得，因此不值得
  缓存在工件中的事实；或
- `ambiguous`——当前证据仍支持实质不同的 owner。

返回一个完整结论：`rule`、`skill`、`split`、`environment-owned` 或 `ambiguous`。
`split` 要求至少有一项由 Rule 独立拥有的义务和一项由 Skill 独立拥有的义务。对于生成契约，
分类未来目标的义务，并把目标运行时政策或流程留在契约之外。

## 比较所有权

将受支持的结论与请求的 owner 比较；对于现有工件，还要与当前 owner 比较。

- 二者一致时，不询问所有权问题并继续。不能仅因为创建或编辑的是 Rule 就要求另行批准。
- 二者冲突时，说明证据、每种有依据的放置方式对行为和加载的影响，以及建议的保留、移动或拆分
  结果。返回 `decision-required`，并在用户选择 owner 前停止写入候选。
- 两个方向使用同一边界：Rule 到 Skill 与 Skill 到 Rule 的重新归属都需要这个明确的所有权决定。
- 结论为 `ambiguous` 时返回 `decision-required`。不要用请求的包装方式来决定语义所有权。

完整结论为 `environment-owned` 时，指出活动 owner 和可发现证据，返回 no-candidate 结果，并停止，
不写入 Rule 或 Skill。

所选 owner 仍必须满足对应的 Rule 或 Skill 语义及完整 Acceptance Standard。用户选择解决的是
所有权意图；它不会把持续政策变成触发式工作，也不会免除语义关卡。

## 返回 Ownership Review

对于明确的只读 review，检查所选工件以及发现重复或错位所需的相关 owner。针对每个工件返回：

- 当前 owner 和受支持的 owner；
- 每项义务的分类和完整结论；
- 证据、影响、建议和任何确切缺失的决定；以及
- 所有权一致时返回 `PASS`，否则返回 `decision-required`。

声明未修改任何文件，然后停止，不创建 Candidate Revision，也不启动 Pruning、机器验证、
Semantic Review 或 Acceptance。
