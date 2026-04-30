# Plan DSL 语法

## 概述

Plan DSL 使用 YAML 格式定义执行计划。每个编排原语或任务调用作为 YAML 的 key，额外参数通过 YAML value 传递。

## 核心规则

1. **key** = 编排原语或任务调用（含简单参数），如 `sequence()`、`"collect_data(source=jira)"`
2. **value** = 不适合放在 key 一行里的额外参数：
   - 若 value 是**数组** → 填充到 body 参数（如 sequence/parallel 的子任务列表）
   - 若 value 是**映射** → 按具名参数填充到方法中
   - 若 value 是 **null** → 无额外参数（叶子节点）
3. **顶层结构**：Plan 的最外层默认是一个 `sequence`，直接写为 YAML 数组

**参数在 key 和 value 之间的分配**：

```yaml
# 简单参数放 key
"collect_data(source=jira, sprint=23)":

# 复杂参数放 value
"collect_data(source=jira)":
  filters: ["open", "in_progress", "done"]
  config:
    timeout: 3600
    retry: 3
```

## 编排原语

### sequence

顺序执行 Task。后续任务可以看到前序任务对 Context 的修改。

```yaml
# 顶层隐式 sequence（推荐）
- "collect_data(source=jira)":
- "collect_data(source=monitor)":
- analyze_results():

# 显式 sequence
sequence():
  - "collect_data(source=jira)":
  - analyze_results():
```

### parallel

并行执行多个 Task，等待所有完成。并行任务之间看不到彼此对 Context 的修改，每个任务基于相同的初始 Context 在隔离副本中执行。各 Task 应写入不同的 Context key，完成后直接合并；如果两个 Task 写了同一个 key 则为冲突错误（parallel 的语义是独立任务，需要合并同 key 的场景应使用 map）。

可通过 `max_concurrency` 限制同时执行的 Task 数量（默认无限制）。

```yaml
parallel():
  - "collect_data(source=jira)":
  - "collect_data(source=monitor)":
  - "collect_data(source=gitlab)":

# 限制并发数
"parallel(max_concurrency=2)":
  - "collect_data(source=jira)":
  - "collect_data(source=monitor)":
  - "collect_data(source=gitlab)":
```

### condition

根据 Task 的输出结果选择执行分支。value 是映射，按具名参数填充。

**参数**：

- `check`：返回布尔值的 Task
- `then`：条件为 true 时执行的 Task 或 Task 数组（数组默认为 sequence）
- `else`：条件为 false 时执行的 Task 或 Task 数组（可选）

`check` 先执行并更新 Context，`then`/`else` 可以看到 `check` 的修改。

```yaml
# 单个 Task
condition():
  check: check_jira_data_count()
  then: "generate_doc(type=detailed)"
  else: "generate_doc(type=summary)"

# Task 数组
condition():
  check: check_jira_data_count()
  then:
    - "analyze_results(method=deep)":
    - "generate_doc(type=detailed)":
  else:
    - "analyze_results(method=quick)":
    - "generate_doc(type=summary)":
```

### loop / map

对列表中的每个 item 执行 Task。

- `loop`：顺序执行，每次迭代基于前一次迭代完成后的父 context，后续迭代能看到前序迭代的修改
- `map`：并行执行，每个元素基于相同的初始父 context，迭代之间互不可见。可通过 `max_concurrency` 限制并发数

**参数**：

- `items`：返回列表的 Task
- `body`（value 数组）：要执行的 Task
- `max_concurrency`（map 专用，可选）：最大并发数，默认无限制

items Task 决定如何将当前 item 放入 context，body Task 通过参数自动绑定获取当前 item。完成后由 items Task 定义的合并策略合并到父 context。

```yaml
"loop(items=get_data_sources())":
  - collect_data():

"map(items=get_data_sources())":
  - collect_data():

# 限制并发数
"map(items=get_data_sources(), max_concurrency=3)":
  - collect_data():
```

### context

创建隔离的 Context 作用域，在其中执行 Task。body 执行完成后，Context 修改合并到父 Context。

```yaml
context():
  - "collect_data(source=jira)":
  - analyze_results():
```

## Task 参数传递

Task 参数名与 Context 字段名匹配时自动绑定，无需显式传递。

**绑定规则**：

- key 中只能传递字面量，不支持变量
- 如果 key 中显式传递了参数值，使用显式值
- 如果未传递某参数，Task 执行时尝试从 Context 中读取同名字段

```yaml
"collect_data(source=jira, sprint=23)":  # 显式传递所有参数
"collect_data(source=jira)":             # sprint 从 context.sprint 绑定
```

### 等价关系

```yaml
"collect_data(source=jira, sprint=23)":
```

等价于：

```yaml
Task_A:
  id: "task:/collect_data?source=jira&sprint=23"
  input:
    source: "jira"
    sprint: "23"
```

## DSL 辅助方法

Task 类型可以在 `task-type.md` 中注册辅助方法，简化常见模式。

```yaml
# 定义（在 task-type.md 中）
dsl_helpers:
  - name: collect_jira_data
    params: [sprint, time_range]
    expands_to: "collect_data(source=jira, sprint=${sprint}, time_range=${time_range})"
```

```yaml
# 使用
"collect_jira_data(sprint=23, time_range=7d)":

# 等价于
"collect_data(source=jira, sprint=23, time_range=7d)":
```

## 完整示例

```yaml
# 顶层隐式 sequence
- parallel():
    - "collect_data(source=jira, sprint=23)":
    - "collect_data(source=monitor, time_range=7d)":
- condition():
    check: check_jira_count_gt_100()
    then:
      - "analyze_results(method=deep)":
      - "generate_doc(type=detailed, format=markdown)":
    else:
      - "analyze_results(method=quick)":
      - "generate_doc(type=summary, format=markdown)":
- "loop(items=get_stakeholders())":
    - "send_notification(template=daily_report_template)":
```

## 设计原则

- **纯 YAML**：不引入自定义语法，所有内容是合法 YAML
- **key-as-call**：key 采用函数调用风格，表达"做什么 + 简单参数"
- **value 按类型分派**：数组 → body，映射 → 具名参数，null → 叶子节点
- **声明式**：描述"做什么"而非"怎么做"，原语可以任意嵌套组合
- **不可变**：Plan 定义不可变，修改创建新版本
- **Task 驱动**：所有数据操作（比较、判断、运算）都通过 Task 来处理，YAML 只负责流程编排
