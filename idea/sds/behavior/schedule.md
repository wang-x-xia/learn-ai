# Schedule — 定时任务

## 目标

定义按时间规则周期性执行的系统操作——cron 表达式或固定间隔触发，由指定模块负责执行。Schedule 适用于定期结算、健康检查、数据清理等不依赖外部事件的场景。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `SCH-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 任务名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `owner_module_id` | ref | `MOD-\d+` | 负责执行的模块 |
| `target_entity_id` | ref | `ENT-\d+` | 操作的目标实体（可选） |
| `cron` | string | UNIX cron 表达式（如 `0 2 * * *`） | 定时规则（与 `interval` 互斥） |
| `interval` | duration | 如 `30m`、`6h` | 固定间隔（与 `cron` 互斥） |
| `timezone` | string | IANA 时区（如 `Asia/Shanghai`） | 执行时区（仅 `cron` 时需要） |

---

## 格式

```yaml
id: "SCH-1"
name: "DailySettlement"
description: "每日凌晨 2 点执行商户结算"

owner_module_id: "MOD-12"
target_entity_id: "ENT-7"
cron: "0 2 * * *"
timezone: "Asia/Shanghai"
```

```yaml
id: "SCH-2"
name: "HealthCheck"
description: "每 30 秒检查支付网关可用性"

owner_module_id: "MOD-3"
interval: "30s"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `OWNS` | [Module](../module.md) |
| 出 → | `TARGETS` | [Entity](../contract/entity.md) |
