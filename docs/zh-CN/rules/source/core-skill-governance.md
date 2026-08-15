# Skill 治理

强度：`Mandatory`

适用范围：项目、插件和外部 Skill 之间的 Skill 权限、优先级与工作流路由。

## 权限

- 每个 Skill 都必须在用户直接指令和所有适用 Rule 的约束内执行。Skill 可以定义更具体的过程或完成
  gate，但不得扩大授权、削弱 Mandatory Rule，或重新定义其他 owner 的政策。
- 适用 Skill 重叠时，应用范围更具体的 Skill。具体性相同时，项目本地 Skill 优先于插件分发的 Skill；
  外部来源本身不产生额外的优先级层级。

## 规划与交付

- 开始会改变状态的实施前，判断已接受的对话、issue、Spec 或其他来源是否已经定义稳定的范围、决策和
  验收标准。
- 当重要行为、契约、测试 seam 或范围决策仍是隐含信息，或需要持久且可审查的单一事实来源时，建议
  用户调用 `to-spec`。
- 当已接受的工作包含多个可独立验证的切片、阻塞关系、并行工作，或工作量超出一个全新实施上下文
  应承担的范围时，建议用户调用 `to-tickets`。Tickets 可以从已接受的 Spec 或当前对话开始。
- 当一个已接受的来源已经使单一范围任务可实施且可验证时，无需 Spec 或 Tickets 即可继续。
- 使用 `implement` 执行来自对话、issue、Spec 或 Tickets 的已接受实施工作。它在
  `smartkit/core-workspace-policy` 选定的工作区中负责实施、验证和 code review。
- Skill 在 `.scratch/` 或 `docs/adr/` 下写入规划或决策产物时，使用英文编写该产物。

## 边界

- Skill 指令涉及工作区选择、本地 Git 状态、commit、push 或 pull request 时，应用
  `smartkit/core-workspace-policy`。
- Harness 原生工具、能力和事件语义由匹配的 Harness Adaptation 负责。
