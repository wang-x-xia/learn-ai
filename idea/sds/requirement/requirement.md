# Requirement — 需求制品

## 目标

承载**完全消歧后**的结构化需求。一条 Requirement 回答了七个消歧维度（主语、对象、条件、边界、异常、副作用、状态变迁）的所有问题，消歧分数达标后方可驱动架构设计和代码生成。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `REQ-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 简短标题 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话摘要 |
| `source_draft_id` | ref | `DRAFT-\d+` | 来源初稿 |
| `type` | enum | 见下方 | 需求类型 |
| `priority` | enum | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` | 优先级 |
| `status` | enum | 见下方 | 审批状态 |
| `disambiguation_score` | float | `[0.0, 1.0]` | 消歧完成度（≥ 0.95 进入开发，≥ 0.98 进入代码生成） |
| `actor_role_id` | ref | `ROLE-\d+` | 执行角色（引用 [Role](../governance/rbac/role.md)） |
| `preconditions` | list\<[Condition](../concepts.md#condition)\> | ≥ 0 条 | 前置条件 |
| `postconditions` | list\<StateChange\> | ≥ 1 条 | 后置状态变更 |
| `exceptions` | list\<Exception\> | ≥ 0 条 | 异常场景与处理策略 |
| `side_effects` | list\<SideEffect\> | ≥ 0 条 | 触发的连带变更 |
| `traces` | Traces | 见下方 | 下游关联制品 |

### type 枚举

| 值 | 含义 |
|----|------|
| `FUNCTIONAL` | 功能性需求 |
| `NON_FUNCTIONAL` | 非功能性需求（性能、安全、可用性等） |

### status 枚举

| 值 | 含义 |
|----|------|
| `DRAFT` | 草稿 |
| `IN_REVIEW` | 审核中 |
| `APPROVED` | 已批准 |
| `DEPRECATED` | 已废弃 |

---

## 子结构定义

### StateChange

| 字段 | 类型 | 约束 |
|------|------|------|
| `field` | string | 点号分隔路径（如 `refund.status`） |
| `becomes` | any | 目标值或表达式（如 `"PROCESSING"` / `"NOW() + 24h"`） |

### Exception

触发方式二选一：异步事件触发（`trigger_event_id`）或同步条件触发（`trigger_condition`），两者互斥。

| 字段 | 类型 | 约束 |
|------|------|------|
| `trigger_event_id` | ref | `EVT-\d+`（与 `trigger_condition` 互斥，引用 [Event](../contract/event.md)） |
| `trigger_condition` | [Condition](../concepts.md#condition) | 同步条件检查（与 `trigger_event_id` 互斥） |
| `resolution` | enum | `PRESERVE_ORIGINAL` / `ESCALATE` / `ABORT` / `FALLBACK` / `RETRY` |
| `fallback_sla` | duration | 可选，仅 `ESCALATE` / `FALLBACK` 时需要 |

### SideEffect

| 字段 | 类型 | 约束 |
|------|------|------|
| `trigger_event_id` | ref | `EVT-\d+`（引用 [Event](../contract/event.md)） |
| `target_entity_id` | ref | `ENT-\d+` |
| `mutation` | enum | `INCREMENT` / `DECREMENT` / `SET` / `UPDATE_STATUS` / `DELETE` / `APPEND` |
| `field` | string | 目标字段路径 |
| `value` | any | 可选，`SET` / `UPDATE_STATUS` 时需要 |

### Traces

| 字段 | 类型 | 约束 |
|------|------|------|
| `user_stories` | list\<ref\> | `US-\d+` |
| `modules` | list\<ref\> | `MOD-\d+` |
| `acceptance_tests` | list\<ref\> | `AT-\d+` |

---

## 格式

```yaml
id: "REQ-0078"
name: "VIP用户优先退款"
description: "金卡和钻石卡用户的退款 SLA 从 72h 缩短为 24h"

source_draft_id: "DRAFT-0078"
type: FUNCTIONAL
priority: HIGH
status: APPROVED
disambiguation_score: 0.98

actor_role_id: "ROLE-3"         # VIP User

preconditions:
  - field: "order.status"
    operator: IN
    values: ["DELIVERED", "COMPLETED"]
  - field: "user.refund_count_this_month"
    operator: "<="
    value: 3

postconditions:
  - field: "refund.status"
    becomes: "PROCESSING"
  - field: "refund.expected_completion"
    becomes: "NOW() + 24h"

exceptions:
  - trigger_event_id: "EVT-8"   # VipStatusExpiredEvent
    resolution: PRESERVE_ORIGINAL
  - trigger_condition:
      field: "refund.amount"
      operator: ">"
      value: 50000
    resolution: ESCALATE
    fallback_sla: "48h"

side_effects:
  - trigger_event_id: "EVT-10"  # RefundSuccessEvent
    target_entity_id: "ENT-5"
    mutation: DECREMENT
    field: "points_balance"
  - trigger_event_id: "EVT-10"  # RefundSuccessEvent
    target_entity_id: "ENT-8"
    mutation: UPDATE_STATUS
    field: "coupon.status"
    value: "REUSABLE"

traces:
  user_stories: ["US-301"]
  modules: ["MOD-010", "MOD-011"]
  acceptance_tests: ["AT-1", "AT-2"]
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `DISAMBIGUATED_INTO` | [Draft](draft.md) |
| 出 → | `DECOMPOSES_INTO` | [User Story](user-story.md) |
| 出 → | `ACTED_BY` | [Role](../governance/rbac/role.md) |
| 出 → | `TESTED_BY` | [Acceptance Test](../test/acceptance-test.md) |
