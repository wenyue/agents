# Skill

Skill 负责一项完整的触发式工作。对于普通工件，本 reference 应用于候选工件本身。对于生成契约，
它定义指导必须为未来目标确定的语义。

## 确立工作与 Skill Shape

根据已接受意图、当前 Skill mechanics 和治理证据，确定 objective、actor、trigger、evidence、
inputs、preconditions、outcome、owner、boundaries、completion、stop、failure、validation 和
handoff。只有证据表明 actions、ordering、recovery、resources 和 commands 会改变执行时才确定
它们。每个适用字段都需要一个有依据的值；只有当证据证明字段不会改变工作时才省略它。

选择一种 Skill Shape：

- **Judgment-led** 是默认值。根据 objective、evidence、principles、invariants、decision
  boundaries 和 prioritized exits 构建 Judgment Frame，并把方法留给 Agent 判断。
- **Procedure-led** 仅在流程会改变正确性、安全性、外部协议合规性、协调、恢复或已接受结果时，
  使用 Job Graph 和 Execution Paths。
- **Hybrid** 从 Judgment Frame 开始，只添加有界 Procedural Islands。每个 island 在其
  prioritized exit 后把控制权交还 Agent 判断。

作者偏好的大纲、希望显得完整，或未经验证的历史顺序，都不能证明规定流程合理。当一个建议步骤只
为改变 Agent 默认行为而存在，且没有观察到的 failure 证明其必要性时，使用生命周期 reference 的
Behavior Control。

对于生成契约，要求指导识别用于选择每个适用目标字段的证据，并在证据仍允许实质不同的工作、owner、
resource、command 或 exit 时停止。不要仅为了让契约看起来完整而虚构目标工作流。

## 确定 invocation metadata

在首次写入候选工件之前，把 model invocation 作为默认值，并根据已接受意图和证据判断是否有必要使用
user-only invocation。保持两种 Harness 表示一致：

- 对于新 Skill，使用 model invocation 继续，无需向用户显示选择；只有当证据表明该 Skill 不应被自动
  发现或调用时才例外。在该例外中，主动建议 user-only invocation，说明实质取舍，并停止等待用户选择。
- 对于现有 Skill，保留其有依据的 invocation 选择。当证据支持更改该选择，或当前表示相互冲突时，
  给出建议及其影响，然后停止等待用户选择；否则，无需向用户显示选择即可继续。
- 通过省略 `disable-model-invocation` 表示 model invocation；省略
  `policy.allow_implicit_invocation` 仍是其有效默认值。当自动路由或另一个 Skill 触达该工作属于其契约
  时，建议显式设置 `policy.allow_implicit_invocation: true`，并把省略视为差异。user-only invocation
  使用 `disable-model-invocation: true` 和 `policy.allow_implicit_invocation: false` 表示。

在同一个 Candidate Revision 中维护 Skill 的 `agents/openai.yaml`。缺失时创建；更新时保留有依据的
interface metadata；只根据上述已确定的选择更改 invocation policy。

## 投影一项完整工作

- 让主文件具备 Entry Sufficiency：识别 Skill Shape、objective 或 entry、适用的 Judgment Frame
  或 Execution Path，以及每个有条件需要的 resource，而不加载无关细节。
- 对 Judgment-led 工作，陈述 evidence、principles、invariants、decision boundaries 和
  prioritized exits，不规定没有依据的方法。
- 对 Procedure-led 工作，让每条真实 Execution Path 可见且 Path-sufficient。把每个分支放在其
  trigger 旁边，且仅当顺序会改变正确性、安全性或结果时使用有序步骤。
- 对 Hybrid 工作，让 Judgment Frame 保持主要地位，只在触达 trigger 时披露对应 Procedural
  Island。
- 为每个 Judgment Frame 和 Execution Path 指定一个有优先级的 completion、stop 或 failure
  出口。说明条件重合时由哪个出口决定；completion 不能绕过必需的 validation、cleanup、
  preservation 或 handoff。
- 只为已验证且允许恢复的 failure 声明 recovery。保留有用的 partial state，并把缺失的决定、
  权限或范围交给其 owner。
- 仅对重复、脆弱且确定性的工作使用自有脚本。定义其 dependencies、inputs、outputs、failures、
  recovery 和安全的代表性 tests。
- 只引用运行工作需要的 resource，并说明何时读取或执行。把持久政策保留在单独拥有的 Rule 中。
- 使用 heading 表示工作阶段或真实分支，使用 numbered list 表示有序动作，使用 bullet 表示独立要求。

## 审查并验收 Skill 语义

Semantic Review 根据候选工件和证据重建完整工作、所选 Skill Shape、Judgment Frame 和适用的
Execution Paths。以下情况应判定失败：字段隐含、规定没有依据的流程、虚构 action、command、
dependency、owner、recovery 或 result、缺少 prioritized exit、出口不可达或过早完成。

只选择风险最高的相关案例：

- normal completion；以及
- 候选工件影响的 non-completion 路径，例如 missing precondition、stop、failure、recovery、
  handoff 或 coincident condition。

与 `ordinary-artifact.md` 一起使用时，对触发式工作和任务应用通用 Acceptance Runner 协议。与
`generation-contract.md` 一起使用时，fresh reviewer 静态验证指导能获取所需证据，并为相同输入
类别选择一个动作或 stop。不要为契约 Acceptance 启动 Runner 或创建目标。
