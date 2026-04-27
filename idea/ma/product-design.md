# 产品设计笔记

## 产品定位

**核心价值主张**: 一个泛用的多Agent协作框架，让非技术人员也能通过自然语言编排多个AI Agent完成复杂任务。

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
- 系统自动协调多个Agent：拉取JIRA数据、分析完成情况、生成Review文档
- 我只需要审阅和微调

**US2: 市场研究**
- 作为产品经理，我想"调研竞品X的定价策略"
- 系统协调Agent：搜索公开信息、分析定价模式、生成对比报告
- 我获得结构化的研究结果

**US3: 跨系统信息整合**
- 作为决策者，我想"汇总所有系统的健康状态"
- 系统协调Agent：查询监控、检查日志、分析趋势、生成健康报告
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
| `decompose` | 任务分解（确定task类型） | "写报告" → [collect_data, analyze, generate_doc] | HTN (Hierarchical Task Networks) |
| `sequence` | 顺序执行 | 先A，再B，再C | 工作流引擎 (Airflow, Temporal) |
| `parallel` | 并行执行 | 同时执行A、B、C | 并行计算、CSP (Communicating Sequential Processes) |
| `condition` | 条件分支 | 如果X则A，否则B | 控制流图、BPMN (Gateway) |
| `loop` | 循环 | 对列表中的每个item执行 | 迭代器、循环结构 |
| `map` | 映射 | 把一个操作应用到每个元素 | 函数式编程 (MapReduce) |
| `context` | 上下文作用域 | 在指定Context中执行Task | 作用域、环境变量、依赖注入

**Task类型与Agent绑定**：

task类型在decompose时确定，直接映射到对应的agent类型：

| Task类型 | 对应Agent | 职责 |
|----------|-----------|------|
| `collect_data` | DataCollector | 信息收集、查询、爬取 |
| `analyze` | Analyzer | 数据分析、模式识别 |
| `generate_doc` | DocumentGenerator | 文档生成、内容创作 |
| `send_email` | EmailSender | 邮件发送 |
| `query_jira` | JiraQuery | JIRA查询 |
| `query_monitor` | MonitorQuery | 监控数据查询 |

**示例**：
```
用户: "帮我准备Sprint Review"

decompose("准备Sprint Review")
  → sequence([
      parallel([
          collect_data(source="jira"),      // → DataCollector
          collect_data(source="monitor")    // → DataCollector
      ]),
      analyze(),                            // → Analyzer
      generate_doc(),                       // → DocumentGenerator
    ])
```

**简化后的架构**：
- decompose时确定每个subtask的类型
- task类型直接映射到agent类型（1:1绑定）
- 不需要运行时匹配、竞标等复杂机制
- 类似"强类型"编程：task的type决定了它的handler

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
- 规划器的核心创新在于用LLM做"语义到语法"的转换

**规划器的工作**：
1. 理解用户需求（自然语言 → 意图）
2. 用原语组合出执行计划（类似写代码）
3. 执行计划并跟踪状态
4. 处理异常和人工干预

**类比**：
- 编排原语 = 编程语言的语法（if/else/for/while）
- 规划器 = 编译器/解释器
- 执行计划 = 编译后的程序

**好处**：
- 规划器本身不需要"懂"所有业务，只需要"懂"原语组合
- 新增业务逻辑 = 新的原语组合，不需要改规划器
- 可调试：执行计划是可视化的
- 可扩展：新增原语即可增强能力

**示例**：
```
用户: "帮我准备Sprint Review"

规划器生成的执行计划:
decompose("准备Sprint Review")
  → sequence([
      parallel(["拉取JIRA数据", "拉取测试结果"]),
      analyze_completion(),
      generate_review_doc(),
      wait_for_human_review()
    ])
assign_to_agents(plan)
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
- Agent可以请求额外上下文
- 支持上下文的增量更新

**上下文修改**:
- Task可以修改Plan Context
- Global Context为只读（基于main branch的特定commit执行，记录commit以确定Task的执行背景）
- 支持Context冲突解决策略

**上下文持久化**:
- 长期任务需要持久化上下文
- 支持断点续传
- 上下文版本管理

### 3. Agent能力定义

**Agent类型**:
- **信息收集Agent**: 搜索、查询、爬取
- **分析Agent**: 数据分析、模式识别
- **生成Agent**: 文档生成、内容创作
- **执行Agent**: 调用API、发送邮件、更新系统
- **规划Agent**: 任务分解、调度（中央规划器）

**Agent能力描述**:
- 每个Agent声明自己的能力（输入/输出格式）
- 规划器根据能力匹配任务
- 支持Agent的动态注册和发现

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
- 3-5个基础Agent（信息收集、分析、生成）
- 简单的上下文管理
- 命令行/简单的Web界面
- 1-2个核心用户故事（如报告生成）

**Phase 2 - 扩展能力（3个月）**
- 更多Agent类型
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
**Agent通信**: 消息队列或事件总线
**上下文存储**: 数据库或文件系统
**LLM集成**: 调用现有的LLM API
**部署**: 可以是SaaS或本地部署

## 风险和挑战

1. **任务分解的准确性**: LLM可能无法准确理解复杂需求
2. **Agent之间的协作**: 需要良好的接口定义和错误处理
3. **上下文管理**: 复杂任务的上下文可能很庞大
4. **用户期望管理**: 用户可能期望系统能做所有事情
5. **成本**: 多Agent调用LLM的成本可能很高

## 成功指标

- **用户采用**: 活跃用户数、使用频率
- **任务成功率**: 任务完成的比例
- **用户满意度**: NPS、用户反馈
- **效率提升**: 相比人工操作的时间节省
