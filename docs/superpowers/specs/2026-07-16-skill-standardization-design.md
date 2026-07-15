# Skill 规范化重构设计

## 背景

仓库当前包含 8 个运行时 skill，以及位于 `agents-zh/skills/` 的对应简体中文阅读镜像。
这些 skill 的方向基本正确，但写法来自不同阶段：部分文件重复规则较多，部分把项目或语言假设写成通用约束，
部分混合了作者工作流、生成结果契约和验收流程。此次重构统一它们的编写规范，同时保留原有职责、
安全边界和工作流方向。

设计参考 Agent Skills 规范、Agent Skills 官方最佳实践、OpenAI skills 范例和 Anthropic skills 范例。

## 目标

- 让每个 skill 聚焦一个明确职责，并能从 `description` 可靠判断何时使用。
- 让正文直接指导执行，减少背景解释、重复警告和互相矛盾的约束。
- 按任务脆弱程度控制自由度：安全关键流程保持严格，判断型任务保留上下文适应能力。
- 明确输入、事实源、停止条件、验证方式和输出结果。
- 保留英文运行时事实源与中文阅读镜像的逐文件对应关系。
- 通过结构校验、同步测试和代表性场景检查证明重构没有破坏原有方向。

## 非目标

- 不改变公共资产目录、同步协议、退役资产清单或平台包装器格式。
- 不新增与现有 skill 职责无关的功能。
- 不为追求统一外观而强迫不同类型的 skill 使用完全相同的章节。
- 不默认增加 references、scripts、README 或独立评测目录；只有现有复杂度确实需要时才增加资源。
- 不把中文镜像变成运行时来源，也不让同步流程管理中文镜像。

## 统一规范

### 事实源和镜像

- `.agents/skills/<name>/SKILL.md` 是唯一运行时事实源。
- `agents-zh/skills/<name>/SKILL.md` 与英文文件保持章节、命令、路径、枚举值和语义一致。
- 中文镜像只翻译说明文字，不改变代码、命令、标识符或行为强度。

### Frontmatter

- 每个文件只保留 `name` 和 `description`。
- `name` 与目录名一致，使用小写字母、数字和连字符。
- `description` 同时说明 skill 做什么和何时使用，并尽早出现关键触发词。
- `description` 只携带发现所需边界，不复述完整工作流。

### 正文

- 使用祈使语气和可执行步骤。
- 只保留代理容易遗漏的事实、顺序、边界、失败处理和项目约定。
- 合并同义警告；安全关键约束可以重复在停止条件中，但不在多个普通章节反复改写。
- 先读取目标仓库的 `AGENTS.md` 和适用规则；目标项目规则优先于通用 skill。
- 提供明确默认路径；只有默认路径不适用时才给出替代方案。
- 使用 references 进行渐进披露时，必须写清楚读取条件。当前重构预计不新增辅助文件。

### 按职责选择结构

| 类型 | 核心结构 |
| --- | --- |
| 执行工作流 | Purpose、Preconditions、Workflow、Stop Conditions、Verification、Result |
| 生成器契约 | Evidence、Authoring Workflow、Generated Contract、Review、Handoff |
| 跨仓库编排器 | Ownership、Reconciliation Workflow、Review、Acceptance、Output |
| 写作规范 | Core Principle、Decision Workflow、Examples、Validation |

章节名称可以根据内容调整，但职责不能混淆。

## 逐 Skill 设计

### `change-set-verification`

保留其作为“生成目标仓库验证 skill 的生成器契约”的方向。

- 将作者如何收集证据、如何决定是否生成脚本，与生成结果必须执行的验证流程分开。
- 保留最小充分范围、风险驱动扩展、formatter/fixer 归一化、语义修复返回父代理和四态结果。
- 合并重复的范围扩展和失败分类说明。
- 明确可选 verification matrix 或 script 的生成条件；没有证据时保持 instruction-only。
- 保留向 `setup-project-agents` 交付完整候选目录的边界。

### `worktree-environment-setup`

保留其作为“生成已创建 linked worktree 环境准备 skill 的生成器契约”的方向。

- 将证据收集、跨平台脚本生成、生成结果契约、失败恢复和交付分成清晰阶段。
- 保留拒绝 primary checkout、平台原生入口、幂等、失败即停和只负责环境就绪的边界。
- 删除与脚本内容重复的细节，要求生成的 `SKILL.md` 说明调用条件和 readiness 验证。
- 保留与 `change-set-verification`、worktree 生命周期和业务实现的职责隔离。

### `debug-mode`

保留显式启用、假设驱动、文件日志和用户复现闭环。

- 将六个阶段压缩成一致的阶段模板：目标、动作、产物、停止点。
- 保留绝对项目路径、禁止 stdout 日志、region 标记、每次复现前清空日志和确认后再清理。
- 将重复的 `NEVER` 规则合并为少量不可违反的 instrumentation contract 与 stop conditions。
- 保留日志过大时先查看规模再筛选的行为。
- 不把普通 bug 自动升级到 debug mode。

### `refactor-code`

保留 format、logic、deep 三种重构深度和逐级扩大的变更权限。

