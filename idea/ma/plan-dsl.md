# Plan DSL 语法

## 概述

Plan DSL 是用于定义执行计划的领域特定语言，采用函数式编程风格，支持嵌套组合。

**顶层结构**：Plan 的最外层默认是一个 `sequence`，不需要显式包裹。

## 语法规范

Plan DSL 采用严格的格式规范，确保代码的一致性和可维护性。所有 Plan 文件必须遵循以下规范。

### 缩进

- 使用 **2 个空格**缩进，不使用 Tab
- 每层嵌套增加 2 个空格

### 数组和对象

- **数组最后一个元素必须有逗号**（trailing comma）
- **对象最后一个元素必须有逗号**（trailing comma）
- 这使得添加新元素时 diff 更清晰，减少版本控制噪音
- **数组作为参数**：当数组作为参数（如 `condition` 的 `then`/`else`）时，不需要显式包裹 `sequence()`

**正确**：
```
sequence([
  task1(),
  task2(),
  task3(),
])
```

**错误**：
```
sequence([
  task1(),
  task2(),
  task3()
])
```

### 函数调用

**单行调用**：参数较少时（≤ 3 个），可以单行：

```
collect_data(source=jira, sprint=23)
```

**多行调用**：参数较多时（> 3 个），每个参数一行，参数名对齐：

```
collect_data(
  source=jira,
  sprint=23,
  time_range=7d,
  filters=["open", "in_progress"]
)
```

### 嵌套结构

嵌套的数组/对象保持一致的缩进：

```
sequence([
  parallel([
    collect_data(source=jira),
    collect_data(source=monitor),
  ]),
  condition(
    check=check_count(),
    then=generate_doc(type=detailed),
    else=generate_doc(type=summary)
  ),
])
```

### 空格规则

- 函数名和左括号之间**无空格**：`sequence(`
- 左括号后**无空格**：`sequence([`
- 右括号前**无空格**：`task3()`
- 逗号后**一个空格**：`source=jira, sprint=23`
- 等号两边**无空格**：`source=jira`
- 冒号后**一个空格**：`check=task_a()`

### 字符串

- **简单值**：不需要引号，如 `jira`、`23`、`true`
- **复杂值**：包含空格或特殊字符时需要引号，如 `"this is a detailed report"`
- 支持双引号和单引号

### 注释

- 使用 `#` 开头的单行注释
- 注释前空一行，与代码保持距离

```
# 收集所有数据源
sequence([
  collect_data(source=jira),
  collect_data(source=monitor),
])
```

注意：此示例用于展示注释和语法规范，实际 Plan 中顶层不需要 `sequence()` 包裹。

### 最大行宽

- 建议每行不超过 **100 字符**
- 超过时自动换行，保持参数对齐

## 数据类型

Plan DSL 采用**字符串优先**的类型系统，不区分数字和字符串。所有值都作为字符串处理。

### 基本类型

**字符串**：所有值都是字符串，引号可选

```
source=jira
sprint=23
timeout=3600
method=deep
```

**复杂字符串**：包含空格或特殊字符时需要引号

```
description="this is a detailed report"
pattern="^error.*"
message='Hello, "world"'
```

**布尔值**：`true` 和 `false` 表示布尔值（引号可选）

```
enabled=true
debug=false
```

**列表**：用方括号表示，元素之间用逗号分隔

```
filters=["open", "in_progress", "done"]
sources=[jira, monitor, gitlab]
```

**对象/字典**：用花括号表示，键值对之间用逗号分隔

```
config={key: value, nested: {key2: value2}}
metadata={name: report, version: 1.0}
```

### 自动类型转换

Plan DSL 不支持自动类型转换。所有数据操作（包括比较、数学运算、布尔判断）都通过 Task 来处理。

**示例**：

比较操作通过 Task：
```
condition(
  check=check_count_gt_100(),
  then=task_a(),
  else=task_b()
)
```

### 设计原则

- **简化解析**：不区分数字和字符串，解析器更简单
- **配置友好**：所有配置项都是字符串，符合 YAML/JSON 等配置文件的习惯
- **引号可选**：简单值不需要引号，复杂值（含空格/特殊字符）需要引号

## 基本语法

### Task 引用

```
task_id()
```

Task 引用调用已定义的 Task，参数通过 Task 的 input 字段传递。

### 原语组合

编排原语可以任意嵌套组合，形成复杂的执行流程。

## 编排原语

### sequence

顺序执行 Task，前一个 Task 完成后执行下一个。后续任务可以看到前序任务对 Plan Context 的修改。

**语法**：
```
sequence([
  task1(),
  task2(),
  task3(),
])
```

**参数**：
- `tasks`：Task 列表，按顺序执行

**Context 传递**：
- 后续任务可以看到前序任务对 Plan Context 的修改
- Task1 的 output 会更新 Context，Task2 可以访问更新后的 Context

**示例**：
```
sequence([
  collect_data(source=jira),
  collect_data(source=monitor),
  analyze_results(),
])
```

