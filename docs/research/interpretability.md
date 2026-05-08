---
title: "可解释性"
description: "LLM 可解释性研究——从理论框架到逆向工程方法，理解模型为什么有效、如何打开黑箱。"
created: 2026-04-14
updated: 2026-04-14
tags: [interpretability, mechanistic-interpretability, representation-engineering, emergence, grokking]
review: 2026-05-08
---

# 可解释性 (Interpretability)

??? note "背景知识"
    - **Transformer 架构**：多层自注意力 + FFN 的堆叠，当前 LLM 的底层结构 → [详见](../foundations/transformer.md)
    - **表示学习**：模型自动学习特征表示，代价是黑箱化 → [详见](../foundations/representation-learning.md)
    - **Embedding 空间**：模型将输入映射到的高维连续向量空间，语义相近的概念距离近
    - **Superposition 假说**：神经网络在低维空间中用叠加方式编码高维特征

> 表示学习让模型自己学特征，代价是黑箱化（见 [从规则到表示学习](../foundations/representation-learning.md)）。可解释性研究试图在不牺牲性能的前提下打开这个黑箱。
>
> 本文档覆盖两个层次的"理解"：**理论框架**（为什么模型能工作）和**逆向工程方法**（模型内部到底在做什么）。
>
> 相关文档：[AI 安全与治理](./safety-and-governance.md) | [Transformer 架构](../foundations/transformer.md)

---

## 1. 理论框架：为什么 Next-Token Prediction 能涌现高级能力

### 1.1 压缩即智能

模型参数量远小于训练数据量，因此模型**必须压缩**。为了用有限参数准确预测下一个 token，模型被迫提取数据中的规律——因果关系、逻辑推理、物理常识等。

这不是偶然：Marcus Hutter 的理论指出，Solomonoff 的通用预测器在数学上等价于 Kolmogorov 的通用最佳压缩器[^hutter-2004]。**预测准 = 压缩好 = 学到了生成数据的底层结构。**

Ilya Sutskever 曾将此概括为"压缩即智能"：模型为了降低 Loss，被迫在权重中构建一套世界模型。

### 1.2 涌现与 Scaling Laws

OpenAI 在 2020 年发现模型损失与参数量、数据量之间存在稳定的幂律关系，跨越七个数量级[^kaplan-2020]。DeepMind 的 Chinchilla 修正了最优配比：参数与训练 token 应等比例增长[^hoffmann-2022]。

Wei et al. (2022) 定义了"涌现能力"：在小模型中完全不存在、但在大模型中突然出现的能力，无法通过外推小模型性能来预测[^wei-2022]。该论文在 GPT-3 (0.3B→175B)、LaMDA (2B→137B)、PaLM (8B→540B) 上实验，涌现拐点因任务而异——简单算术约在 ~10B 出现，复杂推理约在 ~100B。

但 Stanford 的 Schaeffer et al. (2023) 提出质疑：涌现可能是**评估指标的假象**——非线性/离散指标（如精确匹配准确率）会把连续的性能提升呈现为突变；换成连续指标（如 token 级 loss），"突变"消失了[^schaeffer-2023]。

**当前共识**：涌现是否为真实相变仍无定论。但 Grokking 现象（见下节）确实可以用临界指数描述，表现出类似一阶相变的特征。

### 1.3 Grokking（顿悟）

Power et al. (2022) 发现的现象[^power-2022]：模型在训练集上已经过拟合（准确率 100%），继续训练后，验证集准确率在某个时刻突然飙升。

这意味着模型从"死记硬背"切换到了"学会通解"。在实践中，这个 Grokking 拐点已经可以被一定程度地控制——研究发现在拐点瞬间，模型内部的回路发生重组，从统计相关性输出转向类似程序执行的模块化结构。

Grokking 为理解涌现提供了一个微观窗口：它表明模型内部存在从记忆到推理的相变，不仅仅是规模效应。

### 1.4 代码数据与逻辑能力

代码是逻辑密度最高的文本——差一个符号就编译失败。模型在预测代码 token 时被迫学会状态跟踪（记住 100 行前定义的变量类型）、长距离依赖和严格逻辑一致性。

