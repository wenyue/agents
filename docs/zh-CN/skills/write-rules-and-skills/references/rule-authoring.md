# Rule 编写

一个 Rule 是**一项政策、一个所有者和一种含义**。本分支负责 Rule 分类、政策边界、强度、范围、
分发和生成契约。

## 固定政策

固定政策、所有者、强度、范围、适用性、优先级、例外、边界和结果。每个适用字段必须有一个明确值；
缺失字段必须有经过验证的不适用理由。

选择一种 class：

| 条件 | Class | 契约 |
| --- | --- | --- |
| 一个仓库拥有并直接应用该政策 | Project-local Rule | 根据已验证的仓库事实陈述最终政策。将相关要求和例外保留在拥有它们的最窄 project Rule 中。 |
| 一个分发的 Rule 跨仓库直接应用稳定政策 | Shared Rule | 只陈述稳定的跨仓库政策、语义 target 条件、支持的例外和项目本地优先级。将具体实现和更窄决定留在本地。 |
| 一个分发的产物编写完整的 target-owned Rule | Shared Rule-generation contract | 将编写工作流与完整的 target-owned Rule 分离。定义证据、审查、验收和交接，不虚构 target 政策。 |

删除本地细节不会使 Rule 变成共享 Rule。只有政策本身跨仓库稳定时才使用共享 class。当其 class 和
每个契约字段都有一种有依据的解释时，政策固定完成。

## 扩展证据

除共同证据外，还要收集：

- 请求的强度、范围、优先级、例外和排除的政策职责；
- 所属 Rule family、更宽和更具体的 Rules、强制点和生成所有者；
- 对于 project-local Rule，应用它所需的每项仓库事实和模块关系；
- 对于 shared Rule，代表性仓库、稳定的跨仓库政策和支持的项目本地 override；以及
- 对于生成契约，代表性 target Rule family、优先级系统、生成表面和 validator。

只有每项政策选择和可能影响应用的仓库声明都有依据，证据才充分。将可复用过程保留在 Skills 中。

## 编写政策

- 以 governing policy 开头。将每项条件与其要求的结果和例外放在一起。
- 用最近假阳性压力测试每个阈值、分类和条件到结果的映射。陈述排除该情况所需的每个谓词；`valid`、
  `control` 或 `fixed point` 等标签不能承载未陈述的前置条件。
- 在拥有每项当前要求的最窄 Rule 中只表达一次。更宽的 Rule 不得重复或静默覆盖更具体的 Rule。
- 使用可观察的条件和结果。将有序执行过程移入 Skill，除非这是一个编写顺序会改变结果的生成契约。

对于 Rule，heading 表示稳定政策区域或真实适用性分支。只有在顺序会改变结果的有序 Rule-generation
sequence 中才使用 numbered list。政策 checklist 要明确主体、要求的动作或属性和可观察结果。

## 构造 Rule

每个最终 Rule 都以以下内容开头：

```markdown
# Rule Title

Strength: `Mandatory|Default|Advisory`

Scope: One sentence naming the Rule's owned responsibility.
```

只有自有政策需要时才添加 `Boundaries`、`Exceptions` 或 `Precedence`。生成契约要使其生成证据、
完整 target 内容、审查、验收和交接可分别发现。

## 完整 Rule Gate

除完整产物 Gate 外，Rule 只有满足以下条件才通过：

- 其 class、所有者、强度、范围、适用性、优先级、例外和边界均明确或可验证地不适用；
- 每个阈值、分类和条件到结果的映射都能排除最近假阳性，不依赖未定义标签或隐含谓词；并且
- 另一个 Agent 无需虚构执行过程就能确定要求的结果。

## 证明 Rule

- 对于 project-local Rule，在当前仓库中验证具体声明、强制点、例外和跨 Rule 关系。
- 对于 shared Rule，在带有项目本地优先级和支持 override 的代表性上下文中执行。
- 对于生成契约，生成并审查至少一个完整的代表性 target Rule；声称广泛可移植性时使用实质不同的
  target。

## 审查 Rule

在共享独立审查步骤中，针对以下检查尝试证伪完整 Rule：

- 将 class、所有者、强度、范围、适用性、优先级、例外、边界和结果重建为字段到值到证据的矩阵。
  任何隐含值或缺少依据的不适用声明均判定失败。
- 为每个阈值、边界、重叠、范围和排除项构建条件到结果矩阵。测试每一行最近的假阳性和假阴性；任何
  可能改变结果的未定义标签或谓词均判定失败。
- 走查有代表性的更宽 Rule、更具体 Rule、优先级和例外组合。任何产生两个结果、没有结果或未声明
  override 的情况均判定失败。
- 检查 Rule 陈述的是政策，而不是要求虚构执行顺序。对于生成契约，分别检查完整生成 Rule、生成
  证据、Review、Acceptance 和 handoff。
- 只要另一个 Agent 能根据相同的有依据事实得出不同政策结果，就返回 `FAIL`，并提供准确段落、违反
  的 gate 和反例。
