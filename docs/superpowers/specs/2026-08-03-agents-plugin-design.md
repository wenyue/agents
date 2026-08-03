# Agents 跨平台插件设计

## 目标

将 `wenyue/agents` 包装为同时支持 Codex、Cursor 和 GitHub Copilot 的版本化插件，同时保留
项目显式初始化和仓库内可审查配置的现有优势。

插件负责跨项目分发、工具链诊断和升级入口；项目开发者仍需在每个仓库手动运行
`setup-project-agents`。初始化产生的 `AGENTS.md`、Rules、Skills、Agent 包装、平台配置和
项目 Hook 继续提交到目标仓库。

## 非目标

- 安装插件时不自动修改当前项目。
- SessionStart Hook 不静默安装或升级 Superpowers、CodeGraph、Tokscale 或平台 CLI。
- 不尝试设计一个三平台共用的插件清单或 Hook JSON 格式。
- 不把 Cursor Rule 当作 Codex 或 Copilot 的通用 Rule 格式。
- 不复制或内嵌 Superpowers、CodeGraph、Tokscale 的上游源码。

## 包结构

`agents/` 同时作为插件包根目录和公共英文运行资产的唯一事实源，插件 ID 使用 `agents`，市场
源名称使用 `wenyue-agents`。这样 Codex 所要求的插件根 `skills/` 与现有公共 Skill 目录天然
重合，不需要复制、符号链接或第二份清单。各平台只增加薄清单：

```text
agents-repository/
├── .agents/plugins/marketplace.json        # Codex 市场源，source 指向 ./agents
├── .cursor-plugin/marketplace.json         # Cursor 市场源，source 指向 ./agents
├── .github/plugin/marketplace.json         # Copilot 市场源，source 指向 ./agents
└── agents/
    ├── .codex-plugin/plugin.json           # Codex 插件清单
    ├── .cursor-plugin/plugin.json          # Cursor 插件清单
    ├── plugin.json                         # Copilot 插件清单
    ├── skills/                             # 三平台共享 Skills，也是插件根 skills/
    ├── rules/                              # 公共 Rule 事实源
    ├── agents/                             # 公共 Agent 提示词事实源
    └── blueprints/                         # 项目生成契约
```

三份插件清单都从插件根的 `./skills/` 暴露符合 Agent Skills 规范的 Skills。Cursor 和 Copilot
不会直接加载 `agents/rules/` 或 `agents/agents/`：这些资产仍由 `setup-project-agents` 生成或
包装成项目原生格式，避免三平台行为分叉。

插件清单从 `0.1.0` 开始，版本由一次发布变更统一维护。清单校验必须检查插件 ID、版本、共享
Skill 路径和市场源路径在三个平台一致。

## 运行流程

### 首次使用

1. 用户通过当前平台的市场源安装 `agents` 插件。
2. 用户在目标仓库显式调用插件提供的 `setup-project-agents`。
3. Skill 从当前已安装插件包读取 `agents/` 公共目录，不下载可变的 `master.zip`。
4. 现有两阶段模型选择、Blueprint 生成和确定性同步流程保持不变。
5. 同步结果写入项目目录并接受 Git 审查。

### 项目更新

1. 用户通过平台原生插件管理器显式升级 `agents` 插件。
2. 用户在需要更新的项目再次运行 `setup-project-agents`。
3. 同步脚本使用已安装插件版本中的公共资产修复漂移。
4. 项目记录最近一次同步的目录版本，`--check` 对照该版本和受管资产报告漂移。

### 旧安装兼容

项目内已有 `.agents/skills/setup-project-agents` 的仓库继续可用。脚本按以下顺序解析公共源：

1. 显式传入并验证的本地公共源；
2. 当前 Skill 所在插件包中的 `agents/` 公共源；
3. 旧项目 Skill 的远程发行版回退。

远程回退必须引用发布标签或不可变提交，不再默认下载 `master`。过渡期保留清晰错误信息，
不自动删除已有项目 Skill，也不覆盖目标仓库未受管字段。

## 工具链维护

插件提供显式工具链诊断/升级工作流，复用现有 `recommended-tools/*.json` 检测器和
`check_recommended_tools.py`：

- `doctor` 只读取当前平台、Superpowers、CodeGraph 和 Tokscale 的有效版本并给出差异。
- `upgrade` 先展示将执行的原生平台或包管理器命令，再等待用户确认。
- Superpowers 由 Codex、Cursor、Copilot 各自的插件管理器升级。
- CodeGraph 和 Tokscale 使用其原安装来源升级；无法可靠识别来源时只给指引。
- 项目 SessionStart Hook 每项目每天最多检测一次，只提示，不执行升级。

插件首版不携带全局 SessionStart Hook。只有运行过 `setup-project-agents` 的项目才安装项目
健康 Hook，从而保持明确的项目选择加入边界。

## 数据与所有权

- `agents/` 继续拥有公共 Rules、Skills、Agent 提示词、模板、脚本和清单数据。
- 各平台插件 manifest 和 marketplace 文件只拥有平台元数据与路径映射。
- `public_assets.json` 继续拥有目标项目安装内容。
- 目标仓库继续拥有生成的项目 Rule、Skill 和非受管配置字段。
- `agents-zh/` 只镜像人类可读 Markdown，不进入插件运行时或市场源。

项目同步版本写入 `.agents/config.json` 的受管 `catalog` 块，至少包含插件 ID、语义版本和源
修订。该元数据用于诊断和 `--check`，不作为自动升级授权。

## 失败处理与安全边界

- 插件源缺少 `agents/`、manifest 版本不一致或公共清单无效时，在写入目标项目之前失败。
- 三个平台 Hook 继续使用各自原生信任机制；脚本不得写入编辑器内部信任存储。
- 外部工具升级失败不回滚或破坏已经有效的项目配置。
- 同步继续使用临时目录完成下载和校验，再执行目标写入。
- 任何自动化测试不得依赖真实插件市场、真实模型或用户主目录。

## 验证

新增或扩展测试覆盖：

1. Codex、Cursor、Copilot manifest 和 marketplace 的结构、版本与路径一致性。
2. 插件包本地公共源优先于远程源，且本地路径逃逸会被拒绝。
3. 旧项目远程回退只接受固定发行版或提交引用。
4. 初始化仍生成三平台配置、Hook、Rule 包装和 Agent 包装。
5. `.agents/config.json` 的目录版本能够被同步和 `--check` 检测。
6. Hook 只诊断，不执行安装或升级命令。
7. 现有项目的非受管配置和无关工作区改动保持不变。

完成实现后运行仓库要求的全部验证：

```sh
python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

## 实施顺序

1. 添加三平台插件与市场清单及其结构测试。
2. 让同步脚本优先解析插件包本地公共源，并增加固定远程回退。
3. 写入和校验项目目录版本元数据。
4. 增加显式工具链诊断/升级 Skill，保持 Hook 只读诊断。
5. 更新英文 README、中文镜像和三平台安装/升级说明。
6. 运行完整测试并验证旧项目兼容路径。
