# Project Rules 规范化重构设计

## 目标

规范化重写 `.agents/rules/` 下的全部规则，同时保留现有规则的职责、技术选择、
强度和大体方向。重写后的规则应更容易扫描、解释一致、边界清楚，并减少因措辞、
章节结构或重复表达造成的理解偏差。

## 范围

本次覆盖以下规则源文件：

- `00-global-rule-config.md`
- `01-global-personality.md`
- `02-global-response-format.md`
- `03-global-skill-config.md`
- `10-base-code.md`
- `11-base-cpp.md`
- `11-base-flutter.md`
- `11-base-go.md`
- `12-base-arb.md`
- `20-project-tools.md`
- `21-project-rules.md`
- `22-project-structure.md`

本次不修改 `.agents/skills/`、平台包装器、agent prompt、脚本或其他仓库资产。规则中可以
继续引用 skill，以说明职责边界和移交条件，但不重新定义 skill 内部流程。

## 保留原则

- 保留每个文件现有的 `Strength`；文件内部的措辞冲突通过澄清条目解决，不改变文件强度。
- 保留现有技术政策，包括 Flutter、Go、C++ 和 ARB 的具体技术选择、阈值及测试要求。
- 保留 `00–09`、`10–19` 和 `20–29` 的编号及职责分层。
- 保留 `.agents/rules/` 作为规则事实源、平台文件作为薄包装器的模型。
- 保留 `20/21/22` 作为一组项目规则生成契约，并维持三者现有的所有权边界。
- 只合并语义相同的重复项，不以精简为由改变规则效果。

## 规范化标准

### 文件结构

每个文件保持以下开头：

1. 一个一级标题。
2. `Strength: <level>`。
3. `Scope: <scope>`。
4. 按执行或理解顺序排列的二级章节。

不要求所有文件使用相同章节名。全局规则、语言规则和生成契约采用各自最合适的结构，
但同一规则家族保持一致。

### 规范词语

- `Must` 和 `Do not` 表示必须遵守的要求与禁令。
- `Use` 表示已经确定的项目或语言约定。
- `Prefer` 表示默认选择，允许存在有依据的例外。
- `May` 只用于明确许可的行为。
- 避免对同一强度混用 `Always`、`Never`、`should` 和含糊的建议语气。

文件级 `Strength` 决定整份规则的默认约束等级；条目措辞用于表达条目自身是否允许例外。

### 条目形态

- 每个条目表达一个主要要求。
- 当适用范围不是显而易见时，条目同时写明触发条件或适用对象。
- 例外紧跟主要要求，不放在远处章节中。
- 使用可由代码、配置、命令输出或仓库结构验证的描述。
- 保持路径、命令、符号、配置键和字面量的 Markdown 代码格式一致。
- 避免只含抽象口号的条目；抽象原则必须连接到具体行为。

### 示例

- 保留能够解释真实歧义或项目特殊写法的示例。
- 统一使用 `Avoid` / `Prefer` 或 `BAD` / `GOOD`，同一文件内不混用。
- 示例不得引入正文没有规定的新要求。
- 示例应紧邻其解释的规则。

## 分层设计

### `00–03`：全局规则

#### `00-global-rule-config.md`

保留强度定义、冲突优先级、事实源、包装器、编号约定、MCP 配置和 skill 布局。按以下顺序
组织：规则解释模型、事实源、包装器维护、编号、工具与 skill 边界。合并重复的事实源与包装器
说明，但保留新增规则和新增 subagent 时的同步要求。

#### `01-global-personality.md`

将内容组织为 `Understand`、`Change`、`Verify`、`Communicate` 四个阶段。保留根因优先、
控制范围、尊重所有权、避免无关重构、验证后报告以及失败后停止猜测等行为。标题可改为更准确的
工程工作原则名称，但不改变规则身份或路径。

#### `02-global-response-format.md`

分离必须遵守的语言及标签协议与默认格式建议。使用一张紧凑表格定义
`🎯`、`⚠️`、`✅`、`❌`、`🤖`，删除后续对同一标签的重复解释。保留英文目标复述、其余内容
默认使用简体中文、简单回复可省略标题，以及 review 与 implementation 的报告要求。

#### `03-global-skill-config.md`

保留 subagent、Superpowers、Git/worktree 和 prose 输出政策。按触发阶段明确每个 skill 的
职责移交点，减少对 skill 内部步骤的复述。保留禁止主动调用 brainstorming、禁止擅自丢弃本地
修改、未经请求不得 push 或创建 PR，以及 design 与 plan 的语言约定。

### `10–12`：基础规则

#### `10-base-code.md`

保留 ownership、naming、extraction、data/state、dependencies、control flow 和 comments。
统一为从边界与所有权到局部实现细节的阅读顺序。合并 public boundary、test seam 和 helper
extraction 中语义重叠的部分，但保留现有约束效果。

