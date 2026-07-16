# Dart 与 Flutter 指引

强度：`Default`

适用范围：Dart 语言形态，以及 Flutter 应用的架构、状态、生命周期、UI、路由、模型、导入和分析默认约定。

## 适用性

- 本规则应能在不同 Dart 和 Flutter 应用中复用。
- 本规则中不要写入应用名称、项目模块、自定义 lint 包、项目生成路径或项目专用 API。
- 仓库 API、模块边界、自定义 lint、构建 watcher 和应用专用辅助函数应放在项目规则中。

## 公共接口与归属

- 公共 API 使用显式类型。局部变量的初始化器足够清楚时，让其类型自行推断。
- 公共边界应保持精简并由产品需求决定。不要为测试或便利而公开辅助函数。
- 必需的领域输入放在前面；`BuildContext?`、`WidgetRef?` 或 provider reader 等可选执行上下文放在最后。
- 面向框架的辅助函数，以及具有多个可选输入的函数，优先使用命名参数。
- 默认将所有者内部的行为保留为实例成员。
- 只有类型级行为、静态状态、实例创建前的工作或私有构造支持才使用静态成员。
- 顶层函数只用于框架入口点、文件级声明、共享算法或没有明确所有者的逻辑。
- 用于维护不变量的创建或规范化逻辑，应放在拥有该不变量的值类型上。

```dart
// BAD: `_isValid` exists only for `Parser` but is declared at file scope.
bool _isValid(String value) => value.isNotEmpty;

// GOOD: The helper stays with its owner.
class Parser {
  bool _isValid(String value) => value.isNotEmpty;
}
```

## 数据形态

- 泛型应保持具体。除非边界确有需要，否则不要使用原始泛型类型或 `dynamic`。
- 优先使用不可变值。默认使用 `final`，编译期值使用 `const`。
- record 只用于小型局部元组返回，并且命名类型不能提升清晰度的情况。
- Dart 能够推断时，不要在解构中重复 record 字段类型。

```dart
// BAD: Destructuring repeats the record field types.
final (String title, int count) = readSummary();

// GOOD: The record shape already carries the field types.
final (title, count) = readSummary();
```

## 命名

- 类型使用 `PascalCase`，成员使用 `camelCase`，私有声明使用 `_privateName`，文件使用
  `snake_case.dart`，常量使用 `kName`。
- 布尔值按条件命名，例如 `isReady`、`hasFocus`、`canSubmit` 或 `shouldRetry`。
- 操作按其效果命名：`load`、`save`、`update`、`delete`、`remove` 或 `clear`。
- 销毁归属的持久化数据使用 `delete`。
- 从集合、关系、选择、缓存或视图中取出项目使用 `remove`。
- 清空容器但保留容器本身使用 `clear`。

## 声明顺序

- 每个分区注释都视为一个新的成员排序组。
- 每组内部依次排列：构造函数、公共静态字段、私有静态字段、公共实例字段、私有实例字段、getter、
  setter、公共静态方法、私有静态方法、公共实例方法、私有实例方法。
- 公共声明的修饰符顺序为 `protected`、`override`、无注解、`visibleForTesting`。

```dart
class SearchController {
  SearchController(this.query);

  static const maxResults = 50;
  static final _cache = <String, List<Result>>{};

  final String query;
  var _isLoading = false;

  bool get isLoading => _isLoading;

  static bool isCached(String query) => _cache.containsKey(query);

  Future<List<Result>> search() async => _readResults();

  Future<List<Result>> _readResults() async => _cache[query] ?? const [];
}
```

## 分区注释

- 分区注释只用于文件的顶层区域，或类与成员的分组。
- 不要把分区注释用作声明文档。
- 每条边框必须正好使用 20 个 `/` 字符：`////////////////////`。
- 分区注释与该分区的第一个声明之间留一个空行。

```dart
////////////////////
/// Public actions.
////////////////////

Future<void> refresh() async {
  await repository.refresh();
}
```

## 文档与注释

- 注释用于说明意图、不变量、生命周期、约束和不直观的失败处理。
- 不要复述代码。
- 声明文档和文件头使用 `///`。
- 函数体内，以及行内说明、TODO、FIXME 和 ignore 注释使用 `//`。
- 文字注释以大写字母开头，并以 `.`、`?` 或 `!` 结尾。
- 不超过 16 个字符且不超过三个单词的短行内注释，可以不加结尾标点。
- `TODO(name): ...` 和 `FIXME(name): ...` 必须包含具体动作或问题。
- 阶段注释只用于较长的多步骤函数内部。

```dart
/// Loads the first page and preserves existing content while refreshing.
Future<void> refresh() async {
  // Keep stale content visible until the new page arrives.
  final previous = state.valueOrNull;

  // TODO(owner): Remove the fallback after the migration completes.
  state = await AsyncValue.guard(() => repository.load(previous?.cursor));
}
```

