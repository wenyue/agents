---
name: track-worktree-time
description: 当任务创建或复用链接 Git Worktree 来修改代码时使用。
---

# 记录 Worktree 任务指标

创建一份最小任务凭据；完成后再根据已登记 Session 日志生成 wall-clock、Token、估算费用和观察到的
工具活动。不要维护人工阶段切换。

## 工作流

1. 准备 Worktree 前运行 `start --task "<summary>" --repository "<repository>" --worktree
   "<intended-worktree>"` 并保存任务 ID。Codex 使用 `CODEX_THREAD_ID`，以最近一条用户消息的时间戳
   划定边界但不保存正文；其他环境必须同时提供稳定的 `--client` 和 `--session-id`。
2. 每个额外且可归因的 Session 运行一次 `attach <task-id>`。只有该 Session 在 `start` 后专为本任务
   创建时才用 `--entire-session`，否则记录基线。
3. 参与者没有稳定 Session ID 时运行 `gap <task-id> --label "<participant>" --reason
   "<reason>"`。整体归因将标为 partial；不得按 Workspace 或日期猜测。
4. `report <task-id>` 只生成只读快照。集成或选定结束方式完成后运行 `finish <task-id>`，把事后
   Markdown 报告放入最终交接。`finish` 会关闭边界，因此最终回复生成不计入报告。

POSIX 命令前缀为 `sh .agents/skills/track-worktree-time/scripts/task-metrics.sh`；Windows 使用
`powershell -File .agents/skills/track-worktree-time/scripts/task-metrics.ps1`。两者调用 Python 3.11+
的确定性 `scripts/timing.py` 核心。

## 指标契约

- `wall-clock` 是凭据起止之间的实际时间。
- Tokscale Token、费用与模型活动是已显式登记 client/session/model 行的结束值减基线值；rollout 前缀
  ID 只按稳定 Session ID 后缀匹配。
- `model activity` 是累计处理时长；`tool activity` 事后分类已完成的 Codex 工具调用区间。两者可重叠，
  不是 wall-clock 阶段，也不另算“并行时长”。
- 日志缺失、调用未闭合、归因缺口或快照无法对账时，必须给出 unavailable 或 partial 的具体诊断。
- 费用标为 Tokscale `API 等价估算费用`，不得称为实际账单。

## 隐私与失败边界

- 使用 Tokscale 原始 `--json --group-by client,session,model`；不得调用 Summarizer、`tokscale report`
  任务聚类、`tokscale submit` 或网络发布。
- Transcript 只可临时读取；仅保存计数、时长、标识符和诊断，不保存 Prompt、Response、Command 或输出。
- Tokscale 是可选增强；其失败不得阻止 wall-clock 完成。
- `scripts/timing.py` 可结束旧 schema-1 凭据，但其 Token 和费用仍为 unavailable。

## 验证与结果

确认凭据唯一、纳入的 Session 均已显式登记、计数器未倒退，并解释 partial/unavailable。报告时间戳、
wall-clock、登记 Session、归因缺口、各类 Token、模型累计活动、可用时的 Tokscale 版本与 API 等价估算
费用、观察到的工具活动、诊断和恢复情况。
