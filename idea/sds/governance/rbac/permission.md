# Permission — 授权条目

## 目标

定义一条精确的授权规则——什么动作、在什么资源上、允许还是拒绝。Permission 将 Role 中原来的 `permitted_interface_ids`（扁平列表）提升为独立制品，支持更细粒度的访问控制（读 / 写区分、条件限制、显式拒绝）。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `PERM-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 权限名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `action` | enum | 见下方 | 授权动作 |
| `resource_type` | enum | `INTERFACE` / `ENTITY` | 资源类型 |
| `resource_id` | ref | `API-\d+` / `ENT-\d+` | 资源 ID |
| `effect` | enum | `ALLOW` / `DENY` | 效果（DENY 优先于 ALLOW） |
| `conditions` | list\<[Condition](../../concepts.md#condition)\> | ≥ 0 条 | 附加条件（可选，满足时该条目才生效） |

### action 枚举

| 值 | 含义 |
|----|------|
| `INVOKE` | 调用接口（`resource_type: INTERFACE`） |
| `READ` | 读取数据（`resource_type: ENTITY`） |
| `WRITE` | 写入数据（`resource_type: ENTITY`） |
| `DELETE` | 删除数据（`resource_type: ENTITY`） |

---

## 格式

```yaml
id: "PERM-1"
name: "调用退款接口"
description: "允许调用创建退款申请接口"

action: INVOKE
resource_type: INTERFACE
resource_id: "API-20"
effect: ALLOW
```

```yaml
id: "PERM-4"
name: "调用 VIP 退款接口"
description: "允许调用 VIP 专属退款通道"

action: INVOKE
resource_type: INTERFACE
resource_id: "API-21"
effect: ALLOW
```

```yaml
id: "PERM-10"
name: "禁止删除订单"
description: "禁止直接删除订单实体数据"

action: DELETE
resource_type: ENTITY
resource_id: "ENT-3"
effect: DENY
```

```yaml
id: "PERM-15"
name: "有条件写入退款"
description: "仅当金额 ≤ 50000 时允许写入退款实体"

action: WRITE
resource_type: ENTITY
resource_id: "ENT-5"
effect: ALLOW
conditions:
  - field: "refund.amount"
    operator: "<="
    value: 50000
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `HAS_PERMISSION` | [Role](role.md) |
| 出 → | `ON_RESOURCE` | [Interface](../../contract/interface.md) / [Entity](../../contract/entity.md) |
