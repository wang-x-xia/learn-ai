---
title: "KV Cache 与推理优化"
description: "KV Cache 机制、注意力变体（GQA/MLA）、PagedAttention、Prefix Caching 与长上下文挑战。"
created: 2026-04-09
updated: 2026-04-09
tags: [kv-cache, gqa, mla, paged-attention, inference]
review:
---

# KV Cache 与推理优化

> KV Cache 是 LLM 自回归推理的核心机制，也是长上下文时代最大的工程瓶颈。本文档涵盖 KV Cache 原理、注意力变体（GQA/MLA）、显存管理（PagedAttention）和压缩技术。
>
> 相关文档：[Transformer 架构](./transformer.md) | [Mamba 与状态空间模型](./mamba-and-ssm.md)

---

## 1. KV Cache：自回归推理的核心机制

自回归生成每步只产出一个 token，但注意力计算需要当前 token 的 Query 与**所有历史 token** 的 Key/Value 做点积。如果每步都重新算所有历史 token 的 K/V，计算量随序列长度二次增长。KV Cache 的思想很直接：把每一层已经算过的 K/V 向量缓存起来，下一步直接复用[^pope-2023]。

```
步骤 t:   缓存 K = [k_1, ..., k_{t-1}]   V = [v_1, ..., v_{t-1}]
          只计算新 token 的 q_t, k_t, v_t
          K ← append(K, k_t)     V ← append(V, v_t)
          output_t = Attention(q_t, K, V)
```

这将每步的计算量从 O(t · d) 降到 O(d)（只需一个 token 的投影），代价是需要维护一块**随序列长度线性增长**的显存。

### 1.1 内存占用分析

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

---

## 2. 注意力变体：KV 头的效率优化

标准 MHA 的问题是推理时 KV Cache 的内存占用随头数线性增长。这催生了一系列 KV 头共享方案：

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

## 3. Prefill 与 Decode：两个截然不同的阶段

LLM 推理分两个阶段，硬件瓶颈完全不同：

| 阶段 | 做什么 | 瓶颈 | 特征 |
|------|--------|------|------|
| **Prefill** | 一次性处理完整 prompt，生成全部 KV Cache | **计算受限** (compute-bound) | 高度并行，GPU 利用率高 |
| **Decode** | 逐 token 自回归生成，每步读取全部 KV Cache | **内存带宽受限** (memory-bound) | 每步只做一个 token 的计算，大量时间在读 KV Cache |

这个区分对系统设计影响深远：Prefill 需要算力，Decode 需要带宽。vLLM 的 Chunked Prefill、Sarathi 的 Prefill-Decode 分离，本质上都是在调和这两个阶段对硬件的不同需求。

---

## 4. PagedAttention：用虚拟内存思想管理 KV Cache

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

---

## 5. Prefix Caching / Prompt Caching

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

---

## 6. KV Cache 压缩技术

除了 GQA/MLA 在模型架构层面减少 KV 头数（见第 2 节），还有多种正交的工程手段进一步压缩 KV Cache：

| 方案 | 思路 | 效果 | 代表工作 |
|------|------|------|----------|
| **KV Cache 量化** | 将缓存从 FP16 降到 INT8/FP8/INT4 | 显存减半至 1/4，质量损失可控 | KIVI[^kivi-2024], KVQuant |
| **Token 驱逐** | 根据注意力分数淘汰不重要的历史 token | 固定 cache 大小上限 | H₂O (Heavy-Hitter Oracle)[^h2o-2023], Scissorhands |
| **滑动窗口注意力** | 只对最近 W 个 token 做全注意力 | KV Cache 上限 = W | Mistral 7B (W=4096)[^mistral-2023] |
| **跨层共享** | 相邻层复用同一组 KV Cache | 减少 L 的系数 | CLA (Cross-Layer Attention) |

**H₂O 的关键洞察**：注意力分数的分布高度不均匀——少数"Heavy Hitter"token（如标点、语法词）始终获得高注意力分数。保留这些 token + 最近的局部窗口，就能在极小的 cache 预算下维持大部分生成质量[^h2o-2023]。

**滑动窗口的巧妙之处**：Mistral 将滑动窗口和完整注意力交替使用——底层用滑动窗口（捕获局部模式），高层用完整注意力（捕获全局依赖）。这比全部使用滑动窗口的质量损失小得多。

---

## 7. 长上下文时代的挑战

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

## 参考资料

[^pope-2023]: Pope et al. *Efficiently Scaling Transformer Inference*. 2023. https://arxiv.org/abs/2211.05102
[^llama2-2023]: Touvron et al. *Llama 2: Open Foundation and Fine-Tuned Chat Models*. 2023. https://arxiv.org/abs/2307.09288
[^deepseek-v2-2024]: DeepSeek-AI. *DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model*. 2024. https://arxiv.org/abs/2405.04434
[^vllm-2023]: Kwon et al. *Efficient Memory Management for Large Language Model Serving with PagedAttention*. 2023. https://arxiv.org/abs/2309.06180
[^sglang-2024]: Zheng et al. *SGLang: Efficient Execution of Structured Language Model Programs*. 2024. https://arxiv.org/abs/2312.07104
[^kivi-2024]: Liu et al. *KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache*. 2024. https://arxiv.org/abs/2402.02750
[^h2o-2023]: Zhang et al. *H₂O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models*. 2023. https://arxiv.org/abs/2306.14048
[^mistral-2023]: Jiang et al. *Mistral 7B*. 2023. https://arxiv.org/abs/2310.06825
