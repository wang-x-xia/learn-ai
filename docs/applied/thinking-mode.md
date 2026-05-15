---
title: Thinking Mode (思考模式)
description: 推理时计算扩展的核心优势、自适应推理机制、与普通 completion 和 plan/execute 的权衡。
created: 2026-04-17
updated: 2026-04-17
tags:
  - thinking-mode
  - reasoning
  - test-time-compute
  - claude
review: 2026-05-15
---

# Thinking Mode (思考模式)

??? note "背景知识"
    - **LLM 推理**：模型根据输入生成输出 token 的过程，每个 token 消耗计算资源 → [详见](../foundations/transformer.md)
    - **Chain-of-Thought (CoT)**：让模型逐步推理而非直接给答案，提升复杂任务准确率
    - **Agent 执行循环**：思考→行动→观察的迭代，Thinking 影响"思考"环节的深度 → [详见](../agent/ai-agents.md)

> Thinking mode 是 2025 年引入的重要技术，让模型能够在回答前进行深度推理，显著提升复杂任务的表现。本文档重点分析其核心优势、自适应推理机制，以及与其他方法的权衡。

---

## 概述

Thinking mode（思考模式）是一种推理时计算扩展技术，核心思想是让模型在生成最终答案前投入更多计算资源进行深度推理。与传统"更大模型 + 更多数据"的 scaling 方向不同，thinking mode 通过"推理时更多计算"来提升性能[^anthropic-2025-thinking][^deepseek-2025-r1]。

### 核心特性

- **不是模型切换**：同一个模型给自己更多时间和计算资源
- **两阶段生成**：先生成内部推理序列，再基于推理生成最终答案
- **可配置预算**：开发者设置 thinking budget 作为推理上限
- **自适应推理**：模型在预算内自主决定推理深度和停止时机

---

## 核心优势

### 1. 推理能力提升

通过推理时计算扩展，在复杂任务上显著提升性能：

- **数学推理**：在 AIME 等数学竞赛中，性能随 thinking tokens 增加对数级提升
- **代码推理**：在 SWE-bench 等代码基准上，能更好地理解复杂逻辑和调试
- **多步推理**：通过深度推理链处理需要多步逻辑的任务

关键洞察：性能提升呈对数关系，边际收益递减，需要找到最优计算预算。

### 2. 自适应推理深度

模型根据任务复杂度自主调整推理深度，而非简单的外部长度限制：

**双层控制机制：**
- **Thinking Budget**：开发者设置的最大 tokens 上限（硬约束）
- **模型自适应停止**：模型在 budget 内基于内部质量信号决定何时停止

**实际行为：**
- 简单任务：快速响应，使用少量 thinking tokens
- 复杂任务：深度推理，使用更多 thinking tokens
- 即使允许使用整个 budget，模型通常会在推理充分时提前停止

**技术实现方法：**
- **基于不确定性监控**：通过条件熵、token 熵等信号判断推理质量
- **过程奖励模型 (PRM)**：每个推理步骤都有质量评分，分数不再提升时停止
- **强化学习训练**：模型通过 RL 学习自适应分配计算资源
- **复杂度感知**：根据问题复杂度动态调整推理策略[^zhao-2025-t2][^xie-2026-early][^guo-2025-entropy]

优势：避免简单任务的过度计算，同时确保复杂任务有足够推理资源。

### 3. 成本效率

与传统 plan/execute 相比，thinking mode 在成本上有显著优势：

- **单次 API 调用**：避免了多轮调用的固定开销
- **无上下文累积**：每轮独立推理，不会因历史累积而增加成本
- **可控预算**：通过 thinking budget 精确控制最大成本

对比：plan/execute 需要 2-N 次 API 调用，且每轮都要包含完整历史，上下文窗口压力随轮数增长。

### 4. 训练出来的推理能力

Thinking mode 的推理能力通过专门训练获得，而非 prompt engineering：

- **强化学习训练**：通过 RL 激励模型探索有效的推理模式
- **过程奖励模型**：每个推理步骤都有质量评估，及时纠正错误
- **自然涌现的能力**：自我验证、反思、回溯、探索多个角度等推理行为自然涌现

优势：推理质量更高，更接近人类思维过程，而非机械地遵循指令模板。

---

## 与其他方法的对比

### 与普通 Completion 的区别

| 特性 | 普通 Completion | Thinking Mode |
|------|----------------|---------------|
| **生成阶段** | 单阶段直接生成答案 | 两阶段：先推理后答案 |
| **计算资源** | 固定计算量 | 可变计算量（根据 thinking budget） |
| **推理深度** | 浅层推理 | 深度推理 |
| **适用场景** | 简单问答、创意任务 | 复杂推理、数学、代码 |

**关键区别：**
- 普通 completion：推理过程隐藏在模型内部，通过 max_tokens 控制输出长度
- Thinking mode：推理过程通过 thinking tokens 显式表达（可选可见），通过 thinking_budget 控制推理深度
- 性能提升：普通 completion 主要取决于模型规模，thinking mode 可通过增加推理计算来提升

### 与 Plan/Execute 的区别

| 维度 | Thinking Mode | Plan/Execute |
|------|---------------|--------------|
| **实现方式** | 训练出来的推理能力 | 通过 prompt 设计实现 |
| **API 调用** | 单次调用 | 多次调用（2-N次） |
| **推理质量** | 专门训练，质量更高 | 依赖模型指令遵循能力 |
| **可控性** | 相对黑盒 | 完全可控，每步可见 |
| **成本结构** | 单次成本，无累积 | 多次成本，上下文累积 |

**核心权衡：**

**Thinking Mode 优势：**
- 推理质量更高（RL + PRM 专门训练）
- 成本效率更高（单次调用，无上下文累积）
- 自适应能力（模型自主决定推理深度）
- 自然涌现的推理行为（自我验证、反思、回溯）

**Plan/Execute 优势：**
- 完全可控（精确控制每一步的指令和行为）
- 可插拔性（随时插入工具调用、外部验证、人工干预）
- 可调试性（每一步都可见，容易调试和优化）
- 工具集成（更容易集成复杂的外部工具和 API）

**适用场景：**

**选择 Thinking Mode 当：**
- 任务主要是推理密集型（数学、逻辑、代码分析）
- 不需要外部工具调用
- 希望控制 API 调用次数和成本
- 推理过程不需要人工干预

**选择 Plan/Execute 当：**
- 需要调用外部工具或 API
- 需要多轮交互（与用户或环境）
- 需要精确控制每一步的行为
- 需要在推理过程中插入人工验证

---

## 参考资料

[^anthropic-2025-thinking]: Anthropic. *Claude's Extended Thinking*. 2025. https://www.anthropic.com/news/visible-extended-thinking
[^deepseek-2025-r1]: DeepSeek-AI. *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via RL*. 2025. https://github.com/deepseek-ai/DeepSeek-R1
[^zhao-2025-t2]: Zhao et al. "T²: An Adaptive Test-Time Scaling Strategy for Contextual Question Answering". 2025. https://arxiv.org/abs/2505.17427
[^xie-2026-early]: Xie et al. "Statistical Early Stopping for Reasoning Models". 2026. https://arxiv.org/abs/2602.13935
[^guo-2025-entropy]: Guo. "Measuring Reasoning Utility in LLMs via Conditional Entropy Reduction". 2025. https://arxiv.org/abs/2508.20395
