# Requirement — 需求制品

## 目标

承载**严格定义的句子模式**需求。支持结构化的句子格式（如 Given-When-Then-And），每个语义元素对应 Business Concept，驱动架构设计和代码生成。

---

## 字段定义

### 通用字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `REQ-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 简短标题 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话摘要 |
| `source_draft_id` | ref | `DRAFT-\d+` | 来源初稿 |
| `sentence_type` | enum | 见下方 | 句子类型 |
| `done` | boolean | - | 是否完成 |

### sentence_type 枚举

| 值 | 含义 |
|----|------|
| `GWT` | Given-When-Then-And 模式 |
| `EARS` | EARS 模式（预留） |
| `SVO` | 主谓宾模式（预留） |
| `CUSTOM` | 自定义模式（预留） |

### GWT 模式字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `gwt` | object | - | GWT 模式专用字段容器 |
| `gwt.user_story_id` | ref | `US-\d+` | 关联的用户故事（引用 [User Story](user-story.md)） |
| `gwt.actor_concept_id` | ref | `BC-\d+` | 执行者（引用 [Business Concept](business-concept.md)，对应 as_actor） |
| `gwt.condition_concept_ids` | list\<ref\> | `BC-\d+` | 触发条件（引用 Business Concept，对应 as_attribute，支持多个 AND） |
| `gwt.action_concept_id` | ref | `BC-\d+` | 执行动作（引用 Business Concept，对应 as_action） |
| `gwt.result_concept_ids` | list\<ref\> | `BC-\d+` | 执行结果（引用 Business Concept，对应 as_result，支持多个 AND） |

### EARS 模式字段（预留）

### SVO 模式字段（预留）

### CUSTOM 模式字段（预留）

---

## 格式

```yaml
id: "REQ-0078"
name: "VIP用户优先退款"
description: "金卡和钻石卡用户的退款 SLA 从 72h 缩短为 24h"

source_draft_id: "DRAFT-0078"
sentence_type: GWT
done: false

gwt:
  user_story_id: "US-301"
  actor_concept_id: "BC-001"         # VIP用户
  condition_concept_ids:
    - "BC-002"                       # 订单已支付
    - "BC-003"                       # 用户本月退款次数<=3
  action_concept_id: "BC-004"        # 发起退款
  result_concept_ids:
    - "BC-005"                       # 退款状态变为处理中
    - "BC-006"                       # SLA设为24h
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `DISAMBIGUATED_INTO` | [Draft](draft.md) |
| 出 → | `ACTED_BY` | [Business Concept](business-concept.md) |
| 出 → | `MAPPED_TO` | [User Story](user-story.md) |
