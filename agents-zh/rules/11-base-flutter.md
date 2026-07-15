# Dart 与 Flutter 品味

强度：`Default`

适用范围：与具体项目无关的 Dart 和 Flutter 应用默认规则。

## 边界

- 本规则只保留可复用于不同 Dart/Flutter 应用的内容。
- 不要加入应用名称、项目 module、自定义 lint package 名称、生成项目路径或项目专用 API。
- 仓库 API、module 边界、自定义 lint、build watcher 和应用专用 helper 放入项目规则。

## Dart 结构

### 公共表面

- 显式声明公共 API 类型；当 initializer 清楚时，让局部变量推断类型。
- 公共边界应窄且由产品需求驱动，不要为测试或便利公开 helper。
- 必需领域输入放在前面；可选执行 context（如 `BuildContext?`、`WidgetRef?` 或 provider reader）放在最后。
- 面向框架的 helper，以及具有多个可选输入的函数，优先使用命名参数。

### 所有权与成员

- Owner-local 行为默认使用 instance member。
- Static member 只用于类型级行为、static state、实例创建前的工作或 private construction support。
- 顶层函数只用于框架入口、文件级声明、共享算法或没有明确所有者的逻辑。
- 保持不变量的创建或规范化逻辑应放在拥有该不变量的 value type 上。

```dart
// 不好：`_isValid` 只服务于 `Parser`。
bool _isValid(String value) => value.isNotEmpty;

// 良好：helper 保留在其所有者内。
class Parser {
  bool _isValid(String value) => value.isNotEmpty;
}
```

### 数据形状

- Generic 使用具体类型。除非边界要求，否则不要使用 raw generic type 或 `dynamic`。
- 优先不可变值。默认使用 `final`；编译期值使用 `const`。
- Record 只用于局部小型 tuple return，且命名类型不会增加清晰度的情况。
- Record 解构时不要重复 Dart 可以推断的 field type。

```dart
// 不好：解构重复 record field type。
final (String title, int count) = readSummary();

// 良好：record 形状已携带 field type。
final (title, count) = readSummary();
```

### 局部风格

- 代码、标识符和注释使用英文。行宽不超过 100 字符。
- 优先清晰名称和直接控制流，不使用花哨缩写。
- 当精确类型或 early return 可行时，避免 `dynamic`、cast 和 nullable escape hatch。

## 命名

- Type 使用 `PascalCase`，member 使用 `camelCase`，private 声明使用 `_privateName`，文件使用 `snake_case.dart`，常量使用 `kName`。
- Boolean 名称描述条件：`isReady`、`hasFocus`、`canSubmit`、`shouldRetry`。
- 操作按效果命名：`load`、`save`、`update`、`delete`、`remove`、`clear`。
- 销毁自有持久数据使用 `delete`。
- 从 collection、relationship、selection、cache 或 view 中移除项目使用 `remove`。
- 清空容器但保留容器本身使用 `clear`。

## 声明顺序

- 每个 section comment 都开始一个新的 member 排序组。
- 每组内部顺序为：constructor、public static field、private static field、public instance field、private instance field、getter、setter、public static method、private static method、public instance method、private instance method。
- Public 声明 modifier 顺序为 `protected`、`override`、无 annotation、`visibleForTesting`。

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

## Section Comment

- Section comment 只用于顶层文件区域或 class/member 分组。
- 不要把 section comment 当作声明文档。
- 每条边界线必须正好包含 20 个 `/`：`////////////////////`。
- Section comment 后与第一个声明之间保留一个空行。

```dart
////////////////////
/// Public actions.
////////////////////

Future<void> refresh() async {
  await repository.refresh();
}
```

## 文档与注释

- 注释用于意图、不变量、生命周期、约束和不直观的失败处理。
- 不要复述代码。
- 声明文档和文件头使用 `///`。
- 函数体内注释、inline note、TODO、FIXME 和 ignore comment 使用 `//`。
- Prose comment 以大写字母开头，并以 `.`、`?` 或 `!` 结尾。
- 不超过 16 个字符且不超过 3 个词的短 inline comment 可例外。
- 使用带有具体动作或问题的 `TODO(name): ...` 与 `FIXME(name): ...`。
- Phase comment 只用于长多步骤函数。

