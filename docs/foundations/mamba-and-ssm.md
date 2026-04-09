---
title: "Mamba 与状态空间模型 (SSM)"
description: "状态空间模型从 S4 到 Mamba 的演进路径、替代架构（RWKV/xLSTM/RetNet）以及 Transformer-SSM 混合架构的深度解析。"
created: 2026-04-08
updated: 2026-04-09
tags: [mamba, ssm, state-space-model, rwkv, xlstm, jamba, hybrid-architecture]
review:
---

# Mamba 与状态空间模型 (SSM)

> 状态空间模型是 Transformer 之外最重要的序列建模范式。本文档追踪从 S4 到 Mamba 的技术演进、替代架构的探索，以及 Transformer-SSM 混合架构的前沿实践。
>
> 相关文档：[Transformer 架构](./transformer.md) | [大语言模型概览](./large-language-models.md)

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

## 2. 从 S4 到 Mamba：SSM 的演进

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

### 2.1 S4（Structured State Spaces for Sequence Modeling, 2021）

S4[^s4-2021] 的关键突破是发现 `A` 矩阵的初始化方式决定了一切：

- 使用 **HiPPO（High-order Polynomial Projection Operator）** 矩阵初始化 `A`，使隐状态能够最优地压缩输入历史
- HiPPO 的数学含义：将输入信号投影到 Legendre 多项式基上，等效于对历史信号的最优低秩近似

S4 在长程建模基准（Long Range Arena, Path-X）上大幅超越 Transformer，但在语言建模上表现不佳。原因：**A, B, C 是固定的（输入无关）**，模型无法根据当前输入选择性地记忆或遗忘。

### 2.2 H3（Hungry Hungry Hippos, 2022）

H3[^h3-2022] 在 S4 基础上加入了类似注意力的门控机制和乘法交互，缩小了与 Transformer 在语言任务上的差距。更重要的是，H3 揭示了 SSM 与注意力之间的数学联系——SSM 可以视为一种**结构化的线性注意力**。

---

## 3. Mamba：选择性状态空间模型

Mamba[^mamba-2023] 是 SSM 范式的决定性突破，首次在语言建模上匹配 Transformer 质量，同时保持线性复杂度。

### 3.1 核心创新：选择性机制（Selection Mechanism）

S4 的 A, B, C 矩阵是固定参数；Mamba 让 **B, C 和时间步长 Δ 成为输入的函数**：

```
S4:    B, C, Δ = 固定参数
Mamba: B = f_B(x_t), C = f_C(x_t), Δ = f_Δ(x_t)    # 输入依赖
```

这个看似简单的改变有深刻的含义：

1. **选择性记忆**：模型可以根据当前输入决定记多少（大 Δ → 快速吸收新信息，遗忘旧状态）或忘多少（小 Δ → 保持旧记忆，忽略当前输入）
2. **等效于门控 RNN**：选择性 SSM 在概念上等价于一个数据依赖的门控 RNN，但计算方式完全不同
3. **内容感知推理**：Transformer 的注意力天然是内容感知的（token 间的相似度决定权重）；选择性机制让 SSM 也获得了这种能力

### 3.2 硬件感知的并行扫描算法

**选择性破坏了高效计算**：S4 之所以高效，是因为固定的 A, B, C 可以预计算卷积核，用 FFT 做 O(n log n) 的序列并行。参数变成输入依赖后，卷积不再适用。

Mamba 的工程创新在于将选择性 SSM 实现为**并行前缀和（parallel scan）**，利用结合律在 GPU 上高效并行：

```
朴素循环: h_t = Ā_t h_{t-1} + B̄_t x_t    # O(n) 顺序计算
并行扫描: 将 (Ā_t, B̄_t x_t) 视为半群元素 → 前缀和 → O(log n) 并行深度
```

配合 Flash Attention 式的 kernel fusion（在 SRAM 中完成所有中间计算，避免 HBM 读写），Mamba 在 A100 上的实际速度是同参数量 Transformer 的 **3-5x**（长序列时）。

### 3.3 架构细节

```
输入 x
 ├── 线性投影 → 扩展到 2E 维度（E = expand factor, 通常 2）
 ├── 分支 1: Conv1d → SiLU → 选择性 SSM → ...
 ├── 分支 2: SiLU (门控路径) → ...
 └── 两分支逐元素相乘 → 线性投影回 D 维度 → 输出
```

注意 Mamba **没有注意力层、没有 MLP 层**——整个 block 就是上面这个结构重复 N 次。比 Transformer 的 Attention+FFN 更简洁。

---

