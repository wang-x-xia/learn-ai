---
title: Agent 记忆系统
description: Agent 记忆系统的分类、技术实现与前沿研究——从上下文窗口到持久化记忆的工程挑战。
created: 2026-04-10
updated: 2026-05-15
tags:
  - agent
  - memory
  - vector-db
  - context-management
review: 2026-05-15
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

## 2. 关键技术问题

### 写入：什么值得记住

不是所有交互都值得持久化。核心挑战是从海量循环输出中**筛选**有价值的信息：

- 事实性知识 vs 临时性推理过程
- 成功经验 vs 失败教训（[Reflexion](ai-agents.md#33-reflexion) 模式将反思显式写入记忆）
- 用户偏好 vs 单次指令

### 检索：如何高效召回

当记忆库膨胀后，检索质量成为瓶颈。主流方案：

- **向量相似度检索**：embedding + ANN 搜索，适合语义匹配
- **混合检索**：BM25 + 向量 + 元数据过滤，通过 RRF 融合提升准确率（与 [RAG](../applied/rag.md) 技术高度重合）→ [混合检索详解](../foundations/information-retrieval.md#4)
- **时间衰减**：近期记忆权重更高，模拟人类遗忘曲线

### 遗忘：什么该丢弃

无限制记忆会导致噪声累积和检索质量下降。需要有策略的遗忘机制——这是当前研究的活跃方向。

---

## 3. 结构化记忆组织

传统记忆系统将记忆视为扁平的向量集合或简单图结构，缺乏层次化和语义抽象。2025 年起，结构化记忆组织成为研究热点。

### 四网络架构（Hindsight）

[Hindsight](https://arxiv.org/pdf/2512.12818) 将记忆组织成四个逻辑网络，区分不同类型的信息[^hindsight-2025]：

**开源实现**：[vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) - MIT 许可，9.8k stars，支持 LLM Wrapper 和 MCP 协议

| 网络类型 | 内容 | 用途 |
|----------|------|------|
| **世界事实网络** | 客观事实、领域知识 | 提供可靠的事实基础 |
| **Agent 经验网络** | 历史交互、成功/失败案例 | 指导未来决策 |
| **实体摘要网络** | 人物、组织、概念的聚合信息 | 快速理解关键实体 |
| **演化信念网络** | Agent 的动态观点和假设 | 支持反思和修正 |

**核心操作**：
- **Retain**：将新信息分类并写入对应网络
- **Recall**：从多个网络检索相关信息
- **Reflect**：基于检索结果更新信念网络

**优势**：明确区分证据和推断，支持可追溯的推理过程。

### Zettelkasten 方法（A-Mem）

[A-Mem](https://arxiv.org/abs/2502.12110v1) 受 Niklas Luhmann 的 Zettelkasten 方法启发，将记忆组织成相互连接的知识网络[^amem-2025]：

**开源实现**：[WujiangXu/AgenticMemory](https://github.com/WujiangXu/AgenticMemory)

**核心原理**：
- 每个记忆是一个原子笔记，包含结构化属性（上下文描述、关键词、标签）
- 自动分析历史记忆，建立语义连接
- 新记忆的加入可以触发现有记忆的更新（记忆演化）

**技术实现**：
- 生成唯一 ID（基于内容哈希）
- 提取关键词（TF-IDF）
- 基于余弦相似度建立连接（阈值 0.25）
- 双向链接，支持图遍历

**优势**：无需预定义 schema，结构从内容中涌现，适合自主 Agent。

### 分层记忆架构

**H-MEM**：基于语义抽象程度的多级记忆组织[^hmem-2026]：
- 每层记忆向量包含指向下一层相关子记忆的位置索引
- 推理时通过索引路由逐层检索，避免全量相似度计算
- 高层记忆是低层记忆的语义抽象

**MEM1**：端到端强化学习框架，维护紧凑的共享内部状态[^mem1-2025]：
- **开源实现**：[MIT-MI/MEM1](https://github.com/MIT-MI/MEM1)
- 在每个回合更新内部状态，支持记忆整合和推理
- 策略性丢弃无关或冗余信息

**MemTree**：动态树状记忆表示[^memtree-2025]：
- 每个节点封装聚合文本内容、语义嵌入、抽象级别
- 根据语义嵌入动态调整树结构
- 类似人类认知模式，支持复杂推理

**MemVerse**：多模态记忆框架，支持文本、图像、音频、视频[^memverse-2025]：
- **开源实现**：[KnowledgeXLab/MemVerse](https://github.com/KnowledgeXLab/MemVerse)
- 分层知识图谱组织长期记忆
- 周期性蒸馏机制将长期记忆压缩到参数模型

**HMO (Hierarchical Memory Orchestration)**：三层目录结构[^hmo-2026]：
- 主缓存：近期和关键记忆 + 用户画像
- 高优先级次级层：重要历史记录
- 全局档案：完整交互历史
- 用户画像驱动记忆在层级间重新分配

### Schema-Based 组织（PISA）

[PISA](https://www.arxiv.org/pdf/2510.15966) 通过 Schema Engine 实现任务导向的记忆组织[^pisa-2025]：

**三层结构**：
- **Memory Pool**：原始经验池
- **Buckets**：按任务类型分类的记忆桶
- **Schema**：结构化知识（Meta、Element、Element-Value、经验 ID）

**动态适应**：
- 将新经验同化到现有 schema
- Schema 演化或创建新 schema
- 冲突分析指导适应策略

**优势**：支持任务特定的记忆组织，灵活可扩展。

---

## 4. 领域自适应记忆管理

不同场景、领域、Agent 偏好需要不同的记忆管理策略。2025 年的研究强调记忆系统的自适应能力。

### 上下文工程（ACE）

[ACE (Agentic Context Engineering)](https://www.microsoft.com/en-us/research/publication/agentic-context-engineering-evolving-contexts-for-self-improving-language-models/) 将上下文视为演化的 playbooks[^ace-2025]：

**核心思想**：
- 上下文不是静态文本，而是可演化的策略集合
- 通过生成、反思、策展的模块化过程积累和优化策略
- 防止上下文坍塌（迭代重写侵蚀细节）

**应用场景**：
- 离线：系统 prompt 演化
- 在线：Agent 记忆演化
- 领域特定：金融、医疗等专业领域的上下文适应

**优势**：无需标注监督，通过自然执行反馈自我改进。

### 记忆即动作（MemAct）

[MemAct (Memory as Action)](https://arxiv.org/html/2510.12635v2) 将上下文管理视为可学习的原语[^memact-2025]：

**核心思想**：
- 上下文管理不是被动机制，而是可学习的动作
- Agent 学习何时保留、压缩、丢弃历史片段
- 通过函数调用动作实现记忆策略

**学习策略**：
- 强化学习训练记忆策略
- 不同模型涌现不同策略
- 策略可迁移跨任务复杂度和领域

**优势**：在任务性能和上下文效率间自动平衡。

### 程序化记忆

**Mem^p**：将过去轨迹蒸馏成程序化记忆[^memp-2025]：
- 细粒度步骤指令
- 高层脚本抽象
- 动态更新、修正、废弃机制

**MACLA**：分层程序化记忆[^macla-2025]：
- **开源实现**：[S-Forouzandeh/MACLA-LLM-Agents-AAMAS-Conference](https://github.com/S-Forouzandeh/MACLA-LLM-Agents-AAMAS-Conference)
- 贝叶斯后验跟踪可靠性
- 期望效用评分选择动作
- 对比成功/失败精炼过程

**优势**：记忆可迁移（强模型构建的记忆可用于弱模型），支持终身学习。

### 角色对齐记忆

[Intrinsic Memory Agents](https://arxiv.org/html/2508.08997v1) 为多 Agent 系统维护角色对齐的记忆模板[^intrinsic-2025]：

**核心特性**：
- 每个 Agent 有特定的记忆模板
- 记忆保持专业化视角
- 专注任务相关信息

**优势**：在多 Agent 协作中保持角色一致性，提升 token 效率。

---

## 5. 前沿研究（更新）

### 记忆保真度
- **MemMachine**：通过校验机制确保记忆保真度，解决 Agent 多轮交互后的记忆失真问题

### 生物学启发
- **SuperLocalMemory V3.3**：认知量化（重要性分级）、遗忘机制（模拟生物遗忘曲线）、多通道检索（零 LLM 依赖）

### 多 Agent 记忆
- **Memory Intelligence Agent**：专门的 Agent 负责记忆的写入、检索、整理和清洗
- **Intrinsic Memory Agents**：角色对齐的记忆模板，支持多 Agent 协作

### 辩证用户建模
传统的用户记忆是**偏好列表**——"用户喜欢简洁回复"、"用户用 Python"。[Hermes Agent](../ai-personal-software/hermes-agent.md) 通过 [Honcho](../libraries/honcho.md) 框架做**辩证用户建模**：不是记录离散偏好，而是通过多轮交互逐步构建和修正一个"用户心智模型"。本质区别在于：偏好列表是静态的 key-value，心智模型是动态的、可推理的——Agent 能从已有理解**推断**新场景下用户可能的偏好，而不需要每次都被显式告知。

---

## 参考资料

[^wang-2023-survey]: Wang et al. *A Survey on Large Language Model based Autonomous Agents*. 2023. https://arxiv.org/abs/2308.11432
[^hindsight-2025]: Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects. 2025. https://arxiv.org/pdf/2512.12818
[^amem-2025]: A-Mem: Agentic Memory for LLM Agents. 2025. https://arxiv.org/abs/2502.12110v1
[^hmem-2026]: H-MEM: Hierarchical Memory for High-Efficiency Long-Term Reasoning in LLM Agents. 2026. https://aclanthology.org/2026.eacl-long.15/
[^mem1-2025]: MEM1: Learning to Synergize Memory and Reasoning for Efficient Long-Horizon Agents. 2025. https://arxiv.org/html/2506.15841v2
[^memtree-2025]: From Isolated Conversations to Hierarchical Schemas: Dynamic Tree Memory Representation for LLMs. 2025. https://mlanthology.org/iclr/2025/rezazadeh2025iclr-isolated/
[^memverse-2025]: MemVerse: Multimodal Memory for Lifelong Learning Agents. 2025. https://arxiv.org/abs/2512.03627
[^hmo-2026]: Hierarchical Memory Orchestration for Personalized Persistent Agents. 2026. https://arxiv.org/abs/2604.01670v1
[^pisa-2025]: PISA: A Pragmatic Psych-Inspired Unified Memory System for Enhanced AI Agency. 2025. https://www.arxiv.org/pdf/2510.15966
[^ace-2025]: Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models. 2025. https://www.microsoft.com/en-us/research/publication/agentic-context-engineering-evolving-contexts-for-self-improving-language-models/
[^memact-2025]: Memory as Action: Autonomous Context Curation for Long-Horizon Agentic Tasks. 2025. https://arxiv.org/html/2510.12635v2
[^memp-2025]: Mem^p: Exploring Agent Procedural Memory. 2025. https://www.arxiv.org/pdf/2508.06433
[^macla-2025]: Learning Hierarchical Procedural Memory for LLM Agents through Bayesian Selection and Contrastive Refinement. 2025. https://arxiv.org/abs/2512.18950
[^intrinsic-2025]: Intrinsic Memory Agents: Heterogeneous Multi-Agent LLM Systems through Structured Contextual Memory. 2025. https://arxiv.org/html/2508.08997v1
