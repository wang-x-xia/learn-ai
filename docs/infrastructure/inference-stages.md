---
title: 推理过程主要阶段
description: 从 KV Cache 加载到 Prefill 和 Decode 的完整推理流程，以及 Continuous Batching、Chunked Prefilling、Speculative Decoding、PD 分离等优化技术
created: 2026-05-19
updated: 2026-06-12
tags:
  - gpu
  - inference
  - infrastructure
review: 2026-05-19
---

??? note "背景知识"
    - **KV Cache**：推理时缓存 attention 的 K/V 矩阵，避免重复计算历史 token
    - **Prefill/Decode**：生成式推理的两个核心阶段——Prefill 并行处理 prompt，Decode 逐 token 生成
    - **PCIe**：CPU 和 GPU 之间的数据传输总线，带宽约 32 GB/s（PCIe 4.0 x16）
    - **TTFT**：Time To First Token，首个 token 输出的延迟，影响用户体验

## 数据流动视角

```
输入 → 格式转换(CPU) → KV Cache加载(可选) → Prefill(GPU) → Decode(GPU) → 输出处理(CPU)
  ↓       ↓              ↓                  ↓           ↓           ↓
文本/图像 tokenization  磁盘→GPU显存      并行计算    逐token生成   解码/格式化
```

---

## 阶段零：KV Cache 加载（多轮对话时）

| 操作 | 执行位置 | 数据位置 | 说明 |
|------|----------|----------|------|
| KV Cache 读取 | CPU | CPU 内存 | 从磁盘/内存读取历史对话的 KV Cache |
| KV Cache 传输 | CPU → GPU | CPU 内存 → GPU 显存 | 通过 PCIe 传输到 GPU |
| KV Cache 验证 | GPU | GPU 显存 | 检查与当前模型参数匹配 |

**场景**：用户继续对话时，加载之前对话的 KV Cache，避免重新 prefill 整个历史

**数据路径**：
```
磁盘 → CPU 内存 → PCIe → GPU 显存
```

---

## 阶段一：Prefill（处理输入 prompt）

| 操作 | 执行位置 | 数据位置 | 说明 |
|------|----------|----------|------|
| 格式转换 | CPU | CPU 内存 | tokenization、图像预处理 |
| 数据传输 | CPU → GPU | CPU 内存 → GPU 显存 | 新 prompt token IDs 传输 |
| 并行前向传播 | GPU | GPU 显存 | 计算新 prompt 位置的 attention |
| KV Cache 追加 | GPU | GPU 显存 | 将新 prompt 的 K/V 追加到现有 KV Cache |

**特点**：计算密集，一次处理整个 prompt，无串行依赖

**注意**：如果有历史 KV Cache，Prefill 只处理新的 prompt，然后追加到现有 KV Cache

---

## 阶段二：Decode（逐 token 生成）

| 操作 | 执行位置 | 数据位置 | 说明 |
|------|----------|----------|------|
| 读取 KV Cache | GPU | GPU 显存 | 读取完整 KV Cache（历史 + 新 prompt + 已生成） |
| 单步前向传播 | GPU | GPU 显存 | 只计算当前新生成的 token |
| 采样 | GPU | GPU 显存 | greedy/top-k/top-p 采样 |
| KV Cache 追加 | GPU | GPU 显存 | 追加新 token 的 K/V |
| 输出传输 | GPU → CPU | GPU 显存 → CPU 内存 | 生成的 token ID 传回 CPU |
| 解码 | CPU | CPU 内存 | token ID → 文本 |

**特点**：内存带宽密集（反复读写 KV Cache），串行生成

---

## 数据传输路径对比

```
首次推理（无历史）：
输入 → CPU 内存(格式转换) → GPU 显存 → [Prefill] → KV Cache(GPU) → [Decode]

多轮对话（有历史）：
输入 → CPU 内存(格式转换) → GPU 显存
历史 KV Cache → 磁盘 → CPU 内存 → GPU 显存
→ [Prefill 新 prompt] → KV Cache 追加(GPU) → [Decode]
```

---

