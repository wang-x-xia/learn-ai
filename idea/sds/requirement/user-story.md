# User Story — 用户故事

## 目标

将 Requirement 分解为面向实现的最小交付单元，连接需求层（L1）与架构层（L2）。每个 User Story 对应一个可独立验收的行为切片，通过结构化的 Given / When / Then 验收条件消除"完成"的歧义。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `US-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 简短标题 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话摘要 |
| `requirement_ids` | list\<ref\> | `REQ-\d+` | 来源需求 |
| `actor_role_id` | ref | `ROLE-\d+` | 执行角色（引用 [Role](../governance/rbac/role.md)） |
| `priority` | enum | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` | 优先级 |
| `status` | enum | 见下方 | 故事状态 |
| `story_points` | integer | Fibonacci: `1, 2, 3, 5, 8, 13, 21` | 复杂度估算 |
| `acceptance_criteria` | list\<Criterion\> | ≥ 1 条 | 结构化验收条件 |

### status 枚举

| 值 | 含义 |
|----|------|
| `BACKLOG` | 待排期 |
| `READY` | 已就绪（所有前置条件满足） |
| `IN_PROGRESS` | 开发中 |
| `DONE` | 已完成 |
| `BLOCKED` | 被阻塞 |

---

## 子结构定义

### Criterion（Given / When / Then）

| 字段 | 类型 | 约束 |
|------|------|------|
| `given` | [Condition](../concepts.md#condition) | 前置条件 |
| `when` | ref | `API-\d+` / `SUB-\d+` / `SCH-\d+`（引用 [Interface](../contract/interface.md)、[Reaction](../behavior/reaction.md) 或 [Schedule](../behavior/schedule.md)） |
| `then` | [Assertion](../concepts.md#assertion) | 预期结果 |

---

## 格式

```yaml
id: "US-301"
name: "VIP用户发起退款申请"
description: "金卡/钻石卡用户可在订单完成后发起退款，享受 24h SLA"

requirement_ids: ["REQ-0078"]
actor_role_id: "ROLE-3"          # VIP User
priority: HIGH
status: READY
story_points: 5

acceptance_criteria:
  - given:
      field: "user.membership_level"
      operator: IN
      values: ["GOLD", "DIAMOND"]
    when: "API-20"               # 创建退款申请
    then:
      field: "refund.sla"
      operator: "=="
      expected: "24h"

  - given:
      field: "user.membership_level"
      operator: NOT_IN
      values: ["GOLD", "DIAMOND"]
    when: "API-20"               # 创建退款申请
    then:
      field: "refund.sla"
      operator: "=="
      expected: "72h"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `DECOMPOSES_INTO` | [Requirement](requirement.md) |
| 出 → | `ACTED_BY` | [Role](../governance/rbac/role.md) |
| 出 → | `IMPLEMENTED_BY` | [Interface](../contract/interface.md) / [Orchestration](../behavior/orchestration.md) / [Reaction](../behavior/reaction.md) / [Schedule](../behavior/schedule.md)（从 Criterion.when 派生） |
| 出 → | `TESTED_BY` | [Scenario Test](../test/scenario-test.md) |
