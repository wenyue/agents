# WenYue SmartKit

`WenYue SmartKit` 是同时适配 Codex、Cursor 和 GitHub Copilot 的跨平台插件。安装后只会暴露
`setup-project-agents` 控制面和插件自有的依赖检查 Hooks。共享 Rules、Skills 与 Agent 提示只有在
setup 将受管理快照安装到目标仓库后才可用。

## 安装插件

在使用的每个宿主中安装一次 `smartkit`。

Codex：

```sh
codex plugin marketplace add wenyue/agents
codex plugin add smartkit@wenyue
```

也可以在 Codex 中使用 `/plugins` 浏览已配置的市场。安装完成后请开启新会话。

Cursor：通过 Plugin Marketplace 或 `/add-plugin` 使用当前界面流程安装。若插件尚未公开发布，
请使用团队或私有市场界面导入仓库，或在本地克隆后作为开发插件安装；不要依赖不存在的仓库
命令行安装方式。

GitHub Copilot CLI：

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install smartkit@wenyue
```

需要更新时，使用原生命令，例如先执行
`copilot plugin marketplace update wenyue`，再执行 `copilot plugin update smartkit`；
市场名称不同则先通过 `copilot plugin list` 核对。

## 为每个项目执行设置

在每个目标仓库中，明确要求已安装的插件使用 `setup-project-agents`。选择目标宿主；默认选择
Codex、Cursor 和 Copilot。仅安装插件绝不会修改项目中的受版本控制文件。

每次设置都会拉取远程 `main`、验证内容，并在 prepare、apply、check 的整个会话中固定到同一
提交。想让项目跟进新的 `main` 时，再次手动运行设置即可。设置控制面始终保留在插件内，不会
复制到目标项目。

生成的快照只拥有 lock 中记录的文件和配置字段。它会保留目标项目的其他文件，以及用户自行维护的
`.agents/config.json` 选项。

## Hook、多智能体与工具维护

Hook 属于插件，并通过各宿主的插件格式声明。宿主安装或加载插件时会发现这些 Hook；
`setup-project-agents` 不再写入项目 Hook 定义或 Hook 启用字段。宿主级信任、工作区信任和全局
Hook 开关仍是最终约束。插件自带的 SessionStart Hook 会运行推荐工具 doctor，检查工具和所需宿主
能力，包括多智能体支持；它不会把 Hook 执行视为同意，也不会自行变更工具。

工具需要安装或升级时，Hook 会要求智能体列出受影响工具并征求同意，但不展示底层命令。用户
同意后，插件私有的白名单执行器会逐项执行受支持的原生动作；不支持自动化的动作会返回官方
手动指引。该维护流程始终为插件私有能力，不会复制到项目快照。

## 目录说明

```text
skills/                         插件可见控制面；仅包含 setup-project-agents
hooks/                          插件自有的生命周期 Hook 定义
runtime/recommended-tools/      Hook 私有执行程序；不会成为可发现的 Skill
policies/recommended-tools/     共享的推荐工具策略
setup-assets/catalog/           资产、配置与锁定状态契约
setup-assets/rules/             安装到目标仓库的 Rules
setup-assets/skills/            安装到目标仓库的 Skill 文档
setup-assets/agents/            安装到目标仓库的 Agent 提示
setup-assets/blueprints/        生成项目自有 Rules 与 Skills 的契约
setup-assets/templates/         宿主配置与包装模板
docs/zh-CN/                     中文文档
.agents/rules/                  本仓库开发规则
.agents/skills/                 write-rule 与 write-skill 的本地薄包装
.agents/plugins/                本仓库本地插件市场配置
```

插件清单只暴露 `skills/` 和各宿主的 Hook 入口，不暴露 `runtime/`、`policies/` 或
`setup-assets/`。`docs/zh-CN/` 仅供阅读，不会被加载或安装。