在这个例子中：
1. `collect_data(source=jira)` 执行完成后，其 output 会更新 Context
2. `collect_data(source=monitor)` 可以访问到 Context 中 jira 数据
3. `analyze_results()` 可以访问到完整的 jira 和 monitor 数据

### parallel

并行执行多个 Task，等待所有 Task 完成。并行任务之间看不到彼此对 Plan Context 的修改。

**语法**：
```
parallel([
  task1(),
  task2(),
  task3(),
])
```

**参数**：
- `tasks`：Task 列表，并行执行

**Context 传递**：
- 并行任务之间看不到彼此对 Plan Context 的修改
- 每个任务基于相同的初始 Context 执行
- 所有任务完成后，它们的 output 会合并到 Context 中

**示例**：
```
parallel([
  collect_data(source=jira),
  collect_data(source=monitor),
  collect_data(source=gitlab),
])
```

在这个例子中：
1. 三个数据收集任务并行执行
2. 每个任务基于相同的初始 Context，看不到其他任务的修改
3. 所有任务完成后，它们的 output 会合并到 Context 中

### condition

根据 Task 的输出结果选择执行哪个分支。

**语法**：
```
condition(
  check=check_task(),
  then=task_a(),
  else=task_b()
)
```

**参数**：
- `check`：返回布尔值的 Task，其 output 会作为条件判断
- `then`：条件为 true 时执行的 Task 或 Task 数组（数组默认为 sequence）
- `else`：条件为 false 时执行的 Task 或 Task 数组（数组默认为 sequence）（可选）

**Context 传递**：
- `check` task 先执行，其 output 会更新 Context
- `then` 或 `else` 可以看到 `check` task 对 Context 的修改
- 只有一个分支会被执行

**示例**：

单个 Task：
```
condition(
  check=check_jira_data_count(),
  then=generate_doc(type=detailed),
  else=generate_doc(type=summary)
)
```

Task 数组（默认为 sequence）：
```
condition(
  check=check_jira_data_count(),
  then=[
    analyze_results(method=deep),
    generate_doc(type=detailed),
  ],
  else=[
    analyze_results(method=quick),
    generate_doc(type=summary),
  ]
)
```

**使用 DSL 辅助方法**：

通过 Task 类型注册的辅助方法，可以简化条件检查：

```
condition(
  check=check_jira_count_gt_100(),
  then=[
    analyze_results(method=deep),
    generate_doc(type=detailed),
  ],
  else=[
    analyze_results(method=quick),
    generate_doc(type=summary),
  ]
)
```

辅助方法定义（在 task-type.md 中）：

```
dsl_helpers:
  - name: check_jira_count_gt_100
    params: []
    expands_to: check_jira_data_count(field=count, operator=gt, value=100)
```

### loop

对列表中的每个 item 顺序执行 Task。每次迭代创建新的 context，包含当前 item。

**语法**：
```
loop(
  items=get_data_sources(),
  body=collect_data()
)
```

**参数**：
- `items`：返回列表的 Task，其 output 会作为 items 列表
- `body`：要执行的 Task

**Context 传递**：
- 先执行 items Task，获取列表数据
- 每次迭代创建新的 context，包含当前 item
- items Task 决定如何将当前 item 放入 context（可以放在任意字段）
- body Task 通过参数自动绑定获取当前 item
- 不同迭代之间的 context 隔离，互不影响
- 每次迭代完成后，context 修改会合并到父 context

**示例**：
```
loop(
  items=get_data_sources(),
  body=collect_data()
)
```

**参数绑定**：
- items Task 负责创建 context，并决定使用哪些字段存放循环数据
- 例如，items Task 可以将当前数据源放在 `data_source` 字段，或 `source` 字段
- body Task 的参数自动绑定到 context 字段
- 如果 body Task 有参数 `source`，则从 `context.source` 绑定
- 如果 body Task 有参数 `data_source`，则从 `context.data_source` 绑定

### map

对列表中的每个 item 并行执行 Task。每个元素创建新的 context，包含当前 item。

**语法**：
```
map(
  items=get_data_sources(),
  body=collect_data()
)
```

**参数**：
- `items`：返回列表的 Task，其 output 会作为 items 列表
- `body`：要执行的 Task

**Context 传递**：
- 先执行 items Task，获取列表数据
- 每个元素创建新的 context，包含当前 item
- items Task 决定如何将当前 item 放入 context（可以放在任意字段）
- body Task 通过参数自动绑定获取当前 item
- 并行任务之间的 context 隔离，互不影响
- 所有任务完成后，context 修改会合并到父 context

**示例**：
```
map(
  items=get_data_sources(),
  body=collect_data()
)
```

**参数绑定**：
- items Task 负责创建 context，并决定使用哪些字段存放循环数据
- 例如，items Task 可以将当前数据源放在 `data_source` 字段，或 `source` 字段
- body Task 的参数自动绑定到 context 字段
- 如果 body Task 有参数 `source`，则从 `context.source` 绑定
- 如果 body Task 有参数 `data_source`，则从 `context.data_source` 绑定

### context

创建或引入新的 Context 作用域，在指定 Context 中执行 Task。

