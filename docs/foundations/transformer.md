---
title: "Transformer 架构"
description: "Transformer 架构深度解析——自注意力机制、KV cache 优化、Flash Attention、位置编码、归一化、FFN 设计与 MoE。"
created: 2026-04-08
updated: 2026-04-08
tags: [transformer, attention, kv-cache, rope, flash-attention, moe, gqa, mla]
review:
---

# Transformer 架构

> Transformer 是当前几乎所有前沿语言模型的底层架构。本文档聚焦其核心机制的技术原理和设计权衡，不涉及具体模型。
>
> 相关文档：[Mamba 与状态空间模型](./mamba-and-ssm.md) | [大语言模型概览](./large-language-models.md)

---

## 1. 架构原理

Transformer 由 Vaswani 等人在 2017 年提出[^vaswani-2017]，用**纯注意力机制**替代了 RNN 的循环结构。原始设计是 Encoder-Decoder 架构（用于机器翻译），但后续演化出三个分支：

| 变体 | 代表模型 | 适用任务 | 关键差异 |
|------|----------|----------|----------|
| **Encoder-only** | BERT, RoBERTa | 分类、NER、语义理解 | 双向注意力，看到完整上下文 |
| **Decoder-only** | GPT 系列, Llama, Claude | 文本生成、对话、推理 | 因果掩码，只看到左侧 token |
| **Encoder-Decoder** | T5, BART, UL2 | Seq2Seq（翻译、摘要） | 编码器双向 + 解码器因果 |

**为什么 Decoder-only 成为 LLM 的主流？** 这不是偶然的——有深层的 scaling 原因：

1. **统一的训练目标**：Decoder-only 只做 next-token prediction，目标函数简单，不需要区分编码/解码阶段，scaling 行为更可预测
2. **参数效率**：Encoder-Decoder 要分两组参数，总参数量相同时 Decoder-only 的生成能力更强
3. **涌现能力的载体**：in-context learning、chain-of-thought 等涌现能力天然适配自回归生成
4. **工程简洁**：一个统一的 forward pass，推理优化（KV cache、投机解码）更容易实现

---

## 2. 自注意力机制

自注意力是 Transformer 的核心计算单元。对输入序列中的每个 token，计算它与所有其他 token 的关联权重：

```
Attention(Q, K, V) = softmax(QK^T / √d_k) · V
```

- `Q`（Query）、`K`（Key）、`V`（Value）：输入向量经过三个不同的线性投影
- `√d_k`（缩放因子）：防止点积过大导致 softmax 梯度消失

**为什么要除以 √d_k？** 当 `d_k` 较大时，`QK^T` 的方差约为 `d_k`，除以 `√d_k` 将方差归一化到 1，使 softmax 不会退化成 one-hot（梯度几乎为零）。这个看似简单的 trick 对训练稳定性至关重要。

**Multi-Head Attention (MHA)** 将 Q/K/V 拆分成 `h` 个头并行计算，每个头学习不同的注意力模式（如语法关系、共指消解、位置邻近性等），最后拼接：

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W_O
head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
```

---

## 3. 注意力变体：效率与质量的权衡

标准 MHA 的问题是推理时 KV cache 的内存占用随头数线性增长。这催生了一系列 KV 头共享方案：

| 方案 | KV 头数 | 代表模型 | 核心权衡 |
|------|---------|----------|----------|
| **MHA** | 等于 Q 头数 | GPT-3 | 质量最优，内存最大 |
| **MQA** | 1 | PaLM, Falcon | 内存最小，质量有损 |
| **GQA** | Q 头数 / G | Llama 2/3, Mistral | 分组折中，质量接近 MHA |

**GQA 为什么成为事实标准？** Llama 2 的实验表明 GQA-8（8 组 KV 头）在质量上几乎无损于完整 MHA，但推理吞吐提升 ~1.5x。这是一个 Pareto 最优点——进一步减少 KV 头收益递减，而质量损失加速[^llama2-2023]。

### Multi-head Latent Attention (MLA)

DeepSeek-V2 提出的 MLA 走了一条不同于 GQA 的路径[^deepseek-v2-2024]：不是共享 KV 头，而是**将 KV 投影到低秩潜空间**再缓存。

```
标准 GQA:  缓存 [K_group, V_group] → 大小 ∝ n_kv_heads × d_head
MLA:       缓存 compressed_kv       → 大小 ∝ d_compress (远小于 n_kv_heads × d_head)
           推理时: compressed_kv → 上投影还原 K, V
