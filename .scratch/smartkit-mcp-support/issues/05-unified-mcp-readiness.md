# 05 — 统一 MCP Readiness 检查

Category: enhancement
Status: resolved
Blocked by: 01 — Plugin Playwright MCP 三端交付; 02 — Daily Project Check Gate; 04 — Project stdio MCP 与平台差异

## What to build

在 Daily Project Check Gate 放行后，通过一个 runner 聚合现有 recommended tools、required
values、Plugin MCP Readiness Profile 和 Project MCP Readiness Profile，并向用户交付一次可
操作的诊断。

- [x] readiness profile 与对应 MCP declaration 共同拥有生命周期。
- [x] 支持 command availability、allowlisted runtime minimum、workspace file 和环境变量存在性检查。
- [x] runtime version 通过受信任 profile 选择，项目不能注入任意命令或 shell 脚本。
- [x] Playwright 检查 Node 最低版本和 npx，且不检查 npm cache 或启动 MCP。
- [x] Flutter Inspector 只检查项目 executable，不要求 debug session 在线。
- [x] Sentry 与 OtakuRoom HTTP MCP 不执行网络、OAuth、端口或服务健康探测。
- [x] 所有 findings 聚合成一次宿主原生提示，并沿用现有 consent 边界。
- [x] 无效 readiness 产生非阻塞诊断，且当天不会自动重试。
- [x] 所有 detector 类型、平台过滤和安全边界具有外部行为测试。

## Comments

- 只有所有 blocker 完成后本 ticket 才进入 frontier。
- 2026-08-10：Daily runner 聚合 tool/required-value、Plugin MCP 与 Project MCP；
  readiness 仅支持 command、Node minimum、workspace path 与 env-name 四类静态检查。
- 2026-08-10：补齐平台过滤、拒绝 shell/非 allowlist runtime、聚合及一次性 gate 测试；
  `python3 -m unittest tests.test_recommended_tools tests.test_sync_mcp_adapters` 通过
  （38 tests）。
