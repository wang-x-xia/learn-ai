---
title: 分布式训练基础设施
description: 大模型训练的数据流、存储与并行架构——从数据加载到梯度更新的完整链路
created: 2026-05-15
updated: 2026-05-15
tags:
  - distributed-training
  - data-loading
  - checkpoint
  - parallelism
review: 2026-05-15
---

??? note "背景知识"
    - **Transformer 架构**：自注意力 + FFN 的堆叠，当前 LLM 的底层结构 → [详见](../foundations/transformer.md)
    - **反向传播**：通过链式法则计算梯度，更新模型参数的核心算法
    - **GPU 显存层次**：HBM（高带宽显存）、SRAM（片上缓存）的层次结构影响数据访问模式

---

## 核心问题：大模型怎么训练？

训练一个 LLM 不是"把数据喂给模型"那么简单，而是一个复杂的系统工程：

```
原始数据 → 预处理 → 分布式存储 → 数据加载器 → GPU 计算 → 梯度同步 → 检查点保存
   ↓           ↓           ↓           ↓          ↓          ↓          ↓
PB级文本   清洗/分词   Lustre/3FS   DataLoader   前向/反向   All-Reduce  定期保存
```

每个环节都有专门的 infra 设计和优化。

---

## 数据流全景

### 1. 数据存储层

**原始数据位置**：
- 本地文件系统：小规模实验
- 对象存储（S3/OSS）：云端训练
- 并行文件系统（Lustre/3FS）：超算集群

**存储格式**：
- 原始文本：JSONL、Parquet
- 预处理后的 token：二进制格式（如 IndexedDataset）
- 检查点：模型权重 + 优化器状态 + 训练状态

**关键设计**：
- **数据分片**：将大数据集分成多个 shard，每个 GPU 读取不同 shard
- **本地缓存**：首次从远程存储读取后，缓存到本地 SSD，避免重复网络传输
- **预取（Prefetch）**：GPU 计算 batch N 时，CPU 提前加载 batch N+1 的数据

### 2. 数据加载层

**DataLoader 的工作流程**：

```python
# 伪代码
for epoch in range(num_epochs):
    for batch in dataloader:
        # 1. 从存储读取数据（CPU）
        tokens = storage.read(shard_id, offset, size)
        
        # 2. 数据预处理（CPU）
        tokens = pad(tokens, max_length)
        tokens = maybe_augment(tokens)
        
        # 3. 传输到 GPU（PCIe）
        gpu_tokens = tokens.to('cuda')
        
        # 4. GPU 计算
        loss = model(gpu_tokens)
        loss.backward()
        
        # 5. 梯度同步（GPU 间通信）
        all_reduce_gradients()
        
        # 6. 更新参数
        optimizer.step()
```

**性能瓶颈**：
- 存储 I/O：读取速度跟不上 GPU 计算速度
- PCIe 带宽：CPU 到 GPU 的数据传输限制
- 数据预处理：CPU 计算成为瓶颈

**优化手段**：
- **多线程数据加载**：独立的 DataLoader 进程/线程，不阻塞 GPU 计算
- **GPU 加速预处理**：用 GPU 做 padding、mask 生成等
- **NVIDIA DALI**：专门的 GPU 数据加载库，支持 JPEG 解码、图像增强等

### 3. 计算层

**单 GPU 的计算流程**：

```
输入 tokens → Embedding → Transformer 层 → 输出 logits → Loss → 梯度
```

**显存占用**：
- 模型参数：FP16/FP8 存储权重
- 激活值：前向传播的中间结果（需要保存用于反向传播）
- 梯度：反向传播计算的梯度
- 优化器状态：Adam 的动量、方差等（通常是参数的 2-3 倍）

**显存优化**：
- **梯度检查点（Gradient Checkpointing）**：不保存所有激活值，反向时重新计算部分激活值，用计算换显存
- **混合精度训练**：FP16 计算降低显存和计算量，FP32 master weights 保证数值稳定性
- **ZeRO（零冗余优化器）**：将优化器状态、梯度、参数分片到不同 GPU，打破单卡显存限制

