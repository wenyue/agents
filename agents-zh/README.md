# 中文阅读镜像

这里存放英文公共源目录 `agents/` 中人工可读 Markdown 文件的简体中文镜像，仅供查阅。

- `agents/` 始终是公共目录的唯一英文事实源；中英文内容不一致时，以英文源文件为准。
- 本仓库自己的运行时资产位于 `.agents/`，不属于本中文镜像的来源。
- 镜像范围包括 `rules/`、`agents/`、各 Skill 的 `SKILL.md`，以及 Markdown 格式的参考文件和模板。
- 脚本、清单、平台配置和其他机器读取文件不在镜像范围内。
- 不要从 `AGENTS.md`、Cursor、Copilot、Codex 或其他平台配置引用本目录。
- 不要把本目录加入 `setup-project-agents` 的公共资产清单或同步流程。
- 英文 Markdown 发生实质变化时，应在同一变更中手工更新对应的中文镜像。

除本说明外，镜像文件沿用 `agents/` 中的相对路径和文件名，便于逐份对照。

## 安装插件

为你使用的平台安装一次 `agents`。

Codex：

```sh
codex plugin marketplace add wenyue/agents
codex plugin add agents@wenyue-agents
```

Cursor：将 `https://github.com/wenyue/agents` 添加为插件源，然后安装 `agents`。

GitHub Copilot CLI：

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install agents@wenyue-agents
```

安装插件只会让平台能够使用其中的 Skill，不会修改任何仓库。打开每个目标仓库，并要求已安装
的插件使用 `setup-project-agents`。需要将仓库同步到已安装的目录版本时，再次运行该 Skill。

## 审查项目 Hook

`setup-project-agents` 会为每个受支持的平台安装一个项目健康检查 `sessionStart` Hook。该 Hook
每个项目每天最多检查一次推荐工具和有效运行时要求；它只报告漂移，绝不安装、升级或信任
工具。允许运行前，请通过平台的正常信任流程审查命令。

| 智能体 | 项目 Hook | 用户需要执行的操作 |
| --- | --- | --- |
| Codex | `.codex/hooks.json` | 启动 `codex`，输入 `/hooks`，检查项目 Hook，并信任其当前的精确定义。 |
| Cursor | `.cursor/hooks.json` | 将仓库作为受信任工作区打开，然后在 `Cursor Settings > Hooks` 中检查该 Hook。 |
| GitHub Copilot | `.github/hooks/*.json` | 在仓库中启动 `copilot`，并在提示时确认信任当前目录。 |

三个平台都显式启用 Hook 支持。项目配置不会强制启用多智能体能力；健康检查会验证各平台的
有效默认状态，并在它被禁用时发出报告。
