# Matt Pocock Skills 插件内置迁移 Implementation Plan

> **Historical terminology:** 本计划中的 `platform-config` 路径和 `platform integration` 提交文本
> 记录当时的真实名称。当前契约使用 `Harness` 表示 Codex、Cursor 和 Copilot，并使用 `Platform`
> 表示 Windows、Linux 或 macOS；不要把这些历史命令当作当前入口。
> 本计划中的 `Workflow Configuration` 也是当时的真实 Rule 标题；当前 owner 已拆分为
> `Skill Governance` 和 `Workspace Policy`，不要把旧标题当作当前 Rule。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Matt Pocock Skills 的完整官方稳定集合直接作为 SmartKit 插件 Skills 分发，并提供可审计、可回滚的上游同步与插件升级能力。

**Architecture:** SmartKit 的三个插件 manifest 已把 `skills` 指向 `./skills/`，因此把 Matt 官方 promoted skills 平铺 vendoring 到根目录，例如 `skills/ask-matt/` 和 `skills/tdd/`，与 `skills/setup-project-agents/` 一起构成一个安装单元。维护脚本从 Matt 的稳定 release 和 `.claude-plugin/plugin.json` 生成 vendored 目录、上游锁和许可证；用户通过更新 SmartKit 插件并开启新会话获得新版 Skills。`setup-project-agents` 在同一次 start/review/finish 事务中生成 Matt 所需的 `docs/agents/` 配置和 `AGENTS.md` 指针，正常首次设置不要求用户再单独调用 `setup-matt-pocock-skills`。

**Tech Stack:** Python 3.10+ 标准库、Git、JSON、PowerShell/POSIX wrappers、Agent Skills 标准、Codex/Cursor/Copilot 插件 manifests、`unittest`

## Global Constraints

- “完整 Matt Skills”定义为 `mattpocock/skills` v1.2.3 的 `.claude-plugin/plugin.json` 所列 25 个 promoted skills，对应 commit `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e`。
- 不同步上游 `in-progress/`、`misc/`、`deprecated/`；只有官方插件 manifest 中的目录属于稳定能力面。
- Vendored Skill 目标固定为根 `skills/` 下与 frontmatter 同名的目录，例如 `skills/ask-matt/`；`skills/setup-project-agents/` 始终由 SmartKit 自己拥有，任何上游同名冲突必须停止同步。
- 同步必须保留每个 Skill 的完整目录，包括 `SKILL.md`、references、scripts、templates、assets 和 `agents/openai.yaml`；不得改写上游 Skill 内容或 frontmatter 名称。
- `vendor/mattpocock-skills.lock.json` 是上游 version、tag、commit、promoted set 和 vendored file hashes 的单一凭据。
- 后续升级必须显式执行“检查稳定 release → 同步到临时目录 → 审核 diff → 测试 → 提升 SmartKit 版本 → 发布插件”；不得浮动跟随 `main` 或在用户机器上静默替换文件。
- 插件更新后必须开启新的 Codex/ChatGPT/Cursor/Copilot 会话，已运行会话不得被当作新版 Skill 验收环境。
- 目标项目不得再通过 SmartKit setup、`npx skills update` 或另一份 Matt 插件安装同一集合；重复安装会造成命名空间和触发歧义。
- 每个目标仓库仍需要一次 Matt context bootstrap，但正常路径由 `setup-project-agents` 在自己的 Review Gate 内完成；`setup-matt-pocock-skills` 只保留为后续显式重新配置或修复入口。
- `setup-project-agents` 产出的项目快照属于仓库共享契约，必须提交到 Git：至少包括 `AGENTS.md`、`.agents/**`、受管宿主 wrapper/config、`docs/agents/**`，以及实际生成的 `CONTEXT.md`、`CONTEXT-MAP.md`、`docs/adr/**`；不得把这些路径加入 `.gitignore`。
- 团队只由一名维护者在仓库初始化或快照契约升级时运行 setup、审核并提交结果；其他开发者通过 clone/pull 获得同一快照，不需要各自运行 setup。
- setup 私有 session、缓存、日志、凭据和其他纯本机运行状态不属于项目快照，必须留在系统临时目录或 ignore；任何受管项目文件都不得包含 secret。
- 保留现有 `debug-mode` 项目级外部 Skill；它不是 Superpowers 上游的一部分，仍按自身显式触发边界工作。
- Matt 上游内容按 MIT 许可证分发；SmartKit 插件必须携带未经改写的许可证声明和来源信息。
- Superpowers 的推荐工具检测、安装配方、Copilot marketplace 配置和运行时 Rule 依赖全部退休。
- 现有项目自有 Rule、Skill、Agent、用户结构化配置和 worktree integration 能力必须保持。
- 这是 0.x 默认工作流和插件能力面的变更，SmartKit 版本从 `0.1.8` 提升到 `0.2.0`。

---

## File Structure

