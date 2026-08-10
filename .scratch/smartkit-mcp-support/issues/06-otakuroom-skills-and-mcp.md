# 06 — OtakuRoom Skills 与 Project MCP 接入

Category: enhancement
Status: resolved
Blocked by: 03 — Project HTTP MCP 管理闭环; 04 — Project stdio MCP 与平台差异; 05 — 统一 MCP Readiness 检查

## What to build

通过正式 setup workflow 让 OtakuRoom 使用三个官方 Flutter Skills，以及 Sentry、Flutter
Inspector、OtakuRoom 三个 Project MCP，同时保留应用自己的测试、layout 和 runtime
ownership。

- [x] 三个官方 Flutter Skills 从上游来源解析、快照并记录 resolved commit 与文件 hash。
- [x] 外部 Skill 快照不包含 OtakuRoom 本地修改。
- [x] 本地测试路由把 unit/widget tests 与 integration tests 分开。
- [x] layout 修复路由复用 runtime error 与 screenshot 能力。
- [x] responsive layout 继续服从 RootLayoutWidget 和项目 orientation helpers。
- [x] Sentry 在三端使用直接 HTTP，不再使用 npm bridge。
- [x] Flutter Inspector 使用三端适用的 stdio executable path，并声明静态文件 readiness。
- [x] OtakuRoom MCP 使用约定的静态默认 endpoint，不进行运行时端口发现。
- [x] 既有 Dart MCP 和其他用户配置保持不变。
- [x] setup 通过公开 start/finish workflow 完成，并报告 check clean。
- [x] 项目配置解析、MCP ownership、command exposure 和受影响 owner 的聚焦测试通过。

## Comments

- 只有所有 blocker 完成后本 ticket 才进入 frontier。
- 2026-08-10：正式 setup finish 返回 `check: clean`；Flutter Skills 固定于
  `flutter/skills@141bccd9a3a9d43d698752272ecf56a32026d174`，Sentry Skill 固定于
  `getsentry/plugin-codex@c900f2f12324920d33338db38f037de251b71349`。
- 2026-08-10：三端 MCP parity、ownership lock 与全部外部 Skill hash 校验通过；
  pinned Flutter `command_mcp_server_test.dart` 通过（15 tests）。
- 2026-08-10：项目配置不再声明许可证元数据；正式 setup 从上游根许可证文件自动识别
  Sentry 为 MIT、Flutter 为 BSD-3-Clause，并再次返回 `finish/check=clean`。
