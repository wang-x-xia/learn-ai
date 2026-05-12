# Entity — 数据实体

## 目标

定义系统中的数据实体——字段、类型、索引、约束。Entity 是数据层（L3）的核心制品，其 `fields` + `constraints` 本身就是数据合法性的完备定义（**定义即约束，无需额外的数据测试制品**）。对数据行为的验证（如"提交负数金额会怎样"）由上层 [Scenario Test](../test/scenario-test.md) 在用户动作上下文中覆盖。

每个 Entity 归属于一个 Module（`owner_module_id`）。当多个模块需要同一现实概念时，各模块定义自己的投影实体，通过 `projects_from_id` 指向主实体，只包含本模块所需的字段子集。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `ENT-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 实体名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | DDD 分类 |
| `owner_module_id` | ref | `MOD-\d+` | 权威所有者模块（唯一写入者） |
| `projects_from_id` | ref | `ENT-\d+` | 投影来源（可选，主实体不填） |
| `fields` | list\<Field\> | ≥ 1 条 | 字段列表 |
| `indexes` | list\<Index\> | | 索引列表 |
| `constraints` | list\<TableConstraint\> | | 表级约束 |

### type 枚举

| 值 | 含义 |
|----|------|
| `AGGREGATE_ROOT` | 聚合根——事务和一致性的边界 |
| `ENTITY` | 普通实体——有独立 ID，从属于聚合根 |
| `VALUE_OBJECT` | 值对象——无独立 ID，不可变 |
| `ENUM_TABLE` | 枚举表——存储系统级枚举值 |

---

## 子结构定义

### Field

| 字段 | 类型 | 约束 |
|------|------|------|
| `name` | string | snake_case |
| `type` | enum | `UUID` / `STRING` / `INTEGER` / `DECIMAL` / `BOOLEAN` / `DATETIME` / `ENUM` / `JSON` / `REF` |
| `required` | boolean | |
| `primary_key` | boolean | 默认 `false` |
| `foreign_key` | ref | 格式 `ENT-XXX.field_name`（可选） |
| `enum_values` | list\<string\> | 仅 `type: ENUM` 时 |
| `precision` | integer | 仅 `type: DECIMAL` 时 |
| `default` | any | 默认值（可选） |

### Index

| 字段 | 类型 | 约束 |
|------|------|------|
| `fields` | list\<string\> | 字段名列表 |
| `type` | enum | `BTREE` / `HASH` / `COMPOSITE` / `FULLTEXT` / `GIN` |
| `unique` | boolean | 默认 `false` |

### TableConstraint

| 字段 | 类型 | 约束 |
|------|------|------|
| `type` | enum | `UNIQUE` / `CHECK` / `FOREIGN_KEY` |
| `fields` | list\<string\> | 涉及的字段 |
| `expression` | string | 仅 `CHECK` 时，SQL 表达式（如 `total_amount >= 0`） |

---

## 格式

```yaml
id: "ENT-3"
name: "Order"
description: "订单实体，记录用户购买行为的完整生命周期"

type: AGGREGATE_ROOT
owner_module_id: "MOD-5"     # OrderService

fields:
  - name: order_id
    type: UUID
    required: true
    primary_key: true
  - name: user_id
    type: UUID
    required: true
    foreign_key: "ENT-001.user_id"
  - name: total_amount
    type: DECIMAL
    required: true
    precision: 2
  - name: status
    type: ENUM
    required: true
    enum_values: ["CREATED", "PAID", "SHIPPED", "DELIVERED", "COMPLETED", "CLOSED", "CANCELLED"]
  - name: created_at
    type: DATETIME
    required: true
    default: "NOW()"

indexes:
  - fields: [user_id]
    type: BTREE
    unique: false
  - fields: [status, created_at]
    type: COMPOSITE
    unique: false

constraints:
  - type: UNIQUE
    fields: [order_id]
  - type: CHECK
    fields: [total_amount]
    expression: "total_amount >= 0"
```

### 投影实体示例

NotificationService 只需要订单 ID 和用户 ID，不需要金额和状态细节：

```yaml
id: "ENT-30"
name: "NotifOrder"
description: "通知服务的订单投影——仅包含发送通知所需的最少字段"

type: ENTITY
owner_module_id: "MOD-8"     # NotificationService
projects_from_id: "ENT-3"    # 投影自主实体 Order

fields:
  - name: order_id
    type: UUID
    required: true
    primary_key: true
  - name: user_id
    type: UUID
    required: true
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `PROJECTS_FROM` | [Entity](entity.md)（投影实体 → 主实体） |
| ← 入 | `READS` / `WRITES` | [Module](../module.md) |
| ← 入 | `USES_TYPE` | [Interface](interface.md) |
| ← 入 | `TRANSITIONS` | [Process](../behavior/process.md) |
