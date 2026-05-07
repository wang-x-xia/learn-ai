---
title: 提示工程 (Prompt Engineering)
description: 从手工技巧到系统设计思维——提示工程如何适应 Agent 时代的 AI 交互范式。
created: 2026-04-07
updated: 2026-05-07
tags: [prompt-engineering, cot, few-shot, dspy, agents]
review: 2026-05-07
---

# 提示工程 (Prompt Engineering)

> 提示工程是与 LLM 高效交互的艺术和科学。随着模型能力提升和 Agent 系统兴起，提示工程从"手工打磨技巧"演变为"系统设计思维"——关注如何通过提示定义 Agent 行为、工具使用和协作模式。

---

## 1. 概述

### 什么是提示工程

提示工程 (Prompt Engineering) 是设计和优化输入给 LLM 的文本（提示/Prompt），以引导模型生成期望输出的技术。

### 为什么重要（2024-2025 年视角）

随着模型能力提升和应用范式转变，提示工程的重要性发生了变化：

| 维度 | 2022-2023 年（早期） | 2024-2025 年（当前） |
|------|---------------------|---------------------|
| **核心场景** | 直接对话、单轮任务 | Agent 编排、工具调用、多步推理 |
| **技能门槛** | 高（需要掌握 CoT、Few-shot 等技巧） | 低（模型更"听话"，自然语言即可） |
| **边际收益** | 10x 性能提升 | 1.2x 性能提升 |
| **关注点** | 提示词本身 | Agent 行为定义、工具描述、协作协议 |
| **固化方式** | 手工编写 | 系统提示、产品化配置（Skills、GPTs） |

### 与其他方法的关系（更新）

```
提示工程 (交互设计基础)
    ↓ 
Agent 编排 (LangGraph、MAF、AutoGen)
    ↓
工具调用 (Function Calling、MCP)
    ↓
RAG (需要外部知识时)
    ↓
微调 (需要特定行为/风格时)
```

**关键变化**：提示工程不再是一个独立的"优化手段"，而是 Agent 系统的**基础设施**——通过提示定义 Agent 的行为边界、工具使用策略和协作模式。

---

## 2. 提示技巧概览

提示技巧从手工打磨发展到系统化方法论，主要包括：

- Zero-shot/Few-shot 提示
- System Prompt 角色设定
- 输出格式控制
- 采样参数调优（Temperature、Top-p）
- Chain-of-Thought (CoT) 思维链[^wei-2022-cot]
- Zero-shot CoT 零样本思维链
- Self-Consistency 自洽性验证[^wang-2022-sc]
- Tree of Thoughts (ToT) 树状推理[^yao-2023-tot]
- ReAct 推理-行动协同[^yao-2022-react]
- 结构化输出（JSON Mode、Schema 约束）

这些技巧通过提供示例、引导推理步骤、多次采样投票等方式提升模型性能，但随着模型能力提升，许多技巧已内化为模型默认行为。

---

## 3. 提示框架与程序化

提示框架和程序化工具提供结构化的提示开发方式：

- **CRISPE 框架**：涵盖 Capacity（角色能力）、Role（具体角色）、Insight（背景信息）、Statement（具体任务）、Personality（风格）、Experiment（限制）
- **CO-STAR 框架**：涵盖 Context（背景）、Objective（目标）、Style（风格）、Tone（语气）、Audience（受众）、Response（回复格式）
- **DSPy[^dspy-2023]**：将提示工程程序化，通过定义输入输出 Schema 自动优化提示，实现可测试、可迭代的提示开发流程

---

## 4. 发展趋势与 Agent 时代的新角色

### 4.1 为什么提示工程"热度下降"？

2024-2025 年，提示工程作为独立技术话题的讨论热度显著下降，主要原因：

1. **模型能力提升，指令遵循增强**
   - GPT-4.5、Claude 3.5/4、Gemini 2.0 等模型在指令遵循能力上有显著提升
   - 以前需要精心设计的 CoT 提示词，现在模型自己就能主动推理
   - 以前需要复杂的格式约束，现在模型能更好地理解结构化输出要求
   - **结果**：简单的自然语言指令就能得到不错的结果

