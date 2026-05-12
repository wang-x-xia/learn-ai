# Scenario Test — 场景测试

## 目标

验证 [User Story](../requirement/user-story.md) 的单条验收条件。每个 Scenario Test 对应一个 Given / When / Then 切片，是最小粒度的行为验证单元。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `ST-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 用例名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `user_story_id` | ref | `US-\d+` | 验证的用户故事 |
| `criterion_index` | integer | ≥ 0 | 对应 `acceptance_criteria` 的索引 |
| `tags` | list\<enum\> | 见下方 | 分类标签 |
| `given` | list\<[Condition](../concepts.md#condition)\> | | 前置条件 |
| `when` | ref | `API-\d+` / `SUB-\d+` / `SCH-\d+`（引用 [Interface](../contract/interface.md)、[Reaction](../behavior/reaction.md) 或 [Schedule](../behavior/schedule.md)） | 触发动作 |
| `then` | list\<[Assertion](../concepts.md#assertion)\> | ≥ 1 条 | 预期结果 |

### tags 枚举

`HAPPY_PATH` / `EDGE_CASE` / `ERROR_HANDLING` / `BOUNDARY` / `REGRESSION`

---

## 格式

```yaml
id: "ST-1"
name: "金卡用户退款获得 24h SLA"
description: "验证金卡用户发起退款时系统分配 24h SLA"

user_story_id: "US-301"
criterion_index: 0
tags: [HAPPY_PATH]

given:
  - field: "user.membership_level"
    operator: IN
    values: ["GOLD", "DIAMOND"]

when: "API-20"                    # 创建退款申请

then:
  - field: "refund.sla"
    operator: "=="
    expected: "24h"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `TESTED_BY` | [User Story](../requirement/user-story.md) |
