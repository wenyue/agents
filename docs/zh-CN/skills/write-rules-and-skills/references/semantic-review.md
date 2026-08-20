# Semantic Review

本 reference 负责 review packet、Semantic Review 关卡和 reviewer verdict。父 Skill 负责关卡顺序、
reviewer 隔离、finding 分类处理、修正和 handoff。所选生命周期与语义类型 reference 负责适用的
counterexample 和 Acceptance portfolio。

## 提供有界 packet

向 reviewer 提供：

- 已接受结果和语义账本；
- Readiness 要求 Behavior Control 时所选的任务及其原始结果；
- 完整候选工件、自有资源以及加载或分发表面；
- 治理证据和适用 reference；以及
- 精确的机器验证结果和未测试表面。

排除 diff、作者推理、怀疑的缺陷、预期修复和预期 verdict。

## 尝试证伪候选工件

完整阅读候选工件，并用两到四个风险最高且有证据支持的反例尝试证伪它。返回单独的 Semantic
Review `PASS` 或 `FAIL`。

每个阻塞 finding 都要指出其关卡、证据、具体反例，以及一种共享 finding 分类。对于
`decision-required`，还要指出确切的未决选择、decision owner，以及每种有依据且实质不同的结果所
对应的证据；finding 的数量不构成这种证据。
