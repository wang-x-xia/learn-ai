# Pipeline — 流水线制品

## 目标

定义交付流程——从代码提交到生产上线的完整阶段序列、质量关卡、触发条件。Pipeline 是环境与配置域的核心制品，它将 Module、Environment 和 Constraint 串联成可执行的交付链路。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `PIPE-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 流水线名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `trigger` | enum | 见下方 | 触发方式 |
| `stages` | list\<Stage\> | ≥ 1 个 | 阶段序列 |
| `build_module_ids` | list\<ref\> | `MOD-\d+` | 构建的模块列表 |
| `deploy_to_env_id` | ref | `ENV-\d+` | 部署目标环境（引用 [Environment](environment.md)） |
| `gate_constraint_ids` | list\<ref\> | `CON-\d+` | 质量关卡（引用 [Constraint](../governance/constraint.md)） |

### trigger 枚举

| 值 | 含义 |
|----|------|
| `ON_COMMIT` | 每次提交触发 |
| `ON_PR` | PR 创建/更新时触发 |
| `ON_TAG` | Git tag 推送时触发 |
| `MANUAL` | 手动触发 |
| `SCHEDULED` | 定时触发（cron） |

---

## 子结构定义

### Stage

| 字段 | 类型 | 约束 |
|------|------|------|
| `name` | string | 阶段名称 |
| `type` | enum | `BUILD` / `TEST` / `DEPLOY` / `VERIFY` |
| `allow_failure` | boolean | 默认 `false` |
| `parallel` | boolean | 默认 `false` |

---

## 格式

```yaml
id: "PIPE-1"
name: "Production Deployment"
description: "生产环境部署流水线"

trigger: ON_TAG
build_module_ids:
  - "MOD-1"    # UserService
  - "MOD-2"    # OrderService

deploy_to_env_id: "ENV-1"     # Production CN

gate_constraint_ids:
  - "CON-1"   # 测试覆盖率 >= 80%
  - "CON-2"   # 安全扫描无高危漏洞
  - "CON-3"   # 性能回归 < 5%

stages:
  - name: "Build"
    type: BUILD
    parallel: false

  - name: "Test"
    type: TEST
    parallel: true

  - name: "Security Scan"
    type: VERIFY
    allow_failure: false

  - name: "Deploy to Production"
    type: DEPLOY
    parallel: false
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `BUILDS` | [Module](../module.md) |
| 出 → | `DEPLOYS_TO` | [Environment](environment.md) |
| 出 → | `GATES_ON` | [Constraint](../governance/constraint.md) |
