# Configuration — 配置项制品

## 目标

定义系统配置项——键名、类型、默认值、环境覆盖。Configuration 是环境与配置域的基础单元，它声明单个配置项的结构化定义，确保配置的可验证性和可追溯性。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `CONF-\d+` | 唯一标识符 |
| `name` | string | snake_case，≤ 80 字符 | **描述性** — 配置键名 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 配置类型 |
| `default_value` | any | | 默认值（可选） |
| `required` | boolean | 默认 `false` | 是否必填 |
| `sensitive` | boolean | 默认 `false` | 是否敏感（敏感配置应使用 [Secret](secret.md)） |
| `validation` | Validation | | 验证规则（可选） |

### type 枚举

| 值 | 含义 |
|----|------|
| `STRING` | 字符串 |
| `INTEGER` | 整数 |
| `FLOAT` | 浮点数 |
| `BOOLEAN` | 布尔值 |
| `JSON` | JSON 对象 |
| `LIST` | 列表 |
| `ENUM` | 枚举值 |
| `DURATION` | 时长（如 `30s`、`5m`、`1h`） |
| `SIZE` | 大小（如 `100MB`、`1GB`） |

---

## 子结构定义

### Validation

| 字段 | 类型 | 约束 |
|------|------|------|
| `pattern` | string | 正则表达式（仅 `type: STRING`） |
| `min` | number | 最小值（数值类型） |
| `max` | number | 最大值（数值类型） |
| `allowed_values` | list\<any\> | 允许的值列表（仅 `type: ENUM`） |

---

## 格式

```yaml
id: "CONF-1"
name: "database_connection_pool_size"
description: "数据库连接池大小"

type: INTEGER
default_value: 10
required: false
sensitive: false

validation:
  min: 1
  max: 100
```

```yaml
id: "CONF-2"
name: "feature_flag_new_checkout"
description: "新结账流程功能开关"

type: BOOLEAN
default_value: false
required: false
sensitive: false
```

```yaml
id: "CONF-3"
name: "cache_ttl"
description: "缓存过期时间"

type: DURATION
default_value: "5m"
required: false
sensitive: false
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `CONTAINS` | [Config Set](config-set.md) |