## PCIe 传输特点

| 阶段 | 传输频率 | 传输量 | 瓶颈 |
|------|----------|--------|------|
| KV Cache 加载 | 1 次（多轮对话） | 历史对话的 KV Cache（可能很大） | **潜在瓶颈** |
| Prefill | 1 次 | 新 prompt tokens | 可忽略 |
| Decode | 每次 1 token（可选） | 1 token ID | 可忽略 |

**KV Cache 加载的瓶颈**：
- 历史对话越长，KV Cache 越大（与 seq_len 成正比）
- PCIe 带宽限制（32 GB/s for PCIe 4.0 x16）
- 长对话场景下，加载 KV Cache 可能比重新 prefill 更慢

---

## 显存占用

```
推理显存 = 模型参数 + KV Cache

- 模型参数：FP16/FP8/INT4 量化
- KV Cache：batch_size × total_seq_len × hidden_dim × 2 (K+V) × bytes_per_value
  - 首次推理：KV Cache = prompt_len + generated_len
  - 多轮对话：KV Cache = 历史_len + 新_prompt_len + generated_len
```

---

## 推理优化技术

### MTP（Multi-Token Prediction）

MTP 让模型一次预测多个 token 而不是一个，加速 decode 过程[^mtp]。

**传统 Decode vs MTP**：
```
传统 Decode（单 token 预测）:
输入: "我 喜欢 吃"
输出: "的" (1 个 token)

MTP（多 token 预测）:
输入: "我 喜欢 吃"
输出: "的 味道 很 好" (4 个 token，并行预测)
```

**实现方式**：
- **多输出头**：模型最后添加多个输出头，每个头预测不同位置的 token
- **训练时预测多个位置**：损失函数包含多个位置的预测损失

**优势**：
```
传统 Decode: 生成 4 个 token 需要 4 次 forward pass
MTP: 生成 4 个 token 需要 1 次 forward pass
加速比: 4x (理想情况)
```

**挑战**：
- 预测越远的 token，准确性越低
- 需要修改训练目标和模型架构
- 通常需要配合验证机制

---

### Chunked Prefilling

Chunked Prefilling 将长 prompt 分块处理，降低首个 token 延迟（TTFT）[^chunked-prefill]。

**传统 Prefilling vs Chunked Prefilling**：
```
传统 Prefilling:
输入: "我 喜欢 吃 苹果 的 味道 很 好" (10 个 token)
一次性处理 → 等待整个 prompt 处理完 → 开始 decode

Chunked Prefilling:
输入: "我 喜欢 吃 苹果 的 味道 很 好" (10 个 token)
Chunk 1: "我 喜欢 吃" → 立即开始 decode
Chunk 2: "苹果 的" → 追加到 KV Cache
Chunk 3: "味道 很 好" → 追加到 KV Cache
```

**数据流动对比**：
```
传统 Prefilling:
输入 prompt → [Prefill 全部] → KV Cache 完成 → 开始 decode

Chunked Prefilling:
输入 prompt → [Prefill Chunk 1] → 立即 decode
           → [Prefill Chunk 2] → 追加 KV Cache
           → [Prefill Chunk 3] → 追加 KV Cache
```

**适用场景**：
| 场景 | 传统 Prefilling | Chunked Prefilling |
|------|----------------|-------------------|
| 短 prompt (< 1K tokens) | ✅ 适合 | ❌ 不必要 |
| 长 prompt (> 10K tokens) | ❌ TTFT 高 | ✅ 降低 TTFT |
| 流式输入 | ❌ 必须等输入完成 | ✅ 边输入边处理 |
| 显存受限 | ❌ 一次性占用大量显存 | ✅ 分批处理，显存峰值降低 |

**关键优势**：
- 降低 Time To First Token (TTFT)：不需要等整个 prompt 处理完就能开始生成
- 支持流式输入：用户边输入边生成
- 显存峰值降低：不需要一次性保存整个 prompt 的 KV Cache