```

MLA 的 KV cache 压缩比可达 **93.3%**（DeepSeek-V2 数据），同时保持了完整 MHA 的表达能力。这是因为低秩投影保留了 KV 的主要信息，而 GQA 的硬共享则丢弃了头间差异。

代价是推理时需要额外的上投影计算，但这被 KV cache 内存节省所带来的更大 batch size 抵消。DeepSeek-V3/R1 延续了这一设计。

---

## 4. KV Cache：自回归推理的核心机制

自回归生成每步只产出一个 token，但注意力计算需要当前 token 的 Query 与**所有历史 token** 的 Key/Value 做点积。如果每步都重新算所有历史 token 的 K/V，计算量随序列长度二次增长。KV Cache 的思想很直接：把每一层已经算过的 K/V 向量缓存起来，下一步直接复用[^pope-2023]。

```
步骤 t:   缓存 K = [k_1, ..., k_{t-1}]   V = [v_1, ..., v_{t-1}]
          只计算新 token 的 q_t, k_t, v_t
          K ← append(K, k_t)     V ← append(V, v_t)
          output_t = Attention(q_t, K, V)
```

这将每步的计算量从 O(t · d) 降到 O(d)（只需一个 token 的投影），代价是需要维护一块**随序列长度线性增长**的显存。

### 4.1 内存占用分析

KV Cache 的显存公式：

```
KV Cache 显存 = 2 × L × n_kv × d_h × s × b × bytes_per_param

其中:
  2         — K 和 V 两个矩阵
  L         — 层数
  n_kv      — KV 头数（MHA 等于 Q 头数，GQA 除以组数）
  d_h       — 每个头的维度
  s         — 序列长度
  b         — 并发 batch size
  bytes     — 数据类型（FP16=2, FP8=1）
```

以 Llama-3-70B（80 层, GQA-8, d_h=128）为例，单请求 128K 上下文：

```
2 × 80 × 8 × 128 × 131072 × 1 × 2 bytes ≈ 34 GB
```

一个 80GB H100，仅 KV Cache 就可能消耗近半显存。这就是为什么 KV Cache 管理是 LLM 推理的**核心工程问题**——它直接决定了能同时服务多少个请求。

### 4.2 Prefill 与 Decode：两个截然不同的阶段

LLM 推理分两个阶段，硬件瓶颈完全不同：

| 阶段 | 做什么 | 瓶颈 | 特征 |
|------|--------|------|------|
| **Prefill** | 一次性处理完整 prompt，生成全部 KV Cache | **计算受限** (compute-bound) | 高度并行，GPU 利用率高 |
| **Decode** | 逐 token 自回归生成，每步读取全部 KV Cache | **内存带宽受限** (memory-bound) | 每步只做一个 token 的计算，大量时间在读 KV Cache |

这个区分对系统设计影响深远：Prefill 需要算力，Decode 需要带宽。vLLM 的 Chunked Prefill、Sarathi 的 Prefill-Decode 分离，本质上都是在调和这两个阶段对硬件的不同需求。

### 4.3 PagedAttention：用虚拟内存思想管理 KV Cache

传统实现为每个请求预分配一块**连续**的 KV Cache 显存，大小按最大序列长度计算。问题是：大多数请求不会用满最大长度，导致严重的内部碎片（实测浪费 60-80%）[^vllm-2023]。

vLLM 提出的 PagedAttention 借鉴了操作系统的虚拟内存分页机制：

```
传统方式:
  请求 A: [████████████░░░░░░░░]  ← 预分配 max_len，大量浪费
  请求 B: [██████░░░░░░░░░░░░░░]  ← 更短的请求，浪费更多
  显存碎片 → batch size 受限 → 吞吐低

PagedAttention:
  物理显存被分成固定大小的 block（如 16 tokens/block）
  每个请求维护一个 block table（类似页表）
  请求 A: [blk3][blk7][blk1]       ← 按需分配，不必连续
  请求 B: [blk5][blk2]             ← 用多少分配多少
  显存利用率接近 100%
