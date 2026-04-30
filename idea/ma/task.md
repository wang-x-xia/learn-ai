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
- `/<type>`：path，表示 task type（固定，不可自定义）
- `?<query>`：query，编码 task 的 input 参数
- `#<fragment>`：fragment，可选扩展信息

**默认 ID 生成规则**：

默认使用括号表示法（bracket notation）将所有 input 编码到 query 中，没有 fragment：

```
# 简单参数
task:/collect_data?source=jira&sprint=23

# 数组参数
task:/collect_data?filters[]=open&filters[]=in_progress&filters[]=done

# 嵌套参数
task:/collect_data?source=jira&config[timeout]=3600&config[retry]=3
```

**自定义 ID 生成器**：

Task type 可以自定义 ID 生成逻辑，但**只允许自定义 query 和 fragment 部分**，scheme 和 path 固定不变。用途包括：
- 省略不影响唯一性的参数，缩短 ID
- 利用 fragment 携带版本、实例标识等扩展信息

```
# 默认生成（全量 input）
task:/generate_doc?type=review_summary&format=markdown&lang=zh

# 自定义生成（只保留关键参数 + fragment 标识版本）
task:/generate_doc?type=review_summary#v2
```

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
    - "collect_data(source=jira)":
    - "collect_data(source=monitor)":
    - analyze_results():
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

完整的状态机定义（含状态转换图、进度管理、重试策略、超时机制）见 [Plan 与 Task 生命周期](plan-lifecycle.md)。以下是核心设计的摘要。

**宏观状态**（4个核心状态，编排逻辑只关心这一层）：
```
new → working → done
         ↓
      delegated → done
```

**状态说明**：

| 状态 | 描述 | 触发条件 |
|------|------|----------|
| `new` | Task已创建，等待执行 | Plan生成后Task被创建 |
| `working` | Task正在执行中 | Impl开始处理Task |
| `delegated` | Task已展开为子Plan，等待子Plan完成 | Impl 生成子 Plan，交由 Plan Executor 执行 |
| `done` | Task执行结束 | Impl返回结果或错误，或子Plan完成 |

**执行结果**：Task 进入 `done` 时，由独立的 `result` 字段记录结果（success / failed / cancelled），不使用 sub-status 编码成败。

**Sub-status**（用于内部跟踪和监控，不影响编排逻辑）：
- `working.running` — 正在执行
- `working.waiting` — 等待依赖 Task 完成
- `working.retrying` — 执行失败，正在重试
- `delegated.planning` — Impl 正在生成子 Plan
- `delegated.validating` — Plan Executor 正在校验子 Plan
- `delegated.executing` — 子 Plan 正在执行

**设计原则**：
- 宏观状态保持简单（4个），便于理解和调试
- Sub-status 用于内部跟踪和监控，不影响编排逻辑
- 状态转换由Plan Executor控制，Impl不直接修改Task状态

## Task 展开为 Plan

当选中的 Impl 的 `can_expand_to_plan: true` 时，该 Impl 会为 Task 生成一个子 Plan：

```yaml
Task_A:
  id: "task:/analyze?target=test_results"
  type: "analyze"
  plan:  # 由 Impl 生成
    - "collect_data(source=jira)":
    - "collect_data(source=monitor)":
    - analyze_results():
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
