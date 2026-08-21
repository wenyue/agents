# Standalone Task

要求 `history_policy=consolidate-checkpoints`、完整的未发布 checkpoint 范围、与所选流程匹配的
target policy、`evidence.review_kind=formal-review`，以及等于 `merge-locally`、
`create-pull-request`、`keep-for-later` 或 `return-for-review` 的 `authorized_outcome`。

## 选择获准结果

只读取匹配的流程：

- 本地合并：[`merge-local.md`](merge-local.md)
- 创建 pull request：[`create-pull-request.md`](create-pull-request.md)
- 保留备用：[`keep-for-later.md`](keep-for-later.md)
- 返回审查：[`return-for-review.md`](return-for-review.md)

## 最终化已 Review 历史

1. 刷新 target。只通过 current ancestry 或 equivalent-change evidence 加 required verification
   检测 **Already Delivered**。
2. 仅当 accepted evidence 决定 conflict behavior 时，才可将 moved target 合并到 task branch。
   调用 `resolving-merge-conflicts` 前检查 accepted behavior 和双方。证据允许多个结果时，恢复
   pre-merge task state 并请求决定。任何 synchronization 都会使 review 失效，并将 changed task
   交回 verification 和 formal review。
3. 要求 formal review 在精确 fixed point 和 source tree 上覆盖 accepted task，且没有 blocking
   finding。
4. 根据 accepted source 和 repository convention 推导 commit message。只有这些来源允许实质不同
   含义时才询问。
5. 创建唯一 recovery ref，并针对精确 target 运行 `scripts/consolidate_task_commit.py`。证明 Task
   Commit 具有 expected sole parent、tree 与 reviewed source 字节完全一致、hooks 成功且 worktree
   干净。

完成要求一个已证明的 Task Commit 或 Already Delivered。

## 执行并验证

对于 Already Delivered，应用所选流程的匹配出口，不创建 Task Commit。否则，只执行所选流程的
final rechecks、mutations、verification、recovery 和 handoff。重新检查 target；对于 Already
Delivered，通过 expected-old-value checks 只删除 workflow-owned recovery refs。严格按授权删除
或保留其他 recovery refs；cleanup failure 保留剩余 refs，并使结果失败。失败时保留所有 owned
state，除非 exact attempted mutation 有已证明的 owned rollback。

返回公共结果，加适用的 checkpoint 与 Task Commit ranges，以及所选结果证明。
