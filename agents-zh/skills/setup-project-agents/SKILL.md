---
name: setup-project-agents
description: 从 wenyue/agents 公共目录设置或更新仓库 agent 资产时使用，包括公共同步、生成的项目规则和 skill、wrapper、退役资产以及目标自有运行时配置。
---

# 设置项目 Agent

对初始 setup 和后续 update 运行相同的完整协调。通过一个幂等工作流协调公共、生成、退役和目标自有 agent 资产。使用目标仓库的当前证据，审查完整候选，并在声明 setup 为最新之前验收实质变更。

## 所有权

- 始终获取配置的公共 GitHub archive。不要使用本地源 checkout、cache 或陈旧 snapshot。
- 精确镜像 catalog 列出的公共资产，并且只删除 catalog 声明的退役资产。
- 保留公共、生成和退役集合之外的项目本地资产。报告所有权冲突，不要静默解决。
- 将托管项目资产重新生成为完整候选。只把旧版本用作遗漏清单，并重新验证每个保留事实。
- 将目标自有 model、reasoning、permission、MCP、hook 和平台设置排除在公共 catalog 之外。根据当前平台和项目证据协调它们。

## 托管项目资产

- `.agents/rules/20-project-tools.md`
- `.agents/rules/21-project-rules.md`
- `.agents/rules/22-project-structure.md`
- `.agents/skills/worktree-environment-setup/`
- `.agents/skills/change-set-verification/`

验收后的候选成为目标仓库的运行时事实源。

## 共享生成要求

- 使用英文编写每个生成或刷新的项目自有规则和 skill。
- 使用当前证据。省略陈旧、推测、不受支持和重复的指引。
- 生成完整文件和目录，而不是 patch 片段。
- 使每条规则符合 `.agents/rules/00-global-rule-config.md`，包括标题、`Strength:`、`Scope:`、编号、事实源所有权和薄 wrapper 要求。
- 每个生成 skill 的 frontmatter 只包含 `name` 和 `description`。使用祈使指令、skill 自有相对引用和语义化目标描述。
- 对特定资产内容，遵循目标 generator contract 和每个目标规则的 generation contract，不要在此重复其 policy。
- 只有所有者契约和仓库证据证明需要时才包含 reference 或 script。

## 协调工作流

1. 读取 `AGENTS.md` 和所有适用的 `00-*` 到 `09-*` 规则。
2. 运行 `python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`。
3. 审查每项报告的创建、更新、删除、退役和 wrapper 变更。确认公共所有权和无关本地资产得到保留。
4. 收集工具、runtime、服务、生成文件、API、约定、模块、依赖、agent wrapper 和平台配置的当前证据。
5. 将旧托管资产盘点为遗漏清单，然后重新验证每项保留声明。
6. 使用下述边界审查目标自有 agent runtime 和平台配置。
7. 使用共享证据集派发一个 subagent，为所有托管项目资产生成完整候选。如果 subagent 不可用，报告阻塞；不要在不一致证据集之间拆分生成。
8. 审查每个完整候选和支持资源。在替换对应托管资产前解决所有发现。
9. 应用审查通过的候选，然后运行公共同步，使 wrapper 和入口文件收敛到验收后的事实源。
10. 按依赖顺序验收每个创建或实质变更的规则和 skill：规则、环境 setup、change-set verification。跳过字节等价候选。
11. 当已安装平台提供安全代表性调用时，smoke test 变更的 runtime 字段；否则将结果报告为 inconclusive。
12. 再运行一次公共同步，然后以 `python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check` 完成最终检查。

## Agent Runtime 审查