**挑战**：
- Attention 计算：每个 chunk 需要重新计算与之前 chunks 的 attention
- KV Cache 管理：需要动态管理 KV Cache 的追加
- Chunk 大小选择：太小增加开销，太大失去优势（通常 512-4096 tokens）

---

### Continuous Batching（动态批处理）

传统静态批处理等一批请求全部完成才接新请求——先完成的请求白等，GPU 空转。Continuous Batching[^orca-2022] 在**每次迭代**时动态加入/移除请求：

```
静态批处理：
请求 A: [===Prefill===][=D1=][=D2=][=D3=][=D4=]  ← A 完成
请求 B: [===Prefill===][=D1=][=D2=][ 空等 ][ 空等 ]  ← B 早完成，GPU 空转
请求 C: [           等 A+B 全部完成后才开始          ]  ← C 被阻塞

Continuous Batching：
请求 A: [===Prefill===][=D1=][=D2=][=D3=][=D4=]
请求 B: [===Prefill===][=D1=][=D2=]               ← B 完成立即释放
请求 C:                             [=Prefill=][=D1=]...  ← C 立即填入空位
```

| 指标 | 静态批处理 | Continuous Batching | 权衡 |
|------|-----------|-------------------|------|
| GPU 利用率 | 40-60% | 70-90% | 调度开销略增 |
| 吞吐 | 1x | 2-3x | — |
| P99 延迟 | 高（等待整批） | 低（动态调度） | — |

Continuous Batching 是 Chunked Prefilling 的基础——后者在此之上进一步解决长 Prefill 阻塞 Decode 的干扰问题。

---

### Speculative Decoding（推测解码）

自回归生成每步只产出一个 token，每个 token 都需要完整的模型前向传播——即使模型很确定下一个词是什么。Speculative Decoding[^leviathan-2023] 的核心范式：**小模型快速草拟，大模型并行验证**。

```
传统 Decode（串行）：
大模型: [fwd]→"The" [fwd]→"cat" [fwd]→"sat" [fwd]→"on"     4 步

Speculative Decoding（草拟+验证）：
小模型: [fwd fwd fwd fwd]→"The cat sat on"                   快速草拟 4 个候选
大模型: [单次 fwd 并行验证 4 个]→ 接受 "The cat sat"，拒绝 "on"   1 步验证
```

验证使用**拒绝采样**：接受概率 $\min(1,\, p_{\text{大}}(x) / q_{\text{小}}(x))$，被拒绝的 token 从修正分布重采样——数学上保证输出分布与大模型完全一致。

| 方法 | 辅助结构 | 需额外训练 | 加速 | 权衡 |
|------|---------|-----------|------|------|
| Speculative Decoding[^leviathan-2023] | 独立小模型 | 否 | 1.5-2.5x | 需维护两套模型，显存开销大 |
| Medusa[^medusa-2024] | 原模型加多预测头 | 是（冻结主干） | 1.8-2.8x | 显存仅增 ~5%，但需微调 |
| EAGLE[^eagle-2024] | 特征空间自回归头 | 是 | 2.0-3.0x | 连续空间推测，接受率更高 |
| Lookahead Decoding | n-gram 匹配 | 否 | 1.2-2.0x | 无需辅助模型，依赖内容重复度 |

推测解码与 PD 分离正交——两者可叠加：Prefill 走标准路径，Decode 走推测路径。

---

### PD 分离（Prefill-Decode Disaggregation）

Prefill 和 Decode 的硬件需求截然对立（见§阶段一 vs §阶段二），放在同一 GPU 上相互干扰：长 Prefill 阻塞 Decode 的逐 token 生成（延迟抖动），Decode 的低算力利用率拖累 Prefill 吞吐。

PD 分离将两个阶段拆到**独立的 GPU 集群**，各自按最优配置运行[^distserve-2024]：

``` mermaid
graph LR
    Req["用户请求"] --> Sched["全局调度器"]
    Sched --> P["Prefill 集群\n(计算密集，追求高 MFU)"]
    P -->|"KV Cache\n(RDMA 传输)"| D["Decode 集群\n(带宽密集，追求低 TPOT)"]
    D --> Resp["流式响应"]
```

