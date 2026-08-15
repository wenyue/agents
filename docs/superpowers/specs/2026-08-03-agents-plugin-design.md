# Smartkit 项目 Agent 设置设计

> **Historical terminology:** 本文保留的“平台”“三平台”和 `platform-*` 名称记录当时的真实术语。
> 当前契约使用 `Harness` 表示 Codex、Cursor 和 Copilot，并使用 `Platform` 表示 Windows、Linux
> 或 macOS；不要把这些历史术语、路径或命令当作当前入口。

## 目标

Smartkit 从远端规范 `master` 为一个目标仓库生成可重复收敛的 Rule、Skill、Agent 和平台配置
快照。每次 setup 都以本次固定的来源和生成结果为准，直接替换 Smartkit 管理的内容，同时
保留自动发现的项目私有 Rule、Skill 和结构化配置中的非受管字段。

## 来源

`workflow.py` 通过配对 wrapper 暴露 `start`、`finish` 和 `cancel`。Start 自动创建带所有权标记
的系统临时私有 session，再由 `bootstrap.py` 拉取远端 `master`，验证插件 manifest、版本、catalog、控制面
入口和所有 catalog 来源，然后把实际 commit 和来源根目录交给固定入口。POSIX 使用目录描述符
和不可替换发布；Windows 使用经过链接与目录边界检查的私有 session 候选目录。只有远端不可用
时才能使用已安装来源，拉取到无效内容时必须停止。

## 配置

`.agents/config.json` 只保存无法从目录推导的选择：

- 平台与共享 Rule、Skill、Agent 选择；
- `skills.external` 中第三方 Skill 的 `name`、`repository`、`ref` 和 `path`。

项目私有 Rule 和 Skill 不登记在配置中。Setup 自动扫描 `.agents/rules/*.md` 和
`.agents/skills/*/SKILL.md`，并排除 catalog 与第三方 Skill 已占用的路径。

## Catalog

`setup-assets/catalog/assets.json` 声明共享来源、生成蓝图、平台模板、wrapper 和
`retired_assets`。仍在 catalog 中但取消选择的已知目标会直接删除；结构化配置只删除对应模板
字段。`retired_assets` 是已经没有有效 catalog 声明的旧路径唯一删除入口，setup 不从目标历史
状态推断删除所有权。

## Session

Start 在脚本拥有的系统临时私有 `SESSION` 中产生：

- 固定的规范来源；
- `request.json`；
- 从现有平台 Agent 配置预填、未定义模型仍留空的 `models.json`；
- 五个待生成输出目录；
- 每个配置第三方 Skill 的最新 `ref` 快照。

Agent 只填写仍为空或用户明确要求修改的模型槽位和五个语义输出。Finish 从受保护的请求推导
全部执行参数，自动运行内部 apply 和 check、汇总结果并删除 session；生成无法继续时由 cancel
安全删除 session。第三方 Skill 拉取失败、名称不匹配、缺少 `SKILL.md` 或包含链接时，在目标
写入前停止。

## 渲染

Renderer 形成一个完整期望状态：

- 复制选中的共享 Rule、Skill 和 Agent；
- 接收五个生成的项目 Rule 与 Skill；
- 根据平台生成 wrapper 和原生配置；
- 把自动发现的项目 Rule 加入 `AGENTS.md`，但不复制或修改项目私有 Rule 与 Skill；
- 深度合并结构化模板，只把模板叶字段视为受管字段；
- 删除取消选择的已知 catalog 目标，并在平台关闭时删除对应模板字段；
- 把第三方 Skill 快照复制到对应目标目录；
- 标记共享和第三方 Skill 目录为整体替换根；生成 Skill 只覆盖请求的 `SKILL.md`，自动保留其
  项目自有辅助资源。

## 计划与事务

Planner 只比较当前内容和本次期望内容，产生排序后的 `CREATE`、`UPDATE`、`DELETE` 和
`UNCHANGED`。已有受管文件即使被本地修改，也会得到 `UPDATE`，不会产生所有权冲突。

Transaction 在写入前验证路径与入口类型，为所有变更保存备份，通过同目录临时文件替换目标，
并在任一操作失败时逆序回滚。POSIX 使用目录描述符避免链接与路径替换；Windows 使用重复边界
检查的 fallback，并保持二进制内容不发生换行转换。

## Check

Check 使用与 apply 相同的 request、renderer 和 planner，但不写入。目标已经收敛时返回零和
`drift: null`；存在差异时返回一、`desired_state_diff` 和排序后的路径。

## 所有权边界

- Smartkit 直接覆盖 catalog 选中的共享内容、五个生成输出、平台 wrapper 和配置的第三方
  Skill。
- Smartkit 只覆盖结构化模板声明的字段，保留同一文件中的其他字段。
- 项目私有 Rule 和 Skill 由目标仓库拥有；setup 只发现和引用，不覆盖正文。
- `setup-project-agents` 控制面、插件 Hooks、推荐工具运行时和策略不进入目标快照。
