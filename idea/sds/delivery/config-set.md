# Config Set — 配置集合制品

## 目标

定义配置集合——按环境或模块分组的配置项集合及其覆盖值。Config Set 是环境与配置域的组织单元，它将多个 Configuration 聚合成可部署的配置包，支持环境级覆盖。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `CSET-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 配置集合名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `scope` | enum | 见下方 | 作用范围 |
| `target_id` | ref | `ENV-\d+` / `MOD-\d+` | 目标环境或模块 |
| `config_overrides` | list\<ConfigOverride\> | ≥ 1 条 | 配置覆盖列表 |

### scope 枚举

| 值 | 含义 |
|----|------|
| `ENVIRONMENT` | 环境级配置（引用 [Environment](environment.md)） |
| `MODULE` | 模块级配置（引用 [Module](../module.md)） |

---

## 子结构定义

### ConfigOverride

| 字段 | 类型 | 约束 |
|------|------|------|
| `config_id` | ref | `CONF-\d+`（引用 [Configuration](configuration.md)） |
| `value` | any | 覆盖值（必须符合配置项的类型约束） |

---

## 格式

```yaml
id: "CSET-1"
name: "Production Config"
description: "生产环境配置集合"

scope: ENVIRONMENT
target_id: "ENV-1"    # Production CN

config_overrides:
  - config_id: "CONF-1"
    value: 50         # 生产环境连接池大小为 50
  - config_id: "CONF-2"
    value: true      # 生产环境启用新结账流程
  - config_id: "CONF-3"
    value: "10m"     # 生产环境缓存过期时间为 10 分钟
```

```yaml
id: "CSET-2"
name: "OrderService Config"
description: "订单服务模块配置"

scope: MODULE
target_id: "MOD-2"    # OrderService

config_overrides:
  - config_id: "CONF-1"
    value: 20         # 订单服务连接池大小为 20
  - config_id: "CONF-3"
    value: "2m"       # 订单服务缓存过期时间为 2 分钟
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `APPLIES_TO` | [Environment](environment.md) / [Module](../module.md) |
| 出 → | `OVERRIDES` | [Configuration](configuration.md) |
