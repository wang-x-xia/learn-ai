# Business Concept — 业务概念

## 目标

定义业务概念的概念，包括语义位置、与技术制品的对齐关系，以及产品经理如何用业务概念来描述产品。

---

## 一、基于 SDS 实际制品的映射

根据 SDS 制品体系的实际设计，映射应直接对应到现有制品：

**SDS 现有制品**：
- **治理域**：Role, Permission, Constraint, Dependency
- **契约域**：Entity, Interface, Event, Error
- **行为域**：Process, Orchestration, Reaction, Schedule
- **组织单元**：Module

---

## 二、七个核心映射位置

| 映射位置 | 主要目标制品 | 对应 Requirement 字段 |
|---------|-------------|---------------------|
| **as_actor** | Role / Module | `actor_role_id` |
| **as_object** | Entity | `preconditions` / `postconditions` (field 路径) |
| **as_action** | Interface / Orchestration / Reaction / Schedule | `traces.modules` (间接) |
| **as_event** | Event | `exceptions.trigger_event_id` / `side_effects.trigger_event_id` |
| **as_attribute** | Entity.field | `preconditions` / `postconditions` (field 路径) |
| **as_result** | StateChange / Interface Response / Event / SideEffect | `postconditions` / `side_effects` |
| **as_error** | Error | Interface.error_codes |

---

## 三、业务概念层设计

### 3.1 为什么需要业务概念层？

**现实问题**：业务概念与技术概念的不对齐

```
业务概念                    技术概念
VIP会员        →?→    User.role_type IN ('GOLD', 'DIAMOND')
退款单         →?→    Refund 实体 + RefundLineItem 实体
退款SLA        →?→    Refund.expected_completion_time
```

**不对齐的原因**：
1. 一对多：一个业务"订单"可能拆分为多个技术实体
2. 多对一：业务"用户"和"会员"在技术上可能是同一个表
3. 语义漂移：技术重构时，Entity 名称变了，但业务概念不变

### 3.2 业务概念层的设计

```yaml
# BusinessConcept 制品 Schema
id: "BC-\d+"
name: string
description: string         # 一句话说明
defined: boolean             # 是否已定义

# 七个语义位置的映射（每个概念只配置适用的语义位置）
as_actor:
  type: enum                # ROLE / MODULE
  artifact_id: string       # "ROLE-3" / "MOD-010"

as_object:
  type: ENTITY
  artifact_id: string

as_action:
  type: enum                # INTERFACE / ORCHESTRATION / REACTION / SCHEDULE
  artifact_id: string

as_event:
  type: EVENT
  artifact_id: string

as_attribute:
  type: ENTITY_FIELD        # Entity.field
  artifact_id: string       # "ENT-005.expected_completion"

as_result:
  type: enum                # STATE_CHANGE / INTERFACE_RESPONSE / EVENT / SIDE_EFFECT
  artifact_id: string

as_error:
  type: ERROR
  artifact_id: string
```

### 3.3 渐进式引用策略

| 阶段 | 引用类型 | 示例 |
|------|---------|------|
| **Draft** | 无引用 | "VIP用户可以优先退款" |
| **Structured Draft** | 软引用（自然语言标识） | "Given [actor:VIP会员] When [action:发起退款]" |
| **Requirement** | 强引用（typed ID） | `actor_role_id: "ROLE-3"` |
| **User Story** | 强引用 | `when: "API-20"` |


