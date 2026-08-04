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
- 插件安装暴露宿主原生支持的能力和插件自有 Hook，不自动修改当前项目文件。
- 每个项目显式运行 `setup-project-agents` 后，得到完整的 Rules、Skills、Agents 快照；项目同步
  不管理 Hook。
- `setup-project-agents` 是插件控制面，永远不复制进目标项目。
- setup 默认直接拉取远端 `main`，不使用 GitHub Release，也不读取旧项目 updater。
- 不保留旧脚本、旧目录或旧项目安装方式的兼容逻辑。
- Hook 随插件声明并受宿主信任与总开关约束；多代理只检查宿主的有效默认状态。
- Superpowers、CodeGraph、Tokscale 等外部工具由插件 Hook 诊断，并在用户批准后通过插件私有
  执行器升级，不内嵌上游源码。

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
│   ├── rules/                    # 仅维护本仓库所需的最小规则
│   └── skills/                   # write-rule 与 write-skill 的本地薄包装
├── plugin.json                   # Copilot 插件清单
├── VERSION
├── skills/
│   └── setup-project-agents/     # 插件控制面，不复制到项目
├── hooks/                        # 插件自有的三端 Hook 定义
├── runtime/
│   └── recommended-tools/        # Hook 私有检查与维护运行时，不含 SKILL.md
├── policies/
│   └── recommended-tools/
│       ├── codex.json
│       ├── cursor.json
│       └── copilot.json
├── setup-assets/                 # 只供 setup 创建项目快照的资产源
│   ├── catalog/
│   │   ├── assets.json
│   │   ├── project-config.schema.json
│   │   └── project-lock.schema.json
│   ├── rules/                    # 英文运行时 Rule 事实源
│   ├── skills/                   # 项目运行 Skill 文档事实源
│   ├── agents/                   # 英文 Agent 提示词事实源
│   ├── blueprints/               # 项目拥有内容的生成契约
│   └── templates/                # 宿主配置与包装模板
├── docs/
│   └── zh-CN/                    # 中文阅读文档，不参与运行或发布
├── tests/
├── AGENTS.md
├── README.md
└── LICENSE
```

根目录内容就是最终插件包，不引入 `src/` 到 `dist/` 的构建步骤。正式发布通过各平台官方或
独立 Marketplace 完成；仓库内三份 Marketplace 只服务本地开发和验证。

本仓库不对自身运行 `setup-project-agents`。`.agents/` 仅保存维护这个插件所需的项目规则、
本地 Skill 发现包装和 Marketplace 配置；Skill 包装直接引用 `setup-assets/skills/` 的事实源，
不会复制工作流正文，也不会把待发布内容和本仓库开发配置重新耦合起来。

## 插件能力与项目快照

插件安装后只暴露宿主原生支持的能力：

| 宿主 | 插件直接暴露 |
| --- | --- |
| Codex | setup 控制面 Skill、Hooks |
| Cursor | setup 控制面 Skill、Hooks |
| GitHub Copilot | setup 控制面 Skill、Hooks |

插件安装或加载时，宿主从插件清单或约定路径发现插件 Hook，但不会把公共资产复制到当前仓库。
用户显式运行
`setup-project-agents` 后，setup 根据 `setup-assets/catalog/assets.json` 创建项目快照：

- `.agents/rules/`：项目使用的完整 Rule。
- `.agents/skills/`：项目使用的 Skills，但排除 `setup-project-agents`。
- `.agents/agents/`：项目使用的 Agent 提示词。
- `AGENTS.md` 和平台目录：只保存入口、平台配置和薄包装。

项目快照不包含 Hook 定义，也不写入宿主 Hook 启用字段。Hook 生命周期与插件一致，不属于
Catalog、Planner 或项目 lock 的所有权范围。

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
    -> 校验路径、配置和清单
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
- `catalog.py`：加载和校验 `setup-assets/catalog/assets.json`。
- `project.py`：识别项目结构、启用平台及现有配置。
- `planner.py`：产生新增、更新、保留、删除和冲突的统一计划。
- `renderer.py`：复制公共资产，应用 Blueprint，生成平台薄包装。
- `validation.py`：验证输出目录、配置合并和平台 manifest。
- `transaction.py`：暂存、备份、原子应用和失败回滚。

插件 Hook 直接调用 `runtime/recommended-tools/`，并从 `policies/recommended-tools/` 读取策略。
这些文件始终为插件私有能力，setup 不会将其复制到目标项目。

setup 从本次固定的 `SOURCE_ROOT/setup-assets/skills/` 直接读取 `write-rule` 与 `write-skill`
authoring contract，因此首次 setup 不依赖目标项目已经安装这些 Skill。

各模块通过结构化数据通信，不通过打印文本解析彼此结果。

## 配置、Lock 与所有权

目标项目将用户输入和生成状态分开保存：

- `.agents/config.json`：用户拥有，记录启用平台和资产选择。
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
| 插件 Hook | `hooks/hooks.json` | `hooks/cursor.json` | `hooks/copilot.json` |
| 宿主配置 | `.codex/config.toml` | `.cursor/cli.json` | `.github/copilot/settings.json` |

`.agents/` 保存共享正文，平台目录只保存宿主必须的元数据和薄包装。

### Hook

Hook 是插件能力，不是项目快照选项：

- Codex 按插件根的默认 `hooks/hooks.json` 发现 Hook。
- Cursor 和 Copilot 由各自 manifest 指向插件根下的平台 Hook 文件。
- 三端 Hook 通过各自的插件根变量调用插件内同一套推荐工具检查器，不依赖 `.agents/` 快照。
- setup 不接受 Hook 开关、不写项目 Hook 文件，也不修改宿主配置中的 Hook 字段。
- 旧 `--hooks` 参数和 `.agents/config.json` 中的 `hooks_enabled` 字段直接视为无效输入，不提供
  兼容解析或迁移。
- 宿主级信任、工作区信任和全局 Hook 开关仍具有最终决定权，插件不绕过这些约束。
- Hook 只报告状态，不执行安装或升级。

### 多代理

- Hook 读取 Codex 的有效 `multi_agent` 值，并通过 Cursor 和 Copilot 的工具版本判断默认多代理
  支持，不创建项目级开关。
- 检查失败只产生诊断和升级建议；用户批准后，插件私有执行器处理受支持的升级动作。

整体策略固定为：**Hook 归插件所有，多代理检查默认有效状态。**

## 外部工具维护

插件维护 Codex、Cursor、Copilot、Superpowers、CodeGraph 和 Tokscale 的版本策略、检测器、安装
说明和升级适配器。插件私有运行时提供两个清晰动作：

- `doctor`：只读检测有效版本、安装来源和能力状态。
- 维护：只说明需要安装或升级的工具并征求同意，不展示底层命令；获得同意后由内置白名单
  执行器处理指定工具动作。

不支持自动维护时，只给出官方手动指引。插件 SessionStart Hook 只调用 `doctor` 的轻量检查
路径并征求同意；Hook 本身不能静默升级工具，后续已批准轮次才可调用包内执行器。工具升级
失败不回滚已经成功的项目同步，因为两者属于独立事务。

## 失败处理与安全边界

- GitHub 不可达：警告后使用当前插件副本。
- 已抓取的 `main` 无效：写入前失败，不回退旧版本。
- Catalog、规划或渲染校验失败：目标项目零变更。
- 未受管路径冲突：停止并列出冲突，不覆盖用户文件。
- 应用中途失败：使用备份恢复，并保留诊断信息。
- 插件 Hook 加载或信任失败：报告宿主状态，不影响项目同步事务。
- 路径必须保持在目标仓库内；拒绝 `..` 逃逸、绝对目标路径和符号链接越界。
- Git 命令使用固定参数数组，不拼接执行远端或项目提供的 Shell 文本。

## 旧结构一次性退场

本次重构不建立迁移桥：

- 将项目运行内容收敛到 `setup-assets/`，将 Hook 私有执行程序和共享策略分别收敛到
  `runtime/` 与 `policies/`，然后删除旧嵌套目录。
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
- 三个平台的结构化配置合并。
- 三端插件 Hook 清单、插件根路径和只读检查命令。
- Lock 所有权、摘要和受管字段删除。

### 输出快照测试

覆盖 Codex、Cursor、Copilot 和三端同时启用，并分别验证：

- 项目输出中不存在 Hook 文件或 Hook 启用字段。
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
3. 项目得到完整 Rules、Skills、Agents 快照，不包含 Hook 或 setup 控制面。
4. 三端从插件包发现各自 Hook；setup 不接受 Hook 选项，也不写项目 Hook 或宿主 Hook 字段。
5. 多代理和外部工具检查只由插件 Hook 执行，不写项目配置。
6. setup 只能覆盖或删除 lock 拥有的内容。
7. `--check` 与应用模式共享同一 Planner，重复执行保持幂等。
8. 所有跟踪配置和文档使用仓库相对路径，不包含机器绝对路径。
9. 中文文档不参与插件运行、Marketplace 或项目同步。
10. 以下仓库级验证全部通过：

```sh
python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```
