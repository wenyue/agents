# Agents 跨平台插件重构设计

## 背景

当前仓库本质上是“公共资产目录 + 项目同步器”，插件清单只是外层包装：`agents/` 同时承担
插件根、公共目录和同步源，`agents-zh/` 又完整镜像目录，三个 Marketplace 重复维护元数据，
项目同步逻辑集中在一个大型脚本中。这个结构可以工作，但插件不是架构中心，来源、生成、
同步和兼容职责彼此缠绕。

本次重构将仓库改成一个真正的单插件仓库。仓库根目录就是插件根；插件负责跨项目分发、
项目初始化入口和外部工具维护；每个项目仍需显式运行 `setup-project-agents`，将完整、可审查
的项目 Agent 配置写入仓库。

## 已确认的设计决策

- 仓库根目录直接作为插件包，不再保留嵌套的 `agents/` 插件根。
- 同时支持 Codex、Cursor 和 GitHub Copilot，并尽量保持三端行为一致。
- 英文运行资产只有一份；中文内容移入 `docs/zh-CN/`，只作为文档维护。
- 插件安装只暴露宿主原生支持的能力，不自动修改当前项目。
- 每个项目显式运行 `setup-project-agents` 后，得到完整的 Rules、Skills、Agents 快照，并按显式
  选择安装 Hooks。
- `setup-project-agents` 是插件控制面，永远不复制进目标项目。
- setup 默认直接拉取远端 `main`，不使用 GitHub Release，也不读取旧项目 updater。
- 不保留旧脚本、旧目录或旧项目安装方式的兼容逻辑。
- Hook 显式启用；多代理只检查宿主的有效默认状态。
- Superpowers、CodeGraph、Tokscale 等外部工具通过独立工作流诊断和升级，不内嵌上游源码。

## 目标与非目标

### 目标

1. 仓库根目录可以直接被三个宿主识别为插件。
2. 插件内容与项目内容的边界清晰：插件提供控制面，项目保存可审查的运行快照。
3. setup 每次运行都能够从远端 `main` 获取最新版并升级当前项目。
4. 三端共享同一份 Rules、Skills、Agents 和工具检查逻辑，仅由薄适配层处理格式差异。
5. 同步具备明确所有权、幂等规划、写前验证、事务应用和失败回滚。
6. 外部工具的版本策略、检测器和升级入口由插件统一维护。

### 非目标

- 安装插件时自动修改任意项目。
- 自动绕过 Codex、Cursor 或 Copilot 的 Hook 信任和权限确认。
- 将三个宿主强行统一为同一种 manifest、Hook 或 Agent 文件格式。
- 复制或二次分发 Superpowers、CodeGraph、Tokscale 的源码。
- 支持旧项目 updater、旧 archive 回退或旧目录结构迁移。
- 在 setup 的项目写入事务中静默安装或升级外部工具。

## 目标仓库结构

```text
repo/
├── .codex-plugin/
│   └── plugin.json
├── .cursor-plugin/
│   ├── plugin.json
│   └── marketplace.json          # 仅用于本地开发
├── .github/
│   └── plugin/
│       └── marketplace.json      # 仅用于本地开发
├── .agents/
│   ├── plugins/
│   │   └── marketplace.json      # 仅用于本地开发
│   └── rules/                    # 仅维护本仓库所需的最小规则
├── plugin.json                   # Copilot 插件清单
├── VERSION
├── skills/
│   ├── setup-project-agents/     # 插件控制面，不复制到项目
│   ├── manage-agent-tools/
│   └── ...
├── rules/                        # 英文运行时 Rule 事实源
├── agents/                       # 英文 Agent 提示词事实源
├── blueprints/                   # 项目拥有内容的生成契约
├── catalog/
│   └── project-assets.json       # 项目资产、所有权与渲染声明
├── config/
│   └── recommended-tools/
│       ├── codex.json
│       ├── cursor.json
│       └── copilot.json
├── templates/
│   └── project/
│       ├── entry-files/
│       ├── platform-config/
│       ├── hooks/
│       └── wrappers/
├── docs/
│   └── zh-CN/                    # 中文阅读文档，不参与运行或发布
├── scripts/                      # 仓库维护脚本
├── tests/
├── AGENTS.md
├── README.md
└── LICENSE
```

