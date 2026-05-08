---
title: 推理与规划
description: 推理模型、test-time compute scaling、过程奖励模型等前沿方向。
created: 2026-04-07
updated: 2026-04-10
tags: [reasoning, test-time-compute, prm, o1, deepseek-r1]
review:
---

# 推理与规划 (Reasoning & Planning)

??? note "背景知识"
    - **LLM (大语言模型)**：基于 Transformer 的自回归语言模型 → [详见](../foundations/transformer.md)
    - **Chain-of-Thought (CoT)**：让模型逐步推理而非直接给答案，显著提升复杂任务表现
    - **RLHF**：用人类反馈训练奖励模型，再用奖励模型优化 LLM 输出
    - **Scaling Laws**：模型性能随参数量、数据量、计算量的可预测提升规律

> 推理模型是 2024-2026 年 AI 领域最重要的突破之一，本文档追踪推理模型、test-time compute、过程奖励模型等方向的最新进展。

---

## 概述

2024-2026 年 AI 领域最重要的突破之一：让模型在回答前进行**深度推理**，显著提升复杂任务的表现。

## 主要模型

| 模型 | 厂商 | 时间 | 特点 |
|------|------|------|------|
| **o1** | OpenAI | 2024.9 | 首个商业推理模型 |
| **o3** | OpenAI | 2025 | o1 后续，更强推理 |
| **DeepSeek-R1** | DeepSeek | 2025.1 | 开源推理模型标杆 |
| **Gemini Deep Think** | Google | 2026.2 | 面向科学和数学 |
| **QED-Nano** | 研究论文 | 2026.4 | 教小模型证明困难定理 |

## 核心技术

**Test-time Compute Scaling (推理时计算扩展)**

传统 Scaling: 更大的模型 + 更多训练数据 → 更好的性能
新 Scaling: 推理时更多计算 (更多思考 token) → 更好的性能

```
简单问题: 投入少量推理计算 → 快速回答
复杂问题: 投入大量推理计算 → 深度思考后回答
```

**过程奖励模型 (Process Reward Model, PRM)**

```
传统 (ORM): 只看最终答案对不对
PRM:        评估每个推理步骤的正确性

步骤1: 正确 ✓ (+1)
步骤2: 正确 ✓ (+1)
步骤3: 错误 ✗ (-1) ← 这里出了问题
步骤4: 基于错误继续...
```

**QED-Nano (2026.4)**

教极小模型 (Nano 级别) 证明困难的数学定理：
- 使用 LM-Provers 框架
- 证明了小模型在特定推理任务上也能有惊人表现
- 对"推理能力需要多大模型"的认知提出挑战

**ETR: Entropy Trend Reward（2026.4）**

高效 CoT 推理的一个关键问题：如何让模型在推理时既保持足够的思考深度，又不浪费 token 在无效推理上？ETR[^etr-2026] 提出用**熵趋势**作为推理质量的实时信号：

- 监控生成过程中 token 分布的熵变化趋势——有效推理应使后续 token 分布的熵持续下降（越推理越确定）
- 将熵的下降趋势作为 reward，鼓励模型生成"越想越清楚"的推理链，惩罚"越想越混乱"的无效推理
- 本质是为推理过程建立了一个无需外部标注的自监督质量信号

**SFT 泛化的条件性（2026.4）**

"SFT 只会记忆、RL 才能泛化"是 LLM 后训练的主流叙事。Ren et al.[^ren-2026-sft] 用 long-CoT 监督重新审视这一论断，发现跨域泛化**并非缺失，而是有条件的**：

- **优化动力学**：跨域性能先降后升（dip-and-recovery），短训练的 checkpoint 会低估泛化能力
- **数据质量**：低质量解答普遍伤害泛化；经验证的 long-CoT trace 则带来稳定的跨域增益
- **模型能力**：强模型能内化可迁移的程序性模式（如 backtracking），弱模型仅模仿表面冗长
- **不对称性**：推理能力提升的同时安全性下降——问题从"SFT 能否泛化"变为"在什么条件下泛化、代价是什么"

**StepFlow: 修复推理信息流（2026.4, ACL 2026）**

Xu et al.[^xu-2026-stepflow] 提出 Step-Saliency 分析工具，将注意力-梯度分数池化为步骤间信息流图，发现两类反复出现的失败模式：

- **Shallow Lock-in**：浅层过度聚焦当前步骤，几乎不利用早期上下文
- **Deep Decay**：深层对思考段的显著性逐渐衰减，总结段越来越多地自注意

基于此提出 StepFlow——无需重训练的推理时干预：在浅层用 Odds-Equal Bridge 校正显著性模式，在深层用 Step Momentum Injection 注入步骤级残差。在数学、科学、代码任务上提升了多个推理模型的准确率。

**SELFDOUBT: 单次推理的不确定性量化（2026.4）**

推理模型的不确定性估计一直受限于成本：采样方法需要多次推理，单次探针方法又不够可靠。SELFDOUBT[^selfdoubt-2026] 提出 Hedge-to-Verify Ratio——利用推理链中犹豫/对冲表达与验证表达的比率作为不确定性信号，仅需一次推理即可估计置信度。

---

## 参考资料

- Lightman et al., "Let's Verify Step by Step" (Process Reward Models), 2023 - [arXiv:2305.20050](https://arxiv.org/abs/2305.20050)
- QED-Nano: Teaching a Tiny Model to Prove Hard Theorems - [arXiv:2604.04898](https://arxiv.org/abs/2604.04898)
[^etr-2026]: "ETR: Entropy Trend Reward for Efficient Chain-of-Thought Reasoning". 2026. https://arxiv.org/abs/2604.05355
[^ren-2026-sft]: Ren et al. "Rethinking Generalization in Reasoning SFT". 2026. https://arxiv.org/abs/2604.06628
[^xu-2026-stepflow]: Xu et al. "Reasoning Fails Where Step Flow Breaks". ACL 2026. https://arxiv.org/abs/2604.06695
[^selfdoubt-2026]: "SELFDOUBT: Uncertainty Quantification for Reasoning LLMs via the Hedge-to-Verify Ratio". 2026. https://arxiv.org/abs/2604.06389
