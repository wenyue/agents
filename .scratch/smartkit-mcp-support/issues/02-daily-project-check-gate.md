# 02 — Daily Project Check Gate

Category: enhancement
Status: resolved
Blocked by: None

## What to build

让 SmartKit 的自动环境检查在每个 canonical project、每个当前宿主、每个本地日期最多执行
一次。Daily Project Check Gate 必须先于 detector 生效，同时保留人工强制重跑和非阻塞失败
语义。

- [x] 项目根按最近 project-agent 配置、最近 Git 标记、当前目录的顺序解析。
- [x] project、host 和 local date 共同决定独立的 daily identity。
- [x] gate 在任何 detector 前记录 started，使进程异常也不会导致当天自动重跑。
- [x] passed、notified、error 和 started 均拦截当天后续自动检查。
- [x] policy 或 checker 变化不绕过当天 gate，人工 force 可以重跑。
- [x] 并发 SessionStart 只有一个调用进入检查 pipeline。
- [x] cache 无法安全写入时跳过诊断并允许原任务继续。
- [x] Cursor 只在 session start 运行检查，不再逐 prompt 启动检查进程。
- [x] Rule delivery 保持事件驱动，不进入 daily gate。

## Comments

- 发布 ticket 时工作树已有该 slice 的部分未验收实现；验收标准仍以本 ticket 为准。
- 2026-08-10：实现 canonical project root、project/host/date cache identity、started-first
  状态、并发锁、`--force` 和 fail-open gate；Cursor Hook 收敛为 sessionStart。
- 2026-08-10：`python3 -m unittest tests.test_recommended_tools` 通过（31 tests）。
