# Task 定义

## Task 概述

Task 是最小执行单元，代表一个原子化的工作项。Task 可以按需展开为 Plan。

## Task ID

Task 使用自定义 URI 格式的 ID：

**格式**：
```
task:/<type>?<query>#<fragment>
```

**结构解析**：
- `task:`：自定义 scheme
- `/<type>`：path，表示 task type
- `?<query>`：query，意图相关的参数（由 task type 定义解析规则）
- `#<fragment>`：fragment，可选扩展信息（由 task type 定义用途）

**示例**：
```
task:/collect_data?source=jira&sprint=23
task:/analyze?target=test_results&method=regression
task:/generate_doc?type=review_summary#v2
```

**设计原则**：
- query 和 fragment 由对应的 task type 定义解析规则
- query 参数只包含"意图相关"的参数，不是全部参数
- fragment 可用于版本、实例标识等扩展信息

Task 类型的详细定义见 [Task 类型](task-type.md)。

## Task 实例

Task 实例包含完整的执行信息：

```yaml
Task_A:
  id: "task:/collect_data?source=jira&sprint=23"
  type: "collect_data"
  state: "new"
  input:
    source: "jira"
    sprint: "23"
  plan:  # 可选字段，如果有就展开为子 Plan
    sequence([
      collect_data(source="jira"),
      collect_data(source="monitor"),
      analyze_results()
    ])
  output: null
  error: null
  created_at: "2026-04-17T10:00:00Z"
  started_at: null
  completed_at: null
```

**字段说明**：

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `id` | URI | 是 | Task ID，格式 `task:/<type>?<query>#<fragment>` |
| `type` | string | 是 | Task 类型 |
| `state` | string | 是 | Task 状态（new/working/delegated/done） |
| `input` | object | 是 | Task 输入参数 |
| `plan` | object | 否 | 可选，子 Plan 定义 |
| `output` | any | 否 | Task 执行结果 |
| `error` | string | 否 | 错误信息 |
| `created_at` | datetime | 是 | 创建时间 |
| `started_at` | datetime | 否 | 开始执行时间 |
| `completed_at` | datetime | 否 | 完成时间 |

## Task 生命周期

**宏观状态**（4个核心状态）：
```
new → working → delegated → done
```

**状态说明**：

| 状态 | 描述 | 触发条件 |
|------|------|----------|
| `new` | Task已创建，等待执行 | Plan生成后Task被创建 |
| `working` | Task正在执行中 | Impl开始处理Task |
| `delegated` | Task已展开为子Plan，等待子Plan完成 | Task有plan字段，Plan Executor展开为子Plan |
| `done` | Task执行完成（成功或失败） | Impl返回结果或错误，或子Plan完成 |

**Subtype（可选的细粒度状态）**：
- `working.waiting` - 等待依赖Task完成
- `working.retrying` - 重试中
- `delegated.waiting_plan` - 等待子Plan完成
- `done.success` - 成功完成
- `done.failed` - 执行失败
- `done.cancelled` - 被取消

**设计原则**：
- 宏观状态保持简单（4个），便于理解和调试
- Subtype用于内部跟踪和监控，不影响编排逻辑
- 状态转换由Plan Executor控制，Impl不直接修改Task状态

## Task 展开为 Plan

当选中的 Impl 的 `can_expand_to_plan: true` 时，该 Impl 会为 Task 生成一个子 Plan：

```yaml
Task_A:
  id: "task:/analyze?target=test_results"
  type: "analyze"
  plan:  # 由 Impl 生成
    sequence([
      collect_data(source="jira"),
      collect_data(source="monitor"),
      analyze_results()
    ])
```

**展开规则**：
- 是否展开由选中的 Impl 决定（`can_expand_to_plan`），不是 Task 类型决定
- Impl 生成 Plan 后，Plan Executor 进行结构校验（partners 范围、参数合法性、DSL 结构）
- 校验通过后，创建子 Plan Context（继承父 Plan Context），递归执行子 Plan
- 子 Plan 完成后，结果合并到父 Plan Context
- Task 状态变为 `delegated`，等待子 Plan 完成

## Task 与 Impl 的关系

Impl 是 Task 的执行者：

- **输入**：Task + Context
- **输出**：Result + 新Context
- **无状态**：Impl本身不维护状态，状态在Context中

**映射关系**：

```
Task Type ← 1:N → Impl
  collect_data ←┬─ collect_data/jira-script   (kind: script)
                └─ collect_data/gpt-4o-mini   (kind: llm)
  analyze      ←┬─ analyze/gpt-4o             (kind: llm)
                └─ analyze/gpt-4o-mini        (kind: llm)
  generate_doc ←── generate_doc/gpt-4o        (kind: llm)
```

每个 Task Type 可以有多个 Impl，由 Plan Executor 的选择策略决定使用哪个。评价体系在 Impl 级别运作。