```

**核心收益**：显存利用率从 ~20-40% 提升到接近 100%，意味着相同显存可以服务 **2-4 倍**的并发请求。PagedAttention 现已成为几乎所有生产级推理框架的标配。

### 4.4 Prefix Caching / Prompt Caching

很多场景下，多个请求共享相同的 system prompt 或少样本示例。Prefix Caching 的思路是：对**相同前缀**只计算一次 KV Cache，后续请求直接复用。

```
请求 1: [system prompt] + [用户问题 A]
请求 2: [system prompt] + [用户问题 B]
                ↑
       相同前缀的 KV Cache 只算一次，
       后续请求跳过 prefill 这部分
```

**Radix Attention**（SGLang 提出）将这一思想推广到**任意共享前缀**的场景，用 radix tree 管理所有缓存的 KV 前缀，自动匹配最长公共前缀[^sglang-2024]。

商业 API 也在跟进：OpenAI 的 Prompt Caching（自动对 1024+ token 的重复前缀缓存）、Anthropic 的 Prompt Caching（需显式标记缓存断点）、Google Gemini 的 Context Caching。这些本质上是相同思想的不同实现策略。

### 4.5 KV Cache 压缩技术

除了 GQA/MLA 在模型架构层面减少 KV 头数（见第 3 节），还有多种正交的工程手段进一步压缩 KV Cache：

| 方案 | 思路 | 效果 | 代表工作 |
|------|------|------|----------|
| **KV Cache 量化** | 将缓存从 FP16 降到 INT8/FP8/INT4 | 显存减半至 1/4，质量损失可控 | KIVI[^kivi-2024], KVQuant |
| **Token 驱逐** | 根据注意力分数淘汰不重要的历史 token | 固定 cache 大小上限 | H₂O (Heavy-Hitter Oracle)[^h2o-2023], Scissorhands |
| **滑动窗口注意力** | 只对最近 W 个 token 做全注意力 | KV Cache 上限 = W | Mistral 7B (W=4096)[^mistral-2023] |
| **跨层共享** | 相邻层复用同一组 KV Cache | 减少 L 的系数 | CLA (Cross-Layer Attention) |

**H₂O 的关键洞察**：注意力分数的分布高度不均匀——少数"Heavy Hitter"token（如标点、语法词）始终获得高注意力分数。保留这些 token + 最近的局部窗口，就能在极小的 cache 预算下维持大部分生成质量[^h2o-2023]。

**滑动窗口的巧妙之处**：Mistral 将滑动窗口和完整注意力交替使用——底层用滑动窗口（捕获局部模式），高层用完整注意力（捕获全局依赖）。这比全部使用滑动窗口的质量损失小得多。

### 4.6 KV Cache 在长上下文时代的挑战

随着上下文窗口从 4K → 128K → 1M+ 扩展，KV Cache 成为最大的工程瓶颈：

1. **显存墙**：128K 上下文的 70B 模型，单请求 KV Cache 就需要 ~34GB——一张 H100 几乎只能服务一个请求
2. **带宽墙**：Decode 阶段每步都要读取全部 KV Cache，128K 上下文意味着每步读取 GB 级数据
3. **首 token 延迟**：Prefill 128K 个 token 需要数秒到数十秒

应对策略正在多个层面并行演进：
- **架构层**：GQA/MLA 减少每层 KV 大小、Mamba/RWKV 等 SSM 架构完全绕过 KV Cache（见 [Mamba 与状态空间模型](./mamba-and-ssm.md)）
- **算法层**：稀疏注意力、Token 驱逐、KV Cache 量化
- **系统层**：PagedAttention、Prefix Caching、KV Cache offloading 到 CPU/SSD
- **硬件层**：更大的 HBM（H200: 141GB, B200: 192GB）、更高的带宽

---

## 5. Flash Attention：IO 感知的算法革新

Flash Attention[^flash-attention-2022] 不改变注意力的数学结果，而是重新组织计算顺序以减少 GPU HBM（高带宽内存）访问（这也直接降低了 KV Cache 的 IO 开销）：

**核心问题**：标准注意力实现需要先在 HBM 中实体化 `n×n` 的注意力矩阵 `S = QK^T`，然后读取 `S` 做 softmax，再与 `V` 相乘。这三次 HBM 读写是瓶颈——SRAM 速度是 HBM 的 ~10x，但容量小得多。

**解法（Tiling + Online Softmax）**：

1. 将 Q/K/V 分成小块（tile），每块可以放进 SRAM
2. 在 SRAM 内完成 `QK^T → softmax → ×V` 的全部计算
3. 使用 online softmax（Milakov & Gimelshein, 2018）在不看到完整行的情况下增量计算正确的 softmax
4. 永远不把 `n×n` 注意力矩阵写入 HBM

**效果**：2-4x 加速，内存从 O(n²) 降到 O(n)，且结果**精确等价**（非近似）。

Flash Attention 2 进一步优化了并行性（在序列长度维度并行而非 batch 维度），Flash Attention 3 利用了 Hopper GPU 的异步特性（TMA + WGMMA）。

**为什么 Flash Attention 如此重要？** 它证明了一个原则：**在现代硬件上，算法的 IO 复杂度往往比计算复杂度更重要**。标准注意力的 FLOPs 完全相同，但 IO 模式决定了实际速度。这一洞察影响了后续几乎所有高效架构的设计。

---

## 6. 位置编码的演进

Transformer 本身是**置换不变**的——打乱输入顺序不影响输出。位置编码注入序列顺序信息：

| 方案 | 机制 | 外推性 | 代表模型 |
|------|------|--------|----------|
| **正弦位置编码** | 固定的 sin/cos 函数 | 差 | 原始 Transformer |
| **可学习位置编码** | 训练出的 embedding | 无 | GPT-2, BERT |
| **RoPE** | 旋转矩阵编码相对位置 | 中（需配合外推） | Llama, Qwen, Mistral |
| **ALiBi** | 注意力分数加线性偏置 | 好 | BLOOM, MPT |

### RoPE 的技术本质

RoPE（Rotary Position Embedding）[^rope-2021] 的核心思想：将位置信息编码为**旋转角度**，使得两个 token 的注意力分数只取决于它们的**相对距离**。

```
q_m = R(mθ) · q    # 位置 m 的 query 乘以旋转矩阵 R(mθ)
k_n = R(nθ) · k    # 位置 n 的 key 乘以旋转矩阵 R(nθ)
q_m · k_n = q^T R((m-n)θ) k    # 点积只依赖相对位置 (m-n)
```

每个维度对 `(d_{2i}, d_{2i+1})` 以频率 `θ_i = 10000^{-2i/d}` 旋转。低频维度编码远距离关系，高频维度编码近距离关系——类似傅里叶分解。

**长度外推问题**：RoPE 在训练长度内效果优异，但超出训练长度后角度外推会产生分布外的注意力模式。解决方案：

- **NTK-aware Scaling**：调大基础频率 `θ`，等效于"放大旋转盘"，低频维度不受影响、高频维度被压缩
- **YaRN**：NTK 的改进版，对不同频率维度施加不同的缩放策略
- **持续预训练**：在目标长度的数据上继续训练（最可靠，但最昂贵）

---

## 7. 归一化：训练稳定性的关键

归一化层的位置和类型对深度 Transformer 的训练稳定性影响巨大：

| 方案 | 位置 | 特点 |
|------|------|------|
| **Post-LN** | Attention/FFN 后 | 原始 Transformer；深度增加时梯度不稳定 |
| **Pre-LN** | Attention/FFN 前 | 训练稳定但最终层输出无归一化 |
| **Sandwich-LN** | 前后各一个 | 同时保证稳定性和输出归一化 |

**为什么 Pre-LN 更稳定？** 在 Post-LN 中，残差路径上的激活值随深度累积增长（因为归一化在残差相加之后），导致深层梯度爆炸。Pre-LN 在进入注意力/FFN 之前归一化，残差路径保持"干净"，梯度可以畅通地反向传播。

**RMSNorm 取代 LayerNorm**：LayerNorm 计算均值和方差两个统计量；RMSNorm 只计算均方根（root mean square），省去了均值计算。实验表明性能几乎无损，但速度更快。Llama 系列率先采用 RMSNorm，现已成为标准。

---

## 8. 前馈网络与激活函数

Transformer 每层包含一个前馈网络（FFN），负责非线性变换和知识存储。研究表明 FFN 是模型记忆事实知识的主要载体（key-value memory 假说[^geva-2021]）。

**激活函数演进**：

```
ReLU: max(0, x)                    — 简单但有"死神经元"问题
GELU: x · Φ(x)                    — 平滑版 ReLU，GPT-2/BERT 采用
SwiGLU: Swish(xW₁) ⊙ (xW₂)       — 门控线性单元，现代 LLM 标配
```

**SwiGLU 为什么是当前最优？** GLU（Gated Linear Unit）引入了一个门控路径，让网络可以选择性地让信息通过[^shazeer-2020]。Shazeer 2020 年的实验表明 SwiGLU 在相同参数量下 consistently outperform GELU/ReLU。直觉上，门控机制让 FFN 获得了类似注意力的"选择性"——不是所有输入维度都同等对待。

---

## 9. MoE：稀疏激活的参数扩展

Mixture of Experts 不是独立的架构，而是 Transformer FFN 层的一种替换策略：

```
标准 FFN:   x → FFN(x)
MoE FFN:    x → Router(x) → 选择 Top-K Expert → Σ(gate_i · Expert_i(x))
```

| 模型 | 总参数 | 活跃参数 | Expert 数 | Router 策略 |
|------|--------|----------|-----------|-------------|
| Mixtral 8x7B | 46.7B | 12.9B | 8, Top-2 | Token-choice |
| DeepSeek-V3 | 671B | 37B | 256, Top-8 | 辅助 loss-free 均衡 |
| Qwen2.5-MoE | 14.3B | 2.7B | 60, Top-4+4 shared | Fine-grained |

**MoE 的关键工程挑战**：

1. **负载均衡**：如果 Router 总选同几个 Expert，其他 Expert 白训练。传统方案加辅助 loss 强制均衡，但这个 loss 会干扰主任务。DeepSeek-V3 提出 **loss-free 均衡**——用动态偏置调节 Router 分数，不引入额外 loss
2. **Expert 并行**：256 个 Expert 不可能放在一张卡上，需要跨设备调度。通信开销是瓶颈
3. **Token 丢弃**：当某个 Expert 过载时需要丢弃 token，影响质量

---

## 参考资料

[^vaswani-2017]: Vaswani et al. *Attention Is All You Need*. 2017. https://arxiv.org/abs/1706.03762
[^llama2-2023]: Touvron et al. *Llama 2: Open Foundation and Fine-Tuned Chat Models*. 2023. https://arxiv.org/abs/2307.09288
[^deepseek-v2-2024]: DeepSeek-AI. *DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model*. 2024. https://arxiv.org/abs/2405.04434
[^flash-attention-2022]: Dao et al. *FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness*. 2022. https://arxiv.org/abs/2205.14135
[^rope-2021]: Su et al. *RoFormer: Enhanced Transformer with Rotary Position Embedding*. 2021. https://arxiv.org/abs/2104.09864
[^shazeer-2020]: Shazeer. *GLU Variants Improve Transformer*. 2020. https://arxiv.org/abs/2002.05202
[^geva-2021]: Geva et al. *Transformer Feed-Forward Layers Are Key-Value Memories*. 2021. https://arxiv.org/abs/2012.14913
[^pope-2023]: Pope et al. *Efficiently Scaling Transformer Inference*. 2023. https://arxiv.org/abs/2211.05102
[^vllm-2023]: Kwon et al. *Efficient Memory Management for Large Language Model Serving with PagedAttention*. 2023. https://arxiv.org/abs/2309.06180
[^sglang-2024]: Zheng et al. *SGLang: Efficient Execution of Structured Language Model Programs*. 2024. https://arxiv.org/abs/2312.07104
[^kivi-2024]: Liu et al. *KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache*. 2024. https://arxiv.org/abs/2402.02750
[^h2o-2023]: Zhang et al. *H₂O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models*. 2023. https://arxiv.org/abs/2306.14048
[^mistral-2023]: Jiang et al. *Mistral 7B*. 2023. https://arxiv.org/abs/2310.06825
