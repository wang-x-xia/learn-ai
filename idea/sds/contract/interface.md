# Interface — 接口制品

## 目标

定义模块对外或对内暴露的 API 契约——请求参数、响应结构、错误码、认证方式、限流策略。Interface 是接口层（L4）的核心制品，确保服务间通信有严格的契约保障，消除"我以为你返回的是 X"这类集成问题。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `API-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 接口名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `module_id` | ref | `MOD-\d+` | 所属模块 |
| `protocol` | enum | `HTTP` / `gRPC` / `GraphQL` / `WebSocket` / `EVENT` | 通信协议 |
| `method` | enum | `GET` / `POST` / `PUT` / `DELETE` / `PATCH` | HTTP 方法（仅 `protocol: HTTP`） |
| `path` | string | URL 模式（如 `/api/v1/refunds`） | 端点路径 |
| `version` | string | semver | 接口版本 |
| `idempotent` | boolean | | 是否幂等 |
| `auth` | Auth | 见下方 | 认证要求 |
| `request_fields` | list\<[TypedField](../concepts.md#typedfield)\> | | 请求参数 |
| `response_fields` | list\<[TypedField](../concepts.md#typedfield)\> | | 响应字段 |
| `error_ids` | list\<ref\> | `ERR-\d+` | 可能返回的错误（引用 [Error](error.md)） |
| `role_ids` | list\<ref\> | `ROLE-\d+` | 授权角色——谁可以调用（引用 [Role](../governance/rbac/role.md)，可选） |
| `rate_limit` | RateLimit | | 限流策略（可选） |

---

## 子结构定义

### Auth

| 字段 | 类型 | 约束 |
|------|------|------|
| `required` | boolean | |
| `type` | enum | `NONE` / `API_KEY` / `JWT` / `OAuth2` / `mTLS` |

### RateLimit

| 字段 | 类型 | 约束 |
|------|------|------|
| `requests` | integer | 允许的请求数 |
| `window` | integer | 时间窗口长度 |
| `window_unit` | enum | `SECOND` / `MINUTE` / `HOUR` / `DAY` |

---

## 格式

```yaml
id: "API-020"
name: "创建退款申请"
description: "接收退款请求并创建退款工单"

module_id: "MOD-010"
protocol: HTTP
method: POST
path: "/api/v1/refunds"
version: "1.0.0"
idempotent: true

auth:
  required: true
  type: JWT

request_fields:
  - name: order_id
    type: UUID
    required: true
  - name: reason
    type: ENUM
    required: true
    enum_values: ["DEFECTIVE", "WRONG_ITEM", "NOT_NEEDED", "OTHER"]
  - name: amount
    type: DECIMAL
    required: true

response_fields:
  - name: refund_id
    type: UUID
    required: true
  - name: status
    type: ENUM
    required: true
    enum_values: ["PROCESSING", "REQUIRES_REVIEW"]
  - name: expected_completion
    type: DATETIME
    required: true

error_ids: ["ERR-1", "ERR-5", "ERR-10"]

role_ids: ["ROLE-3"]             # VIP User

rate_limit:
  requests: 10
  window: 1
  window_unit: MINUTE
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `EXPOSES` | [Module](../module.md) |
| 出 → | `USES_TYPE` | [Entity](entity.md) |
| 出 → | `RETURNS` | [Error](error.md) |
| 出 → | `AUTHORIZED_BY` | [Role](../governance/rbac/role.md) |
| 出 → | `TESTED_BY` | [Contract Test](../test/contract-test.md) |
