---
name: setup-project-agents
description: 初始化或更新仓库的 Agents Rule、Skill、Agent 与显式启用的 Hook 快照时使用。
---

# 设置项目 Agent

从当前规范 `main` 为一个目标仓库创建或更新受管 Agent 快照。本文件是英文
`skills/setup-project-agents/SKILL.md` 的中文阅读镜像，不参与 runtime、生成或发布；Task 10
会将此镜像整体迁入文档目录。该共享操作型 Skill 负责 setup 会话和项目协调，但绝不把自身安装到
目标项目，也不修改宿主信任记录、插件缓存或升级外部工具。

## 前提条件

- 从目标仓库根目录开始，将平台已加载的 Skill 目录识别为 `SETUP_PROJECT_AGENTS_ROOT`。
- 只询问一次要启用的平台以及是否启用 Hook。`.agents/config.json` 不存在时，默认启用 Codex、
  Cursor、Copilot，且 Hook 关闭；文件存在时，沿用其中的平台、资产选择和 Hook 选择，除非用户
  要求变更。
- 整个会话保持平台和 Hook 选择不变。Hook 必须由用户显式启用；多代理能力只检查宿主实际有效
  状态，不能写入重复默认值。

## 工作流

1. 用 `tempfile.mkdtemp` 创建一个系统临时私有会话；在 POSIX 上确认它归当前用户所有且权限精确
   为 `0700`。在验证完成前保留这个 `SESSION`，不要把它建在目标仓库内：

   ```sh
   SESSION="$(python3 -c 'import tempfile; print(tempfile.mkdtemp(prefix="setup-project-agents-"))')"
   ```

2. 使用 `SETUP_PROJECT_AGENTS_ROOT/scripts/` 中的平台包装器执行 `prepare`，并提供 `--target`、
   `--session`、每个已选平台的 `--platform` 及 `--hooks enabled|disabled`。包装器只启动
   `bootstrap.py`。它获取规范 `main`，在 `SESSION/source` 固定一个 commit 后交给该固定来源继续。
   远端不可用时会报告已安装来源回退；已获取来源无效时，必须在写入目标项目前停止。POSIX 示例：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" prepare \
     --target "$PWD" --session "$SESSION" \
     --platform codex --platform cursor --platform copilot --hooks disabled
   ```

   Windows 使用携带相同参数的 `setup_project_agents.ps1`。

3. 读取 `SESSION/request.json`。它是本会话规范化目标、来源根与 commit、平台与 Hook 选择、资产
   选择、模型请求和五个生成输出的唯一依据。写入一个 JSON object `SESSION/models.json`，满足每个
   Agent/平台请求：每个目标平台 object 必须有非空 `model`；Codex 可选
   `model_reasoning_effort` 和 `sandbox_mode` 存在时必须为字符串，Cursor 可选 `readonly` 存在时必须
   为 Boolean。不得使用 `SESSION` 外的模型文件，也不得在 prepare 后修改 request。

4. 在 `SESSION/generated` 生成 request 中的每个输出，绝不直接写入目标项目。三条 Rule Blueprint
   必须使用 `write-rule`，两条 Skill Blueprint 必须使用 `write-skill`。只能生成下列路径，不能有
   额外文件：

   - `.agents/rules/20-project-tools.md`
   - `.agents/rules/21-project-rules.md`
   - `.agents/rules/22-project-structure.md`
   - `.agents/skills/change-set-verification/SKILL.md`
   - `.agents/skills/worktree-environment-setup/SKILL.md`

5. 从 `request.json` 读取来源根与 commit；记录的 commit 为 `null` 时，CLI commit 参数使用
   `offline`。对固定来源执行
   `skills/setup-project-agents/scripts/setup_project_agents.py apply`，传入相同的目标、会话、
   `SESSION/models.json`、来源根、来源 commit 和 `--no-bootstrap`。apply 会在唯一一次项目事务前
   校验会话 request、生成树、渲染结果和所有权计划：

   ```sh
   python3 "$SOURCE_ROOT/skills/setup-project-agents/scripts/setup_project_agents.py" apply \
     --target "$TARGET" --session "$SESSION" --models "$SESSION/models.json" \
     --source-root "$SOURCE_ROOT" --source-commit "$SOURCE_COMMIT" --no-bootstrap
   ```

6. 使用完全相同的参数执行同一固定入口的 `check`，仅将 `apply` 替换为 `check`。apply 与 check 均会
   向 stdout 输出唯一一个 JSON 结果，其中包括 phase、固定来源 commit、排序后的变更路径、每个平台
   的能力状态、候选刷新命令和 `needs_restart`。check 状态码为零表示项目无变化；状态码一表示发现
   漂移但没有写入。报告前必须读取这个结果中的来源 commit 和受管路径。

7. 展示 JSON 结果中的候选刷新命令或官方 UI 操作。不得在 setup 中自动执行候选命令，只有用户
   单独批准后才能执行。宿主 `needs_restart` 或 Cursor Hook 信任要求必须单独报告；两者都不属于
   项目文件事务。

8. 仅在 apply 和 check 完成后，或报告失败后，删除 `SESSION`。

## 停止条件

会话非私有、`request.json` 与本次调用不匹配、`models.json` 不是 `SESSION/models.json`、模型字段
缺失或无效、生成输出不完整或含额外路径、固定来源无效，或所有权 Planner 发现未受管漂移时，必须
停止且不写入项目。

不得使用 archive 回退、项目本地 setup 副本、宿主信任数据库或插件缓存作为替代路径。只有在单独
获得批准的外部工具诊断或升级时才使用 `manage-agent-tools`。

## 验证与结果

- [ ] 确认 `check` 与 `apply` 使用同一 `SESSION`、来源根、来源 commit、模型文件、renderer 和 planner；确认状态码为零。
- [ ] 确认 `.agents/lock.json` 记录固定来源 commit，且只有 lock 拥有的路径或字段发生变化。
- [ ] 确认目标快照中没有 setup-project-agents；确认 Hook 仅在显式启用时存在。

报告固定来源 commit、已选平台、Hook 选择、变更的受管路径、能力或信任后续事项，以及任何未解决
失败。验证未执行时，不得报告 setup 成功。
