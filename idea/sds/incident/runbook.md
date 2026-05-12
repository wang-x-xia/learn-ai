# Runbook — 运维手册制品

## 目标

定义标准化操作步骤——常见运维任务的执行流程。Runbook 是故障域的操作指南制品，它记录日常运维和故障处理的标准化步骤，确保操作的一致性和可重复性。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `RB-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 手册名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 手册类型 |
| `owner_module_id` | ref | `MOD-\d+` | 归属模块 |
| `prerequisites` | list\<string\> | | 前置条件 |
| `steps` | list\<Step\> | ≥ 1 条 | 操作步骤 |
| `rollback_steps` | list\<Step\> | | 回滚步骤（可选） |
| `verification_steps` | list\<Step\> | | 验证步骤（可选） |
| `estimated_duration` | string | 时长（如 `10m`、`1h`） | 预计执行时间 |
| `risk_level` | enum | 见下方 | 风险等级 |

### type 枚举

| 值 | 含义 |
|----|------|
| `TROUBLESHOOTING` | 故障排查 |
| `MAINTENANCE` | 日常维护 |
| `DEPLOYMENT` | 部署操作 |
| `RECOVERY` | 恢复操作 |
| `DIAGNOSTIC` | 诊断操作 |

### risk_level 枚举

| 值 | 含义 |
|----|------|
| `HIGH` | 高风险——可能影响生产 |
| `MEDIUM` | 中风险——需要谨慎操作 |
| `LOW` | 低风险——常规操作 |

---

## 子结构定义

### Step

| 字段 | 类型 | 约束 |
|------|------|------|
| `order` | integer | 步骤序号（从 1 开始） |
| `action` | string | 操作描述 |
| `command` | string | 执行命令（可选） |
| `expected_result` | string | 预期结果（可选） |
| `verification_method` | string | 验证方法（可选） |

---

## 格式

```yaml
id: "RB-1"
name: "Database Connection Pool Recovery"
description: "数据库连接池耗尽时的恢复操作"

type: RECOVERY
owner_module_id: "MOD-2"    # OrderService

prerequisites:
  - "拥有数据库管理员权限"
  - "确认当前无正在进行的长事务"

steps:
  - order: 1
    action: "检查当前连接池使用情况"
    command: "SHOW STATUS LIKE 'Threads_connected'"
    expected_result: "显示当前连接数"

  - order: 2
    action: "识别并终止长时间运行的查询"
    command: "SHOW PROCESSLIST"
    verification_method: "手动检查执行时间超过 300s 的查询"

  - order: 3
    action: "终止异常查询"
    command: "KILL <query_id>"

  - order: 4
    action: "重启应用服务以释放连接"
    command: "systemctl restart order-service"

  - order: 5
    action: "监控连接池恢复情况"
    command: "curl http://localhost:8080/metrics/db-pool"
    verification_method: "等待使用率降至 80% 以下"

rollback_steps:
  - order: 1
    action: "如果重启失败，回滚到上一版本"
    command: "kubectl rollout undo deployment/order-service"

verification_steps:
  - order: 1
    action: "验证服务恢复正常"
    command: "curl http://localhost:8080/health"
    expected_result: "HTTP 200"

estimated_duration: "15m"
risk_level: MEDIUM
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `RESOLVES` | [Incident](incident.md) |
| ← 入 | `MANAGES` | [Module](../module.md) |
