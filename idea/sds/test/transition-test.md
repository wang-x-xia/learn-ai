# Transition Test — 状态转换测试

## 目标

验证 [Process](../behavior/process.md) 的状态机行为——合法转换是否生效、守卫条件是否正确拦截、禁止路径是否被阻断。每个 Transition Test 聚焦一条状态转换（或一条禁止路径）。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `TT-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 用例名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `process_id` | ref | `PROC-\d+` | 验证的流程 |
| `test_type` | enum | 见下方 | 测试场景类型 |
| `initial_state` | string | 状态 ID | 起始状态 |
| `event_id` | ref | `EVT-\d+` | 触发事件（引用 [Event](../contract/event.md)） |
| `guard_values` | list\<[Condition](../concepts.md#condition)\> | | 守卫条件的输入值 |
| `expected_state` | string \| null | 状态 ID 或 `null` | 预期目标状态（`null` = 转换被拒绝） |
| `expected_action_called` | boolean | | 是否预期触发转换动作 |

### test_type 枚举

| 值 | 含义 |
|----|------|
| `VALID_TRANSITION` | 合法转换——守卫满足，状态应变更 |
| `GUARD_REJECTION` | 守卫拦截——守卫不满足，转换应被拒绝 |
| `FORBIDDEN_TRANSITION` | 禁止路径——显式禁止的转换应被阻断 |

---

## 格式

```yaml
id: "TT-1"
name: "订单支付成功转换"
description: "CREATED 状态收到支付确认后应转为 PAID"

process_id: "PROC-5"
test_type: VALID_TRANSITION
initial_state: "CREATED"
event_id: "EVT-5"                # PaymentConfirmedEvent
guard_values:
  - field: "order.total_amount"
    operator: ">"
    value: 0
expected_state: "PAID"
expected_action_called: true
```

```yaml
id: "TT-2"
name: "零元订单不可支付"
description: "金额为 0 时守卫应拒绝 CREATED → PAID 转换"

process_id: "PROC-5"
test_type: GUARD_REJECTION
initial_state: "CREATED"
event_id: "EVT-5"                # PaymentConfirmedEvent
guard_values:
  - field: "order.total_amount"
    operator: "=="
    value: 0
expected_state: null
expected_action_called: false
```

```yaml
id: "TT-3"
name: "终态不可变更"
description: "CLOSED 状态不允许任何转换"

process_id: "PROC-5"
test_type: FORBIDDEN_TRANSITION
initial_state: "CLOSED"
event_id: "EVT-5"                # PaymentConfirmedEvent
guard_values: []
expected_state: null
expected_action_called: false
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `TESTED_BY` | [Process](../behavior/process.md) |
