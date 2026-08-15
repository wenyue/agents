# 平台运行时对齐实施计划

> **Historical terminology:** 本文保留的“平台”“三平台”和 `platform-*` 名称记录当时的真实术语。
> 当前契约使用 `Harness` 表示 Codex、Cursor 和 Copilot，并使用 `Platform` 表示 Windows、Linux
> 或 macOS；不要把这些历史术语、路径或命令当作当前入口。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不修改 Copilot 包装器的前提下，让 Cursor 推荐工具 Hook 在 Windows 和 Linux 使用各自可靠的 Python 入口，并用可执行测试固化三平台的共同能力与原生差异。

**Architecture:** 保留现有 `.ps1` 和 `.sh` 为平台实现，新增一个 Cursor 使用的 polyglot `.cmd` 分发器：Windows 进入批处理块并调用 PowerShell，POSIX shell 跳过批处理块并调用 `.sh`。平台能力矩阵放在契约测试中，直接验证真实清单、分发器和宿主入口；README 及中文镜像只说明经测试支持的结果。

**Tech Stack:** Python 3.10+ 标准库、PowerShell、POSIX sh、JSON、`unittest`。

## Global Constraints

- 不修改 `setup-assets/templates/wrappers/agent-wrappers/github.agent.md` 或 `setup-assets/templates/wrappers/rule-wrappers/github.instructions.md`。
- 不新增第三方依赖。
- Cursor Windows 使用现有 PowerShell 入口及 `python`；Cursor Linux 使用现有 sh 入口及 `python3`。
- Hook 模式继续 fail-open，不得因检查器故障阻塞会话。
- 完成后运行仓库全量测试和 `git diff --check`。

---

### Task 1: Cursor 跨平台 Hook 分发器

**Files:**
- Create: `runtime/recommended-tools/run_recommended_tools.cmd`
- Modify: `hooks/cursor.json`
- Test: `tests/test_plugin_manifests.py`

**Interfaces:**
- Consumes: `check_recommended_tools.ps1` 和 `check_recommended_tools.sh` 的现有参数与退出码契约。
- Produces: `run_recommended_tools.cmd [check|hook] ...`，由 Windows CMD 或 POSIX shell 分发到对应入口。

- [ ] **Step 1: 写失败测试**

  增加测试，要求 Cursor 两个 Hook 都调用同一个 `run_recommended_tools.cmd`，并在当前 OS 实际执行分发器的 `--help` 路径。

- [ ] **Step 2: 验证测试因分发器不存在而失败**

  Run: `python -m unittest tests.test_plugin_manifests.PluginManifestTest.test_cursor_hook_uses_cross_platform_dispatcher`

- [ ] **Step 3: 实现最小分发器并更新 Cursor 清单**

  Windows 批处理块调用 `check_recommended_tools.ps1`；POSIX 块 `exec sh check_recommended_tools.sh`。两个 Cursor 事件只保留 delivery 参数差异。

- [ ] **Step 4: 验证聚焦测试通过**

  Run: `python -m unittest tests.test_plugin_manifests.PluginManifestTest.test_cursor_hook_uses_cross_platform_dispatcher`

### Task 2: 三平台能力契约和文档矩阵

**Files:**
- Modify: `tests/test_plugin_manifests.py`
- Modify: `README.md`
- Modify: `docs/zh-CN/README.md`

**Interfaces:**
- Consumes: 三个平台 Hook 清单和 setup 已有显式模型契约。
- Produces: 可执行的 Windows/Linux Hook 路由矩阵，以及一一对应的英文和中文支持说明。

- [ ] **Step 1: 写失败的能力矩阵测试**

  用表驱动断言 Codex、Cursor、Copilot 都声明 Windows/Linux 路由；允许各宿主使用不同字段，不比较文本外形。

- [ ] **Step 2: 验证测试先失败**

  Run: `python -m unittest tests.test_plugin_manifests.PluginManifestTest.test_hook_platform_contract`

- [ ] **Step 3: 让能力矩阵读取真实入口并补齐双语说明**

  Cursor 的能力来自新分发器；Codex 和 Copilot 继续使用现有原生平台字段。README 表格只描述 Windows/Linux、入口和平台专属差异。

- [ ] **Step 4: 运行聚焦测试**

  Run: `python -m unittest tests.test_plugin_manifests`

### Task 3: 完整验证

**Files:**
- Verify only.

**Interfaces:**
- Consumes: Task 1 和 Task 2 的完整变更。
- Produces: 当前工作区的全量验证证据。

- [ ] **Step 1: 运行仓库全量测试**

  Run: `python -m unittest discover -s tests -p 'test_*.py'`

- [ ] **Step 2: 检查 diff 完整性**

  Run: `git diff --check`

- [ ] **Step 3: 审查最终 diff 和 Git 状态**

  确认没有 Copilot 包装器改动，且新增 `.cmd` 在 Git 中保留 POSIX 可执行位。