- `skills/setup-project-agents/`：SmartKit 自有控制面，不受 Matt 同步器管理。
- `skills/ask-matt/`、`skills/tdd/` 等 lock 声明目录：25 个由同步器独占管理的 Matt vendored Skills。
- `vendor/mattpocock-skills.lock.json`：固定上游版本、commit、清单和逐文件 SHA-256。
- `licenses/mattpocock-skills-LICENSE.txt`：Matt MIT 许可证原文。
- `scripts/sync_matt_skills_upstream.py`：只读检查和事务式更新 Matt vendor tree。
- `plugin.json`、`.codex-plugin/plugin.json`、`.cursor-plugin/plugin.json`：继续使用 `skills: "./skills/"`，由各宿主发现 SmartKit 与 Matt Skills。
- `setup-assets/catalog/assets.json`：只保留需要写入目标项目的外部 Skills，例如 `debug-mode`；不再列出 Matt。
- `skills/setup-matt-pocock-skills/` 中的 seed templates：由 `setup-project-agents` 作为锁定上游输入读取，用来生成目标 `docs/agents/`；不得复制成第二份 SmartKit 模板源。
- `setup-assets/templates/entry-files/AGENTS.md`：渲染固定的 `## Agent skills` 指针区块。
- `policies/recommended-tools/` 与 `runtime/recommended-tools/`：不再检测或安装 Superpowers/Matt，Matt 已包含在 SmartKit 插件本身。
- `.agents/rules/04-global-skill-config.md` 与 `setup-assets/rules/04-global-skill-config.md`：定义 Matt、项目 Skill 和 worktree 的职责边界。
- `setup-assets/skills/worktree-integrate/SKILL.md`：移除 Superpowers 分支收尾依赖。
- `README.md` 与 `docs/zh-CN/README.md`：说明内置能力、一次性仓库配置、升级和重复安装冲突。
- 目标仓库的 setup 输出：作为可审查、可复现的 Git 快照提交；只有 session、cache、log、credential 等本机状态不进入仓库。
- `tests/`：覆盖 vendor 同步、插件发现、上游完整性、退休配置、文档和发布验收。

---

### Task 1: 固定插件内置目录和所有权契约

**Files:**
- Create: `vendor/mattpocock-skills.lock.json`
- Create: `licenses/mattpocock-skills-LICENSE.txt`
- Modify: `.agents/rules/21-project-rules.md`
- Modify: `.agents/rules/22-project-structure.md`
- Modify: `tests/test_plugin_manifests.py`

**Interfaces:**
- Consumes: Matt v1.2.3 plugin manifest 和 SmartKit 现有根 `skills/`。
- Produces: `MATT_PROMOTED: dict[str, str]` 测试常量、vendor lock 格式和清晰的目录所有权边界。

- [ ] **Step 1: 写当前插件能力面失败测试**

在 `tests/test_plugin_manifests.py` 定义完整 promoted mapping：

```python
MATT_PROMOTED = {
    'ask-matt': 'skills/engineering/ask-matt',
    'diagnosing-bugs': 'skills/engineering/diagnosing-bugs',
    'grill-with-docs': 'skills/engineering/grill-with-docs',
    'triage': 'skills/engineering/triage',
    'improve-codebase-architecture': 'skills/engineering/improve-codebase-architecture',
    'setup-matt-pocock-skills': 'skills/engineering/setup-matt-pocock-skills',
    'tdd': 'skills/engineering/tdd',
    'to-spec': 'skills/engineering/to-spec',
    'to-tickets': 'skills/engineering/to-tickets',
    'wayfinder': 'skills/engineering/wayfinder',
    'implement': 'skills/engineering/implement',
    'prototype': 'skills/engineering/prototype',
    'research': 'skills/engineering/research',
    'domain-modeling': 'skills/engineering/domain-modeling',
    'codebase-design': 'skills/engineering/codebase-design',
    'code-review': 'skills/engineering/code-review',
    'resolving-merge-conflicts': 'skills/engineering/resolving-merge-conflicts',
    'wizard': 'skills/engineering/wizard',
    'grill-me': 'skills/productivity/grill-me',
    'grilling': 'skills/productivity/grilling',
    'handoff': 'skills/productivity/handoff',
    'teach': 'skills/productivity/teach',
    'to-questionnaire': 'skills/productivity/to-questionnaire',
    'wait-what': 'skills/productivity/wait-what',
    'writing-for-agents': 'skills/productivity/writing-for-agents',
}
```

断言根 `skills/` 的直接子目录恰好是 `setup-project-agents` 加上述 25 个名字；每个目录有名称匹配的 `SKILL.md`，Matt 目录都有 `agents/openai.yaml`，三个插件 manifest 的 `skills` 均为 `./skills/`。

- [ ] **Step 2: 运行测试并确认 Matt Skills 尚未 vendoring**

Run: `python tests/test_plugin_manifests.py`

Expected: 根 `skills/` 缺少 25 个 Matt 目录。

