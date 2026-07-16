# C++ 指引

强度：`Default`

适用范围：C++ 的语言、命名、函数形态、数据归属、错误、测试、标准库用法和并发默认约定。

## 语言与文档

- 代码和文档使用英语。
- 使用显式类型，并遵守单一定义规则。
- 公共 API 使用 Doxygen 文档。

## 命名

- 类使用 `PascalCase`，变量和函数使用 `camelCase`，常量和宏使用 `ALL_CAPS`，文件使用
  `snake_case`。
- 函数名称以动词开头。
- 布尔值使用 `isX`、`hasX` 或 `canX` 等谓词形式命名。
- 使用命名常量，不要使用魔法数字。

## 函数

- 每个函数只负责一个目的，通常不超过 20 行。
- 使用提前返回，让主路径保持平直。
- 将成组的标志或模式参数替换为结构化选项类型。

```cpp
// BAD: Deep nesting and several flag parameters obscure the operation.
void process(int x, bool flag, bool verbose, int mode) {
  if (flag) {
    if (verbose) {
      /* ... */
    }
  }
}

// GOOD: Structured options and early returns keep the main path visible.
struct ProcessOpts {
  bool flag;
  bool verbose;
  int mode;
};

void process(int x, const ProcessOpts& opts) {
  if (!opts.flag) {
    return;
  }
  if (!opts.verbose) {
    return;
  }
  /* ... */
}
```

## 数据与类

- 不会变化的值使用 `const`，编译期常量使用 `constexpr`。
- 可空值使用 `std::optional`。
- 遵循 SOLID 原则，优先使用组合而不是继承。
- 类大致控制在 200 行以内。

## 资源安全

- 按归属需要遵循零法则或五法则。
- 优先使用智能指针，不要使用负责所有权的裸指针。
- 所有资源都使用 RAII 管理。

## 错误

- 只有真正意外的失败才使用异常。
- 对预期的失败模式使用 `std::optional`、`std::expected` 或错误码。

## 测试

- 测试按 Arrange、Act、Assert 组织。
- 每个公共函数添加一个单元测试。
- 在模块边界添加集成测试。

## 标准库与并发

- 优先使用标准类型和容器，包括 `std::string`、`std::vector`、`std::map`、
  `std::optional`、`std::variant`、`std::filesystem` 和 `std::chrono`。
- 优先使用 `std::vector`，不要使用 C 风格数组。
- 并发使用 `std::thread`、`std::mutex` 和 `std::lock_guard`。
- 无锁共享状态使用 `std::atomic`。
