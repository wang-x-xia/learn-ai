---
title: "Mamba 与状态空间模型 (SSM)"
description: "状态空间模型核心原理、Mamba 选择性机制、Mamba-2 的 SSD 框架以及 Transformer-SSM 混合架构的深度解析。"
created: 2026-04-08
updated: 2026-04-28
tags: [mamba, ssm, state-space-model, jamba, hybrid-architecture]
review: 2026-04-28
---

# Mamba 与状态空间模型 (SSM)

??? note "背景知识"
    - **Transformer 自注意力**：O(n²) 复杂度，每个 token 看所有历史 token → [详见](./transformer.md#2)
    - **KV Cache**：自回归推理时缓存历史 K/V 向量，显存随序列长度线性增长 → [详见](./kv-cache.md)
    - **RNN (循环神经网络)**：按时间步顺序处理序列，用隐状态传递历史信息，训练无法并行
    - **离散化**：将连续时间的微分方程转换为离散时间步的递推公式，使其可在数字计算机上执行

> 状态空间模型是 Transformer 之外最重要的序列建模范式。本文档覆盖 SSM 核心原理、Mamba 的选择性突破、替代架构的探索，以及 Transformer-SSM 混合架构的前沿实践。
>
> 相关文档：[Transformer 架构](./transformer.md)

---

## 1. 为什么需要 Transformer 的替代方案？

Transformer 的核心瓶颈是**注意力的二次复杂度**：

| 操作 | 训练复杂度 | 推理复杂度（生成第 t 个 token） |
|------|-----------|-------------------------------|
| 自注意力 | O(n²d) | O(td)（需看所有历史，但 KV cache 帮助） |
| KV cache 内存 | — | O(n · d · layers)，随上下文线性增长 |
| FFN | O(nd²) | O(d²)（与序列长度无关） |

当上下文长度达到 128K-2M 时，KV cache 内存成为实际部署的主要瓶颈。例如，Llama-70B 在 128K 上下文时，KV cache 需要 ~40GB——可能比模型参数本身还大。

这催生了对**线性复杂度序列建模**的需求。

---

## 2. 状态空间模型基础

### 直觉理解

对比两种"记笔记"策略，可以快速抓住 SSM 与 Transformer 的本质区别：

- **Transformer**：逐字记录老师说的每句话（KV cache）。回答问题时翻遍所有笔记，找到最相关的几句（attention）。笔记越长，翻得越慢、本子越厚。
- **SSM**：只维护一份固定长度的"摘要"（隐状态 h）。每听到一句新话，就更新摘要——有的内容融进去，有的旧内容被覆盖。回答问题时只看这份摘要，大小永远不变。

这个类比也预示了 SSM 的根本限制：摘要终究是有损压缩，精确回忆不如逐字记录（详见[第 5 节](#5-ssm-vs-transformer)）。

### 形式化定义

状态空间模型（State Space Model）将序列建模形式化为连续动力系统的离散化：

```
连续形式:
  h'(t) = Ah(t) + Bx(t)    # 状态转移
  y(t)  = Ch(t) + Dx(t)    # 输出

离散化 (零阶保持):
  h_t = Ā h_{t-1} + B̄ x_t
  y_t = C h_t + D x_t
```

其中 `h` 是隐状态，`A` 是状态转移矩阵（编码了"记忆"的结构），`B`/`C` 是输入/输出投影。

**各矩阵的作用：**
- **Ā**：控制"记住多少过去"（记忆衰减系数）
- **B̄**：控制"吸收多少现在"（输入吸收系数）
- **C**：控制"从记忆中提取多少来输出"（记忆提取系数）
- **D**：控制"直接从输入输出多少"（通常很小或为 0）

**一维简化示例**：假设隐状态只有一个数字，Ā = 0.9，B̄ = 0.1（保留 90% 旧记忆，吸收 10% 新输入）：

```
输入序列: x = [5, 3, 8, 1]     初始状态: h₀ = 0

h₁ = 0.9 × 0   + 0.1 × 5 = 0.5    ← 开始记住"5"
h₂ = 0.9 × 0.5 + 0.1 × 3 = 0.75   ← 融入"3"，"5"的影响衰减
h₃ = 0.9 × 0.75 + 0.1 × 8 = 1.475  ← 融入"8"
h₄ = 0.9 × 1.475 + 0.1 × 1 = 1.428  ← "8"的影响已在衰减
```

Ā 越大（接近 1），记忆越长；Ā 越小，遗忘越快。实际模型中隐状态是高维向量、A 是矩阵，但更新逻辑完全相同。

早期 SSM（如 S4、H3）的 A, B, C 矩阵是**固定参数**，无法根据当前输入选择性地记忆或遗忘，导致在语言建模上表现不佳。Mamba 正是为了解决这个问题而生。

---

## 3. Mamba：选择性状态空间模型

Mamba[^mamba-2023] 是 SSM 范式的决定性突破，首次在语言建模上匹配 Transformer 质量，同时保持线性复杂度。

### 核心创新：选择性机制（Selection Mechanism）

Mamba 的核心改变：让 **B 和 C 成为输入的函数**：

```
早期 SSM: B, C = 固定参数
Mamba:    B = f_B(x_t), C = f_C(x_t)    # 输入依赖
```

这个看似简单的改变有深刻的含义：

1. **选择性记忆**：模型可以根据当前输入决定记什么、忘什么
2. **等效于门控 RNN**：选择性 SSM 在概念上等价于一个数据依赖的门控 RNN，但计算方式完全不同
3. **内容感知推理**：Transformer 的注意力天然是内容感知的（token 间的相似度决定权重）；选择性机制让 SSM 也获得了这种能力

Mamba 的工程创新解决了选择性带来的计算效率问题，在长序列时速度可达同参数量 Transformer 的 3-5x。

---

## 4. Mamba-2：结构化状态空间对偶性

Mamba-2[^mamba2-2024] 从理论上统一了 SSM 和注意力机制，提出了 **SSD（Structured State Space Duality）** 框架。

该框架证明了选择性 SSM 等价于一种**半可分矩阵（semiseparable matrix）** 形式的结构化注意力。具体地：

```
SSM 视角:  h_t = A_t h_{t-1} + B_t x_t, y_t = C_t h_t
注意力视角: y = M ⊙ (QK^T) V
           其中 M 是因果掩码 × 衰减矩阵
```

两种计算给出**数学上完全等价**的结果，但计算复杂度不同：

- **SSM 模式**（循环）：O(n) 时间，O(1) 推理步骤内存 → 适合推理
- **注意力模式**（矩阵乘法）：O(n²) 时间，高并行度 → 适合训练

**训练加速的实现**：SSD 理论本身不直接加速训练，但它揭示了两种计算模式的等价性，从而启发了更高效的实现策略。Mamba-2 采用**分块处理**：将序列分成长度 T 的块，块内用矩阵乘法（充分利用 GPU tensor core），块间用循环传递状态。这种实现比 Mamba-1 的训练速度快 2-8x，同时在 scaling 行为上更接近 Transformer++（带 GQA、SwiGLU 等优化的 Transformer）。

---

## 5. SSM vs Transformer：能力边界

SSM 并非万能。关键实验发现：

| 能力 | Transformer | Mamba | 原因 |
|------|-------------|-------|------|
| **In-context learning** | 强 | 弱 | 注意力可以直接"查表"（KV 精确匹配）；SSM 必须将信息压缩进固定大小的隐状态 |
| **精确回忆** | 强（KV cache） | 弱 | 隐状态大小固定，信息量有上限 |
| **长程依赖** | 受窗口限制 | 理论上无限 | SSM 的隐状态可以携带任意远的信息（但有损） |
| **推理效率** | KV cache 随长度增长 | O(1) 状态 | SSM 不需要缓存历史 token |
| **归纳推理** | 弱（但可通过 CoT 缓解） | 更弱 | 两者都不擅长，但 Transformer 的精确回忆能力有助于 CoT |

**核心权衡**：Transformer 用 O(n) 内存（KV cache）换取精确的信息检索；SSM 用 O(1) 内存实现高效推理，但信息必须经过有损压缩。这是信息论意义上的根本矛盾。

---

## 6. 混合架构：融合两个范式

纯 SSM 在精确回忆和 in-context learning 上弱于 Transformer，纯 Transformer 在长序列推理效率上有瓶颈。混合架构尝试两全其美。

### Jamba（AI21 Labs）

Jamba[^jamba-2024] 是第一个大规模部署的 Transformer-Mamba 混合模型：

```
Jamba 架构 (52B 总参 / 12B 活跃参):
  Layer 1-4:   Mamba block
  Layer 5:     Transformer attention block
  Layer 6-9:   Mamba block
  Layer 10:    Transformer attention block + MoE
  ...重复...
```

**设计原理**：大部分层用 Mamba（高效处理序列），每隔几层插入一个 Transformer 注意力层（提供精确的信息检索能力）。MoE 进一步扩大参数容量。

**效果**：256K 上下文窗口；相比同参数量的纯 Transformer，推理吞吐提升 3x，质量持平。

### Zamba（Zyphra）

Zamba 的独特设计：**所有 Mamba 层之间共享同一个注意力层**：

```
Mamba → 共享 Attention → Mamba → 共享 Attention → Mamba → ...
```

这进一步压缩了参数量（注意力层只有一份权重），特别适合端侧部署。Zamba-2 在 2.7B 参数量级上达到了可观的质量。

### 其他混合探索

| 模型 | 组织 | 混合方式 |
|------|------|----------|
| **Griffin** | Google DeepMind | 循环层 (RLKV) + 局部注意力 |
| **RecurrentGemma** | Google | 基于 Griffin 的开源模型 |
| **StripedHyena** | Together AI | Hyena (长卷积) + 注意力交替 |
| **Samba** | Microsoft | Mamba + Sliding Window Attention |

**混合比例是关键**：研究表明注意力层的比例只需 ~15-25% 即可恢复大部分精确回忆能力，更多的注意力层对推理效率的损害大于质量收益。

---

## 7. 工程选型

| 场景 | 推荐架构 | 理由 |
|------|----------|------|
| 通用 LLM（追求最强质量） | Transformer + GQA/MLA | 生态最成熟，scaling 行为最可预测 |
| 超长上下文（>256K） | 混合 Mamba-Transformer | KV cache 是纯 Transformer 的硬瓶颈 |
| 端侧部署 | SSM/混合 + 量化 | O(1) 推理内存，不受上下文长度限制 |
| 高吞吐服务 | 依场景而定 | 短 prompt 选 Transformer（prefill 并行度高）；长 prompt 选混合 |
| 实时流式处理 | SSM/RWKV | 天然的流式推理，无需 KV cache 管理 |

---

## 参考资料

[^mamba-2023]: Gu & Dao. *Mamba: Linear-Time Sequence Modeling with Selective State Spaces*. 2023. https://arxiv.org/abs/2312.00752
[^mamba2-2024]: Dao & Gu. *Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality*. 2024. https://arxiv.org/abs/2405.21060
[^jamba-2024]: Lieber et al. *Jamba: A Hybrid Transformer-Mamba Language Model*. 2024. https://arxiv.org/abs/2403.19887
