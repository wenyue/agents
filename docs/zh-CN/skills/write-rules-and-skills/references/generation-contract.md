# 生成契约

生成契约（Generation Contract）是一个独立的指导工件，用来指导另一个 Agent 编写完整的未来
Rule 或 Skill。本 reference 负责契约本身；未来目标的类型选择 `rule.md` 或 `skill.md`。

## 确定指导契约

根据活动 owner 和项目证据解决每个适用部分：

- 编写 actor、调用或触发条件、已接受请求和所需证据；
- 未来目标的语义类型、owner、包装或 schema、写入位置和允许的辅助变更；
- 有序编写动作、保留边界、目标验证和 handoff；以及
- completion、实质歧义 stop、执行 failure、recovery 和重合出口优先级。

应用契约当前有效的包装机制，不要把宿主或项目事实复制到这个跨项目 reference 中。所选语义类型
reference 定义未来目标必须包含什么。契约必须告诉 Agent 如何从证据确定每个适用目标字段，以及
当证据未能选出唯一结果时在哪里停止。

## 编写可用指导

- 把 inputs、evidence sources、decisions、actions、exits、validation 和 handoff 放在另一个 Agent
  需要它们的位置，使其易于发现。
- 使用可观察谓词。`valid`、`complete` 或 `supported` 等标签不能替代使其成立的事实。
- 保留现有目标语义，除非当前证据或明确批准支持变更。不要把目标自有的运行政策或流程放进契约。
- 当 intent、owner、packaging、schema、write location、authority 或 preserved behavior 仍允许
  实质不同的目标时，在写入目标前停止。
- 仅对重复、脆弱、确定性的工作使用自有脚本。定义并测试其 inputs、outputs、dependencies、
  failures、recovery 和 public entry。
- 要求以后创建的真实目标进入 Ordinary Artifact 路由，并在采用前通过其自身当前的机器验证、
  Semantic Review、Acceptance 和 handoff。

## 静态验收契约

不要启动 Acceptance Runner、生成虚假目标或虚构项目来 qualification 契约。Semantic Review
通过后，由 fresh reviewer 使用以下类别中风险最高且有证据支持的两到四个输入，走查完整指导：

- 不清楚的 intent 或缺失的目标证据；
- 未解决的 owner、packaging、schema、write location 或 authority；
- 相互冲突的证据，或会丢失受支持行为的变更请求；以及
- 相关 validation、resource、failure、recovery 或 coincident-exit 边界。

对每个案例，验证另一个 Agent 无需臆造事实或出口，就能识别一个下一步动作或一个明确 stop、继续所需
证据、允许的写入、目标验证和 handoff。正常运行契约自有的确定性资源；静态 Acceptance 不能替代
其机器测试。

当指导对每个选定案例都完整且可执行时，契约 Acceptance 才通过。它不声称尚未创建的未来目标已经
通过。之后编写的目标是新的 Ordinary Artifact 候选，默认使用不同的 fresh reviewer，且不继承
契约结论。