根目录内容就是最终插件包，不引入 `src/` 到 `dist/` 的构建步骤。正式发布通过各平台官方或
独立 Marketplace 完成；仓库内三份 Marketplace 只服务本地开发和验证。

本仓库不对自身运行 `setup-project-agents`。`.agents/` 仅保存维护这个插件所需的项目规则，
避免把待发布内容和本仓库开发配置重新耦合起来。

## 插件能力与项目快照

插件安装后只暴露宿主原生支持的能力：

| 宿主 | 插件直接暴露 |
| --- | --- |
| Codex | Skills |
| Cursor | Skills、Rules、Agents |
| GitHub Copilot | Skills、Agents |

插件安装不自动启用项目 Hook，也不把公共资产复制到当前仓库。用户显式运行
`setup-project-agents` 后，setup 根据 `catalog/project-assets.json` 创建项目快照：

- `.agents/rules/`：项目使用的完整 Rule。
- `.agents/skills/`：项目使用的 Skills，但排除 `setup-project-agents`。
- `.agents/agents/`：项目使用的 Agent 提示词。
- `AGENTS.md` 和平台目录：只保存入口、平台配置和薄包装。
- 项目 Hook：仅在用户明确启用时安装。

Catalog 是项目安装内容的唯一机器可读声明。每项资产至少声明来源、目标、类型、适用平台、
渲染方式和控制面标记。Planner 只处理 Catalog 声明的内容，不通过目录遍历隐式扩大安装范围。

## setup 升级与同步数据流

### 远端 `main` 自举

`setup-project-agents` 同时承担项目初始化和项目资产升级入口。默认在线流程如下：

1. 从规范仓库 `https://github.com/wenyue/agents.git` 抓取远端 `main`。
2. 将本次抓取的 `FETCH_HEAD` 解析为固定 commit SHA。
3. 在临时目录以 detached HEAD 检出该 commit。
4. 校验插件 ID、目录结构、Catalog 和新版 setup 入口。
5. 由临时检出中的新版 setup 接管后续流程，旧进程退出。
6. 新版 setup 扫描目标项目、生成计划、暂存输出、完成验证并事务性应用。
7. 将实际使用的 `source_commit` 和受管结果写入项目 lock。

这里的升级源始终是远端 `main`，不使用 Release、tag 或 `main.zip`。commit SHA 只用于固定单次
执行和记录来源，避免执行期间 `main` 再次变化，不改变“始终跟随 main”的策略。

如果网络不可用，setup 明确报告未检查更新，并使用当前已安装插件副本继续。如果已经成功
拉取远端内容，但远端结构、Catalog 或入口无效，则立即失败，不回退旧版本，也不修改项目。

新架构发布后，自举入口路径和交接参数属于稳定内部协议：当前插件中的 bootstrap 必须能够
启动 `main` 中的 setup，并传递来源根目录、`source_commit` 和“禁止再次自举”标记。本次不兼容
重构只是不支持重构前的旧 updater；后续版本不得在没有过渡入口时破坏这份自举协议。

### 宿主插件更新

项目资产升级不依赖宿主插件缓存已经刷新。setup 可以检测并编排宿主原生更新流程：

- Copilot 使用其原生插件更新命令。
- Codex 刷新 Git Marketplace，并使用宿主当前提供的安装或刷新流程。
- Cursor 使用公开 Marketplace 的刷新机制；没有稳定非交互入口时，提示用户在官方界面刷新。

setup 不直接修改任何宿主的插件缓存、内部数据库或信任存储。宿主插件仍旧时，本次项目升级
可以完成，但结果中必须明确提示刷新或重启宿主。

### 项目同步事务

```text
已安装插件入口
    -> fetch main
    -> 固定 source commit
    -> 新版 setup 接管
    -> 扫描项目与有效宿主状态
    -> 生成统一变更计划
    -> 在临时目录渲染完整结果
    -> 校验路径、配置、Hook 和清单
    -> 备份受影响文件
    -> 原子应用
    -> 写入 lock
```

