# 04 — Project stdio MCP 与平台差异

Category: enhancement
Status: resolved
Blocked by: 03 — Project HTTP MCP 管理闭环

## What to build

以 Flutter Inspector 为 tracer bullet，让 Project MCP 支持一个 canonical stdio declaration，
同时通过受限 host override 表达三端不可避免的 executable path 差异。

- [x] stdio command、args、cwd 和环境变量名引用接受严格校验。
- [x] 环境变量只按名称传递，任何生成文件和 ownership lock 都不包含 secret 值。
- [x] override 只能修改当前 transport 支持的类型化字段，并且只能用于启用的宿主。
- [x] Codex、Cursor、Copilot adapter 保留各自 type、环境变量和工作目录表达。
- [x] command arguments 允许合法重复，环境变量名和宿主列表保持唯一。
- [x] HTTP 与 stdio 字段混用、未知宿主和未知字段均在写入前失败。
- [x] stdio 的接管、冲突、更新、删除和用户配置保留行为与 HTTP 一致。

## Comments

- 只有 ticket 03 完成后本 ticket 才进入 frontier。
- 2026-08-10：实现三端 stdio adapter、名称式 env 传递及受限 platform override；
  补充重复 args、唯一 platforms/env、跨平台迁移和用户条目保留测试。
- 2026-08-10：`python3 -m unittest tests.test_setup_catalog tests.test_setup_renderer`
  通过（41 tests）。
