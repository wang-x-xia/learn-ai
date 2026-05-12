# Playbook — 应急响应预案制品

## 目标

定义应急响应预案——特定故障场景的处置步骤和决策树。Playbook 是故障域的应急预案制品，它针对高风险故障场景提供预先定义的处置流程，包括触发条件、决策分支和升级路径。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `PB-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 预案名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `incident_id` | ref | `INC-\d+` | 关联的故障（引用 [Incident](incident.md)） |
| `owner_module_id` | ref | `MOD-\d+` | 归属模块 |
| `trigger_conditions` | list\<Condition\> | ≥ 1 条 | 触发条件 |
| `response_flow` | ResponseFlow | | 响应流程（决策树） |
| `escalation_policy` | EscalationPolicy | | 升级策略 |
| `communication_plan` | list\<string\> | | 沟通计划（通知对象、内容、渠道） |

---

## 子结构定义

### Condition

| 字段 | 类型 | 约束 |
|------|------|------|
| `metric` | string | 监控指标 |
| `operator` | enum | `>` / `<` / `==` / `>=` / `<=` |
| `threshold` | number | 阈值 |
| `duration` | string | 持续时间（如 `5m`、`10m`） |

### ResponseFlow

| 字段 | 类型 | 约束 |
|------|------|------|
| `steps` | list\<ResponseStep\> | ≥ 1 条 | 响应步骤（支持决策树） |

### ResponseStep

| 字段 | 类型 | 约束 |
|------|------|------|
| `order` | integer | 步骤序号 |
| `condition` | Condition | 触发条件（可选，用于决策分支） |
| `action` | string | 处置动作 |
| `runbook_id` | ref | `RB-\d+`（引用 [Runbook](runbook.md)，可选） |
| `next_step_on_success` | integer | 成功后跳转的步骤序号 |
| `next_step_on_failure` | integer | 失败后跳转的步骤序号 |

### EscalationPolicy

| 字段 | 类型 | 约束 |
|------|------|------|
| `levels` | list\<EscalationLevel\> | ≥ 1 条 | 升级级别 |

### EscalationLevel

| 字段 | 类型 | 约束 |
|------|------|------|
| `level` | integer | 升级级别（1 最高） |
| `trigger_after` | string | 触发时间（如 `15m`、`1h`） |
| `notify_roles` | list\<ref\> | `ROLE-\d+` | 通知的角色 |
| `auto_escalate` | boolean | 是否自动升级 |

---

## 格式

```yaml
id: "PB-1"
name: "Database Connection Pool Exhaustion Response"
description: "数据库连接池耗尽时的应急响应预案"

incident_id: "INC-1"
owner_module_id: "MOD-2"    # OrderService

trigger_conditions:
  - metric: "db_pool_usage_percentage"
    operator: ">"
    threshold: 95
    duration: "5m"

response_flow:
  steps:
    - order: 1
      action: "立即触发告警"
      next_step_on_success: 2
      next_step_on_failure: 5

    - order: 2
      action: "执行 Runbook RB-1 进行恢复"
      runbook_id: "RB-1"
      next_step_on_success: 3
      next_step_on_failure: 4

    - order: 3
      condition:
        metric: "db_pool_usage_percentage"
        operator: "<"
        threshold: 80
      action: "验证恢复成功，关闭告警"
      next_step_on_success: null

    - order: 4
      action: "Runbook 执行失败，进入升级流程"
      next_step_on_success: 5

    - order: 5
      action: "升级到 L2 支持"
      next_step_on_success: null

escalation_policy:
  levels:
    - level: 1
      trigger_after: "15m"
      notify_roles:
        - "ROLE-1"    # On-call Engineer
      auto_escalate: true

    - level: 2
      trigger_after: "30m"
      notify_roles:
        - "ROLE-2"    # Team Lead
        - "ROLE-3"    # DBA
      auto_escalate: true

    - level: 3
      trigger_after: "1h"
      notify_roles:
        - "ROLE-4"    # Engineering Manager
      auto_escalate: false

communication_plan:
  - "通知 On-call 工程师"
  - "在 #incident 频道发布故障公告"
  - "每 15 分钟更新状态"
  - "恢复后发送故障报告"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `HANDLES` | [Incident](incident.md) |
| ← 入 | `MANAGES` | [Module](../module.md) |
| 出 → | `EXECUTES` | [Runbook](runbook.md) |