- 在每次 setup 或 update 中，为每个已安装或目标平台审查 catalog 中每个 agent。
- 不要在公共 catalog 中存储 model 或 reasoning-effort 选择。
- 将现有 wrapper 值视为旧的目标决定，而不是公共默认值。只有确认仍受支持且适合时才保留。
- 使用明确受支持的 model 初始化缺失目标值；不要依赖继承。
- Codex wrapper 要求非空 `model` 和 `model_reasoning_effort`，Cursor 和 GitHub Copilot wrapper 要求非空 `model`。
- 保留有证据支持的 `sandbox_mode` 和其他角色 permission 字段。
- 保留有证据支持的角色 permission 和目标 override。将缺失的必需 runtime 字段视为最终门禁阻塞。
- 最终公共同步必须保留审查后的目标自有 runtime 字段。
- 审查后的 runtime 字段发生变化且已安装平台提供安全 surface 时，运行代表性 smoke invocation；否则将检查报告为 inconclusive。

## 平台配置审查

- 将逐 agent runtime 字段保留在原生 wrapper，将项目级 MCP、hook、concurrency 或 permission policy 保留在原生根配置。
- 不要仅为注册 agent 创建 `.codex/config.toml`，不要仅按名称跨平台翻译字段，不要写入 secret 或修改用户全局设置。
- 报告不确定的平台 schema，不要发出猜测字段。

## 审查门禁

验收前审查完整候选文件。

### 生成规则

- 确认正确标题、`Strength:`、`Scope:`、编号、所有权和证据。
- 确认 `20-project-tools.md`、`21-project-rules.md` 和 `22-project-structure.md` 分别保持工具、约定和结构所有权。
- 确认 wrapper 保持精简、指向单一事实源，并且可从 `AGENTS.md` 发现。

### 生成 Skill

- 确认每项声明都有当前证据，且旧内容只作为遗漏清单。
- 确认共享要求和资产自身 generation contract 已满足。
- 确认 skill reference 和 script 确有必要、可访问且内部一致。
- 确认 `worktree-environment-setup` 包含两个主机入口。
- 确认 `change-set-verification` 只有在其 generator contract 和仓库证据证明需要时才包含 verification matrix 或可执行脚本。
- 确认没有候选吸收 worktree 生命周期、业务实现、Git 集成、公共同步或其他 workflow 的 policy。

仍有任何审查发现时不要开始验收。

## 验收门禁

只在候选审查通过后运行。

### 生成规则

1. 按 `.agents/rules/00-global-rule-config.md` 验证完整规则，并将保留声明追溯到当前证据。
2. 确认正确所有权、编号、从 `AGENTS.md` 的可发现性和已同步薄 wrapper。
3. 拒绝占位语言、重复所有权、不受支持声明和陈旧路径。
4. 在静态和集成检查通过前，使受影响规则保持未验收状态。

### 生成 Skill

两个生成 skill 都发生变化时，复用一个真实临时 linked worktree。先验收环境 skill，再验收 verification skill。

1. 验证完整 skill，并使用原生 shell 工具只解析主机原生 setup 入口：Linux 和 macOS 使用 Bash，Windows 使用 PowerShell。不要解析或调用其他平台的 setup script。
2. 需要时将未提交候选复制到临时 worktree，并验证字节相等。
3. 调用环境入口，并从真实项目配置证明 readiness。
4. 使用窄代表性变更执行 verification skill，同时让无关 dirty 文件保持在范围之外。
5. 存在批准的自动 fixer 时，执行该路径并确认它修改的文件加入验证范围。
6. 执行一个前置条件失败和一个有证据支持的高风险变更。确认它避免无条件 whole-project 检查，并且不会仅为验收运行昂贵完整 suite。
7. 确认范围选择、停止行为、结果分类，以及语义诊断返回父实现 agent。
8. 检查仓库和 worktree 状态是否有无关修改或泄漏文件，然后安全删除临时 worktree。

任何失败都使候选保持未验收状态；报告准确证据，将完整候选返回其生成器，重复审查，并重新开始受影响验收阶段。

## 验证

对 `wenyue/agents` 的公共源编辑运行：

```bash
python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
```

对最终同步后的目标仓库运行：

```bash
python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check
```

## 输出

列出已创建、更新、删除和未改变的托管文件。分别报告公共同步、退役、项目生成、遗漏审查、runtime 审查、候选审查、验收、smoke check 和验证。包含准确命令和阻塞；绝不把跳过或 inconclusive 的检查描述为通过。
