# 停止与恢复

当主 Skill 将 non-complete result 路由到此处时进入。

1. 保留并报告所有 retained batch、target、claim、commit、worktree、branch 和 recovery state，
   以及准确 failed operation 和 next owner。
2. Batch Delivery 前，只使用配置 tracker 所记录的 compare-and-set release，并按逆依赖顺序执行。
   缺少安全 operation 或 compare-and-set failure 时，保留 remaining claims 并停止 release。
3. Batch Delivery 后，保留 unresolved claims 并交接配置的 completion operation。保留 delivered
   commits。
4. 没有单独授权时，不执行 pull、push、pull request、force operation、rebase、rollback、discard
   或未配置的 tracker action。

这个 path 以 `stopped` 或 `failed` 退出；retained state 和 handoff 仍是 recovery boundary。
