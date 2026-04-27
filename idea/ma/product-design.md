# 产品设计笔记

## 产品定位

**核心价值主张**: 一个泛用的多任务协作框架，让非技术人员也能通过自然语言编排多个AI能力完成复杂任务。

**目标用户**:
- 知识工作者（产品经理、PO、分析师）
- 业务决策者
- 不懂编程但需要自动化复杂流程的人

**与软件开发工具的区别**:
- 不是给开发者用的CI/CD或代码生成工具
- 关注业务流程的自动化，而非技术实现
- 输入是自然语言需求，输出是业务结果

## 主要用户故事

**US1: 业务报告生成**
- 作为PO，我想"帮我准备下个Sprint的Review文档"
- 系统自动协调多个Impl：拉取JIRA数据、分析完成情况、生成Review文档
- 我只需要审阅和微调

**US2: 市场研究**
- 作为产品经理，我想"调研竞品X的定价策略"
- 系统协调Impl：搜索公开信息、分析定价模式、生成对比报告
- 我获得结构化的研究结果

**US3: 跨系统信息整合**
- 作为决策者，我想"汇总所有系统的健康状态"
- 系统协调Impl：查询监控、检查日志、分析趋势、生成健康报告
- 我获得全局视图

**US4: 流程自动化**
- 作为运营，我想"每周自动生成周报并发送给团队"
- 系统编排：数据收集、报告生成、邮件发送
- 一次配置，持续运行

## 核心功能模块

### 1. 任务编排与状态流转

**谁来负责任务编排？**

**编排原语抽象**：

把编排拆解成几个简单的原子动作，规划器就是组合这些原语：

| 原语 | 功能 | 示例 | 理论/实践参考 |
|------|------|------|---------------|
| `sequence` | 顺序执行 | 先A，再B，再C | 工作流引擎 (Airflow, Temporal) |
| `parallel` | 并行执行 | 同时执行A、B、C | 并行计算、CSP (Communicating Sequential Processes) |
| `condition` | 条件分支 | 如果X则A，否则B | 控制流图、BPMN (Gateway) |
| `loop` | 循环 | 对列表中的每个item执行 | 迭代器、循环结构 |
| `map` | 映射 | 把一个操作应用到每个元素 | 函数式编程 (MapReduce) |
| `context` | 上下文作用域 | 在指定Context中执行Task | 作用域、环境变量、依赖注入

**Task Type 与 Impl**：

Task Type由Planner在规划时确定，每个Task Type下可以有多个Impl（不同模型/配置/脚本）：

| Task Type | Impl示例 | 职责 |
|----------|-----------|------|
| `collect_data` | collect_data/gpt-4o-mini, collect_data/jira-script | 信息收集、查询、爬取 |
| `analyze` | analyze/gpt-4o, analyze/deepseek-v4 | 数据分析、模式识别 |
| `generate_doc` | generate_doc/gpt-4o | 文档生成、内容创作 |
| `send_email` | send_email/smtp-script | 邮件发送 |
| `query_jira` | query_jira/jira-script | JIRA查询 |
| `query_monitor` | query_monitor/prometheus-script | 监控数据查询 |

**示例**：
```
用户: "帮我准备Sprint Review"

Planner生成的Plan:
  sequence([
    parallel([
        collect_data(source="jira"),
        collect_data(source="monitor"),
    ]),
    analyze(),
    generate_doc(),
  ])
```

**简化后的架构**：
- Planner规划时确定每个subtask的Task Type
- 同一Task Type下可以有多个Impl（不同模型/配置/脚本），由选择策略决定
- 不需要运行时匹配、竞标等复杂机制
- 类似"强类型"编程：Task的Type决定了它的handler

**理论参考文献**：

1. **HTN (Hierarchical Task Networks)** - AI规划理论
   - "Planning and Acting" (Russell & Norvig, AI textbook)
   - 任务分解的经典方法，用于SHOP、SHOP2等规划器

2. **工作流理论**
   - "Workflow Patterns" (van der Aalst et al.)
   - 定义了工作流的基本控制模式：sequence、parallel split、synchronization、choice等

3. **BPMN (Business Process Model and Notation)**
   - OMG标准，定义了业务流程的图形化表示
   - Gateway (exclusive/inclusive/parallel) 对应 condition/parallel

4. **函数式编程**
   - MapReduce (Dean & Ghemawat, 2004)
   - map/reduce/fold 是数据处理的核心原语

5. **Actor模型**
   - "A Universal Modular ACTOR Formalism" (Hewitt, 1973)
   - 消息传递、角色分配、并发处理

**实践参考系统**：

| 系统 | 类型 | 核心原语 |
|------|------|----------|
| **Airflow** | 工作流引擎 | DAG、Task、Operator、Dependency |
| **Temporal** | 持久化工作流 | Workflow、Activity、Child Workflow |
| **Prefect** | 现代工作流 | Flow、Task、State、Dependencies |
| **LangChain** | LLM编排 | Chain、Tool、Agent、Memory |
| **AutoGPT** | 自主Agent | Thought、Plan、Action、Observation |
| **CrewAI** | 多Agent | Crew、Agent、Task、Process |

**关键洞察**：
- 这些原语不是凭空想象的，而是几十年工作流和分布式系统研究的结晶
- LLM时代的新挑战是"自然语言 → 原语组合"的语义理解
- 核心创新在于用LLM做"语义到语法"的转换

