# Reaction — 事件反应器

## 目标

定义系统对领域事件的自动响应——当某个事件发生时，哪个模块负责处理、处理是否幂等。Reaction 是异步驱动架构的核心入口，将"系统内发生了事"转化为自动执行的处理逻辑。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `SUB-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 反应器名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `owner_module_id` | ref | `MOD-\d+` | 负责处理的模块 |
| `target_entity_id` | ref | `ENT-\d+` | 操作的目标实体（可选） |
| `event_id` | ref | `EVT-\d+` | 监听的事件（引用 [Event](../contract/event.md)） |
| `idempotent` | boolean | | 处理是否幂等 |

---

## 格式

```yaml
id: "SUB-1"
name: "OnPaymentConfirmed"
description: "支付确认后更新订单状态并发送确认通知"

owner_module_id: "MOD-5"
target_entity_id: "ENT-3"
event_id: "EVT-5"
idempotent: true
```

```yaml
id: "SUB-2"
name: "OnRefundSuccess"
description: "退款成功后扣减积分并释放优惠券"

owner_module_id: "MOD-10"
target_entity_id: "ENT-5"
event_id: "EVT-10"
idempotent: true
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `OWNS` | [Module](../module.md) |
| 出 → | `LISTENS_TO` | [Event](../contract/event.md) |
| 出 → | `TARGETS` | [Entity](../contract/entity.md) |
