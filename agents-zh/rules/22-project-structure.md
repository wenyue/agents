# 项目结构

强度：`Advisory`

适用范围：仓库布局、module 所有权、依赖方向、共享位置和配置所有权的生成契约。

## 生成契约

根据观察到的仓库结构和强制依赖边界编写目标规则。保持结构图有选择性：记录能指导放置或避免无效
依赖的位置和关系，而不是逐目录清单。

## 证据

- 仓库和 workspace tree、package manifest、module 声明和 import graph。
- Feature 目录、共享 library、配置所有者、测试、资产、生成源码、脚本、基础设施和文档位置。
- Dependency check、lint rule、build target、package 边界和代表性 import。
- 能建立稳定边界的 ownership file 和重复放置模式。

## 内容

- 记录顶层区域及各自负责的职责。
- 记录 feature 和 module 布局、放置约定和共享位置。
- 记录允许和禁止的依赖方向，以及这些边界保护的内容。
- 当相关区域存在时，记录 UI、backend、domain、data、infrastructure、test、asset、generated
  source、configuration、script 和 documentation 之间的所有权。
- 记录真实 enforcement mechanism，但将其准确调用方式保留在 `20-project-tools.md`。

## 边界

- 工具、runtime、build、test 和 verification 命令保留在 `20-project-tools.md`。
- API 契约、payload、领域词汇、生成文件编辑政策和 lint 解释保留在
  `21-project-rules.md`。
- 排除通用架构建议、推测性未来布局，以及名称已自解释且不构成放置或依赖约束的目录。
- 不要在多个 section 或 Rule 中重复同一所有权声明。
