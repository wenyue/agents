# 01 — Plugin Playwright MCP 三端交付

Category: enhancement
Status: resolved
Blocked by: None

## What to build

从一个 canonical Plugin MCP registry 生成 Codex、Cursor、Copilot 的原生 adapter，使安装
SmartKit 后三端都能发现并启动最新版、隔离、无头模式的 Playwright MCP。插件只交付配置，
保留宿主工具审批，不复制 Playwright 服务实现。

- [x] 一个严格校验的 registry 是三端 adapter 的唯一来源。
- [x] Codex、Cursor、Copilot manifest 显式引用各自有效的 MCP 配置。
- [x] 三端 adapter 表达同一个 Playwright 启动意图并保留必要的宿主 schema 差异。
- [x] Copilot adapter 显式暴露全部工具，所有宿主继续使用默认审批行为。
- [x] 只读同步检查能发现 registry 与生成物漂移。
- [x] 未知字段、不安全 readiness 和危险 Playwright flags 被拒绝。
- [x] Codex MCP companion validator 与相关契约测试通过。

## Comments

- 发布 ticket 时工作树已有该 slice 的部分未验收实现；验收标准仍以本 ticket 为准。
- Plugin MCP adapter check、三端 manifest/adapter tests 和 Codex MCP companion validator 已通过。
- 完整旧版 plugin-creator validator 仍报告 SmartKit 既有 Hooks 与 user-invoked Matt Skills；这些
  基线诊断不属于本 ticket 的 MCP companion contract，未通过删除现有能力规避。