**核心设计决策**：KV Cache 从计算副产物变为一等资源——Prefill 产出的 KV Cache 通过高速网络（RDMA / NVLink）传输到 Decode 节点，配合[分层存储](../foundations/kv-cache.md#7)实现跨请求复用[^mooncake-2025]。

| 指标 | 同机混跑 | PD 分离 | 提升来源 |
|------|---------|---------|---------|
| TTFT P99 | 高 | 低 | Prefill 专属集群，无 Decode 干扰 |
| TPOT | 抖动大 | 稳定 | Decode 专属集群，无 Prefill 抢占 |
| GPU 利用率 | 中（折中） | 高（各自最优） | 硬件-负载匹配 |
| 长上下文吞吐 | 1x | 2-5x | KV Cache 复用 + 存储扩展 |

DistServe[^distserve-2024] 首次系统化验证了 PD 分离的可行性，提出 **Goodput**（满足 SLO 的有效吞吐）作为优化目标。Mooncake[^mooncake-2025]（FAST 2025 Best Paper）将其发展为生产级系统，在 Kimi 平台上实现日处理 100B+ tokens，A800 集群请求处理能力提升 115%。其 Transfer Engine 和 Mooncake Store 已开源并集成进 SGLang/vLLM/TRT-LLM → [详见](../libraries/mooncake.md)。

---

### 优化技术对比

| 技术 | 优化目标 | 核心思路 | 适用场景 |
|------|---------|---------|----------|
| MTP | 加速 Decode | 一次前向预测多个 token | 需要快速生成 |
| Continuous Batching | 提升吞吐 | 迭代级动态请求调度 | 所有在线服务 |
| Chunked Prefilling | 降低 TTFT | 长 Prefill 分块，与 Decode 交错 | 长 prompt、流式输入 |
| Speculative Decoding | 加速 Decode | 小模型草拟 + 大模型并行验证 | 有匹配的小模型 |
| PD 分离 | 全局资源效率 | Prefill / Decode 拆分到独立集群 | 大规模部署 |

---

## 与训练的对比

| 维度 | 训练 | 推理 |
|------|------|------|
| 显存占用 | 参数 + 激活值 + 梯度 + 优化器状态 | 参数 + KV Cache |
| 数据流 | 前向 + 反向（需要保存所有激活值） | 仅前向（KV Cache 替代激活值保存） |
| 计算量 | 前向 + 反向（约 2x） | 仅前向 |
| PCIe 瓶颈 | 每个 batch 都要传输数据 | KV Cache 加载可能成为瓶颈（长对话） |

推理流程延续了训练过程的数据流动视角[^training-evolution]，但去除了反向传播和优化器状态，显存占用显著降低。

---

## 参考资料

[^training-evolution]: 训练范式演进 → [详见](./training-evolution.md)
[^mtp]: Multi-Token Prediction. 一种让模型一次预测多个 token 的推理加速技术。相关研究包括 Medusa、Lookahead Decoding 等。
[^chunked-prefill]: Chunked Prefilling. 将长 prompt 分块处理的推理优化技术，用于降低 TTFT 和支持流式输入。常见于 vLLM、TensorRT-LLM 等推理引擎的实现中。
[^orca-2022]: Yu et al. *Orca: A Distributed Serving System for Transformer-Based Generative Models*. OSDI 2022. https://www.usenix.org/conference/osdi22/presentation/yu
[^leviathan-2023]: Leviathan et al. *Fast Inference from Transformers via Speculative Decoding*. ICML 2023. https://arxiv.org/abs/2211.17192
[^medusa-2024]: Cai et al. *Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads*. 2024. https://arxiv.org/abs/2401.10774
[^eagle-2024]: Li et al. *EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty*. ICML 2024. https://arxiv.org/abs/2401.15077
[^distserve-2024]: Zhong et al. *DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving*. OSDI 2024. https://arxiv.org/abs/2401.09670
[^mooncake-2025]: Qin et al. *Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot*. FAST 2025 Best Paper. https://arxiv.org/abs/2407.00079