**规划能力**：

规划不是独立角色，而是 Impl 的能力。当 Impl 的 `can_expand_to_plan: true` 时，它承担规划职责：
1. 理解 Task 的意图
2. 用编排原语组合出子 Plan
3. Plan Executor 校验 Plan 合法性（partners 范围、参数、DSL 结构）
4. 校验通过后由 Plan Executor 执行

**类比**：
- 编排原语 = 编程语言的语法（if/else/for/while）
- Impl（规划时）= 编译器/解释器
- 执行计划 = 编译后的程序

**好处**：
- 规划能力分布在各个 Impl 中，每个 Impl 只需要"懂"自己 partners 范围内的原语组合
- 可调试：执行计划是可视化的
- 可校验：Plan 生成后可做结构校验（partners、参数、DSL），语义正确性通过评价体系感知

**示例**：
```
用户: "帮我准备Sprint Review"

Planner生成的Plan:
  sequence([
    parallel([
        collect_data(source="jira"),
        collect_data(source="test_results"),
    ]),
    analyze_completion(),
    generate_review_doc(),
    wait_for_human_review(),
  ])
```

**状态流转设计**:
```
待处理 → 分解中 → 执行中 → 等待依赖 → 完成/失败
```
- 每个任务有明确的状态
- 支持任务依赖（DAG）
- 支持重试和错误处理

### 2. 上下文管理

**上下文类型**:
- **Global Context**: 全局共享的上下文，指向main branch的特定commit，为Task执行提供确定的背景，系统配置、用户偏好、知识库
- **Plan Context**: Plan调度Task时共享的数据，支持嵌套，子Plan可访问父Plan Context
- **Task Context**: Task的输入、目标、约束（临时数据）

**上下文传递**:
- Plan Executor在Plan和Task间传递必要的上下文
- 子Plan继承父Plan的Context
- Impl可以请求额外上下文
- 支持上下文的增量更新

**上下文修改**:
- Task可以修改Plan Context
- Global Context为只读（基于main branch的特定commit执行，记录commit以确定Task的执行背景）
- 支持Context冲突解决策略

**上下文持久化**:
- 长期任务需要持久化上下文
- 支持断点续传
- 上下文版本管理

### 3. Task Type 与 Impl

**Task Type**：定义"这类工作是什么"——能力契约（输入/输出格式、redo_strategy）。

**Impl**：定义"这类工作怎么做"——同一Task Type下的具体执行方式（不同模型、策略、配置、脚本）。

| Task Type | Impl示例 |
|-----------|----------|
| `collect_data` | collect_data/gpt-4o-mini (kind: llm), collect_data/jira-script (kind: script) |
| `analyze` | analyze/gpt-4o (kind: llm), analyze/deepseek-v4 (kind: llm) |
| `generate_doc` | generate_doc/gpt-4o (kind: llm) |
| `send_email` | send_email/smtp-script (kind: script) |

**Impl选择**：
- Plan Executor将Task分配给Task Type时，由选择策略决定使用哪个Impl
- 评价体系在Impl级别运作，为选择策略提供数据（合格率、成本、速度等）
- 支持Impl的动态注册和发现

### 4. 用户交互

**交互方式**:
- **自然语言输入**: "帮我做X"
- **模板化输入**: 选择预设的任务模板
- **可视化编辑**: 拖拽式任务编排（高级用户）

**反馈机制**:
- 实时进度展示
- 中间结果预览
- 异常处理和人工干预

### 5. 知识和记忆

**短期记忆**:
- 当前会话的上下文
- 任务执行历史

**长期记忆**:
- 用户偏好
- 常用任务模式
- 成功/失败案例

**知识库**:
- 领域知识
- 最佳实践
- 错误处理指南

## MVP范围建议

**Phase 1 - 核心编排（3个月）**
- 中央任务规划器
- 3-5个基础Task Type + Impl（信息收集、分析、生成）
- 简单的上下文管理
- 命令行/简单的Web界面
- 1-2个核心用户故事（如报告生成）

**Phase 2 - 扩展能力（3个月）**
- 更多Task Type和Impl
- 任务模板系统
- 可视化进度展示
- 基础的错误处理和重试
- 更多用户故事

**Phase 3 - 企业级（6个月）**
- 多用户支持
- 权限管理
- 任务调度和定时执行
- 集成更多外部系统
- 完整的监控和日志

## 技术可行性考虑（不深入细节）

**规划器**: 可以基于现有的workflow引擎或自研
**Impl通信**: 消息队列或事件总线
**上下文存储**: 数据库或文件系统
**LLM集成**: 调用现有的LLM API
**部署**: 可以是SaaS或本地部署

## 风险和挑战

1. **任务分解的准确性**: LLM可能无法准确理解复杂需求
2. **Impl之间的协作**: 需要良好的接口定义和错误处理
3. **上下文管理**: 复杂任务的上下文可能很庞大
4. **用户期望管理**: 用户可能期望系统能做所有事情
5. **成本**: 多Impl调用LLM的成本可能很高

## 成功指标

- **用户采用**: 活跃用户数、使用频率
- **任务成功率**: 任务完成的比例
- **用户满意度**: NPS、用户反馈
- **效率提升**: 相比人工操作的时间节省