### 4. 通信层

**为什么需要通信**：
- **数据并行**：每个 GPU 计算不同 batch，需要同步梯度
- **模型并行**：模型被切分到不同 GPU，需要传输激活值
- **流水线并行**：不同 GPU 处理不同层，需要传输中间结果

**通信原语**：
- **All-Reduce**：所有 GPU 的梯度求和并分发（数据并行核心）
- **All-to-All（A2A）**：每个 GPU 向所有其他 GPU 发送不同数据（MoE 核心）
- **Broadcast**：从一个 GPU 向所有 GPU 广播数据
- **Reduce-Scatter**：聚合数据并分片

**通信硬件**：
- **NVLink**：NVIDIA GPU 间的高速互联（单链路 25-50 GB/s）
- **InfiniBand**：服务器间的高速互联（200-800 Gb/s）
- **RoCE**：基于以太网的 RDMA（成本更低，但性能略低）

**通信优化**：
- **梯度累积**：多次小 batch 的梯度累积后再同步，减少通信频率
- **通信计算 overlap**：在 GPU 计算的同时进行通信，用计算掩盖通信延迟
- **压缩通信**：量化梯度（FP16/FP8）减少通信量

### NCCL：NVIDIA 集合通信库

**NCCL（NVIDIA Collective Communication Library）** 是 NVIDIA 提供的 GPU 集合通信库，为分布式训练提供高性能的通信原语（All-Reduce、All-Gather 等）。

**拓扑感知通信**：
- NCCL 自动检测硬件拓扑（PCIe、NVLink、NVLink Switch、InfiniBand、RoCE）
- 根据拓扑结构选择最优通信路径和算法
- 跨节点通信时考虑网络拓扑（如多数据中心场景）

**通信协议**：
NCCL 提供三种通信协议，针对不同消息大小优化带宽和延迟[^nccl-2025-demystifying]：

| 协议 | 适用场景 | 特点 |
|------|----------|------|
| Simple | 大消息（>1MB） | 最大化带宽利用率，使用内存栅栏同步 |
| LL（Low Latency） | 小消息（<1MB） | 优化延迟，使用轻量级 flag 同步（4字节数据+4字节flag） |
| LL128 | 中等消息 | 平衡带宽和延迟，128字节传输单元（120字节数据+8字节flag） |

**集合通信算法**：
- **Ring AllReduce**：环形拓扑，每个 GPU 只与相邻 GPU 通信，带宽利用率高
- **Tree AllReduce**：树形拓扑，层次化 reduce-scatter + allgather，适合大规模集群
- NCCL 动态选择算法，根据消息大小、GPU 数量、网络拓扑等因素

**单 kernel 实现**：
- 每个集合通信操作由单个 CUDA kernel 实现
- 避免多次 kernel 启动和内存拷贝的开销
- 使用 GPUDirect Peer-to-Peer 直接访问 GPU 间内存
- 当 P2P 不可用时，通过 pinned system memory 中转

---

## 并行策略拓扑

大模型训练通常结合多种并行策略：

### 数据并行（Data Parallel, DP）

每个 GPU 有完整模型副本，处理不同 batch 的数据，通过 All-Reduce 同步梯度。详见[数据并行技术文档](./dp.md)。

**适用场景**：模型能放入单卡显存，需要加速训练。

### 模型并行（Tensor Parallel, TP）

```
Layer 1（切分）          Layer 2（切分）
GPU 0: 部分 A  ←─→      GPU 0: 部分 A
GPU 1: 部分 B  ←─→      GPU 1: 部分 B
GPU 2: 部分 C  ←─→      GPU 2: 部分 C
GPU 3: 部分 D  ←─→      GPU 3: 部分 D

通信：All-Reduce（每层内部同步）
```

**特点**：
- 模型被切分到多个 GPU
- 每个 GPU 只存储部分参数
- 每层计算后需要同步中间结果

**适用场景**：模型太大，单卡放不下