2. **Agent 和工具调用成为主流**
   - 开发范式从"提示词工程"转向"Agent 编排"
   - 通过 Function Calling 调用外部 API/数据库，而非依赖提示词中的知识
   - 多 Agent 系统通过协作解决问题，而非单一超级提示词
   - **结果**：工程师关注点从"如何写好提示词"转移到"如何设计 Agent 架构"

3. **系统提示词的最佳实践被固化**
   - 模型厂商在系统提示词中内置了常见最佳实践
   - 平台层提供预设的提示词模板（Anthropic Skills、OpenAI GPTs）
   - 企业级应用使用统一的提示词模板库
   - **结果**：提示词工程变成"配置"而非"工程"，可见度降低

4. **注意力转移到更高层抽象**
   - Agent 编排（LangGraph、MAF、AutoGen）
   - 记忆系统（RAG、向量数据库）
   - 工具生态（MCP、OpenAPI）
   - 推理优化（KV Cache、量化、蒸馏）
   - **结果**：这些更高层技术能带来更大杠杆效应，吸引更多关注

5. **边际收益递减**
   - 早期（2022-2023）：精心设计的提示词能带来 10x 性能提升
   - 现在（2024-2025）：精心设计的提示词可能只带来 1.2x 提升
   - **机会成本**：同样的时间投入在 Agent 设计或 RAG 系统上，收益更大

6. **产品化工具降低门槛**
   - ChatGPT Custom Instructions、GPTs
   - Claude Skills
   - 低代码平台（Dify、Coze）
   - **结果**：用户通过 UI 配置就能实现以前需要提示词工程才能做到的效果

### 4.2 提示工程会消亡吗？

**不会，但角色发生了转变**：

| 角色 | 2022-2023 年 | 2024-2025 年 |
|------|-----------|-----------|
| **形态** | 手工打磨提示词 | 系统设计思维 |
| **场景** | 直接对话优化 | Agent 行为定义 |
| **技能** | 掌握 CoT、Few-shot | 理解 Agent 架构 |
| **固化** | 代码中的字符串 | Skills、GPTs、配置文件 |
| **价值** | 直接提升输出质量 | 定义系统边界和行为 |

提示工程从"显性技术"转为"隐性基础设施"，但仍然是 AI 交互的核心能力。

### 4.3 Agent 时代的提示工程

在 Agent 系统中，提示工程的新关注点从直接对话优化转向 Agent 行为定义：

- **Agent 行为定义**：通过系统提示定义 Agent 的职责边界、工具使用规则、协作协议和错误处理策略
- **工具描述提示**：为 Function Calling 提供清晰的工具语义、使用场景、输入输出格式和约束条件
- **多 Agent 协作提示**：定义 Router Agent 的路由决策逻辑、子 Agent 的能力描述、Agent 间的通信协议和上下文传递规则

### 4.4 程序化提示 (DSPy) 在 Agent 时代的价值

DSPy 从手工编写提示转向程序化定义和自动优化，在 Agent 系统中尤为重要。它将 Agent 行为定义为可测试、可优化的 Schema，支持自动搜索最优的 Agent 提示策略，实现版本控制和 A/B 测试不同的 Agent 配置。

### 4.5 模型特定策略

不同模型对提示的响应不同，Agent 系统需要针对性适配：GPT 系列遵循详细指令效果好，Claude 理解细微语境能力强，Gemini 多模态指令表现优异，开源模型通常需要更明确的指令和更多的示例。

---

## 参考资料

[^wei-2022-cot]: Wei et al. *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. 2022. https://arxiv.org/abs/2201.11903
[^wang-2022-sc]: Wang et al. *Self-Consistency Improves Chain of Thought Reasoning*. 2022. https://arxiv.org/abs/2203.11171
[^yao-2023-tot]: Yao et al. *Tree of Thoughts: Deliberate Problem Solving with Large Language Models*. 2023. https://arxiv.org/abs/2305.10601
[^yao-2022-react]: Yao et al. *ReAct: Synergizing Reasoning and Acting in Language Models*. 2022. https://arxiv.org/abs/2210.03629
[^dspy-2023]: Stanford NLP. *DSPy: Declarative Self-improving Language Programs, Pythonically*. 2023. https://github.com/stanfordnlp/dspy

### 相关文档
- Agent 智能体: [ai-agents.md](ai-agents.md)
- Agent 工具接入: [agent-tools.md](agent-tools.md)
- Agent Skills: [agent-skills.md](agent-skills.md)
