# 项目工具

强度：`Mandatory`

适用范围：仓库级工具事实、能力与调用约束、运行时服务和生成资产工具的生成契约。

## 生成契约

根据当前仓库证据编写目标规则。只保留其他 agent 正确调用、限定范围或保护项目工具所需的稳定事实。

## 证据

- Package manifest、lock file、toolchain pin、workspace 配置和 package manager 文件。
- 仓库脚本、task runner、CI workflow、工具配置和命令帮助输出。
- 运行时入口、服务配置、端口、环境模板和 health check。
- Code generation 配置、生成输出和仓库自有 orchestration selector。
- 影响项目工具的 MCP 和原生 agent 平台配置。

## 内容

- 记录 runtime 版本、package manager、workspace 布局和必需 working directory。
- 记录开发、setup、build、generation、format、analysis、lint、test 和 packaging 命令。对每条命令，
  包含前置条件、输入、输出、支持的 scope selection、mutation behavior、safe-fix capability 和
  相对成本。
- 记录运行时服务、端口、环境变量、数据目录、credential 要求、启动依赖和 health check。
- 记录生成入口及其输入输出。生成文件的语义所有权和禁止手改规则保留在
  `21-project-rules.md`。
- 记录生成式项目 Skill 可以调用且无需复制实现的仓库自有 selector。

## 边界

- 环境准备顺序保留在 `.agents/skills/worktree-environment-setup/`；完成变更后的验证保留在
  `.agents/skills/change-set-verification/`。
- 排除验证触发时机、检查顺序、去重、按风险扩大、baseline 对比和结果政策；这些决定由生成后的
  verification Skill 负责。
- API 和领域约定保留在 `21-project-rules.md`，module 和依赖所有权保留在
  `22-project-structure.md`。
- 不要把命令清单变成运行每条命令的指令。
- 不要推断当前证据无法证明的工具、命令、支持范围或成本。
