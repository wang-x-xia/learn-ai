# Orchestration — 编排制品

## 目标

定义跨模块的 Interface 编排——多个模块的接口按什么顺序调用、失败时如何补偿回滚。Orchestration 是 Interface 的高阶组合器，适用于分布式事务、多步业务流程等需要跨服务协调的场景。

与 [Process](process.md) 的分工：Process 管"单个实体的状态怎么变"，Orchestration 管"多个 Interface 怎么编排"。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `ORCH-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 编排名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `coordinator_module_id` | ref | `MOD-\d+` | 协调者模块——负责驱动整个编排流程 |
| `steps` | list\<Step\> | ≥ 2 步 | 有序编排步骤 |
| `compensation` | enum | `BACKWARD` / `FORWARD_RETRY` | 补偿策略 |
| `max_retries` | integer | ≥ 0 | 单步最大重试次数 |
| `global_timeout` | duration | 如 `30s`、`5m` | 整体超时 |

### compensation 枚举

| 值 | 含义 |
|----|------|
| `BACKWARD` | 逆序补偿——失败时按反向顺序依次调用已完成步骤的补偿接口 |
| `FORWARD_RETRY` | 前向重试——失败时重试当前步骤（要求步骤幂等） |

---

## 子结构定义

### Step

| 字段 | 类型 | 约束 |
|------|------|------|
| `order` | integer | 步骤序号（从 1 开始，相同序号表示可并行） |
| `module_id` | ref | `MOD-\d+` — 参与者模块 |
| `forward_id` | ref | `API-\d+` — 正向动作接口（引用 [Interface](../contract/interface.md)） |
| `compensate_id` | ref | `API-\d+` — 补偿动作接口（引用 [Interface](../contract/interface.md)，可选） |
| `timeout` | duration | 单步超时（如 `5s`、`10s`） |

---

## 格式

```yaml
id: "ORCH-1"
name: "OrderCreation"
description: "订单创建的分布式事务——订单、支付、库存三步编排"

coordinator_module_id: "MOD-5"

steps:
  - order: 1
    module_id: "MOD-5"             # OrderService
    forward_id: "API-30"           # 创建订单（PENDING）
    compensate_id: "API-31"        # 取消订单
    timeout: "5s"

  - order: 2
    module_id: "MOD-3"             # PaymentService
    forward_id: "API-32"           # 扣款
    compensate_id: "API-33"        # 退款
    timeout: "10s"

  - order: 3
    module_id: "MOD-7"             # InventoryService
    forward_id: "API-34"           # 扣减库存
    compensate_id: "API-35"        # 恢复库存
    timeout: "5s"

compensation: BACKWARD
max_retries: 3
global_timeout: "30s"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `COORDINATES` | [Module](../module.md)（参与者模块） |
| 出 → | `COMPOSES` | [Interface](../contract/interface.md)（正向 / 补偿接口） |
| 出 → | `TESTED_BY` | [Integration Test](../test/integration-test.md) |
