# 03 — Project HTTP MCP 管理闭环

Category: enhancement
Status: resolved
Blocked by: None

## What to build

以 Sentry HTTP MCP 为 tracer bullet，让项目从一个严格的 canonical declaration 经公开 setup
workflow 生成三端 native configuration，并用 Managed MCP Entry lock 精确管理自己的条目。

- [x] Project MCP 是现有 version 1 项目配置中的可选 server 数组，每项具有稳定 ID。
- [x] HTTP transport、URL、宿主范围和类型化 override 接受严格校验。
- [x] setup request 完整保留并验证 Project MCP 选择，不存在第二套读取入口。
- [x] Codex、Cursor、Copilot 生成符合各自 schema 的 HTTP MCP 条目。
- [x] ownership lock 只记录受管 native path/key，不记录 secret 或服务制品信息。
- [x] 首次运行可接管语义相等的既有条目，并拒绝不相等的用户条目。
- [x] 删除 canonical server 只删除 lock 记录的条目，并保留所有无关用户 MCP。
- [x] setup apply/check 事务、回滚和 request round-trip 测试通过。

## Comments

- 发布 ticket 时工作树已有该 slice 的部分未验收实现；验收标准仍以本 ticket 为准。
- 2026-08-10：新增 version 1 `mcp.servers[]` HTTP 契约、三端 adapter、精确
  `project-mcp.lock.json` ownership，以及 prepare/apply/check round-trip 覆盖。
- 2026-08-10：HTTP tracer-bullet 与 catalog/renderer 聚焦测试通过（41 tests）。
