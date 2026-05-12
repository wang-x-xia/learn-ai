## Software Defined by Structured Artifacts — 完整讨论总结

> **撰写日期：2026-05-11**
> **状态：阶段性总结（V1.0）**
> **目的：完整记录本次对话中逐步演进的核心思想、设计方案与技术判断，以供后续深化和实现。**

---

## 一、宏大目标

### 1.1 一句话定义

> **除了最开始那份反映人类意图的、模糊的"需求初稿"之外，软件生命周期内的一切——从系统架构、API 接口、数据库设计、业务流程、模块依赖到测试用例和代码本身——都必须由严谨的"结构化制品（Structured Artifacts）"来定义和驱动。**

### 1.2 目标全景

```
人类模糊的需求初稿（唯一允许非结构化的输入）
        │
        ▼
┌──────────────────────────────────────┐
│    消歧引擎（渐进式结构化转化）         │
│    将模糊需求转化为良好定义的制品        │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│    结构化制品体系（软件的真正"源码"）    │
│                                      │
│    需求制品 → 架构制品 → 数据制品       │
│    → 接口制品 → 流程制品 → 测试制品     │
│    → 代码制品                          │
│                                      │
│    所有制品之间通过严格的关系边互联       │
└──────────────────────────────────────┘
        │
        ▼
    代码仅仅是这些结构化制品的"执行态副产品"
```

### 1.3 核心信念

- **软件的本质不是一堆散乱的源代码文件，而是一个由高层结构化制品层层推演的确定性图谱。**
- **多义性不是需求的固有属性，而是信息不足的表现。** 通过在产品侧系统性地补充结构化信息，任何多义的需求都可以被收敛为良好定义的制品。
- **语义鸿沟不是不可逾越的天然屏障，而是应该被主动"填平"的沟壑。** 填充物就是结构化信息。

---

## 二、核心运转机制：从"模糊意图"到"确定性映射"

整个系统的工作流表现为单向的**"熵减"过程**：

| 阶段 | 名称 | 输入 | 输出 | 特征 |
|------|------|------|------|------|
| **Phase 0** | 需求初稿 | 人类的模糊想法 | 自然语言描述 | **唯一允许非结构化的节点** |
| **Phase 1** | 消歧与结构化 | 自然语言需求 | 良好定义的结构化需求制品 | 渐进式引导消歧 |
| **Phase 2** | 架构与设计 | 结构化需求 | 模块/接口/数据/流程制品 | 严格的 Schema 约束 |
| **Phase 3** | 代码生成 | 全部上游制品 | 源代码 | 代码是制品的必然映射 |
| **Phase 4** | 验证与闭环 | 代码 + 测试制品 | 测试报告 + 一致性报告 | 自动化契约验证 |

**关键原则：如果要修改软件，首先修改的是"结构化制品"，然后系统自动向下重构代码——而非反过来。**

---

## 三、结构化制品的七层模型

### 3.1 层级总览

| 层级 | 名称 | 结构化程度 | 格式 | 说明 |
|------|------|-----------|------|------|
| **L0** | 愿景层 | 半结构化 | 结构化 Markdown | 产品目标、用户画像、核心价值主张 |
| **L1** | 需求层 | **严格结构化** | JSON / YAML | 功能性/非功能性需求、验收标准、消歧完成度 |
| **L2** | 架构层 | **严格结构化** | YAML + 图谱 | 模块划分、服务拓扑、通信协议、技术选型 |
| **L3** | 数据层 | **严格结构化** | JSON Schema | 实体定义、字段类型、关系、约束 |
| **L4** | 接口层 | **严格结构化** | OpenAPI / Protobuf | 所有对外/对内接口的输入、输出、错误码 |
| **L5** | 行为层 | **严格结构化** | 状态机 YAML / DAG | 状态机定义、业务流程、事件流转规则 |
| **L6** | 约束层 | **严格结构化** | 形式化规则 | 安全策略、性能边界、合规要求、架构红线 |
| **L7** | 测试层 | **严格结构化** | JSON / Gherkin | 每个模块的输入/输出契约、边界条件、预期行为 |

### 3.2 制品之间的关系

所有制品之间通过严格的**关系边（Edges）**互联，形成一个可追溯的知识图谱：

```
REQ-0078 ──TRACES_TO──→ US-301
US-301   ──IMPLEMENTED_BY──→ RefundService
RefundService ──DEPENDS_ON──→ VIPEngine
RefundService ──READS_FROM──→ OrderDatabase
RefundService ──EXPOSES──→ POST /api/v1/refunds
REQ-0078 ──TESTED_BY──→ TC-401, TC-402, TC-403
```

