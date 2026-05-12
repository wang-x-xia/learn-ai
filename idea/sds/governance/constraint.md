# Constraint — 约束制品

## 目标

定义系统中可量化、可验证的规则和限制——性能边界、安全策略、合规要求、架构红线。每条 Constraint 都必须有明确的度量指标、比较运算符和阈值，做到"是否违反"可以被程序自动判定。Constraint 是约束层（L6）的核心制品。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `CON-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 约束名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 约束类别 |
| `scope` | enum | 见下方 | 作用范围 |
| `target_id` | ref | 任意制品 ID | 约束对象 |
| `metric_id` | ref | `MET-\d+` | 度量指标（引用 [Metric](metric.md)） |
| `operator` | enum | `<=` / `>=` / `==` / `!=` / `IN` / `NOT_IN` | 比较运算符 |
| `threshold` | number | | 阈值 |
| `enforcement` | enum | 见下方 | 执行强度 |
| `violation_action` | enum | 见下方 | 违反时的处理 |

### type 枚举

| 值 | 含义 |
|----|------|
| `PERFORMANCE` | 性能约束（延迟、吞吐、资源使用） |
| `SECURITY` | 安全约束（认证、加密、访问控制） |
| `COMPLIANCE` | 合规约束（数据保留、审计、隐私） |
| `ARCHITECTURE` | 架构约束（依赖方向、技术选型、部署拓扑） |
| `BUSINESS` | 业务约束（金额上限、操作频率、SLA） |
| `DATA_INTEGRITY` | 数据完整性约束（一致性、唯一性、引用完整性） |

### scope 枚举

| 值 | 含义 |
|----|------|
| `SYSTEM` | 全系统级 |
| `SERVICE` | 单个服务 / 模块级 |
| `ENDPOINT` | 单个接口级 |
| `ENTITY` | 单个实体级 |
| `FIELD` | 单个字段级 |

### enforcement 枚举

| 值 | 含义 |
|----|------|
| `HARD_BLOCK` | 强制阻断——违反时系统拒绝操作 |
| `SOFT_WARN` | 软告警——违反时发出警告但不阻断 |
| `AUDIT_LOG` | 仅记录——违反时写入审计日志 |

### violation_action 枚举

| 值 | 含义 |
|----|------|
| `REJECT` | 拒绝请求 |
| `ALERT` | 触发告警通知 |
| `ESCALATE` | 升级到人工处理 |
| `LOG` | 仅写日志 |
| `CIRCUIT_BREAK` | 触发熔断 |

---

## 格式

```yaml
id: "CON-010"
name: "退款接口延迟上限"
description: "退款接口 P99 延迟不超过 300ms"

type: PERFORMANCE
scope: ENDPOINT
target_id: "API-020"
metric_id: "MET-1"              # P99 延迟 (unit: ms)
operator: "<="
threshold: 300
enforcement: HARD_BLOCK
violation_action: ALERT
```

```yaml
id: "CON-011"
name: "退款幂等性"
description: "退款接口必须保证幂等"

type: ARCHITECTURE
scope: ENDPOINT
target_id: "API-020"
metric_id: "MET-3"              # 幂等性 (unit: count)
operator: "=="
threshold: 1
enforcement: HARD_BLOCK
violation_action: REJECT
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `CONSTRAINED_BY` | 任意制品（[Module](../module.md)、[Interface](../contract/interface.md)、[Entity](../contract/entity.md) 等） |
| 出 → | `MEASURES` | [Metric](metric.md) |
| 出 → | `TESTED_BY` | [Benchmark](../test/benchmark.md) |
