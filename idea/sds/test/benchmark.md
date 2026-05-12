# Benchmark — 基准测试

## 目标

验证 [Constraint](../governance/constraint.md) 中定义的量化指标是否达标——在指定负载和环境下测量实际值并与阈值比较。Benchmark 与 Constraint 一一对应：Constraint 说"不得超过 300ms"，Benchmark 就是那个拿着秒表去量的测试。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `BM-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 用例名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `constraint_id` | ref | `CON-\d+` | 验证的约束 |
| `environment` | enum | 见下方 | 测试环境 |
| `load_profile` | LoadProfile | 见下方 | 负载配置 |
| `metric_id` | ref | `MET-\d+` | 度量指标（引用 [Metric](../governance/metric.md)，应与 Constraint.metric_id 一致） |
| `operator` | enum | 同 [Constraint](../governance/constraint.md) | 比较运算符（应与 Constraint.operator 一致） |
| `threshold` | number | | 阈值（应与 Constraint.threshold 一致） |
| `pass_criteria` | enum | 见下方 | 通过标准 |

### environment 枚举

`DEV` / `STAGING` / `PRODUCTION`

### pass_criteria 枚举

| 值 | 含义 |
|----|------|
| `ALL_SAMPLES` | 所有采样值均满足阈值 |
| `P99` | 第 99 百分位满足阈值 |
| `P95` | 第 95 百分位满足阈值 |
| `AVERAGE` | 平均值满足阈值 |

### LoadProfile

| 字段 | 类型 | 约束 |
|------|------|------|
| `concurrent_users` | integer | 并发用户数 |
| `duration_seconds` | integer | 持续时间（秒） |
| `ramp_up_seconds` | integer | 预热时间（秒） |

---

## 格式

```yaml
id: "BM-1"
name: "退款接口 P99 延迟"
description: "在 100 并发下验证退款接口 P99 延迟不超过 300ms"

constraint_id: "CON-10"
environment: STAGING

load_profile:
  concurrent_users: 100
  duration_seconds: 300
  ramp_up_seconds: 30

metric_id: "MET-1"              # latency_p99
operator: "<="
threshold: 300
pass_criteria: P99
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `TESTED_BY` | [Constraint](../governance/constraint.md) |
