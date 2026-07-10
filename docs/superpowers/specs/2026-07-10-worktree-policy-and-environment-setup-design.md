# Worktree 技能分工与安全集成设计

## 背景

当前公共 `Git And Worktree` 规则混合了策略、触发条件和执行步骤；公共
`project-development-workflow` 生成契约又同时承担 worktree 选择、创建、环境准备、
验证、审查、合回和清理。这些职责与 Superpowers 已有的 `using-git-worktrees` 和
`finishing-a-development-branch` 部分重叠，并导致项目环境事实与通用 Git 生命周期耦合。

本次调整只修改 `wenyue/agents` 公共仓库。目标项目通过后续
`setup-project-agents` 刷新获得新规则和项目本地技能；本次不直接修改任何目标项目或
Superpowers 技能。

## 目标架构

Worktree 开发生命周期拆分为三个技能和一层薄策略：

| 阶段 | 责任所有者 |
| --- | --- |
| 是否隔离、授权、检测和创建 | `superpowers:using-git-worktrees` |
| 目标项目环境准备 | `worktree-environment-setup` |
| 默认返回待审修改、按需自动合回 | `worktree-integrate` |
| 技能路由和不可违反的 Git 政策 | `03-global-skill-config.md` |

该分工不重新定义 worktree 使用时机。`using-git-worktrees` 继续根据自身触发条件、用户
偏好、当前隔离状态和平台能力决定是否询问、复用或创建 worktree。

## 全局策略层

`03-global-skill-config.md` 的 `Git And Worktree` 只保留以下内容：

- Worktree 选择、授权、现有隔离检测、目录选择和创建机制交给
  `superpowers:using-git-worktrees`；公共规则不重复定义触发条件。
- 当目标项目提供 `worktree-environment-setup` 时，使用它替代
  `using-git-worktrees` Step 2 的通用依赖自动检测；没有项目技能时才使用通用 setup。
- `using-git-worktrees` Step 3 的 clean-baseline 测试保持有效。它验证代码初始状态，
  不等同于环境技能的生成期验收。
- Worktree 任务完成后默认使用 `worktree-integrate` 的 `review` 模式，把业务修改作为
  current/base branch 的 unstaged changes 返回；只有用户明确要求自动合回时才使用
  `commit` 模式。
- `review` 和 `commit` 都先把 worktree 业务修改整理为一个恢复用提交；为创建 worktree
  而在基线分支产生的 `.gitignore` 等基础设施提交不属于业务提交，不参与压缩。
- 用户选择 PR、保留分支或丢弃工作时，不使用 `worktree-integrate`，继续使用
  `finishing-a-development-branch` 的相应路径。
- 不得覆盖、自动 stash、reset、clean 或丢弃用户改动。
- Push、PR、远程分支修改和强制操作始终需要用户明确授权。

公共规则只表达路由与约束，不保存完整命令序列，避免再次演变为内嵌工作流。

## Using Git Worktrees 集成

`using-git-worktrees` 是 worktree 启动阶段的唯一所有者：

- 检测当前是否已在 linked worktree，并防止嵌套创建。
- 区分 submodule、普通 checkout、命名分支和 detached HEAD。
- 在没有既定用户偏好时请求同意。
- 优先使用平台原生 worktree 工具，仅在没有原生能力时使用 Git fallback。
- 按其既有规则选择目录并处理项目内 `.worktrees/` 的 ignore 要求。
- Worktree 创建完成后，把环境阶段交给项目的 `worktree-environment-setup`。
- 环境准备完成后，继续执行其 clean-baseline 测试；失败时按该技能要求请求用户决定。

如果 Git fallback 需要在 current/base branch 提交 `.gitignore`，该提交是允许的独立
基础设施提交。任务分支应从包含该提交的新基线创建，后续“单提交”只统计
`base..task` 范围内的业务提交。

## Worktree Environment Setup

### 名称与调用边界

