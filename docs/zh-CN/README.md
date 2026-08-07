# WenYue SmartKit

`WenYue SmartKit` 是同时适配 Codex、Cursor 和 GitHub Copilot 的跨平台插件。它帮助项目统一
Agent 规则、常用技能和协作方式，并在会话开始时检查推荐工具是否可用。

## 安装插件

请在实际使用的每个宿主中分别安装一次 `smartkit`。

Codex：

```sh
codex plugin marketplace add wenyue/agents
codex plugin add smartkit@wenyue
```

也可以在 Codex 中使用 `/plugins` 完成安装。

> **必须完成的 Codex Hook 审查：** 安装或启用 SmartKit 不会自动信任其内置 Hook。安装后，
> 请打开 Codex CLI 会话，运行 `/hooks`，审查并信任 SmartKit 的 `SessionStart` Hook，然后开启
> 新的 Codex 会话或运行 `/clear`。完成信任前，Codex 会跳过 SmartKit 的推荐工具检查。只有更新
> 改变了 Hook 定义且 Codex 将其重新标记为待审查时，才需要再次审查。

Cursor：通过 Plugin Marketplace 或 `/add-plugin` 安装；私有版本请通过团队市场或本地插件方式
导入。

GitHub Copilot CLI：

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install smartkit@wenyue
```

需要更新 Copilot 插件时，先运行 `copilot plugin marketplace update wenyue`，再运行
`copilot plugin update smartkit`。

## 内置 Matt Skills

SmartKit 将完整的稳定版 Matt Pocock Skills 集合作为插件的一部分分发。不要再通过 skills.sh、Matt
插件或其他本地副本安装相同 Skills；重复名称会导致调用歧义。需要采用新版内置集合时，更新
SmartKit 并开启新的宿主会话。普通 Skill 更新不要求重新运行任一 setup 工作流。

## 平台支持

三个宿主都支持 Windows 和 Linux。初始化会为每个生成的 Agent 设置显式模型；宿主专属字段仍使用
各自的原生形式。

| 宿主 | Windows 推荐工具 Hook | Linux 推荐工具 Hook | 原生 Agent 字段 |
| --- | --- | --- | --- |
| Codex | PowerShell | POSIX sh | `model_reasoning_effort`、`sandbox_mode` |
| Cursor | 通过 polyglot 分发器调用 PowerShell | 通过 polyglot 分发器调用 POSIX sh | `readonly` |
| GitHub Copilot | `powershell` 处理器 | `bash` 处理器 | `disable-model-invocation` |

## 为每个项目执行设置

进入目标仓库后，请 Agent 使用 `setup-project-agents` 完成初始化。初始化流程每次都会配置 Codex、
Cursor 和 Copilot，并在 `docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md` 和
`docs/agents/domain.md` 中创建 Matt 仓库上下文。

新仓库由一名维护者运行 setup、审查结果并提交受管项目快照。其他开发者通过 clone 或 pull 获取，
无需逐人运行 setup。只有项目需要采用新版 setup 受管快照契约时，才再次运行
`setup-project-agents`。

SmartKit 只管理自己生成的内容，并尽量保留项目原有文件和用户配置。应提交 `AGENTS.md`、
`.agents/`、受管宿主 wrapper 和配置以及 `docs/agents/`；不要将它们加入 `.gitignore`。Session
数据、缓存、日志和凭据留在仓库外，生成的项目文件不得包含 secret。

## Hook、多智能体与工具维护

插件会自动检查推荐工具和必要能力，例如 CodeGraph、Tokscale 与多智能体支持。检查只负责发现
问题，不会自行安装工具或修改相关配置。

发现缺失或过期工具时，SmartKit 会先列出需要处理的项目并询问用户，只执行用户明确同意的维护
操作。如果用户明确拒绝列出的操作，SmartKit 会直接跳过，不再重复询问，Agent 随后继续原任务。
不能自动处理的项目会给出手动操作建议。Cursor 在交互会话中会阻止受影响的提示；在 headless
`--print` 会话中，则通过会话上下文要求 Agent 先询问并结束本轮。

## 典型使用流程

```text
安装或更新 SmartKit → 开启新的宿主会话 → 完成宿主 Hook 审查（Codex：/hooks）→ 由维护者运行
setup-project-agents → 审阅并提交生成快照 → 其他开发者 pull → 开始使用
```

如果检查提示需要安装或升级工具，请先确认工具名称和操作，再决定是否授权。
