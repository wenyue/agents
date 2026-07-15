# C++ 指南

强度：`Default`

适用范围：C++ 代码风格、文档、命名和安全默认规则。

## 核心默认值

代码和文档使用英文。显式类型。公共 API 使用 Doxygen。遵守 ODR。

## 命名

class 使用 PascalCase；变量/函数使用 camelCase；常量/macro 使用 ALL_CAPS；文件使用 snake_case。

不要使用魔法数字。函数以动词开头。Boolean 使用 `isX`、`hasX` 或 `canX`。

## 函数

- 保持单一职责，通常不超过 20 行。使用 early return 减少嵌套。

```cpp
// ❌ 不好：深层嵌套、参数过多
void process(int x, bool flag, bool verbose, int mode) {
  if (flag) {
    if (verbose) {
      /* ... */
    }
  }
}

// ✅ 良好：扁平控制流、结构化参数
struct ProcessOpts { bool flag; bool verbose; int mode; };

void process(int x, const ProcessOpts& opts) {
  if (!opts.flag) { return; }
  if (!opts.verbose) { return; }
  /* ... */
}
```

## 数据与 Class

- 不变化的值使用 `const`，编译期常量使用 `constexpr`，nullable 值使用 `std::optional`。
- 遵循 SOLID，优先组合而不是继承。class 保持在约 200 行以内。
- 遵循 Rule of Five / Rule of Zero。拥有资源时使用 smart pointer，不使用 raw pointer。所有资源都使用 RAII。

## 错误

- 真正意外的错误使用 exception；预期失败使用 `std::optional`、`std::expected` 或 error code。

## 测试

使用 Arrange-Act-Assert。每个公共函数至少一个单元测试；每个模块边界包含集成测试。

## STL 与并发

- 优先使用标准容器和类型：`std::string`、`std::vector`、`std::map`、`std::optional`、`std::variant`、`std::filesystem`、`std::chrono`。始终优先使用 `std::vector` 而不是 C 风格数组。
- 并发使用 `std::thread`、`std::mutex`、`std::lock_guard`；无锁共享状态使用 `std::atomic`。
