# 07 — SmartKit 1.1.0 发布契约与跨仓验收

Category: enhancement
Status: resolved
Blocked by: 01 — Plugin Playwright MCP 三端交付; 02 — Daily Project Check Gate; 03 — Project HTTP MCP 管理闭环; 04 — Project stdio MCP 与平台差异; 05 — 统一 MCP Readiness 检查; 06 — OtakuRoom Skills 与 Project MCP 接入

## What to build

把已完成的 Plugin MCP、Project MCP、Daily Project Check Gate 和 OtakuRoom adoption 收敛为
SmartKit 1.1.0 的完整可发布契约，并提供跨仓验证证据。

- [x] 根版本、三端 manifests、marketplaces 和 setup catalog 同步为 1.1.0。
- [x] 英文与简体中文公共文档说明 Plugin MCP、Project MCP、readiness 和第三方 Skill 边界。
- [x] ADR 记录 Skill snapshot delivery 与 MCP configuration delivery 的选择及 host adapter tradeoff。
- [x] 项目 Rules、结构边界和 setup Skill 描述唯一当前契约，不保留旧 throttle 或 bridge 行为。
- [x] Plugin MCP adapter check、版本 check、Codex MCP companion validator 和完整 SmartKit unit suite 通过。
- [x] 旧版完整 plugin-creator validator 的既有不兼容诊断已复现并记录，未通过删除 Hooks 或改变 Matt Skill 触发契约规避。
- [x] SmartKit 与 OtakuRoom 都通过 diff whitespace/conflict-marker 检查。
- [x] OtakuRoom 使用其固定 Flutter/Dart 环境完成与改动风险相称的配置分析和聚焦测试。
- [x] 最终差异不包含 secret、cache、session 文件或未经授权的用户配置变更。
- [x] 所有 ticket 的验收标准都能映射到最终证据，无未说明的跳过项。

## Comments

- 只有所有 blocker 完成后本 ticket 才进入 frontier。
- 2026-08-10：`sync_mcp_adapters.py --check`、`sync_plugin_version.py --check`、
  Codex MCP companion validator 与 SmartKit 全量单元测试通过（211 tests，1 skipped）。
- 2026-08-10：系统内置的旧版完整 plugin-creator validator 仍报告 SmartKit 既有的
  Copilot Hooks 和 14 个 user-invoked Matt Skills；这些不是 MCP companion 错误，保留现有契约。
- 2026-08-10：SmartKit 与 OtakuRoom `git diff --check`、冲突标记、secret/cache/session
  审计通过；OtakuRoom 正式 setup 为 `finish/check=clean`，pinned Flutter 聚焦测试通过
  （15 tests）。