## 4. Mamba-2：结构化状态空间对偶性

Mamba-2[^mamba2-2024] 从理论上统一了 SSM 和注意力机制：

### SSD（Structured State Space Duality）框架

证明了选择性 SSM 等价于一种**半可分矩阵（semiseparable matrix）** 形式的结构化注意力。具体地：

```
SSM 视角:  h_t = A_t h_{t-1} + B_t x_t, y_t = C_t h_t
注意力视角: y = M ⊙ (QK^T) V
           其中 M 是因果掩码 × 衰减矩阵
```

两种计算给出**数学上完全等价**的结果，但计算复杂度不同：

- **SSM 模式**（循环）：O(n) 时间，O(1) 推理步骤内存 → 适合推理
- **注意力模式**（矩阵乘法）：O(n²) 时间，高并行度 → 适合训练

Mamba-2 的实际做法是**分块处理**：将序列分成长度 T 的块，块内用矩阵乘法（利用 GPU tensor core），块间用循环传递状态。这是两种模式的最优混合。

**性能提升**：Mamba-2 比 Mamba-1 训练速度快 2-8x，同时在 scaling 行为上更接近 Transformer++（带 GQA、SwiGLU 等优化的 Transformer）。

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

## 6. 替代架构

### 6.1 RWKV（Receptance Weighted Key Value）

RWKV[^rwkv-2023] 试图将 Transformer 的 attention "线性化"并转换为 RNN 形式：

- **训练时**：按 Transformer 风格并行（矩阵运算）
- **推理时**：按 RNN 风格循环（O(1) 步骤复杂度）

RWKV 的关键设计是 **WKV（Weighted Key-Value）** 操作，类似于 attention 但用指数衰减替代 softmax：

```
wkv_t = Σ_{i=1}^{t-1} e^{-(t-1-i)w + k_i} · v_i + e^{u+k_t} · v_t
```

其中 `w` 是可学习的时间衰减参数。这个公式可以递推计算，因此推理时是 O(1)。

**RWKV 的局限**：时间衰减是单调递减的，无法像注意力那样"跳跃式"地关注远处的特定 token。RWKV-6/7 通过数据依赖的衰减和门控机制持续改进，但在精确回忆任务上仍不及 Transformer。

当前 RWKV 发展到 v7 (Goose)，社区活跃，最大模型到 14B 规格，是纯开源社区驱动的唯一竞争性 LLM 架构。

### 6.2 xLSTM（Extended LSTM）

xLSTM[^xlstm-2024] 由 LSTM 的发明者 Sepp Hochreiter 提出，本质是"如果用现代技术重新设计 LSTM 会怎样"：

- **sLSTM（scalar LSTM）**：引入指数门控，缓解梯度消失
- **mLSTM（matrix LSTM）**：将标量记忆扩展为矩阵记忆，容量大幅提升。mLSTM 的更新规则与线性注意力 + 衰减非常相似，可以并行训练

xLSTM 在中等规模实验中表现不错（400M-1.3B），但缺乏大规模 scaling 的验证。

### 6.3 RetNet（Retentive Network）

微软提出的 RetNet[^retnet-2023] 引入 **retention 机制**——一种带指数衰减的注意力变体：

```
Retention(Q, K, V) = (QK^T ⊙ D) V    其中 D_{ij} = γ^{i-j} (因果衰减掩码)
```

支持三种等价的计算模式：
1. **并行模式**：类注意力的矩阵乘法 → 适合训练
2. **循环模式**：类 RNN → 适合推理
3. **分块模式**：块内并行 + 块间循环 → 平衡训练和推理

这个三模式等价性后来被 Mamba-2 的 SSD 框架所吸收和泛化。

### 6.4 Phase-Associative Memory (PAM, 2026)

PAM[^pam-2026] 是一种完全基于复数域的循环序列模型，核心思想是将联想记忆推广到**复 Hilbert 空间**。

**架构核心**：所有表征为复数值，联想通过外积累积在矩阵状态 S_t ∈ ℂ^{d×d} 中，检索通过共轭内积 K_t* · Q_t / √d 完成：

```
状态更新: S_t = S_{t-1} + V_t ⊗ K_t*    # 外积累积（矩阵联想记忆）
检索输出: y_t = S_t · Q_t                 # 共轭内积检索
```

**为什么从向量记忆升级到矩阵记忆**：向量状态模型（如全息绑定 holographic binding）的联想记忆容量以 O(1/√n) 速率退化——叠加的联想越多，每条的保真度越低。矩阵状态将容量瓶颈从 O(√d) 提升到 O(d)，根本性地解决了这个问题。

