# Draft — 需求初稿

## 目标

捕获人类原始的、非结构化的意图。Draft 是整个制品体系的**唯一**非结构化入口点——它不直接驱动任何下游工程行为，必须经过消歧引擎转化为 [Requirement](requirement.md) 后才可进入开发流程。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `DRAFT-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 简短标题 |
| `description` | string | 自由文本 | **描述性** — 原始自然语言输入 |
| `author` | string | 团队成员 ID | 提交人 |
| `created_at` | datetime | ISO 8601 | 创建时间 |
| `status` | enum | 见下方 | 生命周期状态 |

### status 枚举

| 值 | 含义 |
|----|------|
| `PENDING` | 等待消歧 |
| `DISAMBIGUATING` | 正在消歧中 |
| `RESOLVED` | 已转化为 Requirement |
| `REJECTED` | 被驳回（不可行 / 重复） |

---

## 格式

```yaml
id: "DRAFT-0078"
name: "VIP退款优先处理"
description: "VIP用户可以优先退款"
author: "zhangsan"
created_at: "2026-01-15T10:30:00+08:00"
status: PENDING
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `DISAMBIGUATED_INTO` | [Requirement](requirement.md) |