- [ ] **Step 3: 写入 v1.2.3 vendor lock 和许可证**

lock 使用完整结构：

```json
{
  "schema_version": 1,
  "repository": "mattpocock/skills",
  "upstream_version": "1.2.3",
  "tag": "v1.2.3",
  "commit": "6acc160e4e0cd062dbbbd7a1b26ae92855edf07e",
  "manifest_path": ".claude-plugin/plugin.json",
  "license_path": "LICENSE",
  "skills": [
    {"name": "ask-matt", "source_path": "skills/engineering/ask-matt"}
  ],
  "files": {
    "skills/ask-matt/SKILL.md": "3d38910535f5f01e15bc5fd7f6ca8880d628cd248741f08e6780dd7c1828e832"
  }
}
```

实际 `skills` 和 `files` 必须覆盖 25 个 Skill 及其全部 vendored files；hash key 使用 SmartKit 目标相对路径。许可证文件内容必须与该 commit 根 `LICENSE` bytes 一致。

- [ ] **Step 4: 使用 `write-rule` 更新本仓库所有权规则**

`21-project-rules.md` 规定根 `skills/setup-project-agents` 为 SmartKit-owned，lock 中列出的其他根 Skill 目录为 vendor-owned；修改 vendor-owned 内容只能运行同步器，不允许手改。`22-project-structure.md` 更新依赖方向：vendored Skills 通常是只读插件能力；唯一允许的 setup 依赖是 `setup-project-agents` 读取 `setup-matt-pocock-skills/SKILL.md` 及其五份 seed templates 来生成 Matt context 配置，runtime Hook 不得依赖任何 vendored Skill。`setup-assets/skills/` 仍是其他目标项目内容来源。

- [ ] **Step 5: 暂时只提交所有权和锁契约**

在 Task 2 同步器产生实际 vendor tree 前，本任务测试保持红色；不单独提交无法工作的中间状态。Task 1 和 Task 2 作为一个 reviewer gate 一起提交。

---

### Task 2: 实现 Matt vendor 同步、升级和回滚脚本

**Files:**
- Create: `scripts/sync_matt_skills_upstream.py`
- Create: `tests/test_sync_matt_skills_upstream.py`
- Create: `skills/ask-matt/**` and the other 24 lock-declared Matt Skill directories
- Modify: `vendor/mattpocock-skills.lock.json`
- Modify: `licenses/mattpocock-skills-LICENSE.txt`
- Modify: `.agents/rules/20-project-tools.md`
- Modify: `tests/test_plugin_manifests.py`

**Interfaces:**
- Consumes: GitHub latest stable release、指定 `vMAJOR.MINOR.PATCH` tag、上游 plugin manifest 和旧 vendor lock。
- Produces: `--check` 的只读 drift 结果、`--update` 的事务式 vendor replacement，以及精确的 version/commit/file-hash 报告。

- [ ] **Step 1: 写离线上游解析失败测试**

通过注入 HTTP reader 和本地 Git fixture，不访问真实 GitHub。覆盖：

```python
release = {'tag_name': 'v1.2.4', 'draft': False, 'prerelease': False}
manifest = {
    'name': 'mattpocock-skills',
    'version': '1.2.4',
    'license': 'MIT',
    'skills': [
        './skills/engineering/ask-matt',
        './skills/engineering/tdd',
    ],
}
```

断言拒绝 draft、prerelease、非 semver tag、manifest name/version/license 不一致、重复目标名、路径逃逸、symlink/junction、缺失 `SKILL.md`、frontmatter name 不匹配、与 `setup-project-agents` 或非 lock 管理目录重名。

- [ ] **Step 2: 写 `--check` 状态测试**

断言：

- local lock、vendor hashes、license 和 latest stable 全部一致时 exit 0；
- 上游有新 stable release 或本地 vendor/lock/license drift 时 exit 1，并分别报告 current/latest 或具体 drift path；
- 网络、Git、JSON、UTF-8 或上游验证失败时 exit 2，不修改任何文件。

- [ ] **Step 3: 写事务式 `--update` 与回滚测试**

在临时 SmartKit fixture 中保留一个非 Matt `skills/setup-project-agents`、旧 Matt dirs、lock 和 license。成功更新后断言：

- 新 manifest 的全部 Skill 被平铺到根 `skills/` 下的同名目录；
- 上游已移除的旧 Matt Skill 目录被删除；
- `setup-project-agents` 和其他非 lock 管理目录 bytes 不变；
- lock version/tag/commit/list/hashes 与 vendor tree 一致；
- license 与新 commit 一致。

在每个 replace/delete 阶段注入失败，断言旧 Matt dirs、lock 和 license 全部恢复，临时目录清理，非 Matt 目录始终未触碰。

- [ ] **Step 4: 运行同步器测试并确认脚本尚不存在**

Run: `python tests/test_sync_matt_skills_upstream.py`

Expected: FAIL，无法导入同步器。

- [ ] **Step 5: 实现同步器 CLI**