实验证据：从训练数据中剔除代码后，模型推理能力出现显著下降。代码训练带来的逻辑能力可以迁移到自然语言任务——这可能是当前模型写作逻辑清晰（第一点、第二点……）的来源。

### 1.5 批评视角

| 批评者 | 观点 | 参考 |
|--------|------|------|
| **Bender et al. (2021)** | LLM 只是"随机鹦鹉"——概率性地链接词语，不考虑意义[^bender-2021] | 该论文引发 Gebru 被 Google 辞退事件 |
| **Gary Marcus** | 神经网络无法可靠外推和进行形式推理；规模定律正在遇到收益递减[^marcus-2018] | 持续批评至 2025 CACM 访谈 |

这些批评指向一个核心问题：当前的可解释性方法还无法判定模型究竟是"真正理解"还是"高级模式匹配"。

---

## 2. 逆向工程方法：打开黑箱的四条路线

### 2.1 事后归因 (Post-hoc Attribution)

最早出现的路线：模型不动，事后解释"输出主要被输入的哪部分影响"。

| 方法 | 时间 | 做法 | 权衡 |
|------|------|------|------|
| **LIME** | 2016 | 对输入做局部扰动，拟合线性模型近似局部决策边界[^ribeiro-2016] | 只解释局部，不同运行结果可能不一致 |
| **SHAP** | 2017 | 基于博弈论 Shapley value，给每个输入特征分配贡献值[^lundberg-2017] | 计算成本高，特征间交互难以捕捉 |
| **注意力可视化** | — | 画 attention heatmap，看模型"注意了哪些词" | 注意力权重 ≠ 重要性[^jain-2019] |

**局限**：只告诉你"模型看了哪里"，不告诉你"模型怎么处理看到的东西"。适合快速 debug，不适合深层理解。

### 2.2 机械可解释性 (Mechanistic Interpretability)

Chris Olah 开创、Anthropic 主推的路线。目标最雄心：**逆向工程神经网络，还原为人类可读的算法。**

**核心概念**

- **特征 (Features)**：模型内部学到的有意义的概念表示（如"Golden Gate Bridge"特征在提到金门大桥时激活）
- **叠加 (Superposition)**：模型用 N 个神经元表征远多于 N 个概念，类似压缩编码，这是可解释性的核心难题
- **稀疏自编码器 (SAE)**：从叠加表示中提取独立的可解释特征（`模型隐藏状态 → SAE → 独立特征`）
- **回路分析 (Circuit Analysis)**：追踪模型内部特定行为的信息流动路径

**关键成果**

| 成果 | 时间 | 意义 |
|------|------|------|
| **Induction Heads**[^olah-2022] | 2022 | 发现负责 in-context learning 的具体回路——模型学会了"A 后面跟过 B，下次见 A 就预测 B"这个算法 |
| **Scaling Monosemanticity**[^anthropic-2024-sae] | 2024 | 在 Claude Sonnet 上用 SAE 提取数百万可解释特征，证明该方法可扩展到大模型 |
| **Golden Gate Claude** | 2024 | 放大特定特征可因果地改变模型行为，证明提取的特征是因果性的 |
| **情感概念与功能** | 2026.4 | 理解模型如何表征和使用情感概念 |
| **行为差异检测工具** | 2026.3 | "diff" 工具发现新旧模型的行为差异 |
| **ADAG**[^adag-2026] | 2026.4 | 自动将回路归因图转化为自然语言描述，降低可解释性研究门槛 |

**工具生态**：TransformerLens (Neel Nanda / EleutherAI)、SAELens、Neuronpedia（在线浏览 SAE 特征）、Gemma Scope 2 (Google DeepMind, 2025.12, 开源)

**局限**：只能解释局部回路，离"完全审计模型推理"还很远。SAE 提取的特征是否忠实 (faithful)、是否完备 (complete)，尚无理论保证。

### 2.3 表示工程 (Representation Engineering)

