# Contract Test — 契约测试

## 目标

验证 [Interface](../contract/interface.md) 的输入 / 输出契约——请求参数是否被正确校验、响应结构是否符合定义、错误码是否如约返回。Contract Test 是服务间集成的安全网，防止"我以为你返回的是 X"。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `CT-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 用例名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `interface_id` | ref | `API-\d+` | 验证的接口 |
| `tags` | list\<enum\> | 见下方 | 分类标签 |
| `request_input` | list\<[TypedField](../concepts.md#typedfield)\> | | 请求参数（带测试值 `value`） |
| `expected_status` | integer | HTTP 状态码 | 预期 HTTP 状态码 |
| `expected_response` | list\<[Assertion](../concepts.md#assertion)\> | | 预期响应断言 |
| `expected_error_id` | ref | `ERR-\d+` | 预期错误（可选，错误场景时，引用 [Error](../contract/error.md)） |

### tags 枚举

`HAPPY_PATH` / `INVALID_INPUT` / `AUTH_FAILURE` / `RATE_LIMIT` / `ERROR_CODE`

---

## 格式

```yaml
id: "CT-1"
name: "创建退款 — 正常请求"
description: "验证合法的退款请求返回 PROCESSING 状态"

interface_id: "API-20"
tags: [HAPPY_PATH]

request_input:
  - name: order_id
    type: UUID
    value: "test-order-001"
  - name: reason
    type: ENUM
    value: "DEFECTIVE"
  - name: amount
    type: DECIMAL
    value: 199.00

expected_status: 200

expected_response:
  - field: "refund_id"
    operator: NOT_NULL
  - field: "status"
    operator: "=="
    expected: "PROCESSING"
```

```yaml
id: "CT-2"
name: "创建退款 — 超频限流"
description: "超过限流阈值时返回 429 和 REFUND_LIMIT_EXCEEDED"

interface_id: "API-20"
tags: [RATE_LIMIT, ERROR_CODE]

request_input:
  - name: order_id
    type: UUID
    value: "test-order-overflow"
  - name: reason
    type: ENUM
    value: "NOT_NEEDED"
  - name: amount
    type: DECIMAL
    value: 50.00

expected_status: 429
expected_response: []
expected_error_id: "ERR-5"       # REFUND_LIMIT_EXCEEDED
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `TESTED_BY` | [Interface](../contract/interface.md) |
