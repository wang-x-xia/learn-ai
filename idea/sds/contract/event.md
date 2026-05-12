# Event — 领域事件

## 目标

定义系统中的领域事件——谁发布、谁消费、携带什么数据。Event 是模块间异步通信的契约，也是 Process 状态转换的触发源和 Requirement 异常 / 副作用的信号源。将 Process.trigger_event（裸字符串）和 Requirement.Exception.trigger.event（内联枚举）统一提升为独立制品，使事件的 Schema、发布者、消费者均可追溯。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `EVT-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 事件名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 事件类别 |
| `owner_module_id` | ref | `MOD-\d+` | 负责模块（权威发布者，与 Entity.owner_module_id 一致语义） |
| `consumer_module_ids` | list\<ref\> | `MOD-\d+` | 消费者模块列表 |
| `source_entity_id` | ref | `ENT-\d+` | 触发源实体（可选） |
| `source_transition` | SourceTransition | 见下方 | 触发源状态转换（可选，与 Process 关联时填写） |
| `payload_fields` | list\<[TypedField](../concepts.md#typedfield)\> | | 事件载荷字段 |

### type 枚举

| 值 | 含义 |
|----|------|
| `DOMAIN` | 业务领域事件（OrderCreated、PaymentConfirmed） |
| `INTEGRATION` | 系统集成事件（ConfigChanged、ServiceRegistered） |
| `NOTIFICATION` | 通知类事件（EmailSent、SmsPushed） |

---

## 子结构定义

### SourceTransition

标记该事件由哪个流程的哪条状态转换触发。

| 字段 | 类型 | 约束 |
|------|------|------|
| `process_id` | ref | `PROC-\d+` |
| `from_state` | string | 起始状态 ID |
| `to_state` | string | 目标状态 ID |

---

## 格式

```yaml
id: "EVT-5"
name: "PaymentConfirmedEvent"
description: "支付网关确认支付成功后发布"

type: DOMAIN
owner_module_id: "MOD-3"
consumer_module_ids: ["MOD-5", "MOD-8"]
source_entity_id: "ENT-3"
source_transition:
  process_id: "PROC-5"
  from_state: "CREATED"
  to_state: "PAID"

payload_fields:
  - name: order_id
    type: UUID
    required: true
  - name: amount
    type: DECIMAL
    required: true
  - name: payment_method
    type: ENUM
    required: true
    enum_values: ["WECHAT", "ALIPAY", "CARD"]
```

```yaml
id: "EVT-8"
name: "VipStatusExpiredEvent"
description: "用户 VIP 状态到期时发布"

type: DOMAIN
owner_module_id: "MOD-2"
consumer_module_ids: ["MOD-10"]
source_entity_id: "ENT-1"

payload_fields:
  - name: user_id
    type: UUID
    required: true
  - name: expired_level
    type: ENUM
    required: true
    enum_values: ["GOLD", "DIAMOND"]
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `PUBLISHES` | [Module](../module.md) |
| 出 → | `CONSUMED_BY` | [Module](../module.md) |
| ← 入 | `TRIGGERS` | [Process](../behavior/process.md) Transition |
| ← 入 | `LISTENS_TO` | [Reaction](../behavior/reaction.md) |
| ← 入 | `TRIGGERED_BY` | [Requirement](../requirement/requirement.md) Exception / SideEffect |
