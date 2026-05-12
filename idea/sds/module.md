# Module — 模块制品

## 目标

定义系统的组织单元——按服务边界将制品分组，声明模块间依赖，并将制品映射到具体的代码实现。Module 类似文件夹，负责回答三个问题：

1. **这个模块管哪些制品？**（契约域 + 行为域的制品归属）
2. **这个模块依赖谁？**（模块间运行时依赖）
3. **这些制品对应哪些代码？**（制品到源码的追溯）

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `MOD-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 服务 / 模块名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话职责说明 |
| `type` | enum | 见下方 | 模块类型 |
| `version` | string | semver（如 `2.1.0`） | 当前版本 |
| `owner` | string | 团队 / 人员 ID | 负责人 |
| `status` | enum | 见下方 | 生命周期状态 |
| `dependencies` | list\<Dependency\> | | 依赖的其他模块 |
| `entities` | list\<EntityAccess\> | | 操作的数据实体 |
| `interface_ids` | list\<ref\> | `API-\d+` | 暴露的接口 |
| `process_ids` | list\<ref\> | `PROC-\d+` | 关联的流程 |
| `constraint_ids` | list\<ref\> | `CON-\d+` | 关联的约束 |
| `code_refs` | list\<[CodeRef](#coderef)\> | | 制品到源码的映射 |

### type 枚举

| 值 | 含义 |
|----|------|
| `MICROSERVICE` | 独立部署的微服务 |
| `LIBRARY` | 共享库 / SDK |
| `FUNCTION` | 无状态函数（FaaS） |
| `GATEWAY` | API 网关 / BFF |
| `WORKER` | 后台异步任务处理器 |
| `SCHEDULER` | 定时任务调度器 |

### status 枚举

| 值 | 含义 |
|----|------|
| `DESIGN` | 设计中 |
| `DEVELOPMENT` | 开发中 |
| `ACTIVE` | 已上线 |
| `DEPRECATED` | 已废弃（仍运行） |
| `RETIRED` | 已下线 |

---

## 子结构定义

### Dependency

| 字段 | 类型 | 约束 |
|------|------|------|
| `module_id` | ref | `MOD-\d+` |
| `protocol` | enum | `gRPC` / `HTTP` / `EVENT` / `SDK` / `DB_SHARED` |
| `required` | boolean | `true` = 强依赖（不可降级），`false` = 弱依赖 |

### EntityAccess

| 字段 | 类型 | 约束 |
|------|------|------|
| `entity_id` | ref | `ENT-\d+` |
| `access` | enum | `READ` / `WRITE` / `READ_WRITE` |

### CodeRef

将一个制品映射到其源码实现位置。

| 字段 | 类型 | 约束 |
|------|------|------|
| `artifact_id` | ref | 契约域或行为域制品 ID（`API-\d+` / `ENT-\d+` / `EVT-\d+` / `ERR-\d+` / `PROC-\d+` / `ORCH-\d+` / `SUB-\d+` / `SCH-\d+`） |
| `path` | string | 源代码文件路径（相对于仓库根目录） |
| `symbol` | string | 导出符号名（类名 / 函数名 / 常量名） |

---

## 格式

```yaml
id: "MOD-010"
name: "RefundService"
description: "处理退款申请的核心服务，包含 SLA 计算与审核流程"

type: MICROSERVICE
version: "2.1.0"
owner: "payments-team"
status: ACTIVE

dependencies:
  - module_id: "MOD-003"
    protocol: gRPC
    required: true
  - module_id: "MOD-011"
    protocol: HTTP
    required: true

entities:
  - entity_id: "ENT-003"
    access: READ_WRITE
  - entity_id: "ENT-001"
    access: READ

interface_ids: ["API-020", "API-021"]
process_ids: ["PROC-005"]
constraint_ids: ["CON-010", "CON-011"]

code_refs:
  - artifact_id: "API-020"
    path: "src/refund/handlers/create_refund.ts"
    symbol: "CreateRefundHandler"

  - artifact_id: "API-021"
    path: "src/refund/handlers/approve_refund.ts"
    symbol: "ApproveRefundHandler"

  - artifact_id: "ENT-003"
    path: "src/refund/models/order.ts"
    symbol: "Order"

  - artifact_id: "PROC-005"
    path: "src/refund/machines/refund_lifecycle.ts"
    symbol: "RefundLifecycleMachine"

  - artifact_id: "SUB-2"
    path: "src/refund/subscribers/on_refund_success.ts"
    symbol: "OnRefundSuccessHandler"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 ↔ | `DEPENDS_ON` | [Module](module.md)（自引用） |
| 出 → | `TESTED_BY` | [Integration Test](test/integration-test.md) |
