# Incident — 故障定义制品

## 目标

定义故障——故障类型、影响范围、处理流程。Incident 是故障域的核心制品，它记录已知故障的标准化定义，确保故障处理的一致性和可追溯性。

每个 Incident 归属于一个 Module（`owner_module_id`），用于描述该模块可能出现的故障场景。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `INC-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 故障名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 故障类型 |
| `severity` | enum | 见下方 | 严重程度 |
| `owner_module_id` | ref | `MOD-\d+` | 归属模块 |
| `affected_entity_ids` | list\<ref\> | `ENT-\d+` | 受影响的实体 |
| `symptoms` | list\<string\> | ≥ 1 条 | 故障症状（可观测的表现） |
| `detection_method` | enum | 见下方 | 检测方式 |
| `runbook_id` | ref | `RB-\d+` | 处理手册（引用 [Runbook](runbook.md)） |
| `playbook_id` | ref | `PB-\d+` | 应急预案（引用 [Playbook](playbook.md)，可选） |

### type 枚举

| 值 | 含义 |
|----|------|
| `SERVICE_DOWN` | 服务不可用 |
| `PERFORMANCE_DEGRADATION` | 性能下降 |
| `DATA_INCONSISTENCY` | 数据不一致 |
| `RESOURCE_EXHAUSTION` | 资源耗尽 |
| `DEPENDENCY_FAILURE` | 依赖服务故障 |
| `DATA_LOSS` | 数据丢失 |
| `SECURITY_BREACH` | 安全漏洞 |

### severity 枚举

| 值 | 含义 |
|----|------|
| `CRITICAL` | 严重——核心业务不可用 |
| `HIGH` | 高——重要功能受损 |
| `MEDIUM` | 中——部分功能受限 |
| `LOW` | 低——轻微影响 |

### detection_method 枚举

| 值 | 含义 |
|----|------|
| `ALERT` | 告警触发 |
| `USER_REPORT` | 用户报告 |
| `MONITORING` | 监控发现 |
| `AUDIT` | 审计发现 |

---

## 格式

```yaml
id: "INC-1"
name: "Database Connection Pool Exhaustion"
description: "数据库连接池耗尽导致新请求无法获取连接"

type: RESOURCE_EXHAUSTION
severity: HIGH
owner_module_id: "MOD-2"    # OrderService

affected_entity_ids:
  - "ENT-3"    # Order

symptoms:
  - "API 响应时间 > 5s"
  - "错误日志中出现 'Connection timeout'"
  - "监控显示连接池使用率 100%"

detection_method: ALERT
runbook_id: "RB-1"
playbook_id: "PB-1"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `MANAGES` | [Module](../module.md) |
| 出 → | `AFFECTS` | [Entity](../contract/entity.md) |
| 出 → | `RESOLVED_BY` | [Runbook](runbook.md) |
| 出 → | `EMERGENCY_PLAN` | [Playbook](playbook.md) |