- 删除公共 `project-development-workflow` 占位契约，并新增
  `worktree-environment-setup`。目标项目刷新时同样删除旧技能后重新生成，不迁移旧内容。
- 该技能只在调用时已经位于现成 Git worktree 内运行。它可以验证当前位置，但不得
  决定是否使用 worktree，也不得创建 worktree 或分支。
- 项目专用技能继续由 `setup-project-agents` 根据目标仓库事实生成和刷新。

### 允许职责

环境技能只负责让当前 worktree 具备项目开发所需环境：

- 安装或恢复项目声明的依赖。
- 准备 linter、checker、formatter、编译器和代码生成器等开发工具。
- 生成导入、运行或测试收集所必需的 proto、代码或其他资产。
- 准备确实必需的环境变量、本地数据和本地服务。
- 检查每条环境准备命令自身的退出状态，并报告缺失依赖、凭据、服务或生成资产。

环境事实必须来自目标项目的 `.agents/rules/20-project-tools.md`、包清单、脚本、CI 配置
和其他仓库证据，不得从公共占位契约猜测具体命令。

### 禁止职责

环境技能不得：

- 修改业务代码或实现用户任务。
- 创建、切换、提交、rebase、merge、push、清理分支或 worktree。
- 执行代码审查、提交压缩、clean-baseline 测试、合回后验证或完整任务验收。
- 安装或同步 agent 配置、生成平台 wrapper 或更新公共资产。
- 在日常调用中创建额外 worktree 对自身进行验收。

## Worktree Integrate

新增公共 `worktree-integrate` 技能，负责把已完成且已验证的命名分支 worktree 集成回
current/base branch。它不判断是否使用 worktree，不准备项目环境，也不处理 PR、保留或
丢弃工作。

该技能提供两个互斥模式：

| 模式 | 触发 | 结果 |
| --- | --- | --- |
| `review` | 默认 | Current branch HEAD 不变，业务修改作为 unstaged changes 返回 |
| `commit` | 用户明确要求自动合回 | Current branch 通过 `merge --ff-only` 获得一个业务提交 |

### 前置条件

- 当前目录必须是 linked worktree 且处于命名任务分支；detached HEAD 不允许本地集成。
- 任务要求的验证必须已经通过；失败时停止，不整理提交或集成。
- 从 `git worktree list --porcelain` 和 Git common directory 定位原工作区及其当前基线
  分支。存在多个无法判定的候选原工作区时请求用户指定，不猜测 `main` 或 `master`。
- 记录原工作区的 HEAD、index、staged、unstaged 和 untracked 状态。用户明确授权前，
  不得改变 current branch 历史。

### 单业务提交

- Worktree 中允许在开发期间产生多个中间提交。
- 以任务分支与当前基线的 merge-base 为业务修改起点，把任务分支中的全部业务提交和
  已确认属于本任务的未提交修改整理为一个恢复用业务提交。
- 压缩只改写任务分支，不改写基线分支、`.gitignore` 基础设施提交或用户已有提交。
- 最终提交信息遵循目标项目约定；用户已指定提交信息时优先使用用户内容。
- 整理完成后必须验证任务分支相对当前基线恰好领先一个业务提交。

### Rebase 与冲突

- 在任务 worktree 干净且只有一个业务提交后，把任务分支 rebase 到 current branch
  当前本地基线。
- 冲突仅在双方意图明确、冲突文件属于本任务范围且结果可以验证时由代理解决。
- 解决后运行与冲突区域相关的检查，再执行 `rebase --continue`。
- 语义不清、涉及用户未提交改动、涉及范围外文件或无法可靠验证时执行
  `rebase --abort`，保留任务分支并请求用户决定。
- 禁止丢弃任一方修改、强制 rebase、强制 push 或改写基线历史。

### Review 模式

`review` 是默认模式，目标是在不改变 current branch HEAD 和既有 index 的前提下，把
worktree 业务修改作为 unstaged changes 返回。

