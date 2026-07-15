# 项目规则

强度：`Default`

适用范围：项目 API、领域约定、生成文件所有权、lint 解释、持久化和生命周期行为的生成契约。

## 生成契约

根据稳定行为证据编写目标规则。记录实现和 review agent 必须保留的约束；删除仅属于常见实践或个人偏好的约定。

## 证据

- 公共 API、route、schema、event 定义、serialization 代码和 compatibility test。
- Framework 配置、已建立的调用点、自定义 lint 和仓库专用 analyzer。
- 生成文件 header、源 schema、generator 配置和所有权文档。
- Domain model、persistence/migration 代码、生命周期所有者和并发边界。
- 已重复使用的命名、术语、本地化和用户可见文本约定。

## 内容

- 记录公共 API、route、event、payload 和兼容性契约。
- 记录项目专用 framework 使用方式，以及 formatter、analyzer 或 lint 输出的项目解释。
- 记录生成文件和外部 schema 的语义所有者、重新生成要求和禁止手改的文件。
- 记录领域术语、命名约束、前缀、identifier 和用户可见文本约定。
- 记录持久化、migration、状态所有权、生命周期、取消和并发规则。
- 只有当前项目证据建立了真实覆盖规则时，才声明对基础规则的例外。

## 边界

- 工具调用、生成命令、runtime 和验证能力放入 `20-project-tools.md`。
- 目录所有权、module 布局和依赖方向放入 `22-project-structure.md`。
- 排除基础规则已覆盖的通用语言风格和无证据的架构建议。
- 不要在本规则和 `20-project-tools.md` 中重复同一生成文件事实：本规则负责语义所有权和编辑边界；工具规则负责如何调用 generator。
