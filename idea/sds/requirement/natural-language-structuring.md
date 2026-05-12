# Natural Language Structuring — 自然语言结构化转译

## 目标

定义从非结构化的自然语言需求到完全结构化的 Requirement 制品的转译机制，包括业务概念层、映射类型、语义位置和多映射策略。

---

## 一、背景与动机

### 1.1 问题陈述

当前 SDS 制品体系中：
- **Draft**：完全非结构化的自然语言（人类友好，机器不可读）
- **Requirement**：完全结构化的 YAML/JSON（机器友好，人类难写）

两者之间缺乏中间态，导致：
1. 产品经理难以直接编写结构化需求
2. 消歧过程缺乏渐进式引导
3. 从自然语言到结构化的"语义鸿沟"难以跨越

### 1.2 设计目标

```
非结构化              带约束的自然语言              完全结构化
Draft  -------->  Structured Draft  -------->  Requirement
"VIP用户可以优先退款"   "Given VIP, When 退款, Then SLA=24h"   YAML/JSON
```

**核心原则**：
- 输入：自然语言（人类友好）
- 过程：引导式消歧（系统驱动）
- 输出：严格的结构化制品（机器友好）

---

## 二、主流需求规范模式

### 2.1 EARS (Easy Approach to Requirements Syntax)

由 Rolls-Royce 在 2009 年开发，用于航空发动机控制系统需求规范。

**五种基本模式**：

| 模式 | 语法 | 用途 |
|------|------|------|
| **Ubiquitous** | `The system shall [behavior]` | 始终适用的需求 |
| **Event-Driven** | `When [trigger], the system shall [response]` | 事件驱动的需求 |
| **State-Driven** | `While [state], the system shall [behavior]` | 状态驱动的需求 |
| **Unwanted Behavior** | `If [error condition], then the system shall [recovery action]` | 异常处理 |
| **Optional Feature** | `Where [feature is enabled], the system shall [behavior]` | 可选功能 |

**示例**：
```
# Ubiquitous
The mobile phone shall have a mass of less than 150g.

# Event-Driven
When "mute" is selected, the audio system shall suppress all output.

# State-Driven
While there is no card in the ATM, the ATM shall display "insert card to begin".
```

### 2.2 IREB/Rupp Boilerplates (MASTeR)

国际需求工程委员会标准，**三种基础模板**：

```
# 自主系统活动
THE SYSTEM SHALL/SHOULD/WILL/MAY [verb] [object].

# 用户交互
THE SYSTEM SHALL/SHOULD... [user action] [system response].

# 外部触发
WHEN [external event], THE SYSTEM SHALL [response].
```

### 2.3 Given-When-Then (GWT)

主要用于验收测试和用户故事，**BDD 风格**：

```
Given [precondition]
When [action]
Then [expected outcome]
```

### 2.4 学术参考标准

**PropBank（命题库）**：
- ARG0 = PROTO-AGENT（原型施事者）
- ARG1 = PROTO-PATIENT（原型受事者）
- ARG2-ARG5 = 其他显式参数
- ARGM-XXX = 附加参数（LOC, TMP, MNR, CAU 等）

**FrameNet/VerbNet**：
- Agent, Patient, Theme, Experiencer, Source, Goal, Instrument 等

---

## 三、业务概念层设计

### 3.1 为什么需要业务概念层？

**现实问题**：业务概念与技术概念的不对齐

```
业务概念                    技术概念
VIP会员        →?→    User.role_type IN ('GOLD', 'DIAMOND')
退款单         →?→    Refund 实体 + RefundLineItem 实体
退款SLA        →?→    Refund.expected_completion_time
```

**不对齐的原因**：
1. 一对多：一个业务"订单"可能拆分为多个技术实体
2. 多对一：业务"用户"和"会员"在技术上可能是同一个表
3. 语义漂移：技术重构时，Entity 名称变了，但业务概念不变

### 3.2 业务概念层的设计

```yaml
# BusinessConcept 制品
id: "BC-\d+"
name: string
definition: string

# 针对不同语义位置的映射
artifact_mappings:
  AS_ACTOR:
    primary_target:
      type: ROLE
      artifact_id: "ROLE-3"
    alternative_targets: [...]
    examples: ["VIP用户", "退款服务"]
  
  AS_OBJECT:
    primary_target:
      type: ENTITY
      artifact_id: "ENT-005"
    examples: ["退款单", "订单"]
  
  # ... 其他映射位置
```

### 3.3 渐进式引用策略

| 阶段 | 引用类型 | 示例 |
|------|---------|------|
| **Draft** | 无引用 | "VIP用户可以优先退款" |
| **Structured Draft** | 软引用（自然语言标识） | "Given [actor:VIP会员] When [action:发起退款]" |
| **Requirement** | 强引用（typed ID） | `actor_role_id: "ROLE-3"` |
| **User Story** | 强引用 | `when: "API-20"` |