`--check` 与正常执行必须调用同一个 Planner。区别仅在于前者输出计划后停止，不能拥有独立的
漂移判断实现。

## 组件边界

- `bootstrap.py`：抓取 `main`、固定 commit、创建临时检出并交接新版入口。
- `setup_project_agents.py`：CLI 参数、步骤编排和最终结果展示。
- `source.py`：Git 来源、commit 元数据和离线回退。
- `catalog.py`：加载和校验 `catalog/project-assets.json`。
- `project.py`：识别项目结构、启用平台及现有配置。
- `planner.py`：产生新增、更新、保留、删除和冲突的统一计划。
- `renderer.py`：复制公共资产，应用 Blueprint，生成平台薄包装。
- `validation.py`：验证输出目录、配置合并、Hook 和平台 manifest。
- `transaction.py`：暂存、备份、原子应用和失败回滚。
- `host_adapters/`：封装 Codex、Cursor、Copilot 的检测、配置和更新差异。
- `manage-agent-tools`：诊断和升级外部工具，不参与项目文件事务。

各模块通过结构化数据通信，不通过打印文本解析彼此结果。三端适配器统一返回 `ready`、
`needs_approval`、`needs_restart`、`unsupported` 等状态，由 setup 统一决定下一步。

## 配置、Lock 与所有权

目标项目将用户输入和生成状态分开保存：

- `.agents/config.json`：用户拥有，记录启用平台、资产选择和 Hook 是否启用。
- `.agents/lock.json`：setup 生成，记录 `source_commit`、受管路径、内容摘要和安装结果。

所有权规则如下：

1. setup 只能覆盖或删除 lock 明确拥有的路径或字段。
2. 同名未受管文件属于用户；Planner 报告冲突并停止，不直接覆盖。
3. 平台 JSON/TOML 配置采用结构化合并，保留未受管字段。
4. 用户关闭某项能力时，只删除 lock 记录的对应文件和字段。
5. `setup-project-agents` 始终留在插件中，不出现在项目 lock 或项目快照中。

## 三平台对齐策略

| 能力 | Codex | Cursor | GitHub Copilot |
| --- | --- | --- | --- |
| 项目 Rule 入口 | `AGENTS.md` | `.cursor/rules/` | `.github/instructions/` |
| 项目 Agent 包装 | `.codex/agents/` | `.cursor/agents/` | `.github/agents/` |
| Hook 配置 | `.codex/hooks.json` | `.cursor/hooks.json` | `.github/hooks/` |
| 宿主配置 | `.codex/config.toml` | `.cursor/cli.json` | `.github/copilot/settings.json` |

`.agents/` 保存共享正文，平台目录只保存宿主必须的元数据和薄包装。

### Hook

Hook 是显式选择加入能力：

- Codex 在用户启用 Hook 时写入 `features.hooks = true` 并安装 `.codex/hooks.json`。
- Cursor 安装 `.cursor/hooks.json`；需要宿主信任时，只触发或提示官方确认流程。
- Copilot 安装 `.github/hooks/`，并在用户确认后结构化合并 `disableAllHooks = false`。
- 用户关闭 Hook 时，只移除 lock 管理的 Hook 文件和配置字段。
- 三端 Hook 调用同一个项目本地推荐工具检查器，只报告状态，不执行安装或升级。

### 多代理

- Codex 读取 `codex features list` 并检查 `multi_agent` 的有效值，不重复写入默认配置。
- Cursor 和 Copilot 检查 CLI 版本或公开能力是否已包含默认多代理支持，不创建额外开关。
- 检查失败只产生诊断和升级建议；实际升级交给 `manage-agent-tools`。

整体策略固定为：**Hook 显式启用，多代理检查默认有效状态。**

## 外部工具维护

插件维护 Codex、Cursor、Copilot、Superpowers、CodeGraph 和 Tokscale 的版本策略、检测器、安装
说明和升级适配器。`manage-agent-tools` 提供两个清晰动作：