公开命令：

```text
python scripts/sync_matt_skills_upstream.py --check
python scripts/sync_matt_skills_upstream.py --update
python scripts/sync_matt_skills_upstream.py --update --tag v1.2.3
```

实现要求：

1. `--check` 和无 `--tag` 的 `--update` 从 GitHub Releases API 选择 latest stable；`--tag` 只接受完整稳定 semver tag，用于固定升级或回滚。
2. 用 tag 解析不可变 commit，并 shallow-fetch 到系统临时目录；不信任 `target_commitish`。
3. 读取上游 `.claude-plugin/plugin.json` 和 `LICENSE`，以 manifest `skills` 数组作为唯一 promoted set。
4. 校验每个 source tree 后复制到 staging 根 `skills/` 下的同名目录，计算每个普通文件 SHA-256；不跟随或复制 links。
5. 从旧 lock 取得可删除的旧 Matt names；新/旧集合之外的根 Skill 目录永不删除或覆盖。
6. 完成全部 staging、lock 和 license 生成后才进入 replace；备份所有将变化的路径，失败时按 manifest 恢复。
7. `--update` 不修改 SmartKit `VERSION`，不 commit、push、发布或更新用户已安装插件。
8. 输出 old/new version、tag、commit、Skill 数量、文件数量、changed/removed paths 和最终状态。

- [ ] **Step 6: 用同步器生成 v1.2.3 vendor tree**

Run: `python scripts/sync_matt_skills_upstream.py --update --tag v1.2.3`

Expected: 生成 25 个根 Skill 目录、完整 lock 和 MIT license；报告 commit `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e`。

- [ ] **Step 7: 登记维护命令**

使用 `write-rule` 更新 `.agents/rules/20-project-tools.md`：`--check` 是只读 upstream/vendor drift check；`--update` 是维护者显式生成命令。任何更新都必须审核 Skill 新增/删除、完整 diff、lock 和 license，再执行全仓库验证。

- [ ] **Step 8: 运行同步与插件发现测试**

Run:

```bash
python tests/test_sync_matt_skills_upstream.py
python tests/test_plugin_manifests.py
```

Expected: PASS；三个 manifest 从同一 `./skills/` 暴露 SmartKit control plane 和 25 个 Matt Skills。

- [ ] **Step 9: 提交 vendor tree 和同步器**

```bash
git add skills vendor/mattpocock-skills.lock.json licenses/mattpocock-skills-LICENSE.txt scripts/sync_matt_skills_upstream.py tests/test_sync_matt_skills_upstream.py tests/test_plugin_manifests.py .agents/rules/20-project-tools.md .agents/rules/21-project-rules.md .agents/rules/22-project-structure.md
git commit -m "feat: bundle Matt Pocock's stable skills"
```

---

### Task 3: 退休 Superpowers 平台集成并安全清理旧配置

**Files:**
- Modify: `skills/setup-project-agents/scripts/agents_setup/models.py`
- Modify: `skills/setup-project-agents/scripts/agents_setup/catalog.py`
- Modify: `skills/setup-project-agents/scripts/agents_setup/renderer.py`
- Modify: `setup-assets/catalog/assets.json`
- Delete: `setup-assets/templates/platform-config/copilot.settings.json`
- Modify: `policies/recommended-tools/codex.json`
- Modify: `policies/recommended-tools/cursor.json`
- Modify: `policies/recommended-tools/copilot.json`
- Modify: `runtime/recommended-tools/maintain_recommended_tools.py`
- Modify: `tests/test_setup_catalog.py`
- Modify: `tests/test_setup_renderer.py`
- Modify: `tests/test_recommended_tools.py`

**Interfaces:**
- Consumes: 目标仓库可能已有用户字段和旧 SmartKit Superpowers 字段的 `.github/copilot/settings.json`。
- Produces: `Catalog.retired_fields: tuple[RetiredFieldSpec, ...]`；setup 只删除声明的 dotted keys，其他用户字段保持。

- [ ] **Step 1: 写结构化字段退休失败测试**

catalog 接受：

```json
"retired_fields": [
  {"path": ".github/copilot/settings.json", "key": "extraKnownMarketplaces.superpowers-marketplace"},
  {"path": ".github/copilot/settings.json", "key": "enabledPlugins.superpowers@superpowers-marketplace"}
]
```

拒绝绝对路径、`..`、空 key、重复 `(path, key)` 和未知结构化格式。

- [ ] **Step 2: 写精确清理失败测试**

给现有 settings 同时放入 Superpowers keys、`team-marketplace`、`team-tool@team-marketplace` 和 `editor.theme`。断言只删除两个 Superpowers leaf，保留三项用户数据；只含退休字段时删除空文件。

- [ ] **Step 3: 运行相关测试并确认当前契约失败**

Run:

```bash
python tests/test_setup_catalog.py
python tests/test_setup_renderer.py
```

Expected: catalog unknown field 或 renderer 未删除旧 keys。