---

## 四、需求消歧体系（核心创新）

### 4.1 设计理念

```
不是要求人类"用结构化语言思考"
而是让系统帮助人类"把非结构化的思考，逐步转化为结构化的定义"

输入：自然语言（人类友好）
过程：引导式消歧（系统驱动）
输出：严格的结构化制品（机器友好）
```

### 4.2 多义性的七个维度

| 缺失维度 | 典型多义示例 | 需要补充的结构化信息 |
|---------|-------------|-------------------|
| **主语（Actor）** | "用户可以查看订单" | 哪种用户？买家？卖家？管理员？ |
| **对象（Object）** | "查看订单" | 查看哪些字段？全部还是部分？ |
| **条件（Precondition）** | "可以取消订单" | 什么状态下可以？什么状态下不行？ |
| **边界（Boundary）** | "搜索要快" | 多快？200ms？1s？哪个百分位？ |
| **异常（Exception）** | "用户注册" | 邮箱重复怎么办？网络断了怎么办？ |
| **副作用（Side Effect）** | "删除用户" | 用户的订单怎么办？评论怎么办？ |
| **状态变迁（State）** | "修改订单" | 修改前什么状态？修改后什么状态？ |

### 4.3 消歧流程

```
Phase 0：产品经理输入自然语言需求
            "VIP用户可以优先退款"
                │
Phase 1：系统自动检测多义性
            扫描出 7 个维度的缺失信息
            自动生成消歧问题（选择题/填空题）
                │
Phase 2：产品经理逐一回答消歧问题
            系统将回答填充到结构化字段中
                │
Phase 3：系统计算消歧完成度（Disambiguation Score）
            加权平均 → 0~1 之间的分数
                │
Phase 4：门禁检查
            消歧分数 < 0.95 → 不允许进入开发
            消歧分数 < 0.98 → 不允许进入 AI 代码生成
                │
Phase 5：输出完全结构化的需求制品（REQ-XXXX.yaml）
```

### 4.4 消歧后的完整需求制品示例

```yaml
requirement_resolved:
    id: "REQ-0078"
    source_draft: "DRAFT-0078"
    raw_input: "VIP用户可以优先退款"
    ambiguity_status: "RESOLVED"

    actor:
    type: "User"
    qualifier:
        field: "membership_level"
        operator: "IN"
        values: ["GOLD", "DIAMOND"]

    action:
    verb: "request_refund"
    priority_mechanism:
        type: "SLA_OVERRIDE"
        original_sla: "72h"
        vip_sla: "24h"
        skip_review: false

    preconditions:
    - field: "order.status"
        operator: "IN"
        values: ["DELIVERED", "COMPLETED"]
    - field: "user.refund_count_this_month"
        operator: "<="
        value: 3
    - field: "order.has_return_shipping"
        operator: "=="
        value: true

    postconditions:
    - field: "refund.status"
        becomes: "PROCESSING"
    - field: "refund.expected_completion"
        becomes: "NOW() + 24h"

    boundary:
    max_refund_amount:
        value: 50000
        currency: "CNY"
    exceeds_limit_action: "ESCALATE_TO_MANUAL_REVIEW"

    exceptions:
    - condition: "VIP资格在退款处理期间过期"
        behavior: "维持发起时的VIP时效，不中断"
    - condition: "退款金额超过上限"
        behavior: "转人工审核，SLA变为48h"

    side_effects:
    - trigger: "退款成功"
        actions:
        - "扣回该订单产生的积分"
        - "优惠券标记为'已退回'，状态变为可复用"
        - "用户月退款计数器 +1"

    traces_to:
    stories: ["US-301"]
    modules: ["RefundService", "VIPEngine", "PointsService"]
    test_cases: ["TC-401", "TC-402", "TC-403"]
```

---

## 五、各层制品的结构化示例

### 5.1 数据模型制品（L3）

```json
{
    "entity": "Order",
    "fields": [
    {"name": "order_id",     "type": "UUID",    "primary_key": true},
    {"name": "user_id",      "type": "UUID",    "foreign_key": "User.user_id"},
    {"name": "total_amount", "type": "Decimal",  "precision": 2, "nullable": false},
    {"name": "status",       "type": "Enum",    "values": ["CREATED","PAID","SHIPPED","CLOSED"]},
    {"name": "created_at",   "type": "DateTime","default": "NOW()"}
    ],
    "indexes": [
    {"fields": ["user_id"], "type": "btree"},
    {"fields": ["status", "created_at"], "type": "composite"}
    ],
    "constraints": [
    {"type": "unique", "fields": ["order_id"]},
    {"type": "check",  "expression": "total_amount >= 0"}
    ]
}
```

