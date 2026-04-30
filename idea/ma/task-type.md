# Task 类型

Task 类型定义能力契约，每个 Task Type 可以有多个 Impl。

## Task 类型定义

每个 Task 类型在注册时声明：
1. 重做策略（redo_strategy）
2. URI 参数解析规则（如何解析 query 和 fragment）
3. DSL 辅助方法（dsl_helpers，可选）

**定义结构**：

```
task_types:
  <task_type_name>:
    redo_strategy:
      type: "always_redo" | "context_aware" | "input_driven"
      depends_on: [string]  # context_aware 专用：依赖的 Context 字段列表
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
| `redo_strategy.type` | enum | 是 | 重做策略类型（描述任务本身的性质） |
| `redo_strategy.depends_on` | array | 否 | context_aware 专用：依赖的 Context 字段列表 |
| `uri_params.query` | array | 是 | URI query 参数定义 |
| `uri_params.fragment` | object | 否 | URI fragment 用法定义 |
| `dsl_helpers` | array | 否 | 可在 Plan DSL 中使用的辅助方法 |
| `description` | string | 是 | Task 类型描述 |

## Impl 定义

每个 Impl 在注册时声明：

```
impls:
  <task_type>/<impl_name>:
    kind: "llm" | "script" | "predefined"
    can_expand_to_plan: boolean
    partners: [task_type_name]  # 可协作的 Task Type 列表
    config:
      model: string
      # ... 其他实现特定配置
```

**字段说明**：

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `kind` | enum | 是 | 执行者类型（llm、script、predefined等） |
| `can_expand_to_plan` | boolean | 是 | 是否将Task展开为Plan。强模型可能直接完成，脚本直接执行，弱模型需要拆分 |
| `partners` | array | 是 | 可协作的Task Type列表。生成的Plan只能引用此范围内的Task Type |
| `config` | object | 是 | 实现特定配置（模型、脚本路径等） |

**示例**：

```
impls:
  collect_data/jira-script:
    kind: "script"
    can_expand_to_plan: false
    partners: []
    config:
      script: "scripts/collect_jira.py"

  analyze/gpt-4o:
    kind: "llm"
    can_expand_to_plan: false
    partners: []
    config:
      model: "gpt-4o"

  analyze/gpt-4o-mini:
    kind: "llm"
    can_expand_to_plan: true
    partners: [collect_data, summarize]
    config:
      model: "gpt-4o-mini"
```

## Task Type 与 Impl 的映射

```
Task Type ← 1:N → Impl
```

每个 Task Type 可以有多个 Impl（不同 kind、不同模型/配置），由 Plan Executor 的选择策略决定使用哪个。评价体系在 Impl 级别运作，为选择策略提供数据支持。

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

```yaml
"collect_jira_data(sprint=23)":
"collect_monitor_data(time_range=7d)":
```

而不是：

```yaml
"collect_data(source=jira, sprint=23)":
"collect_data(source=monitor, time_range=7d)":
```

**设计原则**：
- 辅助方法只封装常见模式，不引入业务逻辑
- 参数展开时保持类型安全
- 辅助方法名称应清晰表达其语义
- **条件检查辅助方法**：用于 `condition` 原语，展开为返回布尔值的 Task
  - 命名建议：`check_<condition>` 或 `is_<state>`（可选）
  - 例如：`check_jira_count_gt_100`、`is_data_ready`
  - 如果 Task 既做事情又输出条件，可以使用更语义化的名称，如 `validate_and_check`

## 重做策略

Plan 版本切换时，Plan Executor 需要判断 v2 中的每个 Task 是否需要重新执行。判断依据由 Task Type 的 `redo_strategy` 定义。

### 判断结果

| 决策 | 含义 | Plan Executor 行为 |
|------|------|-------------------|
| `reuse` | 复用 v1 的结果 | 跳过执行，将 v1 结果写入当前 Context |
| `redo` | 完全重新执行 | 正常执行 Task |
| `partial_redo` | 带参考的重新执行 | 将 v1 结果作为 `prior_result` 注入 Task 输入，然后执行 |

**partial_redo**：重新执行 Task，但 Impl 可以访问 `prior_result`（v1 的执行结果）来加速执行。例如，文档生成 Impl 可以在 v1 文档基础上增量修改，而非从零生成。如果 Impl 不支持利用 `prior_result`，行为等同于 `redo`。

### 策略类型

#### always_redo

总是返回 `redo`。不考虑输入或 Context 是否变化。

适用于有外部副作用的操作（发送通知、写入外部系统），无法确定之前的副作用是否仍然有效。

#### context_aware

根据 Context 中依赖字段的变化判断。Task Type 需额外声明 `depends_on`（依赖的 Context 字段列表）。

**判断逻辑**：

1. 获取 v1 执行时 Context 中 `depends_on` 字段的快照
2. 与当前 Context 中对应字段的值比较
3. 所有依赖字段均未变化 → `reuse`
4. 有字段变化 → `partial_redo`

默认返回 `partial_redo` 而非 `redo`，因为 Context 变化通常是增量的（如新增了几条数据），v1 结果有参考价值。

**示例**：

```yaml
task_types:
  collect_data:
    redo_strategy:
      type: context_aware
      depends_on: [sprint_data, monitor_data]
```

#### input_driven

根据 Task 的显式输入参数变化判断。

**判断逻辑**：

1. 比较 v1 和 v2 中该 Task 的显式输入参数（key 中的参数 + value 中的具名参数）
2. 参数完全相同 → `reuse`
3. 参数不同 → `redo`

不关心 Context 变化——适用于输出完全由输入决定的 Task（给定相同输入，无论 Context 如何变化，输出一样）。

**示例**：

```yaml
task_types:
  generate_doc:
    redo_strategy:
      type: input_driven
```

### 版本切换流程

```
Plan v1 → Plan v2
  ↓
Plan Executor 遍历 v2 中的每个 Task
  ↓
v1 中是否存在对应 Task？（通过 Task ID 匹配）
  ↓ No → 按新 Task 执行（redo）
  ↓ Yes
调用该 Task Type 的 redo_strategy
  ↓
按决策执行：reuse / redo / partial_redo
```