---

## 四、映射类型设计

### 4.1 基于 SDS 实际制品的映射

根据 SDS 制品体系的实际设计，映射应直接对应到现有制品：

**SDS 现有制品**：
- **治理域**：Role, Permission, Constraint, Dependency
- **契约域**：Entity, Interface, Event, Error
- **行为域**：Process, Orchestration, Reaction, Schedule
- **组织单元**：Module

### 4.2 八个核心映射位置

| 映射位置 | 是否多映射 | 主要目标制品 | 对应 Requirement 字段 |
|---------|-----------|-------------|---------------------|
| **AS_ACTOR** | 否 | Role / Module | `actor_role_id` |
| **AS_OBJECT** | 否 | Entity | `preconditions` / `postconditions` (field 路径) |
| **AS_ACTION** | 是 | Interface / Orchestration / Reaction / Schedule | `traces.modules` (间接) |
| **AS_EVENT** | 否 | Event | `exceptions.trigger_event_id` / `side_effects.trigger_event_id` |
| **AS_ATTRIBUTE** | 否 | Entity.field | `preconditions` / `postconditions` (field 路径) |
| **AS_CONDITION** | 是 | Condition / Constraint / Process Guard / Rule | `preconditions` / `exceptions` |
| **AS_RESULT** | 是 | StateChange / Interface Response / Event / SideEffect | `postconditions` / `side_effects` |
| **AS_ERROR** | 否 | Error | Interface.error_codes |

### 4.3 多映射的必要性

**AS_CONDITION 的多义性**：
```yaml
# 场景 1：字段条件
"Given 金额 > 50000"
→ 映射到: Condition {field: "amount", operator: ">", value: 50000}

# 场景 2：性能约束
"Given 响应时间 < 300ms"
→ 映射到: Constraint {type: PERFORMANCE, metric_id: "MET-1", operator: "<=", threshold: 300}

# 场景 3：状态条件
"Given 订单状态为已支付"
→ 映射到: Process.transition.guard {field: "order.status", operator: "==", value: "PAID"}
```

**AS_RESULT 的多义性**：
```yaml
# 场景 1：状态变迁
"Then 退款状态变为处理中"
→ 映射到: StateChange {field: "refund.status", becomes: "PROCESSING"}

# 场景 2：返回值
"Then 返回退款单ID"
→ 映射到: Interface.outputs {name: "refund_id", type: "UUID"}

# 场景 3：事件触发
"Then 发布退款成功事件"
→ 映射到: Event {id: "EVT-10", name: "RefundSuccessEvent"}
```

---

## 五、Pattern 解析示例

### 5.1 EARS 模式 → SDS 制品

```yaml
parsed_ears:
  pattern: "EVENT_DRIVEN"
  text: "When 退款申请被提交, the system shall 设置退款SLA为24h"
  
  segments:
    - position: "trigger"
      text: "退款申请被提交"
      concept: "BC-CONCEPT-001"
      mapping_target: "AS_EVENT"
      artifact: "EVT-10"
    
    - position: "response"
      text: "设置退款SLA"
      concept: "BC-CONCEPT-001"
      mapping_target: "AS_ACTION"
      artifact: "API-20"
    
    - position: "response_detail"
      text: "退款SLA为24h"
      concept: "BC-CONCEPT-001"
      mapping_target: "AS_ATTRIBUTE"
      artifact: "ENT-005.expected_completion"
```

### 5.2 GWT 模式 → SDS 制品

```yaml
parsed_gwt:
  pattern: "GIVEN_WHEN_THEN"
  text: "Given VIP会员, When 用户发起退款, Then 退款SLA为24h"
  
  segments:
    - position: "given"
      text: "VIP会员"
      concept: "BC-CONCEPT-002"
      mapping_target: "AS_ACTOR"
      artifact: "ROLE-3"
    
    - position: "when"
      text: "用户发起退款"
      concept: "BC-CONCEPT-001"
      mapping_target: "AS_ACTION"
      artifact: "API-20"
    
    - position: "then"
      text: "退款SLA为24h"
      concept: "BC-CONCEPT-001"
      mapping_target: "AS_ATTRIBUTE"
      artifact: "ENT-005.expected_completion"
```

### 5.3 主谓宾模式 → SDS 制品

