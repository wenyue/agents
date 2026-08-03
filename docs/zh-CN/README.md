# agents 中文文档

`agents` 是同时适配 Codex、Cursor 和 GitHub Copilot 的插件。它提供共享的 Rules、Skills、
智能体提示、模板，以及可选的项目 Hook。插件安装到宿主后不会自动修改任何项目；每个项目都要
明确运行一次 `setup-project-agents`。

## 安装插件

Codex：

```sh
codex plugin marketplace add wenyue/agents
codex plugin add agents@wenyue-agents
```

也可以在 Codex 中使用 `/plugins` 浏览已配置的市场。安装完成后请开启新会话。

Cursor：通过 Plugin Marketplace 或 `/add-plugin` 使用当前界面流程安装。若插件尚未公开发布，
请使用团队或私有市场界面导入仓库，或在本地克隆后作为开发插件安装；不要依赖不存在的仓库
命令行安装方式。

GitHub Copilot CLI：

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install agents@wenyue-agents
```

需要更新时，使用原生命令，例如先执行
`copilot plugin marketplace update wenyue-agents`，再执行 `copilot plugin update agents`；
市场名称不同则先通过 `copilot plugin list` 核对。

## 为每个项目执行设置

在目标仓库中要求已安装的插件使用 `setup-project-agents`。选择要启用的平台，以及是否启用
Hooks；默认选择 Codex、Cursor、Copilot，且 Hooks 为关闭状态。

每次设置都会拉取远程 `main`、验证内容，并在 prepare、apply、check 的整个会话中固定到同一
提交。想让项目跟进新的 `main` 时，再次手动运行设置即可。设置控制面始终保留在插件内，不会
复制到目标项目。

## Hook、多智能体与工具维护

Hook 需要显式启用。设置只写入项目 Hook 定义，不会修改宿主信任存储、工作区信任、插件缓存或
编辑器界面状态。请在相应宿主的 UI 中审查并信任 Hook；Hook 仅做诊断，绝不会安装或升级工具。

多智能体能力检查有效宿主状态或宿主的默认能力，不会写入覆盖默认值的项目配置：Codex 读取有效
`multi_agent` 状态，Cursor 与 GitHub Copilot 根据版本报告默认能力是否可用。

工具维护由 `manage-agent-tools` 单独负责。`doctor` 只读；`upgrade` 会逐条提出原生命令，只有
用户批准准确命令后才执行，并在完成后再次运行 doctor。

## 目录说明

```text
rules/                 共享运行时 Rules
skills/                共享操作 Skills（包括 setup-project-agents）
agents/                共享智能体提示
blueprints/            生成项目自有 Rules 与 Skills 的契约
catalog/               资产与锁定状态契约
templates/project/     宿主配置与包装模板
config/                推荐工具策略
docs/zh-CN/             中文文档
.agents/rules/         本仓库开发规则
.agents/plugins/       本仓库本地插件市场配置
```

根目录的英文运行时内容是插件的事实源。 `docs/zh-CN/` 仅供阅读，不会被加载、安装或同步到目标项目。