- `doctor`：只读检测有效版本、安装来源和能力状态。
- `upgrade`：展示将执行的宿主原生命令或包管理器命令，获得批准后执行。

无法可靠识别安装来源时，只给出指引，不猜测包管理器。项目 SessionStart Hook 只调用
`doctor` 的轻量检查路径，不能静默升级工具。工具升级失败不回滚已经成功的项目同步，因为
两者属于独立事务。

## 失败处理与安全边界

- GitHub 不可达：警告后使用当前插件副本。
- 已抓取的 `main` 无效：写入前失败，不回退旧版本。
- Catalog、规划或渲染校验失败：目标项目零变更。
- 未受管路径冲突：停止并列出冲突，不覆盖用户文件。
- 应用中途失败：使用备份恢复，并保留诊断信息。
- Hook 文件或宿主配置不能完整应用：回滚整个项目同步事务。
- 宿主插件没有刷新：不阻塞项目同步，但返回 `needs_restart` 或明确操作提示。
- 路径必须保持在目标仓库内；拒绝 `..` 逃逸、绝对目标路径和符号链接越界。
- Git 命令使用固定参数数组，不拼接执行远端或项目提供的 Shell 文本。

## 旧结构一次性退场

本次重构不建立迁移桥：

- 将 `agents/` 的运行内容提升到根目录对应区域，然后删除旧嵌套目录。
- 将 `agents-zh/` 的中文 Markdown 移入 `docs/zh-CN/`，不迁移机器文件。
- 删除旧同步脚本、旧 `public_assets.json`、旧 archive 回退和项目内 updater 逻辑。
- 删除被新目录替代的旧模板、manifest 和包装。
- 按新架构重写测试，不保留只验证旧内部结构的断言。

目标项目不会被自动迁移。用户在新插件中再次运行 setup 时，由新的 Planner 根据当前文件和
新 lock 契约建立所有权；无法安全判断的同名文件按未受管冲突处理。

## 测试策略

### 单元测试

- Catalog schema、路径安全和控制面排除。
- `main` 抓取、commit 固定、交接和离线回退。
- Planner 的新增、更新、保留、删除和冲突结果。
- 三个平台适配器、结构化配置合并和有效状态检测。
- Lock 所有权、摘要和受管字段删除。

### 输出快照测试

覆盖 Codex、Cursor、Copilot 和三端同时启用，并分别验证：

- Hook 开启与关闭。
- 多代理有效、无效和无法检测。
- 全新项目与已有配置项目。
- 平台薄包装引用共享正文。
- `setup-project-agents` 未被复制。

### 集成测试

使用临时 Git 仓库模拟远端 `main`：

- 当前已安装的 bootstrap 拉取更新后的 `main` 并由新入口接管。
- `main` 新提交触发受管资产升级。
- 第二次执行没有无意义变更。
- 网络不可用时使用当前插件副本。
- 已抓取远端结构无效时目标项目零变更。
- 未受管文件冲突时拒绝覆盖。
- 注入应用失败后完整回滚。

### 跨平台测试

CI 至少覆盖 Linux、macOS 和 Windows，验证 POSIX Shell、PowerShell、相对路径、JSON/TOML
合并和 Hook 命令格式。真实 Marketplace、真实模型和用户主目录不作为自动化测试依赖。

## 验收标准

1. 仓库根目录可以直接作为 Codex、Cursor 和 Copilot 插件安装。
2. setup 默认检查远端 `main`，单次执行固定并记录准确 commit。
3. 项目得到完整 Rules、Skills、Agents 快照，并按显式选择包含 Hooks，但不包含 setup 控制面。
4. Hook 只有用户明确启用时才落盘并修改宿主配置。
5. 多代理只检查有效状态，不重复写默认配置。
6. setup 只能覆盖或删除 lock 拥有的内容。
7. `--check` 与应用模式共享同一 Planner，重复执行保持幂等。
8. 所有跟踪配置和文档使用仓库相对路径，不包含机器绝对路径。
9. 中文文档不参与插件运行、Marketplace 或项目同步。
10. 以下仓库级验证全部通过：

```sh
python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```