#### `11-base-cpp.md`

保留命名、函数长度、类大小、SOLID、RAII、Rule of Five/Zero、错误模型、测试数量、STL 与
并发政策。将当前压缩式句子改为完整、独立的规范条目；统一示例格式；把 magic number、类型和
资源所有权放入对应章节。固定阈值继续作为既有默认标准。

#### `11-base-flutter.md`

保留 Riverpod、`go_router`、Freezed、`json_serializable`、provider lifecycle、异步边界、
成员顺序、section comments、import 和 analysis 等全部主要方向。重写重点是：

- 将重复出现的 public surface、owner-local helper、record 和 comment 规则合并到单一所有者。
- 让每个章节先写政策，再写必要示例。
- 明确通用 Dart 规则与 Flutter/Riverpod 特定规则之间的章节边界。
- 保持现有技术选型，不将它们改写为条件性或可选建议。
- 减少同一要求在 `Boundaries`、`Data Shape`、`Data Models` 和 `Analysis Defaults` 中重复出现。

#### `11-base-go.md`

保留 `golangci-lint-v2 fmt`、行宽、linter 阈值、命名、错误、注释、并发、集合和日志政策。
将 formatter 与 lint 约束集中在一个章节；把 helper extraction 与跨语言基础规则的关系写清楚，
避免重复解释但不降低 Go 特有约束。

#### `12-base-arb.md`

保留 `zh.arb` 事实源、`en.arb` fallback、排序、key 模式、metadata 语言与长度计算规则。
按照 source files、key grammar、metadata contract、prohibited forms 排列。将 key 模式拆成可扫描的
组成部分，并确保示例与正文完全一致。

### `20–22`：项目规则生成契约

三份文件统一保留以下结构：

1. `Generation Contract`
2. `Evidence`
3. `Content`
4. `Boundaries`

#### `20-project-tools.md`

继续只管理可验证的工具事实、命令能力、运行时服务、生成入口和调用限制。保持命令清单不是执行
顺序的说明，并继续把环境准备与完成后验证流程交给对应 skill。

#### `21-project-rules.md`

继续管理 API、领域约定、生成文件语义所有权、lint 解释、持久化与生命周期行为。保持工具调用
属于 `20`、目录和依赖边界属于 `22`，并明确项目规则只记录具有稳定证据的真实约束。

#### `22-project-structure.md`

继续管理仓库布局、模块职责、依赖方向、共享位置和配置所有权。保持选择性结构地图，不生成目录
清单；只记录会影响代码放置或依赖合法性的边界。

三份生成契约使用平行句式：`Record` 表示目标规则应包含的内容，`Keep` 或 `Exclude` 表示所有权
边界，`Do not infer` 表示证据不足时不得生成的内容。

## 一致性处理

- 统一 `Dart and Flutter`、`C++`、`Go`、`ARB` 等标题大小写。
- 统一 `generated file`、`source of truth`、`ownership`、`boundary`、`verification` 等核心术语。
- 路径全部使用仓库根目录相对形式。
- 相邻规则引用使用文件名；引用 skill 时使用完整仓库相对路径。
- 删除仅由章节标题重复表达、但没有新增约束的信息。
- 不改动为了兼容平台或现有下游流程而存在的文件名。

## 验证设计

完成重写后执行以下验证：

1. 检查仅预期的 `.agents/rules/` 文件发生业务变更。
2. 运行 `git diff --check`，检查 Markdown 空白与补丁格式。
3. 运行仓库现有的 public asset/sync contract 测试，确认规则路径、元信息和引用未破坏同步。
4. 对 `.agents/rules/` 做定向搜索，检查 `Strength`、`Scope`、规则引用和术语一致性。
5. 人工比较每份文件的旧版与新版，确认主要技术政策和禁止事项均被保留。
6. 不通过修改 skill 或放宽测试来迁就规则重写；若现有测试只锁定旧措辞，则报告该验证限制。

## 风险控制

- 最大风险是规范化措辞时无意改变强度。重写时以逐文件语义对照防止 `Must`、`Prefer` 和
  `May` 之间发生漂移。
- 第二个风险是去重时丢失局部适用条件。只有适用范围和结果均相同的条目才合并。
- 第三个风险是规则与 skill 边界漂移。规则只保留长期约束和移交点，不增加多步骤 workflow。
- 仓库现有未跟踪或无关修改不属于本次范围，实施和验证均不得覆盖或清理它们。

## 完成标准

- 全部十二份规则都经过规范化重写。
- 现有技术选择、强度、职责和主要行为约束得到保留。
- 同一家族文件结构和术语一致，跨文件所有权无明显重复或冲突。
- `.agents/skills/` 及其他非规则资产没有被修改。
- 可执行的仓库验证通过；无法运行或与旧措辞耦合的验证被明确报告。