### 流水线并行（Pipeline Parallel, PP）

模型按层切分到不同 GPU，微批次像流水线一样在 GPU 间流动。通过调度策略（GPipe、1F1B、Interleaved 1F1B）减少 GPU 空闲时间。详见[流水线并行技术文档](./pp.md)。

**适用场景**：模型层数很多，需要跨 GPU。

### 混合并行（3D Parallel）

结合 DP + TP + PP，适用于超大规模模型训练（如 GPT-3、DeepSeek-V3）。通信层次包括 TP 组内的 All-Reduce、PP 组间的 P2P 通信、DP 组间的梯度同步。详见[数据并行](./dp.md)和[流水线并行](./pp.md)。

---

## 检查点（Checkpoint）机制

### 为什么需要检查点

训练大模型需要数月，期间可能发生：
- 硬件故障（GPU 挂掉）
- 网络中断
- 作业被抢占（超算集群有时间限制）

检查点允许从上次保存的状态恢复训练，避免从头开始。

### 检查点内容

```
checkpoint/
├── model_weights/          # 模型权重
│   ├── layer_0.pt
│   ├── layer_1.pt
│   └── ...
├── optimizer_state/        # 优化器状态（Adam 的动量、方差）
│   ├── optimizer_0.pt
│   └── ...
├── training_state/         # 训练状态
│   ├── epoch
│   ├── step
│   ├── random_seed
│   └── dataloader_state
└── metadata.json           # 元数据（架构配置、超参数等）
```

### 检查点策略

**保存频率**：
- 太频繁：浪费存储和 I/O
- 太少：故障时丢失大量进度
- 典型：每 100-1000 步保存一次

**分层保存**：
- **频繁保存轻量级状态**：只保存训练状态（step、epoch、dataloader offset）
- **较少保存完整检查点**：保存模型权重 + 优化器状态

**异步保存**：
- GPU 计算下一步时，后台线程保存当前检查点到存储
- 避免保存阻塞训练

**分布式检查点**：
- 每个 GPU 保存自己的分片到不同存储节点
- 避免单点 I/O 瓶颈

---

## 端到端训练流程示例

以 8 卡 GPU 训练一个 7B 模型为例：

```
1. 初始化
   - 8 个 GPU 初始化（加载模型架构）
   - 从存储加载最新检查点（如果有）
   - 初始化 DataLoader（连接存储，准备数据分片）

2. 训练循环
   for step in range(total_steps):
       # 数据加载（CPU，异步）
       batch = dataloader.next_batch()
       
       # 前向传播（GPU）
       logits = model(batch.tokens)
       loss = compute_loss(logits, batch.labels)
       
       # 反向传播（GPU）
       loss.backward()
       
       # 梯度同步（GPU 间通信）
       all_reduce_gradients()  # All-Reduce
       
       # 参数更新（GPU）
       optimizer.step()
       optimizer.zero_grad()
       
       # 检查点保存（异步）
       if step % checkpoint_interval == 0:
           save_checkpoint_async()

3. 训练结束
   - 保存最终检查点
   - 清理资源
```

---

## 常见性能瓶颈

| 瓶颈 | 症状 | 解决方案 |
|------|------|----------|
| 存储 I/O | GPU 利用率低，dataloader 等待 | 本地缓存、预取、更快的存储 |
| PCIe 带宽 | GPU 利用率低，数据传输慢 | GPU 加速预处理、压缩数据 |
| 通信带宽 | GPU 利用率低，all_reduce 慢 | 梯度累积、通信计算 overlap、压缩通信 |
| 显存不足 | OOM 错误 | ZeRO、梯度检查点、混合精度 |
| CPU 瓶颈 | GPU 利用率低，CPU 占用高 | 多线程数据加载、GPU 加速预处理 |

---

## 参考资料

[^nccl-2025-demystifying]: Hu et al. *Demystifying NCCL: An In-depth Analysis of GPU Communication Protocols and Algorithms*. 2025. https://arxiv.org/html/2507.04786v2