### 5.2 模块与服务契约制品（L2 + L4）

```yaml
module:
    name: "PaymentService"
    version: "2.1.0"
    type: "microservice"

    inputs:
    - name: "CreatePaymentRequest"
        fields:
        - {name: "order_id", type: "UUID", required: true}
        - {name: "amount",   type: "Decimal", required: true, min: 0.01}
        - {name: "currency", type: "Enum", values: ["CNY","USD","EUR"]}

    outputs:
    - name: "PaymentResult"
        fields:
        - {name: "transaction_id", type: "UUID"}
        - {name: "status", type: "Enum", values: ["SUCCESS","FAILED","PENDING"]}
        - {name: "error_code", type: "String", nullable: true}

    dependencies:
    - {module: "OrderService", protocol: "gRPC", required: true}
    - {module: "RiskEngine",   protocol: "HTTP", required: true}

    constraints:
    - "MAX_LATENCY_P99 <= 300ms"
    - "MUST_BE_IDEMPOTENT"
```

### 5.3 业务流程 / 状态机制品（L5）

```yaml
process:
    name: "OrderLifecycle"
    type: "state_machine"

    states:
    - {id: "CREATED",   initial: true}
    - {id: "PAID",      initial: false}
    - {id: "SHIPPED",   initial: false}
    - {id: "DELIVERED", initial: false}
    - {id: "CLOSED",    terminal: true}
    - {id: "CANCELLED", terminal: true}

    transitions:
    - from: "CREATED"
        to: "PAID"
        trigger: "PaymentConfirmedEvent"
        guard: "order.total_amount > 0"
        action: "NotifyService.sendPaymentConfirmation(order.user_id)"

    - from: "CREATED"
        to: "CANCELLED"
        trigger: "UserCancelEvent"
        guard: "elapsed_time(order.created_at) < 30min"
        action: "RefundService.refund(order.order_id)"

    forbidden_transitions:
    - {from: "CLOSED",    to: "*", reason: "终态不可变更"}
    - {from: "CANCELLED", to: "*", reason: "终态不可变更"}
```

### 5.4 需求追溯制品（关系边）

```yaml
requirement:
    id: "REQ-0042"
    version: "1.3"
    status: "APPROVED"

    traces_to:
    stories: ["US-101", "US-102"]
    modules: ["PaymentService", "OrderService"]
    code_files:
        - path: "src/services/payment.ts"
        functions: ["createPayment", "validatePayment"]
    test_cases: ["TC-201", "TC-202", "TC-203"]
    api_endpoints: ["POST /api/v1/payments"]

    depends_on: ["REQ-0038", "REQ-0040"]

    change_history:
    - {version: "1.0", date: "2026-01-15", author: "张三", action: "CREATED"}
    - {version: "1.3", date: "2026-03-20", author: "李四", action: "MODIFIED",
        diff: "添加了对微信支付的支持"}
```

---

## 六、可行性与挑战分析

### 6.1 分层可行性矩阵

| 软件要素 | 结构化可行性 | 成熟度 | 核心挑战 |
|----------|-------------|--------|---------|
| **数据模型** | ✅✅✅ 完全可行 | 非常成熟 | 几乎没有 |
| **接口/API 契约** | ✅✅✅ 完全可行 | 非常成熟 | 几乎没有 |
| **模块依赖关系** | ✅✅✅ 完全可行 | 成熟 | 粒度定义需权衡 |
| **业务流程/状态机** | ✅✅ 可行 | 成熟 | "脏逻辑"的特殊处理 |
| **需求追溯** | ✅✅ 可行 | 特定行业成熟 | 维护成本较高 |
| **测试用例** | ✅✅ 可行 | 成熟 | 与需求的同步更新 |
| **需求/用户故事** | ✅✅ 可行（通过消歧引擎） | 探索中 | 需要系统化的消歧流程 |
| **代码逻辑本身** | ⚠️ 有限可行 | 探索中 | 复杂度爆炸、协同演进 |

### 6.2 三大核心挑战

#### 挑战 1：代码与上层制品的协同演进

当程序员修改了代码中的接口参数，必须同步回溯修改上游所有关联制品（需求、模块定义、状态机、API 契约、测试用例等）。如果任何一处忘记同步 → 数据腐化。

