# Error — 错误定义

## 目标

定义系统中的错误类型——业务错误标识、HTTP 状态码、是否可重试、错误分类。Error 是所有 Interface 共享的错误目录，确保同一错误在不同接口上的语义、状态码和重试策略一致，消除"这个接口返回 400、那个接口返回 422"的混乱。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `ERR-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 错误名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `error_key` | string | UPPER_SNAKE_CASE | 唯一业务错误标识 |
| `http_status` | integer | HTTP 状态码 | 默认 HTTP 状态码 |
| `retryable` | boolean | | 客户端是否应重试 |
| `category` | enum | 见下方 | 错误分类 |

### category 枚举

| 值 | 含义 |
|----|------|
| `VALIDATION` | 输入校验失败 |
| `AUTHORIZATION` | 认证 / 授权失败 |
| `RATE_LIMIT` | 限流拒绝 |
| `DEPENDENCY` | 下游依赖故障 |
| `BUSINESS` | 业务规则拒绝 |
| `SYSTEM` | 系统内部错误 |

---

## 格式

```yaml
id: "ERR-1"
name: "无效订单状态"
description: "当前订单状态不允许执行该操作"

error_key: "INVALID_ORDER_STATUS"
http_status: 400
retryable: false
category: VALIDATION
```

```yaml
id: "ERR-5"
name: "退款超频"
description: "用户退款次数超过月度限额"

error_key: "REFUND_LIMIT_EXCEEDED"
http_status: 429
retryable: false
category: RATE_LIMIT
```

```yaml
id: "ERR-10"
name: "支付网关不可用"
description: "第三方支付网关暂时不可用"

error_key: "PAYMENT_GATEWAY_UNAVAILABLE"
http_status: 503
retryable: true
category: DEPENDENCY
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `RETURNS` | [Interface](interface.md) |
