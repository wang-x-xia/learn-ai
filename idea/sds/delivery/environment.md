# Environment — 环境制品

## 目标

定义部署环境——类型、地域、访问端点、配置基线。Environment 是环境与配置域的基础制品，它声明代码运行的目标环境，为 Pipeline 提供部署目的地。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `ENV-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 环境名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 环境类型 |
| `region` | string | ISO 3166-2 地区代码 | 部署地域（如 `cn-north-1`） |
| `url` | string | URL 格式 | 访问端点 |
| `config_set_id` | ref | `CSET-\d+` | 配置集合（引用 [Config Set](config-set.md)） |
| `baseline_module_ids` | list\<ref\> | `MOD-\d+` | 基线模块列表（该环境必须部署的模块） |

### type 枚举

| 值 | 含义 |
|----|------|
| `DEVELOPMENT` | 开发环境——本地或共享开发环境 |
| `TESTING` | 测试环境——集成测试、QA 验证 |
| `STAGING` | 预生产环境——生产环境的镜像 |
| `PRODUCTION` | 生产环境——对外服务 |

---

## 格式

```yaml
id: "ENV-1"
name: "Production CN"
description: "中国区生产环境"

type: PRODUCTION
region: "cn-north-1"
url: "https://api.example.com"
config_set_id: "CSET-1"

baseline_module_ids:
  - "MOD-1"    # UserService
  - "MOD-2"    # OrderService
  - "MOD-3"    # PaymentService
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `DEPLOYS_TO` | [Pipeline](pipeline.md) |
| 出 → | `USES_CONFIG` | [Config Set](config-set.md) |