1. Rebase 后再次确认任务分支相对 current branch 只有一个业务提交；若 current branch
   再次前进，先重新 rebase。
2. 为任务涉及的 current branch 文件建立临时恢复副本，并记录 index 内容摘要；备份不
   写入仓库，不使用 stash。
3. 对 current branch 未修改的任务路径，直接把任务最终内容恢复到 working tree，保持
   index 不变。
4. 对双方都修改的文本文件，使用业务提交父树作为 base、current working file 作为
   current、任务最终文件作为 task 执行三方合并。
5. 同文件修改位于不同代码块、可以同时成立，或能由明确测试和项目约束证明正确时，
   代理自行完成合并；路径重叠本身不是停止条件。
6. 删除与修改、复杂重命名、二进制内容、互斥行为或无法证明双方修改均被保留时，停止
   并请求用户决定。生成文件优先从合并后的源文件重新生成，不手工拼接。
7. 集成完成后确认 current branch HEAD 和原 index 完全不变；用户原有 staged changes
   保持 staged，返回的任务修改全部表现为 unstaged 或 untracked。
8. 运行与组合结果相关的 formatter check、linter、checker 和测试；失败时保留当前修改
   与准确错误，不声明集成完成。
9. 即使验证通过，也保留任务分支和 worktree 作为恢复来源。只有用户确认 review 完成
   或明确要求清理后，才能按所有权规则移除 worktree 并删除任务分支。

任何自动合并都必须同时满足高置信度和可验证性。若尝试失败，使用临时恢复副本把代理
触及的路径还原到操作前状态，并确认 HEAD、index 和用户修改均未丢失。

### Commit 模式

`commit` 仅在用户明确要求自动提交并合回时使用：

1. Rebase 后再次确认任务分支相对基线只有一个业务提交。
2. 返回原工作区并确认其仍处于检测到的基线分支。
3. 若基线再次前进，返回任务 worktree 重新 rebase；不得创建 merge commit。
4. 检查 current branch 用户修改。任务路径不存在本地修改时继续；任务路径存在 staged、
   unstaged 或 untracked 修改时，不临时清除、stash 或混入业务提交，而是自动降级到
   `review` 模式，让高置信度三方合并在不改变历史的路径中处理。
5. 仅使用 `git merge --ff-only <task-branch>` 合回。
6. 在原工作区运行目标项目要求的权威验证。
7. 验证失败时保留任务分支和 worktree，报告准确失败命令和原因。
8. 验证成功后按 worktree 所有权清理：平台/宿主创建的 worktree 交给原生退出或清理
   机制；Git fallback 创建的 worktree 从原工作区移除，再安全删除已合回任务分支。

该技能不得调用普通 `git merge`、产生 merge commit、自动 pull、push、创建 PR 或强制
删除未合回内容。

### 与 Finishing a Development Branch 的关系

- 默认本地人工复审或明确自动合回时，使用 `worktree-integrate`，不再执行
  `finishing-a-development-branch` 的四选一菜单和普通 merge 路径。
- 用户要求 PR、保留分支或丢弃工作时，不使用 `worktree-integrate`，改用
  `finishing-a-development-branch` 对应路径及确认机制。
- 这样两个技能按结果类型互斥，不在同一次完成流程中重复执行。

## 环境技能生成期验收

### 触发条件

`setup-project-agents` 创建或实质修改目标项目的
`worktree-environment-setup` 后，必须执行一次真实验收。候选技能内容未变化时，不重复
验收。

### 验收流程

1. 由 `setup-project-agents` 在环境技能之外创建临时真实 worktree。
2. 让验收 worktree 使用与原工作区候选技能及其相关项目工具规则完全一致的内容；候选
   文件尚未提交时，不得误用 HEAD 中的旧版本。复制或生成后校验内容一致性。