- [ ] **Step 4: 实现 `RetiredFieldSpec` 和清理逻辑**

```python
@dataclass(frozen=True)
class RetiredFieldSpec:
    path: PurePosixPath
    key: str
```

把 `retired_fields` 加入严格 catalog parser。renderer 在合并当前 template 前删除 dotted leaf 并裁剪空父对象；保留非空 siblings。退休字段不成为长期 desired-field owner。

- [ ] **Step 5: 删除 Superpowers 平台依赖**

从三份 policy 和 `_PLATFORM_RECIPES` 删除 Superpowers。删除 `config-copilot-settings` catalog asset 和 source template，用 `retired_fields` 清除旧 marketplace/enabled-plugin keys。不要增加 Matt recommended-tool 项：Matt 已由 SmartKit plugin manifest 分发。

- [ ] **Step 6: 更新 recommended-tools 测试**

期望工具集合：

```python
{
    'codex': {'codex', 'codegraph', 'tokscale'},
    'cursor': {'cursor-agent', 'codegraph', 'tokscale'},
    'copilot': {'copilot', 'codegraph', 'tokscale'},
}
```

把通用 consent/allowlist/render 测试改用 `codegraph` recipe；断言 policy 和 maintenance recipes 不含 `superpowers` 或独立 Matt installer。

- [ ] **Step 7: 运行 catalog、renderer 和 recommended-tools 测试**

Run:

```bash
python tests/test_setup_catalog.py
python tests/test_setup_renderer.py
python tests/test_recommended_tools.py
```

Expected: PASS。

- [ ] **Step 8: 提交平台退休**

```bash
git add skills/setup-project-agents/scripts/agents_setup/models.py skills/setup-project-agents/scripts/agents_setup/catalog.py skills/setup-project-agents/scripts/agents_setup/renderer.py setup-assets/catalog/assets.json policies/recommended-tools runtime/recommended-tools/maintain_recommended_tools.py tests/test_setup_catalog.py tests/test_setup_renderer.py tests/test_recommended_tools.py
git add -u setup-assets/templates/platform-config/copilot.settings.json
git commit -m "feat: retire Superpowers platform integration"
```

---

### Task 4: 用 Matt 工作流更新 Rules 并保留 SmartKit worktree 能力

**Files:**
- Modify: `.agents/rules/04-global-skill-config.md`
- Modify: `setup-assets/rules/04-global-skill-config.md`
- Modify: `docs/zh-CN/setup-assets/rules/04-global-skill-config.md`
- Modify: `setup-assets/skills/worktree-integrate/SKILL.md`
- Modify: `docs/zh-CN/setup-assets/skills/worktree-integrate/SKILL.md`
- Modify: `tests/test_plugin_manifests.py`

**Interfaces:**
- Consumes: plugin-bundled Matt invocation metadata、SmartKit project Skills 和更具体项目 Rules。
- Produces: 无 Superpowers 依赖的稳定调用策略；现有 worktree review/commit modes 保持。

- [ ] **Step 1: 使用 `write-rule` 重写 Workflow Configuration**

规则必须声明：

- Matt Skills 随 SmartKit 插件提供，尊重各 Skill 的用户显式/模型隐式 invocation metadata；不复制会随上游改变的名字列表。
- 依赖 `docs/agents/*` 的 Skill 在配置缺失时停止并要求重新运行 `setup-project-agents` 修复完整项目快照；只有用户明确要单独重配 Matt context 时才使用 `setup-matt-pocock-skills`，不得猜 issue tracker、labels 或 domain layout。
- 项目 `write-rule`、`write-skill`、`change-set-verification`、`worktree-environment-setup` 和更具体项目 Skill 在自己的职责内优先于通用 Matt Skill。
- worktree 可由宿主原生能力或安全的 `git worktree` 创建，随后运行目标环境 setup 和基线验证。
- 完成后提供 local merge、PR、keep、current-checkout integration；只有最后一种交给 `worktree-integrate`，push/PR 仍需明确授权。
- 保留 delegation 与 Git Safety；删除所有 `superpowers:*` 名称和专属触发规则。

- [ ] **Step 2: 使用 `write-skill` 移除 `worktree-integrate` 外部交接**

保留 review/commit mode、备份、冲突、验证和恢复。PR、keep、discard 返回父 Agent，按全局 Git Safety 和已确认选择处理；不得扩大 push、pull、force、stash、reset 或 clean 权限。

- [ ] **Step 3: 同步英文、本仓库规则和中文镜像**

中文文件逐节对应英文 source，保留标题层级、Skill 名、路径和行为。

- [ ] **Step 4: 更新运行时依赖测试**

```python
paths = (
    REPO_ROOT / '.agents/rules/04-global-skill-config.md',
    REPO_ROOT / 'setup-assets/rules/04-global-skill-config.md',
    REPO_ROOT / 'setup-assets/skills/worktree-integrate/SKILL.md',
)
self.assertNotIn('superpowers:', ''.join(path.read_text() for path in paths).lower())
```

