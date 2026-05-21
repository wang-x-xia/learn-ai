---
title: 基础设施
description: AI 系统的物理层——GPU 硬件、网络拓扑、存储系统、推理经济性。
---

# 基础设施

AI 系统的物理层与运营层，聚焦硬件、网络、存储和成本。

<div class="grid cards" markdown>

- :material-server: **[AI 基础设施](infrastructure.md)**

    ---

    GPU 加速器、NVLink、InfiniBand/RoCE、GPUDirect Storage

- :material-history: **[训练范式演进](training-evolution.md)**

    ---

    从 CPU 单卡到 GPU 单卡再到分布式训练的技术演进——以 MNIST 为例

- :material-school: **[LLM 训练流程](llm-training.md)**

    ---

    大语言模型的三阶段训练流程——预训练、指令微调、强化学习对齐

- :material-chart-line: **[分布式训练](distributed-training.md)**

    ---

    数据流、存储、并行策略、检查点机制——从数据加载到梯度更新的完整链路

- :material-view-module: **[数据并行](dp.md)**

    ---

    数据并行的技术设计——梯度同步、通信优化、常见实现（DDP、FSDP、ZeRO）

- :material-pipe: **[流水线并行](pp.md)**

    ---

    流水线并行的调度策略——GPipe、1F1B、Interleaved 1F1B 的技术权衡

- :material-chip: **[推理过程主要阶段](inference-stages.md)**

    ---

    KV Cache 加载、Prefill、Decode——从输入到输出的完整推理流程，以及 MTP、Chunked Prefilling 等优化技术

- :material-harddisk: **[Lustre 并行文件系统](lustre.md)**

    ---

    HPC/AI 超算存储——元数据与数据分离、条带化、LNet

- :material-harddisk: **[3FS 分布式文件系统](3fs.md)**

    ---

    DeepSeek AI 训练存储——CRAQ 强一致性、FoundationDB 元数据、NVMe SSD 集群

- :material-cash-multiple: **[推理经济性](inference-economics.md)**

    ---

    GPU 成本、API 定价、盈亏测算

</div>
