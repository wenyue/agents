# Rule

Rule 负责一项持续生效的政策。对于普通工件，本 reference 应用于候选工件本身。对于生成契约，
它定义指导必须为未来目标确定的语义。

## 确定政策

根据已接受意图、当前 Rule schema 和治理证据，确定 Rule 的 class、owner、policy、strength、
scope、applicability、precedence、exceptions、boundaries 和 outcomes。每个适用字段都需要一个
有依据的值；只有当证据证明字段不会改变政策时才省略它。

对于生成契约，要求指导识别用于选择每个适用目标字段的证据，并在证据仍允许实质不同的政策时停止。
不要仅为了让契约看起来完整而虚构目标政策。

## 编写一项政策

- 以治理政策开头。把每个谓词与其要求的结果和例外放在一起。
- 每项要求保留在拥有它的最窄 Rule 中；不要复制或悄然覆盖更具体的 Rule。
- 使用可观察的谓词和结果。对于每个 threshold、overlap、range、exception 和 exclusion，拒绝
  最近的 false positive 和 false negative，不要依赖未定义标签。
- 把有序执行流程放在 Skill 中。仅当顺序会改变编写结果时，才在 Rule 生成指导中使用顺序。
- 使用 heading 表示稳定政策区域或真实适用分支，使用 list 表示并列要求，仅使用 table 表示精确
  映射或重复字段对比。

## 审查并验收 Rule 语义

Semantic Review 根据候选工件和证据重建每个适用字段及条件到结果的映射。以下情况应判定失败：字段
隐含、缺少依据的不适用、虚构谓词、重复 owner、未声明 override，或者相同事实产生两个结果或没有
结果。

只选择风险最高的相关案例：

- 一个 included 或 applicable 案例，以及最近的 excluded 或 inapplicable 案例；
- 一个受影响的 threshold、range、overlap、exception 或 owner boundary；以及
- 当另一个 Rule 可以改变结果时，一个 precedence 或 conflict 组合。

与 `ordinary-artifact.md` 一起使用时，把已加载 Rule 和任务交给真实政策接缝上的一个隔离
Acceptance Runner。要求产生可观察的决定或动作；解释 Rule 内容不属于应用。与
`generation-contract.md` 一起使用时，fresh reviewer 静态验证指导能获取所需证据，并为相同输入
类别选择一个动作或 stop。不要为契约 Acceptance 启动 Runner 或创建目标。