继续运行英文/中文 Markdown 结构镜像测试。

- [ ] **Step 5: 验证并提交规则变更**

Run: `python tests/test_plugin_manifests.py`

Expected: PASS。

```bash
git add .agents/rules/04-global-skill-config.md setup-assets/rules/04-global-skill-config.md docs/zh-CN/setup-assets/rules/04-global-skill-config.md setup-assets/skills/worktree-integrate/SKILL.md docs/zh-CN/setup-assets/skills/worktree-integrate/SKILL.md tests/test_plugin_manifests.py
git commit -m "feat: make bundled Matt Skills the default workflow"
```

---

### Task 5: 把 Matt 仓库级初始化并入 `setup-project-agents`

**Files:**
- Modify: `skills/setup-project-agents/SKILL.md`
- Modify: `setup-assets/catalog/assets.json`
- Modify: `setup-assets/templates/entry-files/AGENTS.md`
- Modify: `skills/setup-project-agents/scripts/agents_setup/catalog.py`
- Modify: `skills/setup-project-agents/scripts/agents_setup/renderer.py`
- Modify: `README.md`
- Modify: `docs/zh-CN/README.md`
- Modify: `tests/test_setup_catalog.py`
- Modify: `tests/test_setup_renderer.py`
- Modify: `tests/test_setup_cli.py`
- Modify: `tests/test_setup_workflow.py`
- Modify: `tests/test_plugin_manifests.py`

**Interfaces:**
- Consumes: vendored `setup-matt-pocock-skills/SKILL.md`、五份 seed templates、目标 Git remote、现有 `AGENTS.md`/`docs/agents/` 和 monorepo evidence。
- Produces: 八个 `generation_requests`、目标 `## Agent skills` 区块、明确的 Git commit handoff，以及无需第二条手动命令的首次仓库配置。

- [ ] **Step 1: 写三项新增 generation requests 的失败测试**

start/CLI 测试把 generation request 数量从 5 改为 8，并断言新增目标恰好为：

```python
{
    'docs/agents/issue-tracker.md',
    'docs/agents/triage-labels.md',
    'docs/agents/domain.md',
}
```

断言这三个 blueprint source 分别引用 vendored setup Skill 的 GitHub tracker、triage labels 和 domain seed。`setup-project-agents` 的 authoring contract 允许 tracker 生成时按证据改读同目录 GitLab/local seed；catalog 仍只允许这三个明确的 vendor-source blueprint，其他非 control-plane assets 必须位于 `setup-assets/`。

- [ ] **Step 2: 写配置推断、保留和 review 失败测试**

覆盖以下输入与结果：

- GitHub remote → GitHub tracker seed；GitLab remote → GitLab seed；无 remote → local-markdown seed。
- 多个 remote 指向不同 tracker，或现有 tracker doc 与 remote 冲突 → `setup-project-agents` 必须在写生成文件前询问；没有回答时不得进入 Review Gate 或调用 finish。
- 无现有 triage doc → 五个默认 label mappings；现有 doc → byte-preserve，除非用户在 setup 对话中明确更改。
- 无 monorepo signal → single-context；发现 `pnpm-workspace.yaml`、package workspaces 或多个带 `src/` 的 packages → 要求用户确认 single/multi，未确认时不得进入 Review Gate 或调用 finish。
- 已有三个完整 docs → 默认保留内容，重复 setup 不重置日常手改。
- 生成的 `AGENTS.md` 恰好有一个 `## Agent skills` 区块，分别指向三个 docs；重复 setup 不追加第二个区块。

- [ ] **Step 3: 运行 setup 测试并确认当前只有五个生成目标**

Run:

```bash
python tests/test_setup_catalog.py
python tests/test_setup_renderer.py
python tests/test_setup_cli.py
python tests/test_setup_workflow.py
```

Expected: 新增 generation requests、推断状态和 AGENTS 区块断言失败。

- [ ] **Step 4: 扩展 catalog 和 renderer 的受控 vendor blueprint 支持**

在 catalog 中加入三个 `mode: generate` blueprint，source 精确指向：

```text
skills/setup-matt-pocock-skills/issue-tracker-github.md
skills/setup-matt-pocock-skills/triage-labels.md
skills/setup-matt-pocock-skills/domain.md
```

tracker target 始终是 `docs/agents/issue-tracker.md`；选择 GitLab/local 时由 `setup-project-agents` 按 authoring contract 读取同目录 `issue-tracker-gitlab.md` 或 `issue-tracker-local.md`。renderer 继续只接受 catalog 声明的 generated targets，不允许任意 vendored Skill 成为 setup asset source。

- [ ] **Step 5: 扩展 `setup-project-agents` Authoring Workflow**

