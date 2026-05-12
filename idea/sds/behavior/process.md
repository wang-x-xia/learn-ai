# Process — 流程制品

## 目标

定义业务流程和状态机——状态集合、合法转换、守卫条件、禁止路径。Process 是行为层（L5）的核心制品，它精确描述实体在生命周期内**可以走哪些路、不能走哪些路**，消除"这个状态能不能转到那个状态"的歧义。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `PROC-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 流程名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 流程类型 |
| `target_entity_id` | ref | `ENT-\d+` | 管理哪个实体的状态 |
| `target_field` | string | 实体字段名（如 `status`） | 状态字段 |
| `states` | list\<State\> | ≥ 2 个 | 状态集合 |
| `transitions` | list\<Transition\> | ≥ 1 条 | 合法转换规则 |
| `forbidden_transitions` | list\<Forbidden\> | | 显式禁止的转换 |

### type 枚举

| 值 | 含义 |
|----|------|
| `STATE_MACHINE` | 有限状态机——单一状态字段的线性 / 分支流转 |
| `DAG` | 有向无环图——多步骤并行 / 汇聚流程 |
| `PIPELINE` | 流水线——顺序执行的处理阶段 |

---

## 子结构定义

### State

| 字段 | 类型 | 约束 |
|------|------|------|
| `id` | string | 状态标识（UPPER_SNAKE_CASE，如 `CREATED`） |
| `type` | enum | `INITIAL` / `NORMAL` / `TERMINAL` |

### Transition

| 字段 | 类型 | 约束 |
|------|------|------|
| `from` | string | 起始状态 ID |
| `to` | string | 目标状态 ID |
| `event_id` | ref | `EVT-\d+`（引用 [Event](../contract/event.md)） |
| `guard` | [Condition](../concepts.md#condition) | 守卫条件（可选，不满足则转换被拒绝） |
| `action_module_id` | ref | `MOD-\d+` — 执行转换动作的模块（可选） |
| `action_method` | string | 模块方法名（可选） |

### Forbidden

| 字段 | 类型 | 约束 |
|------|------|------|
| `from` | string | 起始状态 ID，`*` 表示任意 |
| `to` | string | 目标状态 ID，`*` 表示任意 |
| `reason` | enum | `TERMINAL_STATE` / `BUSINESS_RULE` / `COMPLIANCE` / `DATA_INTEGRITY` |

---

## 格式

```yaml
id: "PROC-005"
name: "OrderLifecycle"
description: "订单从创建到终态的完整生命周期状态机"

type: STATE_MACHINE
target_entity_id: "ENT-003"
target_field: "status"

states:
  - id: CREATED
    type: INITIAL
  - id: PAID
    type: NORMAL
  - id: SHIPPED
    type: NORMAL
  - id: DELIVERED
    type: NORMAL
  - id: COMPLETED
    type: NORMAL
  - id: CLOSED
    type: TERMINAL
  - id: CANCELLED
    type: TERMINAL

transitions:
  - from: CREATED
    to: PAID
    event_id: "EVT-5"            # PaymentConfirmedEvent
    guard:
      field: "order.total_amount"
      operator: ">"
      value: 0
    action_module_id: "MOD-8"
    action_method: "sendPaymentConfirmation"

  - from: CREATED
    to: CANCELLED
    event_id: "EVT-6"            # UserCancelEvent
    guard:
      field: "elapsed_time(order.created_at)"
      operator: "<"
      value: "30min"
    action_module_id: "MOD-10"
    action_method: "refund"

  - from: PAID
    to: SHIPPED
    event_id: "EVT-11"           # ShipmentCreatedEvent

  - from: SHIPPED
    to: DELIVERED
    event_id: "EVT-12"           # DeliveryConfirmedEvent

  - from: DELIVERED
    to: COMPLETED
    event_id: "EVT-13"           # CompletionTimerEvent

  - from: COMPLETED
    to: CLOSED
    event_id: "EVT-14"           # ArchiveEvent

forbidden_transitions:
  - from: CLOSED
    to: "*"
    reason: TERMINAL_STATE
  - from: CANCELLED
    to: "*"
    reason: TERMINAL_STATE
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `GOVERNED_BY` | [Module](../module.md) |
| 出 → | `TRANSITIONS` | [Entity](../contract/entity.md) |
| 出 → | `TRIGGERS` | [Event](../contract/event.md) |
| 出 → | `TESTED_BY` | [Transition Test](../test/transition-test.md) |