MIT Zou et al. (2023) 提出[^zou-2023]。思路：**在激活空间中找到对应特定概念的方向向量，通过偏移该方向来引导行为。**

比如找到"诚实"方向，推理时加偏移 → 模型变得更诚实。与机械可解释性的区别：表示工程关注高层概念方向，不关心底层回路细节。

**核心假设——线性表示假说 (Linear Representation Hypothesis)**：很多高层概念（诚实、权力追求、情感）在激活空间中表现为线性方向。实验证据支持这一点——如果成立，意味着模型内部的概念组织比想象中规整。

### 2.4 内在可解释模型 (Inherently Interpretable)

另一条路：不解释黑箱，而是**设计天生可解释的模型**。

- **Concept Bottleneck Models**：模型先预测人类定义的中间概念（"有羽毛""会飞"），再基于概念做最终预测，每步透明
- **决策树、规则学习**：传统方法的回归

**权衡**：可解释性和性能之间存在 trade-off。内在可解释模型在复杂任务上通常不如黑箱大模型，因此在前沿能力上应用有限。

---

## 3. 行业投入格局

| 机构 | 侧重 | 投入程度 |
|------|------|----------|
| **Anthropic** | 机械可解释性（SAE、回路分析）| 核心战略，投入最大 |
| **Google DeepMind** | Gemma Scope 工具链，开源给社区 | 中等，工具导向 |
| **OpenAI** | 发过 SAE 论文，2024 年解散超级对齐团队 | 低，非战略重点 |
| **EleutherAI** | 开源工具 (TransformerLens) | 社区驱动 |
| **学术界** | MIT（表示工程）、牛津等 | 零散课题组 |

Anthropic 是唯一把可解释性当核心战略的大厂。其他家更多是"发几篇论文"的程度。

---

## 参考资料

[^hutter-2004]: Hutter, M. *Universal Artificial Intelligence: Sequential Decisions Based on Algorithmic Probability*. 2004.
[^kaplan-2020]: Kaplan, J. et al. *Scaling Laws for Neural Language Models*. 2020. https://arxiv.org/abs/2001.08361
[^hoffmann-2022]: Hoffmann, J. et al. *Training Compute-Optimal Large Language Models (Chinchilla)*. 2022. https://arxiv.org/abs/2203.15556
[^wei-2022]: Wei, J. et al. *Emergent Abilities of Large Language Models*. 2022. https://arxiv.org/abs/2206.07682
[^schaeffer-2023]: Schaeffer, R. et al. *Are Emergent Abilities of Large Language Models a Mirage?*. 2023. https://arxiv.org/abs/2304.15004
[^power-2022]: Power, A. et al. *Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets*. 2022. https://arxiv.org/abs/2201.02177
[^bender-2021]: Bender, E.M. et al. *On the Dangers of Stochastic Parrots*. 2021. https://dl.acm.org/doi/10.1145/3442188.3445922
[^marcus-2018]: Marcus, G. *Deep Learning: A Critical Appraisal*. 2018. https://arxiv.org/abs/1801.00631
[^ribeiro-2016]: Ribeiro, M.T. et al. *"Why Should I Trust You?": Explaining the Predictions of Any Classifier*. 2016. https://arxiv.org/abs/1602.04938
[^lundberg-2017]: Lundberg, S.M. & Lee, S.I. *A Unified Approach to Interpreting Model Predictions*. 2017. https://arxiv.org/abs/1705.07874
[^jain-2019]: Jain, S. & Wallace, B.C. *Attention is not Explanation*. 2019. https://arxiv.org/abs/1902.10186
[^olah-2022]: Olsson, C. et al. *In-context Learning and Induction Heads*. 2022. https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
[^anthropic-2024-sae]: Templeton, A. et al. *Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet*. 2024. https://transformer-circuits.pub/2024/scaling-monosemanticity/
[^zou-2023]: Zou, A. et al. *Representation Engineering: A Top-Down Approach to AI Transparency*. 2023. https://arxiv.org/abs/2310.01405
[^adag-2026]: "ADAG: Automatically Describing Attribution Graphs". 2026. https://arxiv.org/abs/2604.07615