把 managed generation targets 从 5 改为 8。Agent 必须完整读取 vendored `setup-matt-pocock-skills/SKILL.md`，但不把它作为第二个 Skill 隐式调用；在同一 setup 对话中执行其 Explore/Present/Confirm 规则，把确认结果写入 `GENERATED/docs/agents/`。可由证据唯一确定的选择不提问；只有 tracker 冲突和真实 monorepo layout 分支需要输入。

Review Gate 增加：三个 docs 完整、与已确认选择一致、既有用户内容按规则保留、`AGENTS.md` 指针唯一。finish 继续一次性事务应用全部 SmartKit 与 Matt-context outputs；其中任何一项失败都不部分落盘。

- [ ] **Step 6: 更新 AGENTS entry template**

在现有 Rule tables 后加入固定区块：

```markdown
## Agent skills

### Issue tracker

See `docs/agents/issue-tracker.md`.

### Triage labels

See `docs/agents/triage-labels.md`.

### Domain docs

See `docs/agents/domain.md`.
```

具体 tracker、label 和 layout 内容只属于三个 docs，不在 AGENTS 中重复。

- [ ] **Step 7: 更新首次使用、重新配置和升级文档**

公开正常流程：

```text
Install/update SmartKit → start a new host session → run setup-project-agents
→ answer only unresolved project-context questions → review → finish
→ maintainer commits the generated snapshot → other developers pull → start work
```

说明 `setup-matt-pocock-skills` 已内置但正常无需单独运行；仅在日后主动切换 tracker、重映射 labels、重建 domain layout 或修复缺失配置时显式调用。宿主可能显示 namespaced form，例如 `smartkit:setup-matt-pocock-skills`。明确不要同时通过 skills.sh、Matt 官方插件和 SmartKit 安装相同 Skills。

用户升级限定为更新 SmartKit、开启新会话并检查 Skill 可见性；普通 Skill 升级不重写三个项目 docs，也不要求重跑任何 setup。维护者同步命令只留在 `.agents/rules/20-project-tools.md`。

- [ ] **Step 8: 固定 Git tracking 与团队交接契约**

在 `setup-project-agents/SKILL.md` 的成功结果中，把 finish 返回的 `changed_paths` 标为“审核后提交到当前仓库”，并明确以下受管输出必须被 Git 跟踪，而不是加入 `.gitignore`：

```text
AGENTS.md
.agents/**
.codex/**、.cursor/**、.github/** 中由 setup 管理的 wrapper/config
docs/agents/**
CONTEXT.md、CONTEXT-MAP.md、docs/adr/**（实际生成时）
```

README 同步说明责任边界：一名维护者运行 setup 并提交快照，其他开发者只需 pull；每位开发者仍需在自己的宿主中安装/更新 SmartKit 插件并开启新会话。若项目现有 `.gitignore` 屏蔽任何新增受管输出，Review Gate 必须把它报告为阻塞项，要求先修正规则；不得静默留下只有 setup 操作者能看到的本机配置。

测试覆盖英文 README、中文 README 和 Skill handoff 都包含“提交项目快照、其他开发者无需 setup、不要 ignore 受管文件”的等价语义，并覆盖 ignored generated target 不能 finish。setup session、cache、log 和 credential 保持在仓库外，不进入 `changed_paths`。

- [ ] **Step 9: 写一对一中文 README 并验证完整 setup**

保持英文顺序、Markdown、命令、路径、版本和语义一致。

Run:

```bash
python tests/test_setup_catalog.py
python tests/test_setup_renderer.py
python tests/test_setup_cli.py
python tests/test_setup_workflow.py
python tests/test_plugin_manifests.py
```

Expected: PASS。

- [ ] **Step 10: 提交整合后的仓库 bootstrap**

```bash
git add skills/setup-project-agents/SKILL.md setup-assets/catalog/assets.json setup-assets/templates/entry-files/AGENTS.md skills/setup-project-agents/scripts/agents_setup/catalog.py skills/setup-project-agents/scripts/agents_setup/renderer.py README.md docs/zh-CN/README.md tests/test_setup_catalog.py tests/test_setup_renderer.py tests/test_setup_cli.py tests/test_setup_workflow.py tests/test_plugin_manifests.py
git commit -m "feat: configure Matt Skills during project setup"
```

---

### Task 6: 提升版本并执行插件级完整验收

