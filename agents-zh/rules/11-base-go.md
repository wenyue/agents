# Go 基础约定

强度：`Default`

适用范围：本仓库 Go 代码的一般约定。

## 风格目标

- 追求紧凑、成熟、易读的 Go：直接表达意图，缩小作用域，避免重复分支；只有当 helper 命名了真实概念或消除了有意义的复杂度时才拆分。
- 不要为了压缩代码而对抗 linter。保留 `wsl_v5`、`nlreturn` 和 `whitespace` 要求的空行；可读性意味着清晰的代码块，而不是密集代码墙。
- 对无效输入、取消和错误路径使用 early return，使成功主路径浅且易浏览。
- 公共 API 应由产品需求驱动。不要只为测试或推测性复用导出名称、添加 interface 或 seam。

## 格式化

- 使用 `golangci-lint-v2 fmt` 格式化；不要手动调整 import 分组或换行来对抗 `gci`、`gofmt`、`gofumpt`、`goimports` 或 `golines`。
- 行宽控制在 `100` 字符以内，让 `golines` 处理长调用和字符串连接。
- Import 分组依次为标准库、第三方、本地 module；组间空一行并由 formatter 排序。

## 结构

- 函数不超过 `funlen` 限制（`80` 行 / `50` 条 statement），并满足复杂度限制（`cyclop` `16`、`gocyclo` `20`、`nestif` `8`）。
- 当 helper 能扁平化控制流、消除重复或命名领域步骤时进行抽取。只会遮蔽直接代码的一次性微型 helper 应内联。
- 当小型本地 struct 或 private helper type 能澄清数据流时使用它们。不要为单个调用点增加宽泛 package 抽象。
- 不要添加 `init()`。从 constructor、`main` 或 package 自有 setup 函数显式初始化。

## 命名

- 导出标识符使用 `PascalCase`；未导出标识符使用 `camelCase`。
- 缩写保持一致：`ID`、`CID`、`IPFS`、`IPNS`、`DHT`、`URL`、`UDP`、`TCP`。
- Sentinel error 使用 `ErrX`；错误类型以 `Error` 结尾。
- 短名称只用于很小作用域或 lint allow list（`err`、`ok`、`id`、`i`、`j`、`k`、`v`、`db`、`to`）。作用域较大的值应说明其角色。
- Boolean 名称尽量读作 predicate，例如 `ok`、`enabled`、`hasRoute`、`shouldRetry`。

## 错误

- 检查所有返回错误，包括 blank assignment 和 type assertion。
- 跨 package 边界的错误使用有意义的上下文和 `%w` 包装；使用 `errors.Is` / `errors.As` 检查。
- 创建新的动态错误前优先复用现有 sentinel error。
- Type assertion 使用 comma-ok 形式，生产代码不要使用裸 `x.(T)`。
- 除了无法继续的顶层启动路径，避免 `panic`、`logger.Fatal` 和 `os.Exit`。

## 注释

- 注释用于意图、不变量、并发、重试行为、安全权衡或不直观的领域规则，不要复述下一条 statement。
- 导出声明需要以标识符开头并以标点结束的 doc comment。
- 长多步骤函数可以用简短阶段注释改善浏览路径。
- 注释使用英文、首字母大写并带标点，以满足 `godot`、`revive` 和 `misspell`。
- 仅使用带具体后续动作的 `TODO(name): ...` / `FIXME(name): ...`。
- 所有 `//nolint:<linter>` 都必须包含具体原因。优先修改代码以满足 lint。

## 并发与 Context

- 在标准 Go 模式适用时，将 `context.Context` 作为第一个参数传递，并在 loop 或长任务中响应取消。
- 避免在 loop 或 closure 内创建嵌套 context，除非代码说明其生命周期正确。
- 使用所属 package 的同步原语保护共享可变状态。Package global 应有明确目的、保持稳定并在单一位置初始化。

## 数据与集合

- 固定值优先使用 `const`，可调数字使用命名常量。控制流中避免魔法数字。
- 当大小已知或容易获得时，预分配 slice 和 map。
- 使用 `map[T]struct{}` 或小型 helper 去重，并明确顺序与唯一性。
- Struct tag 保持一致，让 `tagalign` 和 `tagliatelle` 决定格式与命名。

## 日志

- 遵循所属 package 的 logger 约定。运行时输出不要引入 `fmt.Print*` 或标准 `log` package。
- 日志消息应说明操作，并包含诊断失败所需的值。带值消息优先使用格式化 logger 方法。
