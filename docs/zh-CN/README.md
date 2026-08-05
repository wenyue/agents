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

## 为每个项目执行设置

进入目标仓库后，请 Agent 使用 `setup-project-agents` 完成初始化。初始化流程每次都会配置 Codex、
Cursor 和 Copilot。

初始化会把项目所需的规则、技能和 Agent 配置写入仓库。想采用 SmartKit 的新版本时，再次运行
`setup-project-agents` 即可。

SmartKit 只管理自己生成的内容，并尽量保留项目原有文件和用户配置。所有改动都可以通过版本控制
查看和审阅。

## Hook、多智能体与工具维护

插件会自动检查推荐工具和必要能力，例如 Superpowers、CodeGraph、Tokscale 与多智能体支持。
检查只负责发现问题，不会自行安装工具或修改相关配置。

发现缺失或过期工具时，SmartKit 会先列出需要处理的项目并询问用户。只有获得明确同意后才会继续；
不能自动处理的项目会给出手动操作建议。Cursor 在交互会话中会阻止受影响的提示；在 headless
`--print` 会话中，则通过会话上下文要求 Agent 先询问并结束本轮。

## 典型使用流程

```text
安装 SmartKit → 完成宿主 Hook 审查（Codex：/hooks）→ 在项目中运行 setup-project-agents →
审阅生成内容 → 开始使用
```

如果检查提示需要安装或升级工具，请先确认工具名称和操作，再决定是否授权。
