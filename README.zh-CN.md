# WenYue SmartKit

[English](README.md) | 简体中文

`WenYue SmartKit` 是同时适配 Codex、Cursor 和 GitHub Copilot 的跨 Harness 插件。它将 Rules、Skills、
Agents 和 MCP 作为平级能力提供，并在会话开始时检查推荐工具和已配置 MCP 的前置条件是否可用。

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

## 插件 Rules、Skills、Agents 与 MCP

| 能力 | SmartKit 提供的内容 |
| --- | --- |
| Rules | Always-on、file-scoped 和 Harness-scoped 指令。优先比较强度（`Mandatory` > `Default` > `Advisory`），再比较项目归属和更窄的文件范围。Harness 范围只控制激活，并与 always-on 处于同一优先级层级。 |
| Skills | SmartKit 工作流，以及经过审查、许可证校验和版本固定的第三方工作流。 |
| Agents | 三个宿主上的 `change-set-verifier`。它使用项目的 change-set-verification Skill；setup 未安装该 Skill 时报告 `inconclusive`，并继承宿主选择的模型。Cursor 和 Copilot 从插件获取它；Codex 通过 setup-managed 默认交付获取它。 |
| MCP | 三个宿主上隔离、无界面模式的 Playwright，并继续遵守宿主正常的审批行为。 |

Codex 和 Copilot CLI 通过 Hook 接收 Rules；Cursor 使用原生插件 Rules。预期 Rule 未生效时，请检查
宿主 Hook 诊断。Copilot cloud agent 不在此插件 Rule 契约范围内。

Codex 插件包不会加载自定义 Agents。请在每个受维护的项目快照中运行 `setup-project-agents`，将
SmartKit 的 Codex Agent adapter 安装到 `.codex/agents/`。该 adapter 仍归插件所有，不需要在
`.agents/config.json` 中添加 Project Agent 声明。

## Harness 与平台支持

三个宿主都支持 Windows 和 Linux。

| 宿主 | Rules | Skills | Agents | MCP |
| --- | --- | --- | --- | --- |
| Codex | 会话、提示词和结构化工具 Hook | 插件 Skill catalog | Setup-managed `change-set-verifier` | Playwright |
| Cursor | 原生插件 Rules | 插件 Skill catalog | `change-set-verifier` | Playwright |
| GitHub Copilot CLI | 会话、转换提示词和结构化工具 Hook | 插件 Skill catalog | `change-set-verifier` | Playwright |

## 为每个项目执行设置

进入目标仓库后，请 Agent 使用 `setup-project-agents` 完成初始化。初始化流程每次都会配置 Codex、
Cursor 和 Copilot，并在 `docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md` 和
`docs/agents/domain.md` 中创建 Matt 仓库上下文。

新项目默认使用 `.scratch/` 下的 Local Markdown issue tracker，不受 Git remote 影响。Setup 会保留
完整的现有 tracker 配置。项目需要将工作发布到远端时，应明确要求使用 GitHub、GitLab 或其他
tracker。

新仓库由一名维护者运行 setup、审查结果并提交受管项目快照。其他开发者通过 clone 或 pull 获取，
无需逐人运行 setup。只有项目需要采用新版 setup 受管快照契约时，才再次运行
`setup-project-agents`。

| 能力 | 项目配置 |
| --- | --- |
| Rules | 将项目自有 source 保存在 `.agents/rules/`；setup 会保留这些 source，并安装请求生成的 Rules。 |
| Skills | 将项目自有 Skills 保存在 `.agents/skills/`，或在 `.agents/config.json` 的 `skills` 中声明 GitHub `source`、可选 `ref` 和非空 `include`。 |
| Agents | 将 canonical source 保存在 `.agents/agents/`，并在 `.agents/config.json` 的 `agents` 中声明匹配的 `id`、`source`、`description` 和 `harnesses`；应编辑这些输入，而不是生成的 adapter。 |
| MCP | 在 `.agents/config.json` 的 `mcp` 中用稳定 ID 和 `url` 或 `command` 之一声明每个 server；环境变量仅按名称引用，不存储 secret 值。 |

Setup 会保留不受其管理的宿主配置；受管条目发生冲突或被本地修改时，会在写入前停止。

### MCP overrides

每条 override 都包含 `when` selector 和 `set` 对象。省略 `when.harnesses` 时匹配该 server 启用的
全部宿主，省略 `when.operatingSystems` 时匹配全部受支持的操作系统（`windows` 和 `linux`）。两者
同时提供时必须都匹配。匹配的规则按数组顺序应用，后面的规则只覆盖其声明的字段：

```json
{
  "id": "inspector",
  "command": "python3",
  "overrides": [
    {
      "when": {"operatingSystems": ["windows"]},
      "set": {"command": "py"}
    },
    {
      "when": {"harnesses": ["cursor", "copilot"]},
      "set": {"cwd": "tools/inspector"}
    }
  ]
}
```

### Project MCP readiness

Project MCP 的前置条件检查默认自动执行。当检查只适用于特定宿主或操作系统时，使用
`readiness.harnesses` 或 `readiness.operatingSystems` 限定范围：

```json
{
  "id": "inspector",
  "command": "cache/inspector.exe",
  "readiness": {
    "operatingSystems": ["windows"]
  }
}
```

添加 `readiness.checks` 可替换自动检查，设为 `[]` 则禁用检查。支持的检查种类包括
`command-exists`、`runtime-version`、`workspace-path` 和 `environment-variable`。

SmartKit 只管理自己生成的内容，并尽量保留项目原有文件和用户配置。应提交 `AGENTS.md`、
`.agents/`、受管宿主 wrapper 和配置以及 `docs/agents/`；不要将它们加入 `.gitignore`。Session
数据、缓存、日志和凭据留在仓库外，生成的项目文件不得包含 secret。

## Hook、多智能体、MCP readiness 与工具维护

插件会按 canonical project、当前宿主和本地日期，每天自动运行一次 readiness pipeline。第一步
就是 daily gate；policy 变化不会绕过它，显式 `--force` 可以重跑。当前检查包括：

- 推荐工具的安装状态和版本，包括 CodeGraph 与 Tokscale；
- 必要的实际配置值，包括 Codex 多智能体支持；
- 适用于当前 Harness 和操作系统的 MCP 前置条件。

这些检查不会安装工具、修改 MCP 配置、启动 MCP server、探测网络或应用端口、触发 OAuth，也不
要求 debug session 在线。因此，Project HTTP MCP 不会执行连接检查。

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
