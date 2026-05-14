# Natural Language Structuring — 自然语言结构化转译

## 目标

定义从非结构化的自然语言需求到结构化需求模式的转译机制，支持主流需求规范模式（EARS、GWT 等）的解析和消歧。

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

## 三、Pattern 解析示例

> **说明**：以下示例展示了如何将自然语言 Pattern 解析为结构化数据。示例中使用的语义位置（如 `as_event`、`as_action` 等）的详细定义见 [业务概念](business-concept.md)。

### 3.1 EARS 模式 → SDS 制品

```yaml
parsed_ears:
  pattern: "EVENT_DRIVEN"
  text: "When 退款申请被提交, the system shall 设置退款SLA为24h"
  
  segments:
    - position: "trigger"
      text: "退款申请被提交"
      concept: "BC-CONCEPT-001"
      mapping_target: "as_event"
      artifact: "EVT-10"
    
    - position: "response"
      text: "设置退款SLA"
      concept: "BC-CONCEPT-001"
      mapping_target: "as_action"
      artifact: "API-20"
    
    - position: "response_detail"
      text: "退款SLA为24h"
      concept: "BC-CONCEPT-001"
      mapping_target: "as_attribute"
      artifact: "ENT-005.expected_completion"
```

### 3.2 GWT 模式 → SDS 制品

```yaml
parsed_gwt:
  pattern: "GIVEN_WHEN_THEN"
  text: "Given VIP会员, When 用户发起退款, Then 退款SLA为24h"
  
  segments:
    - position: "given"
      text: "VIP会员"
      concept: "BC-CONCEPT-002"
      mapping_target: "as_actor"
      artifact: "ROLE-3"
    
    - position: "when"
      text: "用户发起退款"
      concept: "BC-CONCEPT-001"
      mapping_target: "as_action"
      artifact: "API-20"
    
    - position: "then"
      text: "退款SLA为24h"
      concept: "BC-CONCEPT-001"
      mapping_target: "as_attribute"
      artifact: "ENT-005.expected_completion"
```

### 3.3 主谓宾模式 → SDS 制品

```yaml
parsed_svo:
  pattern: "SUBJECT_PREDICATE_OBJECT"
  text: "退款服务处理退款单"
  
  segments:
    - position: "subject"
      text: "退款服务"
      concept: "BC-CONCEPT-003"
      mapping_target: "as_actor"
      artifact: "MOD-010"
    
    - position: "predicate"
      text: "处理"
      concept: "BC-CONCEPT-001"
      mapping_target: "as_action"
      artifact: "API-20"
    
    - position: "object"
      text: "退款单"
      concept: "BC-CONCEPT-001"
      mapping_target: "as_object"
      artifact: "ENT-005"
```

---

## 四、待讨论：是否需要创建新制品

### 4.1 Rule（业务规则）制品

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

### 4.2 Condition 和 StateChange

**现状**：
- 目前是结构，不是独立制品
- Condition 引用 Entity.field
- StateChange 引用 Entity.field

**建议**：
- **保持现状**：不需要独立制品
- 理由：它们本质是对 Entity.field 的断言或操作，不是独立概念

---

## 五、后续工作

1. **实现 Structured Draft 制品**：定义其 Schema 和格式
2. **实现 Pattern 解析引擎**：支持 EARS、GWT 等主流需求规范模式
3. **评估主流 Pattern**：EARS、GWT、主谓宾等在实际项目中的适用性
4. **Rule 制品设计**：如果确定需要，完成详细设计
5. **工具链集成**：与现有的 SDS 工具链集成

---

## 参考资料

[^ears-2009]: Mavin et al. *Easy Approach to Requirements Syntax (EARS)*. 2009. https://alistairmavin.com/ears/
[^propbank-2005]: Palmer et al. *The Proposition Bank: An Annotated Corpus of Semantic Roles*. Computational Linguistics, 31(1). 2005.
[^framenet]: FrameNet. *Berkeley FrameNet Project*. https://framenet.icsi.berkeley.edu/
[^controlled-nl-2021]: Fuchs et al. *On systematically building a controlled natural language for functional requirements*. PMC. 2021.