**Files:**
- Modify: `VERSION`
- Modify: `plugin.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `.cursor-plugin/plugin.json`
- Modify: `.cursor-plugin/marketplace.json`
- Modify: `.github/plugin/marketplace.json`
- Modify: `setup-assets/catalog/assets.json`

**Interfaces:**
- Consumes: 根 `VERSION` 和完整 plugin tree。
- Produces: SmartKit `0.2.0`，三个宿主从同一 bundle 发现 26 个 Skills。

- [ ] **Step 1: 把根版本改为 `0.2.0` 并同步 manifests**

Run:

```bash
python scripts/sync_plugin_version.py
python scripts/sync_plugin_version.py --check
```

Expected: 所有 manifest、marketplace 和 catalog version 为 `0.2.0`，check exit 0。

- [ ] **Step 2: 检查 Matt 上游和本地 vendor 一致性**

Run: `python scripts/sync_matt_skills_upstream.py --check`

Expected: exit 0，报告本地 lock/vendor/license 与最新 stable release 一致。若官方已有新版，先运行 `--update`、审核 Skill diff 并重新执行 Task 2、Task 4 和 Task 5 的测试；不得临时改成浮动 ref。

- [ ] **Step 3: 执行完整单元测试**

Run: `python -m unittest discover -s tests -p 'test_*.py'`

Expected: exit 0。提供至少 10 分钟 timeout；执行通道中断时先检查原进程，不并行重跑。

- [ ] **Step 4: 检查 diff 和残留运行时依赖**

Run:

```bash
git diff --check
rg -n -S "superpowers@|superpowers:|obra/superpowers|Superpowers for" policies runtime setup-assets .agents/rules README.md docs/zh-CN/README.md skills/setup-project-agents
```

Expected: diff check exit 0；当前运行时来源无命中。`docs/superpowers/plans/` 是历史计划位置，不属于运行时扫描。

- [ ] **Step 5: 验证 plugin bundle 内容**

逐项确认：

- 三个 plugin manifests 均指向 `./skills/`；
- 根 `skills/` 恰好含 `setup-project-agents` 和 lock 中的 25 个 Matt dirs；
- 所有 lock hashes、frontmatter names、nested resources 和 `agents/openai.yaml` 通过；
- license bytes 与固定 commit 一致；
- setup catalog 不再复制 Matt 到目标项目；
- setup start/review/finish 管理八个 generation targets，并原子生成三个 `docs/agents/` 配置；
- recommended-tool Hook 不检测或安装 Matt/Superpowers；
- 用户 Copilot 非 SmartKit 字段保持；
- docs 说明正常首次设置无需单独运行 `setup-matt-pocock-skills`，插件更新后开启新会话并避免重复安装。

- [ ] **Step 6: 在三个宿主做代表性插件验收**

在当前可用宿主安装本地 SmartKit `0.2.0`，开启新会话并验证 `setup-project-agents`、`setup-matt-pocock-skills`、`ask-matt`、`tdd` 可见；验证显式调用 Skill 能加载完整指令和 bundled reference。其他两个宿主若当前环境不可用，报告未运行，不用模拟结果代替。

- [ ] **Step 7: 提交版本和验收变更**

```bash
git add VERSION plugin.json .codex-plugin/plugin.json .cursor-plugin/plugin.json .cursor-plugin/marketplace.json .github/plugin/marketplace.json setup-assets/catalog/assets.json
git commit -m "chore: release smartkit 0.2.0"
```

---

## Rollout and Recovery

- 先通过本地 marketplace 安装 SmartKit `0.2.0`，在新会话确认插件列出 26 个 Skills，再发布到远端 marketplace。
- 后续 Matt release 由维护者运行 `python scripts/sync_matt_skills_upstream.py --check` 发现；审核后运行 `--update`、测试、提升 SmartKit 版本并发布。
- 用户只需更新 SmartKit 插件并开启新会话；目标仓库没有 Matt vendor copy，因此无需重跑 `setup-project-agents` 或 `setup-matt-pocock-skills` 来升级 Skills。
- 新仓库或项目快照契约升级时，由一名维护者运行 `setup-project-agents`、审核 `changed_paths` 并提交；团队其余成员只需 pull 这些受管文件，不要逐人 setup，也不要 ignore 它们。
- 若仅 SmartKit 内置的 Matt Skills 升级，团队成员各自在宿主中更新插件并开启新会话；若 SmartKit 的项目 Rule/template/context contract 也变化，才由维护者重跑 setup 并提交新的快照 diff。
- 回滚时选择一个已审核的旧稳定 tag；例如回到本计划基线时运行 `python scripts/sync_matt_skills_upstream.py --update --tag v1.2.3`，验证 lock/vendor/license 后发布一个新的 SmartKit patch version；不得直接编辑单个 vendored Skill。
- 若用户同时安装了另一份 Matt Skills，SmartKit 不自动删除它；报告重复来源并要求用户自行选择保留一个，避免未经授权卸载插件或删除个人 Skills。
- 不删除历史 `docs/superpowers/plans/`；它们是实施记录，不是运行时依赖。

## Self-Review

- Spec coverage: 插件内置、完整 promoted set、三平台发现、同步、升级、回滚、许可证、重复安装、自动仓库初始化、Git-tracked 团队快照、显式重新配置入口、Superpowers 退休、worktree 和验收均有对应任务。
- Placeholder scan: 上游版本、commit、25 个 Skill、目标路径、命令、返回状态和验证结果均已定义。
- Type consistency: vendor lock 的 `skills` 决定可管理目录，`files` 校验 vendored tree；`RetiredFieldSpec(path, key)` 只由 catalog/renderer 使用；setup 不再消费 Matt 外部 Skill specs。
