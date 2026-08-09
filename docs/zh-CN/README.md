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
> 请打开 Codex CLI 会话，运行 `/hooks`，审查并信任 SmartKit 的 Hooks，然后开启
> 新的 Codex 会话或运行 `/clear`。完成信任前，Codex 会跳过 SmartKit 的推荐工具检查和 Rule 分发。只有更新
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

## 插件 Skills 与 Rules

`skills/registry.json` 显式声明 SmartKit 自有 Skills 和 GitHub 外部 Skills。维护者使用
`python scripts/update_external_skills.py --update` 更新所有外部源，或用 `--source owner/repository`
更新单个源；`--check` 只读。省略 ref 时跟随仓库默认分支，也可显式选择分支、标签或 commit。
更新使用环境中的 Git 凭据，校验许可证，并事务化替换聚合锁文件和快照。

`rules/registry.json` 定义插件 Rules 的顺序。`always` Rule 对所有任务生效；`file` Rule 根据项目根
相对的 Git 风格 glob 激活。优先比较强度（`Mandatory` > `Default` > `Advisory`），再比较项目归属，
最后比较更窄的文件范围。Codex 和 Copilot CLI 使用 Hook；Cursor 使用原生插件 Rules。Hook 会在
会话内记住已激活的文件 Rule，在 compact 后恢复，并在此前未发现 Rule 时阻止首次匹配的结构化
写入。Hook dispatcher 会输出包含响应大小的尝试交付诊断；信任、接收、spill 和截断仍以宿主为准，
预期 Rule 未生效时应检查宿主 Hook 诊断。Cursor adapter 无法表达某个文件范围时会拒绝生成，不会
发布语义不同的配置。Copilot cloud agent 不在此插件 Rule 契约范围内。

## 平台支持

三个宿主都支持 Windows 和 Linux。初始化会为每个生成的 Agent 设置显式模型；宿主专属字段仍使用
各自的原生形式。

| 宿主 | 插件 Rule 分发 | 推荐工具 Hook | 原生 Agent 字段 |
| --- | --- | --- | --- |
| Codex | 会话、提示词和结构化工具 Hook | PowerShell / POSIX sh | `model_reasoning_effort`、`sandbox_mode` |
| Cursor | 原生插件 Rules | polyglot 分发器 | `readonly` |
| GitHub Copilot CLI | 会话、转换提示词和结构化工具 Hook | `powershell` / `bash` | `disable-model-invocation` |

## 为每个项目执行设置

进入目标仓库后，请 Agent 使用 `setup-project-agents` 完成初始化。初始化流程每次都会配置 Codex、
Cursor 和 Copilot，并在 `docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md` 和
`docs/agents/domain.md` 中创建 Matt 仓库上下文。

新仓库由一名维护者运行 setup、审查结果并提交受管项目快照。其他开发者通过 clone 或 pull 获取，
无需逐人运行 setup。只有项目需要采用新版 setup 受管快照契约时，才再次运行
`setup-project-agents`。

项目可在 `.agents/config.json` 的 `skills.external_sources` 下声明 GitHub Skill 源。Setup 对每个 URL
只拉取一次，快照其中选定的 Skills，并写入 `.agents/external-skills.lock.json`。生成式项目 Rules
使用 `00–09`，模块 Rules 使用 `10–19`，领域 Rules 使用 `20–29`，包或项目插件 Rules 使用
`30–39`。

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