**初步结果**：~100M 参数在 WikiText-103 上达到 perplexity 30.0，与相同条件训练的 Transformer（27.1）差距约 10%，但 PAM 承受了 4× 的复数运算开销且未使用定制 CUDA kernel。

**与 SSM 的关系**：PAM 可视为 SSM 的"复数化"变体——状态转移和检索都在复数域上操作，保留了 RNN 式的线性推理复杂度。其数学形式也与线性注意力有类比关系，但用相位（phase）编码替代了显式的衰减或门控。

---

## 7. 混合架构：融合两个范式

纯 SSM 在精确回忆和 in-context learning 上弱于 Transformer，纯 Transformer 在长序列推理效率上有瓶颈。混合架构尝试两全其美。

### 7.1 Jamba（AI21 Labs）

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

### 7.2 Zamba（Zyphra）

Zamba 的独特设计：**所有 Mamba 层之间共享同一个注意力层**：

```
Mamba → 共享 Attention → Mamba → 共享 Attention → Mamba → ...
```

这进一步压缩了参数量（注意力层只有一份权重），特别适合端侧部署。Zamba-2 在 2.7B 参数量级上达到了可观的质量。

### 7.3 其他混合探索

| 模型 | 组织 | 混合方式 |
|------|------|----------|
| **Griffin** | Google DeepMind | 循环层 (RLKV) + 局部注意力 |
| **RecurrentGemma** | Google | 基于 Griffin 的开源模型 |
| **StripedHyena** | Together AI | Hyena (长卷积) + 注意力交替 |
| **Samba** | Microsoft | Mamba + Sliding Window Attention |

**混合比例是关键**：研究表明注意力层的比例只需 ~15-25% 即可恢复大部分精确回忆能力，更多的注意力层对推理效率的损害大于质量收益。

---

## 8. 工程选型

| 场景 | 推荐架构 | 理由 |
|------|----------|------|
| 通用 LLM（追求最强质量） | Transformer + GQA/MLA | 生态最成熟，scaling 行为最可预测 |
| 超长上下文（>256K） | 混合 Mamba-Transformer | KV cache 是纯 Transformer 的硬瓶颈 |
| 端侧部署 | SSM/混合 + 量化 | O(1) 推理内存，不受上下文长度限制 |
| 高吞吐服务 | 依场景而定 | 短 prompt 选 Transformer（prefill 并行度高）；长 prompt 选混合 |
| 实时流式处理 | SSM/RWKV | 天然的流式推理，无需 KV cache 管理 |

### 2026 年现状

截至 2026 年 4 月，**Transformer 仍是绝对主流**。所有前沿闭源模型（GPT-5.3, Claude Opus 4.6, Gemini 3）都基于 Transformer（可能有内部改良，但核心是注意力机制）。SSM/Mamba 在开源社区和特定场景（长序列、端侧）中持续推进，但尚未在 >70B 规模上证明可以替代 Transformer。

混合架构是最有前景的方向——不是"Transformer 或 SSM"的二选一，而是在**同一模型内按层分配**注意力和循环计算的比例。

---

## 参考资料

[^s4-2021]: Gu et al. *Efficiently Modeling Long Sequences with Structured State Spaces*. 2021. https://arxiv.org/abs/2111.00396
[^h3-2022]: Fu et al. *Hungry Hungry Hippos: Towards Language Modeling with State Space Models*. 2022. https://arxiv.org/abs/2212.14052
[^mamba-2023]: Gu & Dao. *Mamba: Linear-Time Sequence Modeling with Selective State Spaces*. 2023. https://arxiv.org/abs/2312.00752
[^mamba2-2024]: Dao & Gu. *Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality*. 2024. https://arxiv.org/abs/2405.21060
[^rwkv-2023]: Peng et al. *RWKV: Reinventing RNNs for the Transformer Era*. 2023. https://arxiv.org/abs/2305.13048
[^xlstm-2024]: Beck et al. *xLSTM: Extended Long Short-Term Memory*. 2024. https://arxiv.org/abs/2405.04517
[^retnet-2023]: Sun et al. *Retentive Network: A Successor to Transformer for Large Language Models*. 2023. https://arxiv.org/abs/2307.08621
[^jamba-2024]: Lieber et al. *Jamba: A Hybrid Transformer-Mamba Language Model*. 2024. https://arxiv.org/abs/2403.19887
[^pam-2026]: Vishwakarma & Agostino. *Phase-Associative Memory: Sequence Modeling in Complex Hilbert Space*. 2026. https://arxiv.org/abs/2604.05030
