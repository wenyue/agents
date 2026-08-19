# Acceptance Runner

本 reference 负责普通工件 Acceptance 的通用隔离与执行协议。父 Skill 负责 Acceptance 的开始时机
以及谁可以担任 Runner。所选生命周期和语义类型 reference 负责代表性案例与范围专属通过条件。

## 提供隔离输入

像 runtime 一样向 Runner 提供冻结候选工件、触发式任务或政策应用、所选案例输入，以及仅该案例需要
的 context 或工具。不要把 expected result、semantic ledger、diff、author reasoning、finding、
reviewer instruction 和 prior case output 放入 Runner 的上下文。

每个案例都从其声明的冻结输入开始。不要让一个案例的结果成为另一个案例的输入。当 Readiness 要求
Behavior Control 时，在双方都完成后，将其原始结果与匹配的候选运行比较；不要把任何一方的结果
暴露给另一方 Runner。

## 应用工件

在可用时，使用真实公开工作入口或政策应用接缝。通过公开入口运行自有确定性资源。Runner 必须应用
候选工件；学术式解释或 reviewer 走查不属于 Acceptance 证据。

将环境无法运行的受支持执行报告为未测试。受控走查可以说明该表面，但不能替代隔离应用或证明机器
PASS。

每个案例运行一次。仅当结果不确定或不稳定时，最多使用新的隔离 Runner 重复一次；结果分歧即失败。
把观察到的结果和已测试或未测试表面返回给 reviewer，不根据未披露的 expected result 作出判断。