3. 从验收 worktree 内调用候选 `worktree-environment-setup`。
4. 验证依赖安装、必要 proto/代码生成、必需服务和环境准备命令能够完成。
5. 使用目标项目真实配置执行 linter、checker、formatter 等工具的功能性非写入检查。
   仅执行 `--version` 不算通过；formatter 必须使用 `--check`、`--dry-run` 或等价模式。
6. 若工具没有可靠的局部检查模式，允许运行项目规定的全量只读检查命令。
7. 确认环境技能没有执行业务修改或 Git/worktree 生命周期操作。
8. 验收通过后接受候选技能并清理临时 worktree；失败时记录原始命令和阻塞原因，候选
   技能不得标记为已验收。

### 日常调用

正常 worktree 开发只在当前既有 worktree 中调用环境技能准备环境，不创建嵌套验收
worktree，也不重复生成期的工具功能验收。环境命令失败时仍应立即报告并停止，这是
运行时错误处理，不是重新验收技能。`using-git-worktrees` 随后执行的 clean-baseline
测试也不是环境技能验收。

## 旧技能删除与重建

`setup-project-agents` 刷新已有目标项目时不迁移旧技能内容：

1. 直接删除目标项目的 `.agents/skills/project-development-workflow/`；不读取、复制或
   提取其中的命令和规则。
2. 完全根据目标项目当前的 `.agents/rules/20-project-tools.md`、包清单、脚本、CI 配置
   和其他仓库证据，重新生成 `.agents/skills/worktree-environment-setup/`。
3. 审查候选内容，并按生成期验收流程创建真实 worktree 验证新技能。
4. 验收失败时保留未验收的新候选和准确阻塞信息，不恢复旧技能，也不得把候选描述为
   可用。

`worktree-integrate` 是独立新增的公共通用技能，不读取旧项目技能内容。

## 公共仓库调整范围

- 将 `.agents/rules/03-global-skill-config.md` 的 `Git And Worktree` 重写为薄路由和强制
  政策。
- 删除 `.agents/skills/project-development-workflow/`，新增
  `.agents/skills/worktree-environment-setup/` 生成契约。
- 新增 `.agents/skills/worktree-integrate/` 公共技能，并加入公共技能清单。
- 更新 `setup-project-agents` 的旧技能删除、全量重新生成与生成期验收要求。
- 更新 README、`20/21/22` 项目占位契约中旧职责和旧名称的引用。
- 更新同步脚本和契约测试，覆盖新公共技能同步、旧技能直接删除、全量重新生成、生成期
  验收边界和旧引用清理。

实现时整体重写相关职责段落并删除失效内容，避免通过追加例外形成相互矛盾的规则；
该编辑偏好不写入公共代理规则。

## 验收标准

- `Git And Worktree` 不再自行定义 worktree 触发时机或复制创建步骤。
- 公共技能清单能够同步 `worktree-integrate`，其职责不包含创建、环境准备、PR 或丢弃。
- `review` 是默认模式，current branch HEAD 和 index 保持不变，返回修改全部为 unstaged
  或 untracked，并保留任务分支和 worktree 供人工复审与恢复。
- `commit` 仅在用户明确要求时使用，并只合回一个业务提交；基线上的 `.gitignore`
  基础设施提交可以独立存在。
- `review` 模式下的同文件修改在高置信度且可验证时自动三方合并；无法证明双方修改
  完整保留时停止询问。`commit` 模式遇到任务路径本地修改时自动降级为 `review`。
- 环境技能生成契约不包含 worktree 创建、Git 合回、clean-baseline 或日常自验收职责。
- `setup-project-agents` 明确区分生成期验收和日常调用，并确保验收使用未提交候选技能
  而不是 HEAD 中的旧版本。
- 旧技能内容不会被读取或迁移；旧名称只出现在删除说明和删除行为测试中。
- 公共同步、契约、Markdown 和 JSON 引用检查全部通过。
