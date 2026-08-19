# Skill

Skill 负责一项完整的触发式工作。对于普通工件，本 reference 应用于候选工件本身。对于生成契约，
它定义指导必须为未来目标确定的语义。

## 确定工作

根据已接受意图、当前 Skill mechanics 和治理证据，确定 actor、trigger、inputs、preconditions、
start、actions、outcome、owner、boundaries、completion、stop、failure、recovery、validation、
resources 和 handoff。每个适用字段都需要一个有依据的值；只有当证据证明字段不会改变执行时才省略它。

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

## 编写一项完整工作

- 让主路径保持可见。把每个分支放在其 trigger 旁边，且仅当顺序会改变正确性、安全性或结果时使用
  有序步骤。
- 为每条路径指定一个有优先级的 completion、stop 或 failure 出口。说明条件重合时由哪个出口
  决定；completion 不能绕过必需的 validation、cleanup、preservation 或 handoff。
- 只为已验证且允许恢复的 failure 声明 recovery。保留有用的 partial state，并把缺失的决定、
  权限或范围交给其 owner。
- 仅对重复、脆弱且确定性的工作使用自有脚本。定义其 dependencies、inputs、outputs、failures、
  recovery 和安全的代表性 tests。
- 只引用运行工作需要的 resource，并说明何时读取或执行。把持久政策保留在单独拥有的 Rule 中。
- 使用 heading 表示工作阶段或真实分支，使用 numbered list 表示有序动作，使用 bullet 表示独立要求。

## 审查并验收 Skill 语义

Semantic Review 根据候选工件和证据重建完整工作和分支到出口的映射。以下情况应判定失败：字段隐含，
虚构 action、command、dependency、owner、recovery 或 result，或者路径没有出口、存在多个无优先级
出口、出口不可达或过早完成。

只选择风险最高的相关案例：

- normal completion；以及
- 候选工件影响的 non-completion 路径，例如 missing precondition、stop、failure、recovery、
  handoff 或 coincident condition。

与 `ordinary-artifact.md` 一起使用时，对触发式工作和任务应用通用 Acceptance Runner 协议。与
`generation-contract.md` 一起使用时，fresh reviewer 静态验证指导能获取所需证据，并为相同输入
类别选择一个动作或 stop。不要为契约 Acceptance 启动 Runner 或创建目标。