**语法**：
```
context(
  data={key: value},
  body=[...]
)
```

**参数**：
- `data`：Context 的初始数据，可以是：
  - 字面量对象：`{key: value, nested: {key2: value2}}`
  - Task：`load_config_task()`
- `body`：在该 Context 中执行的 Task 或 Task 数组（数组默认为 sequence）

**Context 传递**：
- 创建新的 Context 作用域
- `body` 中的 Task 基于新的 Context 执行
- `body` 执行完成后，Context 修改会合并到父 Context

**示例**：

从字面量对象创建：
```
context(
  data={project_id: 123, environment: production},
  body=[
    collect_data(source=jira),
    analyze_results(),
  ]
)
```

从 Task 创建：
```
context(
  data=load_config_task(),
  body=[
    collect_data(source=jira),
    analyze_results(),
  ]
)
```

## 嵌套组合

原语可以任意嵌套，形成复杂的执行流程。

**示例**：
```
sequence([
  parallel([
    collect_data(source=jira),
    collect_data(source=monitor),
  ]),
  condition(
    check=check_jira_count_gt_100(),
    then=[
      analyze_results(method=deep),
      generate_doc(type=detailed),
    ],
    else=[
      analyze_results(method=quick),
      generate_doc(type=summary),
    ]
  ),
])
```


## Task 参数传递

Task 参数通过参数自动绑定机制传递。

### 参数自动绑定

Task 参数名与 Context 字段名匹配时自动绑定，无需显式传递。

**绑定规则**：
- Plan 中只能传递字面量，不支持变量
- 如果 Plan 中显式传递了参数值，使用显式值
- 如果 Plan 中未传递某参数，Task 执行时尝试从 Context 中读取同名字段

**示例**：

显式传递所有参数：
```
collect_data(source=jira, sprint=23)
```

部分参数显式传递，部分从 Context 绑定：
```
collect_data(source=jira)  # source 使用 jira，sprint 从 context.sprint 绑定
```

### 等价关系

```
collect_data(source=jira, sprint=23)
```

等价于：

```
Task_A:
  id: "task:/collect_data?source=jira&sprint=23"
  input:
    source: "jira"
    sprint: "23"
```

## DSL 辅助方法

Task 类型可以在 `task-type.md` 中注册辅助方法，用于简化常见模式，避免在 plan 中重复写 Task 的细节。

**使用示例**：

假设 `collect_data` Task 类型注册了以下辅助方法：

```
dsl_helpers:
  - name: collect_jira_data
    params: [sprint, time_range]
    expands_to: collect_data(source=jira, sprint=${sprint}, time_range=${time_range})
```

在 Plan DSL 中可以直接使用：

```
collect_jira_data(sprint=23, time_range=7d)
```

等价于：

```
collect_data(source=jira, sprint=23, time_range=7d)
```

**设计原则**：
- 辅助方法只封装常见模式，不引入业务逻辑
- 保持 Plan DSL 的简洁性和可读性
- 辅助方法由 Task 类型维护者注册，Plan 作者无需了解 Task 的内部细节

## 完整示例

```
sequence([
  parallel([
    collect_data(source=jira, sprint=23),
    collect_data(source=monitor, time_range=7d),
  ]),
  condition(
    check=check_jira_count_gt_100(),
    then=[
      analyze_results(method=deep),
      generate_doc(type=detailed, format=markdown),
    ],
    else=[
      analyze_results(method=quick),
      generate_doc(type=summary, format=markdown),
    ]
  ),
  loop(
    items=get_stakeholders(),
    body=send_notification(
      template=daily_report_template
    )
  ),
])
```

## 设计原则

- **函数式风格**：采用函数组合，无副作用
- **可组合性**：原语可以任意嵌套组合
- **声明式**：描述"做什么"而非"怎么做"
- **不可变**：Plan 定义不可变，修改创建新版本
- **可读性**：语法简洁，易于理解和维护
- **严格格式**：遵循统一的语法规范，确保代码一致性
- **Task 驱动**：所有数据操作（比较、判断、运算）都通过 Task 来处理，DSL 只负责流程编排
- **Context 传递**：
  - `sequence`：后续任务可以看到前序任务的 Context 修改
  - `parallel`：并行任务之间看不到彼此的 Context 修改
  - `condition`：分支任务可以看到 check 任务的 Context 修改
  - `loop`：先执行 items Task 获取列表，每次迭代创建新的 context，items Task 负责创建 context 并决定使用哪些字段存放循环数据，body Task 通过参数自动绑定获取，迭代完成后合并到父 context
  - `map`：先执行 items Task 获取列表，每个元素创建新的 context，items Task 负责创建 context 并决定使用哪些字段存放循环数据，body Task 通过参数自动绑定获取，完成后合并到父 context
  - `context`：创建新的 Context 作用域，body 执行完成后修改会合并到父 Context
- **默认 sequence**：
  - Plan 的最外层默认是一个 `sequence`，不需要显式包裹
  - 接收执行计划的参数（如 `condition` 的 `then`/`else`）可以传入数组，默认为 `sequence`
