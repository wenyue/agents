# Pruning Agent

本 reference 负责 Pruning Agent 的 packet、任务、verdict 和 closure check。父 Skill 负责该关卡的
运行时机、角色隔离、finding 分类处理、修正及后续出口。

## 提供有界 packet

向 Agent 提供：

- 已接受结果和语义账本；
- 完整候选工件、自有资源以及加载或分发表面；
- 治理证据和适用 reference；以及
- 存在前一版本时的基线行数、词数和字节数。

排除前一版本、diff、作者推理、怀疑的缺陷、预期编辑和预期 verdict。

## 检验保持语义的缩减

查找陈旧或重复的含义、无必要缓存的环境事实、位置错误的分支专属材料，以及可以删除或压缩的措辞
或结构。质疑以下显式指令：只是重述已有证据支持的 Agent 或宿主默认行为、重复可靠加载的上层
owner，或者可由 trigger、input、step 或相邻上下文唯一推出。

仅当删除一项指令不会改变任何代表性动作、选择、权限、安全边界以及 completion、stop 或 failure
出口时，才将其视为可删除。声称某项行为是默认行为时，必须有宿主治理证据或适用的 Behavior
Control 支持。

## 返回并关闭

返回 `PASS` 或 `FAIL`。`PASS` 表示不存在有依据且保持语义的进一步缩减；它不要求工件尺寸必须
变小。每个 `FAIL` finding 都要指出证据、候选位置、建议缩减、不变的行为、保留的义务，以及一种
共享 finding 分类。

经过一次获授权的 Pruning Pass 后，使用修订后的候选工件和 finding 执行一次 closure check。
Closure `PASS` 确认不存在有依据的进一步缩减。Closure `FAIL` 指出剩余缩减并停止，不提出下一轮
pass。除非活动 owner 要求，否则不要创建持久 pruning 报告。
