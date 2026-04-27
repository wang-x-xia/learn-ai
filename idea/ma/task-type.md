# Task 类型

Task 类型在 decompose 时确定，直接映射到 Agent 类型。

## Task 类型定义

每个 Task 类型在注册时声明：
1. 是否支持扩展为 Plan（can_expand_to_plan）
2. 重做策略（redo_strategy）
3. URI 参数解析规则（如何解析 query 和 fragment）
4. DSL 辅助方法（dsl_helpers，可选）

**定义结构**：

```
task_types:
  <task_type_name>:
    can_expand_to_plan: boolean
    redo_strategy:
      type: "always_redo" | "context_aware" | "input_driven"
      logic: string  # 策略逻辑描述或引用
    uri_params:
      query:
        - name: string
          required: boolean
          description: string
      fragment:
        usage: string
        description: string
    dsl_helpers:  # 可在 Plan DSL 中使用的辅助方法
      - name: string
        params: [string]
        expands_to: string
    description: string
```

**字段说明**：

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `can_expand_to_plan` | boolean | 是 | 是否支持展开为子 Plan |
| `redo_strategy.type` | enum | 是 | 重做策略类型 |
| `redo_strategy.logic` | string | 是 | 策略逻辑描述或引用 |
| `uri_params.query` | array | 是 | URI query 参数定义 |
| `uri_params.fragment` | object | 否 | URI fragment 用法定义 |
| `dsl_helpers` | array | 否 | 可在 Plan DSL 中使用的辅助方法 |
| `description` | string | 是 | Task 类型描述 |

**URI 参数定义**：

每个 query 参数需要定义：
- `name`：参数名称
- `required`：是否必填
- `description`：参数描述

fragment 需要定义：
- `usage`：用途（如 "version"、"instance_id"）
- `description`：描述

## DSL 辅助方法

`dsl_helpers` 允许 Task 类型注册可在 Plan DSL 中使用的辅助方法，用于简化常见模式，避免在 plan 中重复写 Task 的细节。

**定义结构**：

```
dsl_helpers:
  - name: string           # 辅助方法名称
    params: [string]       # 参数列表
    expands_to: string     # 展开为的 Task 调用（支持 ${param} 引用）
```

**示例**：

```
task_types:
  collect_data:
    dsl_helpers:
      - name: collect_jira_data
        params: [sprint, time_range]
        expands_to: collect_data(source=jira, sprint=${sprint}, time_range=${time_range})
      - name: collect_monitor_data
        params: [time_range]
        expands_to: collect_data(source=monitor, time_range=${time_range})
```

在 Plan DSL 中可以简化为：

```
collect_jira_data(sprint=23),
collect_monitor_data(time_range=7d)
```

而不是：

```
collect_data(source=jira, sprint=23),
collect_data(source=monitor, time_range=7d)
```

**设计原则**：
- 辅助方法只封装常见模式，不引入业务逻辑
- 参数展开时保持类型安全
- 辅助方法名称应清晰表达其语义
- **条件检查辅助方法**：用于 `condition` 原语，展开为返回布尔值的 Task
  - 命名建议：`check_<condition>` 或 `is_<state>`（可选）
  - 例如：`check_jira_count_gt_100`、`is_data_ready`
  - 如果 Task 既做事情又输出条件，可以使用更语义化的名称，如 `validate_and_check`

## 重做策略类型

每个 Task 类型定义自己的 redo_strategy，用于 Plan 版本切换时判断是否重做：

| 类型 | 描述 | 适用场景 |
|------|------|----------|
| `always_redo` | 总是重新执行 | 副作用操作（如发送邮件） |
| `context_aware` | 根据上下文变化判断 | 数据收集、查询 |
| `input_driven` | 根据输入变化判断 | 数据分析、文档生成 |

## 版本切换时的判断逻辑

```
Plan v1 → Plan v2
  ↓
Plan Executor 遍历 v2 中的每个 Task
  ↓
获取 Task 的类型
  ↓
调用该 Task 类型的 redo_strategy
  - 传入：v1中对应Task的信息、v2中Task的参数、Context变化
  - 执行：该类型定义的策略逻辑
  - 返回：reuse / redo / partial_redo
  ↓
Plan Executor 根据决策执行
  - reuse：复用v1的结果
  - redo：重新执行
  - partial_redo：部分重做
```

## Task 类型与 Agent 的映射

Task 类型与 Agent 类型是 1:1 映射关系：

```
Task Type ← 1:1 → Agent Type
```

每个 Task 类型对应一个专门的 Agent，Agent 只处理特定类型的 Task。
