# Integration Test — 集成测试

## 目标

验证 [Module](../module.md) 之间的交互是否符合预期——依赖协议是否正确、失败场景下的降级行为是否生效。每个 Integration Test 聚焦一对模块之间的一种调用场景。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `IT-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 用例名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `source_module_id` | ref | `MOD-\d+` | 发起调用的模块 |
| `target_module_id` | ref | `MOD-\d+` | 被调用的模块 |
| `protocol` | enum | `gRPC` / `HTTP` / `EVENT` / `SDK` / `DB_SHARED` | 通信协议 |
| `tags` | list\<enum\> | 见下方 | 分类标签 |
| `request` | list\<[TypedField](../concepts.md#typedfield)\> | | 请求参数（带测试值 `value`） |
| `expected_response` | list\<[Assertion](../concepts.md#assertion)\> | | 预期响应断言 |
| `failure_mode` | enum | 见下方 | 注入的故障模式 |
| `expected_fallback` | enum | 见下方 | 预期降级行为 |

### tags 枚举

`HAPPY_PATH` / `TIMEOUT` / `ERROR` / `CIRCUIT_BREAK` / `FALLBACK`

### failure_mode 枚举

| 值 | 含义 |
|----|------|
| `NONE` | 正常路径，不注入故障 |
| `TIMEOUT` | 模拟超时 |
| `ERROR_5XX` | 模拟服务端错误 |
| `UNAVAILABLE` | 模拟服务不可用 |
| `RATE_LIMITED` | 模拟被限流 |

### expected_fallback 枚举

| 值 | 含义 |
|----|------|
| `NONE` | 正常路径，无降级 |
| `RETRY` | 自动重试 |
| `CIRCUIT_BREAK` | 触发熔断 |
| `DEGRADE` | 降级为默认值 |
| `FAIL_FAST` | 快速失败并返回错误 |

---

## 格式

```yaml
id: "IT-1"
name: "RefundService 调用 VIPEngine 正常路径"
description: "验证退款服务成功调用 VIP 引擎获取用户等级"

source_module_id: "MOD-10"
target_module_id: "MOD-11"
protocol: HTTP
tags: [HAPPY_PATH]

request:
  - name: user_id
    type: UUID
    value: "test-user-001"

expected_response:
  - field: "membership_level"
    operator: IN
    expected: ["GOLD", "DIAMOND", "SILVER", "BASIC"]
  - field: "http_status"
    operator: "=="
    expected: 200

failure_mode: NONE
expected_fallback: NONE
```

```yaml
id: "IT-2"
name: "RefundService 调用 VIPEngine 超时降级"
description: "VIP 引擎超时时退款服务应降级为默认 SLA"

source_module_id: "MOD-10"
target_module_id: "MOD-11"
protocol: HTTP
tags: [TIMEOUT, FALLBACK]

request:
  - name: user_id
    type: UUID
    value: "test-user-001"

expected_response: []

failure_mode: TIMEOUT
expected_fallback: DEGRADE
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `TESTED_BY` | [Module](../module.md) |
