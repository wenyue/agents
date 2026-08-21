# Finalization Contract

只接受一个闭合契约，其 `mode` 等于 `standalone-task`、`stage-ticket-into-batch` 或
`deliver-ticket-batch`。

每种模式都提供：

- `source` worktree、分支、精确的 `head` 与 `tree`、`creation_owner` 和 `scope_owner`；
- `target` checkout、分支、`expected_head` 和 `target_policy`；
- `evidence` fixed point、验收来源、review 种类和结果、已 review 的 head 与 tree、验证命令和结果，
  以及 findings；
- `history_policy` 及其完整自有范围；
- 恢复 refs 以及当前和下一个 owner；
- 获准的清理和保留状态；以及
- 一个 `authorized_outcome`。

拒绝未知模式、跨模式字段、缺失值和隐含的远程权限。

## 证明当前状态

重新推导每个具名 Git identity、干净的自有状态、祖先关系、范围、发布情况、证据、恢复事实和
owner。快照每个受影响 checkout 的分支、`HEAD`、index tree、staged、unstaged 与 untracked 状态。
每次变更前立即复查它所依赖的事实。遇到过期、模糊、已发布或无关状态时停止。

只有一个闭合模式、精确 source 与 target、当前证据、获准的恢复与清理，以及不相关状态均得到证明
时，公共契约才通过。随后由所选 mode reference 验证其自有历史、结果和附加字段。