## 状态管理

- 共享状态、跨组件状态和功能级状态使用 Riverpod。
- 如果应用已经使用代码生成，provider 使用 `@riverpod` 和生成代码。
- provider 名称带 `Provider` 后缀。
- build 方法中使用 `ref.watch`，事件处理程序中使用 `ref.read`，副作用使用 `ref.listen`。
- 只关心状态对象的一部分时，将 `select` 与 `ref.watch` 或 `ref.listen` 配合使用。
- 不要将 `ref.read` 与 `select` 组合使用。
- 生命周期不应依赖单个页面的服务和仓库使用 `keepAlive: true`。
- 不需要 provider 身份的简单局部事项，优先使用组件局部状态。

```dart
final title = ref.watch(articleProvider.select((article) => article.title));

button.onPressed = () {
  ref.read(articleProvider.notifier).refresh();
};
```

## Provider 生命周期

- provider 的 `build()` 是响应式的；依赖发生变化时，它可能再次运行。
- 创建可释放资源后，立即注册其 `onDispose` 回调。
- 必须在任何 `await` 之前注册释放逻辑。
- `onDispose` 会在重新构建前运行，并在 provider 完全释放时再次运行。
- 不要在 `onDispose` 中给 `state` 赋值、读取 provider 或访问 `Ref`。

```dart
@riverpod
class FeedSubscription extends _$FeedSubscription {
  @override
  Future<void> build() async {
    final subscription = feedStream.listen(_handleEvent);
    ref.onDispose(subscription.cancel);

    await _loadInitialPage();
  }
}
```

## 异步边界

- 只有在 `await` 之后继续使用受生命周期约束的对象时，才添加 mounted 检查。
- 在组件中，一次 mounted 检查即可覆盖绑定到同一组件生命周期的对象。
- 在 notifier 和 provider 中，`await` 之后给 `state` 赋值、再次读取 provider，或按 provider
  自有状态分支前，应检查 `ref.mounted`。
- 如果异步间隔后仍需使用稳定依赖，应在间隔前解析它们。
- 会变化的 provider 状态应在异步间隔和 mounted 检查之后读取。

```dart
Future<void> save() async {
  final repository = ref.read(settingsRepositoryProvider);

  await repository.saveDraft();
  if (!ref.mounted) {
    return;
  }

  final current = ref.read(settingsProvider);
  state = AsyncData(current.markSaved());
}
```

## 组件

- 简单的展示型 UI 优先使用 `StatelessWidget` 或小型函数。
- 需要管理局部 controller 生命周期时，优先使用 `HookWidget` 和 `HookConsumerWidget`。
- 只有需要 `initState`、`dispose` 或 inherited-widget 集成时，才使用 `StatefulHookWidget`
  或 `StatefulHookConsumerWidget`。
- 优先使用 `const` 构造函数和稳定的子组件。
- 引入应用专用主题扩展前，先使用 `Theme.of(context)`。
- 可复用组件中不要硬编码颜色。

## 路由

- Flutter 导航使用 `go_router`。
- 如果应用已经采用生成路由，优先使用生成的类型化路由。
- 页面使用路由 API。
- 由 Navigator 管理的对话框、底部面板和浮层，使用 `Navigator.of(context).pop(result)`。

## 数据模型

- JSON 边界使用 `json_serializable` 和 `json_annotation`。
- 需要相等性、联合类型或 `copyWith` 的不可变数据模型使用 Freezed。
- 如果存储细节与应用逻辑不同，应将持久化模型与领域模型分开。

## 导入

- 导入顺序为 `dart:`、`package:`、相对导入。
- 跨包或功能边界时，优先使用包导入。
- 在同一包或边界紧密的功能内部，优先使用相对导入。

## 分析

- 代码、标识符和注释使用英语。
- 每行不超过 100 个字符。
- 优先使用清晰命名和直接控制流，不要使用炫技式简写。
- 精确类型或提前返回能够解决问题时，避免使用 `dynamic`、类型转换和可空逃生口。
- 默认使用单引号。
- 多行字面量、参数列表和实参列表使用尾随逗号。
- 所有控制流主体都使用花括号；不要把主体与条件写在同一行。
- 文档注释中类似代码的 placeholder 使用反引号包裹。
- 不要使用 `print`；使用应用的日志机制。
- 不要使用已弃用的 API。
- 当前时间会影响行为时，使用可注入或可测试的时间源。

```dart
// BAD: The branch body is hidden on the same line.
if (isReady) submit();

// GOOD: Control flow keeps a stable block shape.
if (isReady) {
  submit();
}
```