- 允许在用户意图明确时直接推断模式；只有范围会实质改变时才询问。
- 用一张模式表定义行为、公共契约和兼容性权限，再为各模式保留必要步骤。
- 抽取所有模式共用的上下文读取、范围控制、验证和死代码清理要求。
- deep 模式继续要求在改变公共接口、持久化格式或用户行为前获得明确确认。
- 删除各模式中重复的“读取、理解、验证”描述。

### `rename`

保留符号身份确认、全引用更新、生成源所有权和验证。

- 删除非标准 frontmatter 字段 `user-invocable`。
- 优先使用项目提供的语义引用工具；不可用时才使用 whole-word 全仓搜索。
- 将字符串、注释、文件名、序列化键和外部契约分成不同所有权类别，避免机械全替换。
- 公共 API 不再无条件创建 deprecated alias；根据兼容性要求选择迁移、别名或破坏性重命名。
- 输出列出重命名对象、影响范围和验证结果，不承诺无法可靠统计的调用点数量。

### `setup-project-agents`

保留公共资产同步、目标仓库资产再生成、候选 review、真实验收和最终同步校验的完整编排职责。

- 保持公共资产、生成资产、退役资产和目标自有资产四类所有权边界。
- 将当前散落的生成要求合并成一个候选契约，将 review 与 acceptance 明确为两个不同 gate。
- 保留一次使用同一证据集生成全部项目候选、完整候选 review、真实 linked worktree 验收和平台 smoke test。
- 保留 runtime 字段与平台根配置的不同所有权，删除跨章节重复说明。
- 将主 workflow 写成带检查点的顺序流程；详细验收仍内联，因为每次发生实质变更都需要读取。
- 保留现有同步脚本、公共资产清单和测试，不新建重复封装。

### `worktree-integrate`

保留 review mode 默认、commit mode 显式启用、外部备份和不破坏 base 本地状态的安全模型。

- 将 task branch 准备、base 快照、传输、验证、恢复分别成段，减少长步骤中的多重职责。
- 保留单一 business commit、rebase 到最新 base、base HEAD/index 不变证明和重叠文本三方合并。
- 保留禁止 stash、reset、clean、pull、push、force-update 和 merge commit。
- 明确 pre-transfer failure 与 post-transfer verification failure 的不同恢复策略。
- 保留创建所有权决定 worktree 清理方式的规则。

### `write-comment`

保留“注释必须符合项目规则并提供代码本身没有的信息”的方向。

- 第一阶段读取目标项目、语言和 lint 的注释规则；项目规则决定语言、标记和文档注释语法。
- 删除把 English、`///` 和 Dart 参数引用写成跨项目硬规则的做法。
- 保留信息密度测试、why/constraint/invariant/edge case 等高价值内容类型和反例。
- 将格式、语气和示例变成“在项目规则允许时采用的默认写法”，避免覆盖语言原生约定。
- 工作流改为：判断是否需要注释、识别注释类型、写非显而易见信息、应用项目格式、运行目标 lint。

## 中文镜像策略

每个英文 skill 完成后立即更新对应中文文件，避免最后统一翻译导致遗漏。镜像检查包括：

- frontmatter 名称完全一致；description 含义等价；
- 标题层级和列表项一一对应；
- 命令、路径、代码块、枚举值和结果状态保持原文；
- `MUST`、`only`、`never` 等强度不因翻译减弱；
- 不把中文目录写入运行时配置或公共同步清单。

## 验证设计

### 结构和仓库契约

1. 对 8 个英文 skill 分别运行 `quick_validate.py`。
2. 运行 `python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`。
3. 运行 `git diff --check`。
4. 检查公共资产清单仍包含原有 6 个公共 skill 和 2 个 project skill generator。

### 内容和镜像

1. 对比英文与中文文件的 frontmatter、标题结构、代码块、路径和命令。
2. 检查 frontmatter 除 `name`、`description` 外没有其他字段。
3. 检查 skill 间引用仍指向现有名称和事实源。
4. 检查没有引入 README、无条件 reference 或重复脚本。

### 代表性场景

- 触发边界：每个 skill 至少包含一个应触发和一个相邻但不应触发的请求。
- 安全行为：`debug-mode`、`setup-project-agents`、`worktree-integrate` 各检查一个停止条件。
- 角色行为：两个生成器分别检查作者工作流与生成结果契约没有混淆。
- 项目适应：`write-comment` 检查非 Dart、非 English-only 项目不会被通用规则覆盖。
- 兼容性：`refactor-code` 和 `rename` 检查公共契约变化仍需要明确确认。

场景检查以静态契约审阅和独立代理前向验证为主，不运行会修改真实外部系统的操作。

## 风险控制

- **过度精简**：以约束是否影响行为为删减标准，而不是目标行数。
- **行为漂移**：逐 skill 对照现有方向、安全门槛和输出契约，记录有意修正的差异。
- **镜像漂移**：英文 skill 与中文镜像成对修改，并在最终验证中比较结构化元素。
- **公共同步回归**：保留清单、脚本和包装器不变，以现有测试验证资产所有权。
- **触发范围漂移**：description 同时使用正向触发词和必要边界，以代表性近邻场景验证。

