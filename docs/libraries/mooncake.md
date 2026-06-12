---
title: "Mooncake：以 KV Cache 为中心的 LLM 推理基础设施"
description: "Mooncake 通过 Transfer Engine 的拓扑感知传输和 Mooncake Store 的分布式 KV 缓存，实现了 PD 分离架构下的高效 KV Cache 管理"
created: 2026-06-12
updated: 2026-06-12
tags:
  - inference
  - kv-cache
  - rdma
  - disaggregation
  - open-source
review:
---

| 属性 | 值 |
|------|-----|
| **开发者** | Moonshot AI (Kimi) |
| **开源协议** | Apache 2.0 |
| **GitHub** | [kvcache-ai/Mooncake](https://github.com/kvcache-ai/Mooncake) |
| **论文** | FAST 2025 Best Paper: [Mooncake: Trading More Storage for Less Computation](https://arxiv.org/abs/2407.00079) |
| **文档** | [kvcache-ai.github.io/Mooncake](https://kvcache-ai.github.io/Mooncake/) |

**一句话定位**：Kimi 的生产级推理基础设施[^mooncake-2025]，核心思想是**用廉价存储换昂贵算力**——将 KV Cache 从计算副产物提升为一等资源，围绕它构建分层存储、高速传输和全局调度。

---

??? note "背景知识"
    - **KV Cache**：推理时缓存 attention 的 K/V 矩阵，避免重复计算 → [详见](../foundations/kv-cache.md)
    - **PD 分离**：Prefill 和 Decode 拆分到独立 GPU 集群 → [详见](../infrastructure/inference-stages.md)
    - **RDMA**：Remote Direct Memory Access，绕过内核直接读写远端内存，延迟 1-5μs
    - **分层存储**：GPU HBM → CPU DRAM → NVMe SSD → 远端内存的多级缓存 → [详见](../foundations/kv-cache.md)

---

## 核心问题：PD 分离后 KV Cache 怎么搬

[PD 分离](../infrastructure/inference-stages.md)解决了 Prefill 和 Decode 的硬件需求冲突，但引入了一个新问题：**Prefill 产出的 KV Cache 必须高效传输到 Decode 节点**。对 Llama-3-70B + 128K 上下文，这意味着每个请求要搬 ~2GB 的 KV Cache。

传统方案（TCP / NCCL Gloo）的问题：

- 单 NIC 带宽瓶颈（25-50 Gbps），长上下文场景传输延迟数百毫秒
- 不感知 GPU/NIC 拓扑，跨 NUMA 传输浪费 PCIe/UPI 带宽
- 无法利用集群中空闲的 CPU DRAM / SSD 做 KV Cache 池化

Mooncake 用模块化架构解决这些问题：

``` mermaid
graph TB
    subgraph 上层集成
        SGLang & vLLM & TRT-LLM
    end
    subgraph Mooncake
        Store["Mooncake Store\n(分布式 KV 缓存)"]
        P2P["P2P Store\n(Checkpoint 分发)"]
        EP["Elastic EP\n(MoE 容错)"]
    end
    subgraph 传输层
        TE["Transfer Engine"]
        TE --- RDMA & TCP & NVMeoF["NVMe-oF"] & NVLink & CXL
    end
    上层集成 --> Mooncake
    Mooncake --> 传输层
```

---

## 技术亮点

### Transfer Engine：拓扑感知的零拷贝传输

Transfer Engine 是整个系统的基石，核心抽象只有两个：

- **Segment**：每个进程一个，覆盖其整个虚拟地址空间（DRAM + VRAM），通过 Buffer 注册暴露给远端
- **BatchTransfer**：异步多对多散聚操作，自动选择最优传输路径

**拓扑感知路径选择**：启动时生成拓扑矩阵，记录每张 NIC 与每块内存（按 NUMA / PCIe Switch 分组）的亲和度。传输时自动选最优 NIC 对——RDMA 走本地 PCIe Switch 而非跨 UPI，GPU 数据走 GPUDirect RDMA 而非先拷到 CPU。

**多 NIC 带宽聚合**：>64KB 的传输自动拆分成 slice，每个 slice 可走不同 NIC。单机多卡带宽叠加而非取最小值：

| 网络配置 | Transfer Engine | TCP | 加速比 |
|---------|----------------|-----|--------|
| 4×200Gbps RoCE | 87 GB/s | 36 GB/s | 2.4x |
| 8×400Gbps RoCE | 190 GB/s | 41 GB/s | 4.6x |

**连接管理**：按需建连（首次请求才创建 RDMA QP），用 SIEVE 算法淘汰冷连接，避免大集群连接爆炸。NIC 故障时自动切换备选路径重发。

**协议覆盖**：TCP、RDMA、AWS EFA、NVMe-oF、NVLink、HIP（AMD）、CXL、Ascend（华为）——同一套 API 屏蔽底层差异。

---

### Mooncake Store：为 LLM 推理设计的分布式 KV 缓存

不是通用缓存（Redis/Memcached），而是专为 KV Cache 不可变语义设计的存储引擎。

**架构的核心设计决策**：

| 设计 | 选择 | 理由 |
|------|------|------|
| 数据路径 | Client → Client，绕过 Master | Master 只管元数据分配，不成为数据瓶颈（类比 HDFS NameNode 不走数据） |
| Client 角色 | 双角色：既发请求，也提供存储 | 推理节点的空闲 DRAM 直接变成 KV Cache 池，无需额外存储节点 |
| 一致性 | Put 后不可变，Get 保证读到完整数据 | KV Cache 天然是写一次读多次，不可变语义大幅简化一致性协议 |
| 副本策略 | Slice 级 best-effort 复制，保证落在不同 Segment | 热点 system prompt 可多副本分散读压力 |

**LLM 负载定制的内存管理**：

- **O(1) 分配器**（OffsetBufferAllocator）：基于 bin 的偏移分配，针对 LLM 推理的块大小分布优化
- **淘汰策略**：近似 LRU + 高水位触发（95%），Lease 机制保护正在读写的对象不被淘汰
- **Soft Pin**：高频对象（system prompt 等）优先保留，TTL 过期自动解除，访问续期
- **Hard Pin**：模型权重等永不淘汰，只能显式删除

**部署灵活性**：嵌入式（与 vLLM 同进程）、Dummy-Real 分离（TP=8 时 8 个 dummy + 1 个 real client）、独立存储服务三种模式。支持 etcd 多 Master 选主的高可用部署。

---

### P2P Store：BitTorrent 式 Checkpoint 分发

无中心 Master 的对等架构，元数据存 etcd：

1. 训练节点 **Register**（做种）→ 只注册元数据，不传数据
2. 推理节点 **GetReplica**（下载 + 成为新种子）→ 后续节点从多个源并行拉取

避免单机出口带宽饱和。生产数据：Kimi-K2（1T 参数）跨数千张 GPU checkpoint 分发，RDMA 模式 ~7.2s 完成（原 TCP 方案 53s，加速 7x）。

---

### Elastic Expert Parallelism：MoE 推理容错

大规模 MoE 推理（如 Kimi-K2，384 Expert）中 GPU 故障概率不可忽略。Mooncake 的做法：

- 自动检测故障 rank
- 配合 EPLB（Expert Load Balancing）模块动态路由 token 到健康 rank
- 推理服务不中断，degraded 模式继续服务

已集成进 SGLang。相关论文：*Surviving Partial Rank Failures in Wide Expert-Parallel MoE Inference*[^ep-2026]。

---

## 生态与生产验证

### 推理引擎集成

Transfer Engine 和 Mooncake Store 已成为 PD 分离架构的事实标准传输层：

| 系统 | 集成内容 |
|------|---------|
| SGLang | HiCache 后端、PD 分离、Encoder Global Cache、Elastic EP |
| vLLM | KV Connector（PD 分离）、Mooncake Store Connector |
| TensorRT-LLM | KV Cache 传输 |
| LMCache | 远端 Connector |
| LMDeploy | PD 分离后端 |

### 生产规模数据

| 场景 | 配置 | 指标 |
|------|------|------|
| Kimi K2 部署 | 128× H200, PD 分离 + Expert 并行 | Prefill 224k tok/s, Decode 288k tok/s |
| Kimi 平台整体 | A800 集群 | 请求处理能力 +115%, 日处理 100B+ tokens |
| SGLang + DeepSeek-R1-671B | PD 分离 + HiCache | Cache 命中时 TTFT 降低 84%（蚂蚁集团评测） |

---

## 为什么值得知道

1. **"存储换算力"的系统化验证**：Mooncake 不是一个点优化，而是围绕"KV Cache 是一等公民"这一设计哲学构建了完整的存储-传输-调度栈，并在 Kimi 的生产环境中验证了其可行性
2. **Transfer Engine 的网络工程创新**：拓扑感知 + 多 NIC 聚合 + 自动故障切换，解决了 RDMA 在大规模异构集群中的实际部署难题，这些工程经验超越了论文层面
3. **开源生态的枢纽地位**：SGLang、vLLM、TRT-LLM 三大推理引擎均已官方集成，Mooncake 正在成为 PD 分离架构的基础设施标准
4. **从推理到训练的扩展**：P2P Store 用于 checkpoint 分发，TorchSpec 用 Mooncake 解耦推理与训练——正在从推理基础设施演进为通用 AI 数据传输层

---

## 参考资料

[^mooncake-2025]: Qin et al. *Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot*. FAST 2025 Best Paper. https://arxiv.org/abs/2407.00079
[^ep-2026]: Sun et al. *Surviving Partial Rank Failures in Wide Expert-Parallel MoE Inference*. 2026. https://arxiv.org/abs/2605.10670