```dart
/// Loads the first page and preserves any existing page while refreshing.
Future<void> refresh() async {
  // Keep stale content visible until the new page arrives.
  final previous = state.valueOrNull;

  // TODO(owner): Remove fallback after the migration completes.
  state = await AsyncValue.guard(() => repository.load(previous?.cursor));
}
```

## 状态管理

- 共享、跨 widget 或 feature 级状态使用 Riverpod。
- 当应用已经使用生成 provider 时，使用带 `@riverpod` 的生成 provider。
- Provider 名称使用 `Provider` 后缀。
- Build method 使用 `ref.watch`，event handler 使用 `ref.read`，副作用使用 `ref.listen`。
- 只关心状态对象的一部分时，将 `select` 与 `ref.watch` 或 `ref.listen` 配合使用。
- 不要将 `ref.read` 与 `select` 组合。
- 生命周期不应依赖单个 screen 的 service 和 repository 使用 `keepAlive: true`。
- 不需要 provider identity 的简单局部关注点优先使用 widget-local state。

```dart
final title = ref.watch(articleProvider.select((article) => article.title));

button.onPressed = () {
  ref.read(articleProvider.notifier).refresh();
};
```

## Provider 生命周期

- 将 provider `build()` 视为 reactive method；依赖变化时它可能重新运行。
- 创建 disposable resource 后立即注册所有 `onDispose` callback。
- 在任何 `await` 之前注册 dispose。
- 预期 `onDispose` 在 rebuild 前运行，并在 provider 最终销毁时再次运行。
- 不要在 `onDispose` 中赋值 `state`、读取 provider 或访问 `Ref`。

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

- 只有在 `await` 后使用生命周期绑定对象时才添加 mounted check。
- Widget 中，一个 mounted check 可以覆盖绑定到同一 widget 生命周期的对象。
- Notifier 和 provider 中，在 `await` 后赋值 `state`、再次读取 provider 或按 provider 自有状态分支前检查 `ref.mounted`。
- 如果异步间隔后仍需要稳定依赖，在间隔前解析它们。
- 会变化的 provider state 应在异步间隔后、mounted check 之后读取。

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

## Widget

- 简单展示 UI 优先使用 `StatelessWidget` 或小函数。
- 需要局部 controller 生命周期时优先使用 `HookWidget` 和 `HookConsumerWidget`。
- 只有需要 `initState`、`dispose` 或 inherited-widget 集成时才使用 `StatefulHookWidget` 或 `StatefulHookConsumerWidget`。
- 优先 `const` constructor 和稳定 child widget。
- 引入应用专用 theme extension 前先使用 `Theme.of(context)`。
- 可复用 widget 不要硬编码颜色。

## 路由

- Flutter 导航使用 `go_router`。
- 应用已使用生成 route 时，优先带 code generation 的 typed route。
- Page 使用 router API。
- 由 Navigator 拥有的 dialog、sheet 和 overlay 使用 `Navigator.of(context).pop(result)`。

## 数据模型

- JSON 边界使用 `json_serializable` 和 `json_annotation`。
- 需要 equality、union 或 `copyWith` 的不可变数据模型使用 Freezed。
- 当存储细节与应用逻辑不同时，将 persistence model 与 domain model 分离。
- Record 只用于命名类型不会增加清晰度的局部小型 tuple return。

## Import

- Import 顺序为 `dart:`、`package:`、relative import。
- 跨 package 或 feature 边界优先 package import。
- 同一 package 或紧密 feature 边界内优先 relative import。

## 分析默认值

- 默认使用单引号。
- Multiline literal、parameter list 和 argument list 使用 trailing comma。
- Control-flow body 不得与条件放在同一行，始终使用大括号。
- 文档注释中的代码式 placeholder 使用反引号包裹。
- 不使用 `print`，使用应用日志机制。
- 不使用 deprecated API。
- 当当前时间影响行为时，使用可注入或可测试的时间源。

```dart
// 不好：分支 body 隐藏在同一行。
if (isReady) submit();

// 良好：控制流保持稳定的 block 形状。
if (isReady) {
  submit();
}
```
