---
title: "KV Cache 与推理优化"
description: "KV Cache 的存储特征、注意力变体（GQA）、推理阶段差异与压缩手段的设计权衡。"
created: 2026-04-09
updated: 2026-04-28
tags: [kv-cache, gqa, inference]
review: 2026-04-28
---

# KV Cache 与推理优化

??? note "背景知识"
    - **自注意力机制**：每个 token 通过 Q·K 点积计算与其他 token 的相关度，再对 V 加权求和 → [详见](./transformer.md#2)
    - **自回归生成**：每步预测下一个 token，追加到序列末尾，重复直到结束 → [详见](./transformer.md#1)
    - **GQA/MQA**：多个 Q 头共用 KV 头，减少 KV 数量的注意力变体 → [详见](./transformer.md#gqa-mqa-kv)
    - **GPU 显存 (HBM)**：GPU 的高带宽内存，是模型权重和中间状态的存储位置，容量有限（H100 为 80GB）

> KV Cache 是 LLM 自回归推理的核心加速机制——用显存换计算，避免重复运算。本文档聚焦它的存储特征和各种优化手段的设计权衡。
>
> 相关文档：[Transformer 架构](./transformer.md) | [Mamba 与状态空间模型](./mamba-and-ssm.md)

---

## 1. KV Cache：用显存换速度

自回归生成每步只产出一个 token，但注意力计算需要当前 token 的 Query 与**所有历史 token** 的 Key/Value 做点积（注意力公式详见 [Transformer 架构 § 自注意力机制](./transformer.md#2)）。

如果每步都从头算，生成第 100 个 token 就要重算前 99 个的 K/V——重复劳动随序列增长越来越严重。KV Cache 把每层算过的 K/V 向量存下来，下一步直接查表复用[^pope-2023]。

**为什么只缓存 K/V，不缓存 Q？** 因为 Q 是"提问方"，K/V 是"被查询方"。每一步只需要当前新 token 的 Q 去匹配所有历史 token 的 K，再从对应的 V 里取信息——之前 token 的 Q 算完就没用了（它们的输出在之前的步骤里已经算好了）。而 K/V 每一步都要被新 token 查询，所以值得缓存：

```
步骤 4（生成"苹果"）:
  需要:   q₄                   ← 当前 token 的 Query（只用一次）
  需要:   K = [k₁,k₂,k₃,k₄]  ← 所有 token 的 Key（每步都要被匹配）
  需要:   V = [v₁,v₂,v₃,v₄]  ← 所有 token 的 Value（匹配后提供信息）
  不需要: q₁,q₂,q₃            ← 已经在之前的步骤里用完了
```

完整流程：

```
步骤 t:   缓存 K = [k₁, ..., k_{t-1}]   V = [v₁, ..., v_{t-1}]
          只计算新 token 的 q_t, k_t, v_t
          K ← append(K, k_t)     V ← append(V, v_t)
          output_t = Attention(q_t, K, V)
```

用「我 喜欢 吃 苹果」来对比每步的计算量：

```
无 KV Cache（每步重算所有 K/V）：
  步骤 1: 算 [我] 的 K/V                           → 1 个 token
  步骤 2: 重算 [我, 喜欢] 的 K/V                    → 2 个 token
  步骤 3: 重算 [我, 喜欢, 吃] 的 K/V                → 3 个 token
  步骤 4: 重算 [我, 喜欢, 吃, 苹果] 的 K/V          → 4 个 token
  总计: 1+2+3+4 = 10 次                              O(n²)

有 KV Cache（只算新 token，旧的读缓存）：
  步骤 1: 算 [我] → 存入缓存                        → 1 个 token
  步骤 2: 算 [喜欢] → 追加缓存                      → 1 个 token
  步骤 3: 算 [吃] → 追加缓存                        → 1 个 token
  步骤 4: 算 [苹果] → 追加缓存                      → 1 个 token
  总计: 1+1+1+1 = 4 次                               O(n)
```

**核心权衡：计算换显存。** 避免了 O(n^2^) 的重复计算，但要在 GPU 显存里维护一块随序列长度线性增长的缓存。序列越长，这块缓存越大——这就是后续所有优化手段的起因。

---

## 2. 存储开销：为什么 KV Cache 是瓶颈

KV Cache 必须存在 **GPU 显存（HBM）** 里——每一步 Decode 都要读取它，放在 CPU 内存或 SSD 上延迟太高。

显存占用和几个因素成正比：

| 因素 | 含义 | 影响 |
|------|------|------|
| 层数 (L) | 每层都有独立的 KV Cache | 层数翻倍 → 显存翻倍 |
| KV 头数 | 每层有多少组 KV 向量 | GQA 通过减少头数降低开销 |
| 序列长度 | 上下文窗口越长，缓存的 token 越多 | 128K vs 4K → 显存差 32 倍 |
| 并发数 | 同时处理多少个请求 | batch 翻倍 → 显存翻倍 |

以 Llama-3-70B（80 层, GQA-8, 每头 128 维, FP16）为例：

```
单请求   4K 上下文:  ≈ 1 GB    → 一张 H100 (80GB) 轻松跑几十个并发
单请求 128K 上下文:  ≈ 34 GB   → 一张 H100 几乎只能服务一个请求
```

**KV Cache 直接决定了能同时服务多少用户、支持多长的上下文。** 后面的所有技术，本质上都在想办法让这块缓存变小，或者让它被更高效地使用。

---

## 3. 推理的两个阶段与 KV 头数的影响

### Prefill 与 Decode

LLM 推理实际上分两步走，硬件瓶颈完全不同：

``` mermaid
graph LR
    Prompt["用户输入\n(prompt)"] --> Prefill

    subgraph Prefill ["① Prefill"]
        P["并行处理全部 prompt\n生成完整 KV Cache"]
    end

    Prefill --> Decode

    subgraph Decode ["② Decode"]
        D1["token₁"] --> D2["token₂"] --> D3["token₃ ..."]
    end

    Decode --> Output["完整回复"]
```

| 阶段 | 做什么 | 瓶颈 | 原因 |
|------|--------|------|------|
| **Prefill** | 一次性处理完整 prompt，生成全部 KV Cache | **算力** (compute-bound) | 所有 token 并行计算，GPU 算力拉满 |
| **Decode** | 逐 token 生成，每步读取全部 KV Cache | **内存带宽** (memory-bound) | 每步只算 1 个 token，大量时间花在从显存读 KV Cache |

两个阶段需要的硬件资源正好相反——Prefill 吃算力，Decode 吃带宽。很多推理系统的优化（如 vLLM 的 Chunked Prefill、Sarathi 的 Prefill-Decode 分离）本质上都是在调和这两种需求。

### GQA/MQA：从架构层面缩小 Cache

Decode 的带宽瓶颈取决于 KV Cache 有多大，而 KV Cache 大小直接由 **KV 头数**决定。标准 MHA 中每个 Q 头独占一组 KV，GQA/MQA 通过让多个 Q 头共用 KV 来减少头数，从而**按比例缩小缓存**（架构原理详见 [Transformer 架构 § GQA/MQA](./transformer.md#gqa-mqa-kv)）。

以 Llama-3-70B（64 个 Q 头, 128K 上下文, FP16）为例：

```
标准 MHA:  64 组 KV → 需缓存 ~270 GB  ← 不现实
GQA-8:      8 组 KV → 需缓存  ~34 GB  ← 勉强一张 H100
MQA:        1 组 KV → 需缓存   ~4 GB  ← 但质量损失大
```

| 方案 | KV 头数 | Cache 大小 | 质量 | 代表模型 |
|------|---------|-----------|------|----------|
| **MHA** | = Q 头数 | 1x (基线) | 最优 | GPT-3 |
| **GQA** | Q 头数 / G | 1/G | 接近 MHA | Llama 2/3, Mistral |
| **MQA** | 1 | 最小 | 有损 | PaLM, Falcon |

**为什么 GQA 成为主流？** Llama 2 的实验表明 GQA-8 在质量上几乎无损于完整 MHA，推理吞吐提升 ~1.5x[^llama2-2023]。这是一个 Pareto 最优点——再减少 KV 头，质量下降加速，而显存收益递减。

---

## 4. 缩小 KV Cache 的其他手段

除了第 3 节的 KV 头共享，还有多种正交的手段：

| 手段 | 思路 | 权衡 |
|------|------|------|
| **量化** | KV Cache 从 FP16 降到 INT8/FP8/INT4 | 显存减半至 1/4，质量损失可控[^kivi-2024] |
| **TurboQuant** | PolarQuant（极坐标变换）+ QJL（随机投影）双重压缩 | 3bit量化，6倍内存压缩，无需重新训练[^turboquant-2025] |
| **Token 驱逐** | 淘汰注意力分数低的历史 token | 固定 cache 上限，可能丢失长距离信息[^h2o-2023] |
| **滑动窗口** | 只缓存最近 W 个 token | cache 上限 = W，需和全注意力交替使用[^mistral-2023] |
| **Prefix Caching** | 多个请求共享相同前缀的 KV Cache | 省掉重复 prefill，需额外缓存管理[^sglang-2024] |
| **Offloading** | 把部分 KV Cache 卸载到 CPU 内存 / SSD | 显存压力降低，但增加读取延迟 |

**H₂O 的洞察**[^h2o-2023]：注意力分数的分布高度不均匀——少数 token（如标点、语法词）始终获得高注意力。保留这些"Heavy Hitter"+ 最近的局部窗口，就能在很小的 cache 预算下维持大部分生成质量。

**TurboQuant 的双重压缩策略**[^turboquant-2025][^polarquant-2025][^qjl-2024]：传统量化方案将数据从 32bit 压到 4bit，理论上省 8 倍空间，但压缩过程本身需要存储量化常量、缩放因子等辅助参数（每个数据块额外占 1-2bit），实际压缩率被这些"附加成本"吃掉一大块。TurboQuant 用两套算法解决这个问题：

1. **PolarQuant（极坐标量化）**：将向量从直角坐标系转到极坐标系——"往东走 3 个路口再往北走 4 个路口"变成"朝 37 度方向走 5 个路口"。转换后角度的统计分布变得高度集中、可预测，不再需要为每个数据块单独存储归一化参数，附加成本归零。

2. **QJL（Johnson-Lindenstrauss 随机投影）**：处理 PolarQuant 的压缩残差。用随机投影只花 1 个 bit（记一个正负号），把残差误差的系统性偏差给抹平——类似秤上的"去皮"按钮，保证误差不会朝一个方向累积。

两步组合可在无需重新训练或微调的情况下实现 3bit 量化，在 H100 上注意力计算比未量化快 8 倍。经济价值显著：假设一张 H100 有 80GB 显存，模型权重占 40GB，剩余 40GB 给 KV Cache。没有 TurboQuant 时每个用户 KV Cache 占 4GB 只能同时服务 10 个用户，压缩后每个用户只占 670MB 左右，同一张卡可服务近 60 个并发，推理费用降到原来的 1/6。

**工程改动：需要重写 attention kernel**。TurboQuant 不是简单的存储格式变化，而是需要在压缩域直接计算注意力（compressed-domain attention）。如果采用"先解量化再计算"的路径（3bit → FP16 → 标准注意力），解量化开销会抵消压缩带来的带宽优势。因此必须重写 attention kernel 的核心计算逻辑，包括点积计算、位操作读取 packed 3bit 数据、内存访问模式等。论文用 JAX 框架测试，生产环境常用 vLLM/TensorRT-LLM/SGLang，需要为每个框架分别适配——这是 TurboQuant 落地的主要工程难点之一[^turboquant-2025]。

---

## 5. 长上下文时代的挑战

随着上下文窗口从 4K → 128K → 1M+ 扩展，KV Cache 问题被急剧放大：

| 挑战 | 具体表现 |
|------|----------|
| **显存墙** | 128K + 70B 模型，单请求 KV Cache ≈ 34GB，一张 H100 几乎只能服务一个请求 |
| **带宽墙** | Decode 每步要读全部 KV Cache，128K 上下文意味着每步读 GB 级数据 |
| **延迟墙** | Prefill 128K 个 token 需要数秒到数十秒，首 token 延迟变长 |

应对方向：

- **架构层**：GQA 减少 KV 头数；Mamba/RWKV 等 SSM 架构完全绕过 KV Cache（见 [Mamba 与状态空间模型](./mamba-and-ssm.md)）
- **算法层**：稀疏注意力、Token 驱逐、量化
- **系统层**：Prefix Caching、KV Cache offloading
- **硬件层**：更大显存（H200: 141GB, B200: 192GB）、更高带宽

---

## 参考资料

[^pope-2023]: Pope et al. *Efficiently Scaling Transformer Inference*. 2023. https://arxiv.org/abs/2211.05102
[^llama2-2023]: Touvron et al. *Llama 2: Open Foundation and Fine-Tuned Chat Models*. 2023. https://arxiv.org/abs/2307.09288
[^kivi-2024]: Liu et al. *KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache*. 2024. https://arxiv.org/abs/2402.02750
[^h2o-2023]: Zhang et al. *H₂O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models*. 2023. https://arxiv.org/abs/2306.14048
[^mistral-2023]: Jiang et al. *Mistral 7B*. 2023. https://arxiv.org/abs/2310.06825
[^sglang-2024]: Zheng et al. *SGLang: Efficient Execution of Structured Language Model Programs*. 2024. https://arxiv.org/abs/2312.07104
[^turboquant-2025]: Zandieh et al. *TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate*. 2025. https://arxiv.org/abs/2504.19874
[^polarquant-2025]: Han et al. *PolarQuant: Quantizing KV Caches with Polar Transformation*. 2025. https://arxiv.org/abs/2502.02617
[^qjl-2024]: Zandieh et al. *QJL: 1-Bit Quantized JL Transform for KV Cache Quantization with Zero Overhead*. 2024. https://arxiv.org/abs/2406.03482
