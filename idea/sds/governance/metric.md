# Metric — 度量指标

## 目标

定义系统中可量化的度量指标——标识符、单位、聚合方式、优化方向。Metric 是 Constraint 和 Benchmark 共享的度量目录，确保"P99 延迟"在所有约束和基准测试中的定义一致，消除 `latency_p99` vs `p99_latency` 的不一致。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `MET-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 指标名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `metric_key` | string | snake_case | 唯一度量标识（如 `latency_p99`） |
| `unit` | enum | 见下方 | 度量单位 |
| `direction` | enum | `LOWER_IS_BETTER` / `HIGHER_IS_BETTER` | 优化方向 |
| `aggregation` | enum | 见下方 | 默认聚合方式 |

### unit 枚举

`ms` / `s` / `req_per_sec` / `MB` / `GB` / `percent` / `count`

### aggregation 枚举

`P50` / `P95` / `P99` / `AVERAGE` / `MAX` / `MIN` / `SUM` / `COUNT`

---

## 格式

```yaml
id: "MET-1"
name: "P99 延迟"
description: "第 99 百分位请求处理延迟"

metric_key: "latency_p99"
unit: ms
direction: LOWER_IS_BETTER
aggregation: P99
```

```yaml
id: "MET-2"
name: "错误率"
description: "5xx 响应占总请求的比例"

metric_key: "error_rate"
unit: percent
direction: LOWER_IS_BETTER
aggregation: AVERAGE
```

```yaml
id: "MET-3"
name: "幂等性"
description: "接口是否保证幂等（1 = 是，0 = 否）"

metric_key: "idempotent"
unit: count
direction: HIGHER_IS_BETTER
aggregation: MIN
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `MEASURES` | [Constraint](constraint.md)、[Benchmark](../test/benchmark.md) |
