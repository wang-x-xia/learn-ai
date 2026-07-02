---
title: Agent 记忆系统
description: Agent 记忆系统的分类、技术实现与前沿研究——从上下文窗口到持久化记忆的工程挑战。
created: 2026-04-10
updated: 2026-07-02
tags:
  - agent
  - memory
  - vector-db
  - context-management
review: 2026-07-02
---

# Agent 记忆系统

??? note "背景知识"
    - **Agent 执行循环**：思考→行动→观察的反复迭代，直到任务完成 → [详见](ai-agents.md)
    - **向量数据库**：将文本编码为高维向量后存储，支持语义相似度检索
    - **RAG (检索增强生成)**：从外部知识库检索相关文档，注入 LLM 上下文以减少幻觉 → [详见](../applied/rag.md)
    - **信息检索基础**：BM25、向量检索、混合检索等检索算法原理 → [详见](../foundations/information-retrieval.md)

> Agent 的记忆系统决定了它能"记住什么、忘记什么、如何检索"——这直接影响[执行循环](ai-agents.md)的质量和持续性。

---

## 1. 记忆的分类

| 记忆类型 | 技术实现 | 生命周期 | 用途 |
|----------|---------|---------|------|
| **工作记忆** | 上下文窗口中的 system prompt + 近期消息 | 单次循环 | 当前任务的即时上下文 |
| **短期记忆** | 对话历史、临时缓冲区 | 单次会话 | 维持多轮对话连贯性 |
| **长期记忆** | 向量数据库、KV 存储 | 跨会话持久化 | 用户偏好、历史经验、知识库 |
| **情景记忆** | 结构化存储（时间线索引） | 跨会话持久化 | 过往交互的具体经历（何时做了什么、结果如何） |

**核心问题**：上下文窗口有限（即使 200K token 也会被复杂任务耗尽），如何在有限窗口中放入最相关的信息[^wang-2023-survey]？

---

## 2. 趋同的技术栈

2025 年后，主流记忆系统在写入、检索、遗忘三个环节的架构已基本趋同：

