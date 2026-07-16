# C++ 指南

强度：`Default`

适用范围：C++ 语言、命名、函数形状、数据所有权、错误、测试、标准库使用和并发默认值。

## 语言与文档

- 代码和文档使用英文。
- 使用显式类型并遵守 One Definition Rule。
- 公共 API 使用 Doxygen 文档。

## 命名

- Class 使用 `PascalCase`，变量和函数使用 `camelCase`，常量和 macro 使用 `ALL_CAPS`，
  文件使用 `snake_case`。
- 函数名以动词开头。
- Boolean 使用 `isX`、`hasX` 或 `canX` 等 predicate 命名。
- 使用命名常量，不使用魔法数字。

## 函数

- 每个函数聚焦一个目的，通常不超过 20 行。
- 使用 early return 使主路径保持扁平。
- 使用结构化 options 类型替换 flag 或 mode 参数集群。

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

## 数据与 Class

- 不变化的值使用 `const`，编译期常量使用 `constexpr`。
- Nullable 值使用 `std::optional`。
- 遵循 SOLID 原则，优先组合而不是继承。
- Class 保持在约 200 行以内。

## 资源安全

- 根据所有权需要遵循 Rule of Zero 或 Rule of Five。
- 优先使用 smart pointer，不使用拥有资源的 raw pointer。
- 每种资源都使用 RAII。

## 错误

- 真正意外的失败使用 exception。
- 预期失败使用 `std::optional`、`std::expected` 或 error code。

## 测试

- 测试使用 Arrange、Act、Assert 结构。
- 每个公共函数添加一个单元测试。
- 在模块边界添加集成测试。

## 标准库与并发

- 优先使用标准类型和容器，包括 `std::string`、`std::vector`、`std::map`、
  `std::optional`、`std::variant`、`std::filesystem` 和 `std::chrono`。
- 优先使用 `std::vector`，不使用 C 风格数组。
- 并发使用 `std::thread`、`std::mutex` 和 `std::lock_guard`。
- 无锁共享状态使用 `std::atomic`。