```yaml
parsed_svo:
  pattern: "SUBJECT_PREDICATE_OBJECT"
  text: "退款服务处理退款单"
  
  segments:
    - position: "subject"
      text: "退款服务"
      concept: "BC-CONCEPT-003"
      mapping_target: "AS_ACTOR"
      artifact: "MOD-010"
    
    - position: "predicate"
      text: "处理"
      concept: "BC-CONCEPT-001"
      mapping_target: "AS_ACTION"
      artifact: "API-20"
    
    - position: "object"
      text: "退款单"
      concept: "BC-CONCEPT-001"
      mapping_target: "AS_OBJECT"
      artifact: "ENT-005"
```

---

## 六、消歧引擎的映射选择策略

### 6.1 上下文感知的映射选择

```yaml
mapping_selection:
  strategy: "context_aware"
  
  context_rules:
    # 如果在 EARS 的 When 从句中，优先映射到 Event
    - if: "pattern == EARS and position == trigger"
      prefer: "AS_EVENT"
    
    # 如果在 GWT 的 Given 从句中，优先映射到 Condition
    - if: "pattern == GWT and position == given"
      prefer: "AS_CONDITION"
    
    # 如果在 GWT 的 Then 从句中，优先映射到 StateChange
    - if: "pattern == GWT and position == then"
      prefer: "AS_RESULT"
    
    # 如果涉及性能指标，优先映射到 Constraint
    - if: "text contains 'ms' or 'latency' or 'throughput'"
      prefer: "AS_CONDITION → CONSTRAINT"
    
    # 如果涉及业务规则关键词，优先映射到 Rule
    - if: "text contains 'rule' or 'policy' or 'must'"
      prefer: "AS_CONDITION → RULE"
```

### 6.2 消歧完成度计算

基于映射的成功率和置信度计算 `disambiguation_score`：

```yaml
disambiguation_calculation:
  # 每个语义位置的映射权重
  position_weights:
    AS_ACTOR: 0.15
    AS_OBJECT: 0.15
    AS_ACTION: 0.20
    AS_CONDITION: 0.15
    AS_RESULT: 0.15
    AS_EVENT: 0.10
    AS_ATTRIBUTE: 0.05
    AS_ERROR: 0.05
  
  # 计算公式
  score = Σ(weight[i] × confidence[i])
  
  # 示例
  parsed_result:
    AS_ACTOR: {confidence: 0.95}
    AS_ACTION: {confidence: 0.90}
    AS_OBJECT: {confidence: 0.85}
    AS_CONDITION: {confidence: 0.70}  # 部分歧义
    AS_RESULT: {confidence: 0.80}
  
  score = 0.15×0.95 + 0.20×0.90 + 0.15×0.85 + 0.15×0.70 + 0.15×0.80
       = 0.1425 + 0.18 + 0.1275 + 0.105 + 0.12
       = 0.675  # 未达到 0.95 阈值，需要进一步消歧
```

---

## 七、待讨论：是否需要创建新制品

### 7.1 Rule（业务规则）制品

**现状**：
- 业务规则（如"VIP用户享受24h SLA"）目前只能写在 Requirement 的描述中
- 没有独立的结构化表示

**建议**：
- **可能需要创建**：`Rule` 制品
- 归属：治理域（与 Constraint 并列）
- 用途：表达业务规则（如折扣规则、审批规则）

**制品设计**：
```yaml
id: "RULE-\d+"
name: string
description: string
type: enum                    # DISCOUNT / APPROVAL / ELIGIBILITY / ...
conditions: list<Condition>
actions: list<RuleAction>
priority: integer
```

### 7.2 Condition 和 StateChange

**现状**：
- 目前是结构，不是独立制品
- Condition 引用 Entity.field
- StateChange 引用 Entity.field

**建议**：
- **保持现状**：不需要独立制品
- 理由：它们本质是对 Entity.field 的断言或操作，不是独立概念

---

## 八、后续工作

1. **实现 Structured Draft 制品**：定义其 Schema 和格式
2. **实现 BusinessConcept 制品**：定义映射结构
3. **实现消歧引擎**：Pattern 解析、映射选择、置信度计算
4. **评估主流 Pattern**：EARS、GWT、主谓宾等在实际项目中的适用性
5. **Rule 制品设计**：如果确定需要，完成详细设计
6. **工具链集成**：与现有的 SDS 工具链集成

---

## 参考资料

[^ears-2009]: Mavin et al. *Easy Approach to Requirements Syntax (EARS)*. 2009. https://alistairmavin.com/ears/
[^propbank-2005]: Palmer et al. *The Proposition Bank: An Annotated Corpus of Semantic Roles*. Computational Linguistics, 31(1). 2005.
[^framenet]: FrameNet. *Berkeley FrameNet Project*. https://framenet.icsi.berkeley.edu/
[^controlled-nl-2021]: Fuchs et al. *On systematically building a controlled natural language for functional requirements*. PMC. 2021.