| 环节 | 趋同方案 | 说明 |
|------|---------|------|
| **写入** | LLM 抽取 → embedding → 向量库 | 由 LLM 从对话中筛选值得持久化的事实，生成 embedding 后写入；图系统额外抽取实体和关系 |
| **检索** | 向量 + BM25 + 图遍历 + 时间索引 | 四路召回，RRF 融合排序（与 [RAG](../applied/rag.md) 技术高度重合）→ [混合检索详解](../foundations/information-retrieval.md#4) |
| **遗忘** | 时间衰减 + 边失效 / ADD-only | 近期记忆权重更高；矛盾信息标记旧记录失效而非删除，保留演化链 |

各系统的差异化不在基础管线，而在**记忆的组织结构**（第 3 节）和**上层管理策略**（第 4 节）。

---

## 3. 结构化记忆组织

传统记忆系统将记忆视为扁平的向量集合或简单图结构，缺乏层次化和语义抽象。2025 年起，结构化记忆组织成为研究热点。共性思想：高层记忆是低层记忆的语义抽象，检索时逐层路由，避免全量相似度计算。

### Hindsight：三通道记忆

[Hindsight](https://github.com/vectorize-io/hindsight)（MIT，9.8k stars）将记忆分为三通道[^hindsight-2025]：

| 通道 | 内容 | 作用 |
|------|------|------|
| **World** | 客观事实 | 事实性知识存储 |
| **Experiences** | Agent 自身经历 | 情景记忆回溯 |
| **Mental Models** | 反思生成的洞察 | 高层抽象推理 |

内置时序索引，支持时间范围检索。提供 MCP 协议接入。

### Graphiti：时序知识图谱

[Graphiti](https://github.com/getzep/Graphiti)（Apache-2.0，28k+ stars）是开源时序图引擎[^zep-2025]。

**四组件架构**：

| 组件 | 内容 | 作用 |
|------|------|------|
| **Entities**（实体节点） | 人物、产品、概念等，摘要随时间演化 | 语义检索 |
| **Facts / Relationships**（事实边） | 实体→关系→实体三元组，携带时间有效窗口 | 精确事实检索 |
| **Episodes**（原始事件） | 原始消息/文本/JSON（非损失性） | 溯源引用 |
| **Custom Types**（本体） | 开发者通过 Pydantic 定义的实体/边类型 | 领域建模 |

**核心创新——双时间线模型**：

- **事件时间线 $T$**：事实实际发生的时间（支持解析"下周四"等相对时间）
- **摄入时间线 $T'$**：数据写入系统的时间（审计用途）
- 每条边携带四个时间戳（$t'_{created}$、$t'_{expired}$、$t_{valid}$、$t_{invalid}$），新信息矛盾时**标记旧边失效**而非删除，实现事实的版本化管理

### Mem0：从图数据库到内置实体链接

[Mem0](https://github.com/mem0ai/mem0)（Apache-2.0，59k+ stars）经历了显著的架构演进[^mem0-2025]。记忆按**四层作用域**组织：

| 层级 | 生命周期 | 用途 |
|------|---------|------|
| **Conversation**（会话） | 单次轮次 | 工具调用、中间计算 |
| **Session**（会话组） | 分钟到小时 | 多步骤任务流 |
| **User**（用户） | 跨会话持久化 | 个人偏好、账户状态 |
| **Org**（组织） | 全局配置 | 共享知识、策略文档 |

通过 `user_id` / `agent_id` / `run_id` / `app_id` 组合过滤，支持多租户和多 Agent 溯源。

#### 对比与权衡

| 维度 | Hindsight | Graphiti | Mem0 |
|------|-----------|----------|---------|
| **记忆结构** | 三通道（平行分类） | 四组件图谱 | 四层作用域 + 实体链接 |
| **图结构** | ❌ | ✅ 完整知识图谱（Neo4j） | ⚠️ 内置实体链接（向量库） |
| **时序支持** | ✅ 时序索引 | ✅ 双时间线 + 边失效 | ⚠️ ADD-only 保留历史 |
| **社区发现** | ❌ | ✅ 标签传播 | ❌ |
| **部署复杂度** | 低 | 高（需 Neo4j） | 低（仅向量库） |

---

## 4. 记忆管理策略

### 上下文工程

记忆系统的核心问题不只是"存什么"和"取什么"，还有**如何管理上下文窗口本身**。

[ACE (Agentic Context Engineering)](https://www.microsoft.com/en-us/research/publication/agentic-context-engineering-evolving-contexts-for-self-improving-language-models/)[^ace-2025] 将上下文视为可演化的策略集合（playbooks），通过生成→反思→策展循环持续优化，防止迭代重写导致的上下文坍塌。[MemAct](https://arxiv.org/html/2510.12635v2)[^memact-2025] 更进一步：把记忆管理建模为 Agent 的**可学习动作**（何时保留、压缩、丢弃历史片段），通过 RL 训练策略，在任务性能和 token 效率间自动平衡。

### 程序化记忆

除了 episodic（发生了什么）和 semantic（知道什么）记忆，产品界开始关注第三种类型：**procedural memory**（如何做）。Mem0 在代码中实现了 `MemoryType.PROCEDURAL`（枚举中唯一实际启用的类型），但整体工具支持仍处于早期。

| 系统 | 核心机制 | 特点 |
|------|---------|------|
| **Mem^p**[^memp-2025] | 轨迹蒸馏为步骤指令 + 高层脚本 | ACL 2026；动态更新/修正/废弃；[开源](https://github.com/zjunlp/MemP) |
| **MACLA**[^macla-2025] | 贝叶斯选择 + 对比精炼 | AAMAS 2026 Oral；2851 轨迹 → 187 可复用程序（15:1 压缩）；[开源](https://github.com/S-Forouzandeh/MACLA-LLM-Agents-AAMAS-Conference) |

**共性价值**：程序化记忆可迁移——强模型构建的记忆用于弱模型仍有显著增益，支持终身学习。

---

## 参考资料

[^wang-2023-survey]: Wang et al. *A Survey on Large Language Model based Autonomous Agents*. 2023. https://arxiv.org/abs/2308.11432
[^hindsight-2025]: Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects. 2025. https://arxiv.org/pdf/2512.12818
[^ace-2025]: Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models. 2025. https://www.microsoft.com/en-us/research/publication/agentic-context-engineering-evolving-contexts-for-self-improving-language-models/
[^memact-2025]: Memory as Action: Autonomous Context Curation for Long-Horizon Agentic Tasks. 2025. https://arxiv.org/html/2510.12635v2
[^memp-2025]: Mem^p: Exploring Agent Procedural Memory. 2025. https://www.arxiv.org/pdf/2508.06433
[^macla-2025]: Learning Hierarchical Procedural Memory for LLM Agents through Bayesian Selection and Contrastive Refinement. 2025. https://arxiv.org/abs/2512.18950
[^zep-2025]: Zep: A Temporal Knowledge Graph Architecture for Agent Memory. 2025. https://arxiv.org/abs/2501.13956
[^mem0-2025]: Chhikara et al. *Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory*. 2025. https://arxiv.org/abs/2504.19413