**缓解方案：**
- 单向生成（代码从制品自动生成，而非反向同步）
- 变更检测引擎（任一层变更时，自动扫描并标记所有受影响的关联节点）
- 在关键里程碑进行一致性检查

#### 挑战 2：版本控制与冲突合并

当所有系统元素都存储为数据库中的复杂图结构时，多人协作的冲突合并比纯文本的 Git Diff/Merge 困难得多。

#### 挑战 3：框架僵化与"脏逻辑"

现实世界的业务充满特例和妥协。试图用一个万能 Schema 包容从"高层目标"到"底层控制流"的所有逻辑，可能导致系统自身变得极其庞大和僵化。

**缓解方案：**
- 核心流程用严格结构化定义
- 特例和"脏逻辑"以附注形式（半结构化）挂载到主流程节点上
- 接受核心流程 vs 边缘逻辑的二元分层

---

## 七、推荐的底层架构

```
┌───────────────────────────────────────────────────┐
│                推荐底座架构                          │
│                                                    │
│  图数据库（Neo4j / 类似）作为核心存储                 │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ 需求节点  │  │ 模块节点  │  │ 代码提交节点      │ │
│  │(消歧后的  │  │(严格结构) │  │(Git Commit SHA)  │ │
│  │ 结构化数据)│  │          │  │                  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────────────┘ │
│       │              │             │               │
│       └──── 关系边 ───┴──── 关系边 ─┘               │
│         TRACES_TO, DEPENDS_ON,                     │
│         IMPLEMENTS, TESTS, PUBLISHES               │
│                                                    │
│  核心价值 = 管理节点之间的"关系边"                    │
│  因为工程中真正出问题的是                            │
│  "改了A却不知道B受影响"——这是关系的问题               │
└───────────────────────────────────────────────────┘
```

---

## 八、行业前沿共振

本讨论中形成的思想体系，与以下行业前沿趋势高度共振：

| 趋势 | 关联 |
|------|------|
| **规范驱动开发（SDD）** | 需求先转化为结构化规范，再由 AI 生成代码 |
| **BMAD v6 框架** | YAML 步骤引擎、Epic/Story 分片、多智能体流水线 |
| **MCP 协议（Model Context Protocol）** | AI Agent 通过标准协议读取软件的完整结构化描述 |
| **GraphRAG** | 知识图谱 + 大模型结合，实现长期迭代下的语义一致性 |
| **多智能体协作（MetaGPT / Claude Agent Teams）** | 通过结构化制品在多个 Agent 节点之间传递状态 |
| **MBSE（基于模型的系统工程）** | 航空航天/汽车领域已经实践的需求全生命周期追溯 |
| **PHPDecide / Kiro Steering Files** | 架构决策和编码规范的代码化、可执行化 |

---

## 九、核心总结

### 9.1 这个体系试图解决的根本问题

在**"人类语言的模糊性"**与**"计算机系统的确定性"**之间，建立一座由**"结构化制品"**构成的坚固桥梁。

### 9.2 人类角色的转变

| 传统模式 | 本体系 |
|----------|-------|
| 人类直接写代码 | 人类定义结构化描述，AI 生成代码 |
| 需求文档是自然语言散文 | 需求是经过消歧的严格数据结构 |
| 架构存在于 PPT 和脑中 | 架构是机器可读的知识图谱 |
| 测试是事后补充 | 测试契约是软件定义的一部分 |
| AI 是辅助工具 | AI 是核心执行者，人类是"架构监理" |
| 语义鸿沟被接受为不可逾越 | 语义鸿沟被系统化地填平 |

### 9.3 一句话总结

> **软件的未来不是"写代码"，而是"定义制品"。代码只是制品的执行态投影。人类的核心职责是确保制品的完备性和一致性——而这，正是可以被结构化、被量化、被系统管理的。**

---

## 十、后续可深入的方向

1. **消歧引擎的具体实现**：如何基于 LLM + 规则引擎构建自动消歧系统
2. **图数据库的建模方案**：如何设计节点和关系边的 Schema
3. **变更传播引擎**：当某个制品变更时，如何自动扫描并更新所有受影响的关联制品
4. **制品到代码的自动映射引擎**：如何从结构化制品自动生成高质量代码
5. **消歧完成度的量化模型**：各维度的权重如何设定，阈值如何动态调整
6. **与现有工具链的集成**：如何与 Git、CI/CD、IDE（Cursor/Claude Code）无缝对接
7. **"脏逻辑"的分层处理方案**：如何在保持核心结构化的同时，优雅地处理业务特例