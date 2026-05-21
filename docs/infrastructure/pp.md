---
title: 流水线并行（Pipeline Parallel）
description: 流水线并行的调度策略——GPipe、1F1B、Interleaved 1F1B 的技术权衡
created: 2026-05-21
updated: 2026-05-21
tags:
  - distributed-training
  - parallelism
  - infrastructure
review:
---

??? note "背景知识"
    - **数据并行**：每个 GPU 处理不同 batch，同步梯度 → [详见](./dp.md)
    - **模型并行**：模型被切分到不同 GPU → [详见](./distributed-training.md)
    - **反向传播**：通过链式法则计算梯度，更新模型参数的核心算法

---

## 核心问题：模型太大单卡放不下怎么办？

当模型参数量超过单卡显存时，无法使用数据并行（每个 GPU 需要完整模型副本）。流水线并行（Pipeline Parallel, PP）将模型按层切分到多个 GPU，每个 GPU 只存储部分层，通过微批次流水线减少 GPU 空闲时间。

**基本思想**：
- 将模型按层切分为多个 stage
- 每个 GPU 负责一个或多个 stage
- 微批次（microbatch）像流水线一样在 GPU 间流动
- 不同 GPU 可以同时处理不同微批次的不同阶段

---

## 流水线并行的核心挑战

### 气泡（Bubble）

流水线并行的问题是：在稳态之前和之后，GPU 会有空闲时间（气泡）。

```
时间 →
GPU 0: [F1] [F2] [F3] [B1] [B2] [B3] [  ] [  ]
GPU 1: [  ] [F1] [F2] [F3] [B1] [B2] [B3] [  ]
GPU 2: [  ] [  ] [F1] [F2] [F3] [B1] [B2] [B3]

F = Forward, B = Backward, [ ] = 空闲（气泡）
```

气泡比例 = `(D - 1) / (M + D - 1)`
- `D`：流水线深度（GPU 数量）
- `M`：微批次数量

**问题**：GPU 越多，气泡比例越大，GPU 利用率越低。

### 微批次（Microbatch）

为了减少气泡，将一个 batch 切分为多个微批次：
- 每个微批次独立前向和反向传播
- 微批次流水线流动，减少 GPU 空闲时间
- 梯度累积到目标 batch size 后再更新参数

**权衡**：
- 微批次越多，气泡越小，但通信开销增加
- 微批次越少，通信开销小，但气泡越大

---

## 调度策略

### GPipe（Google, 2019）

**核心思想**：先完成所有微批次的前向传播，再完成所有微批次的后向传播[^gpipe-2019]。

```
时间 →
GPU 0: [F1] [F2] [F3] [F4] [  ] [  ] [  ] [B1] [B2] [B3] [B4]
GPU 1: [  ] [F1] [F2] [F3] [F4] [  ] [  ] [  ] [B1] [B2] [B3] [B4]
GPU 2: [  ] [  ] [F1] [F2] [F3] [F4] [  ] [  ] [B1] [B2] [B3] [B4]

所有前向完成后才开始反向，显存占用高（需要保存所有激活值）
```

**特点**：
- 简单易实现
- 显存占用高（需要保存所有微批次的激活值）
- 气泡较大

### 1F1B（One Forward One Backward）

**核心思想**：稳态时，每个 GPU 执行一次前向后立即执行一次后向[^megatron-2020-1f1b]。

```
时间 →
GPU 0: [F1] [F2] [F3] [B1] [B2] [B3] [  ] [  ]
GPU 1: [  ] [F1] [F2] [F3] [B1] [B2] [B3] [  ]
GPU 2: [  ] [  ] [F1] [F2] [F3] [B1] [B2] [B3]

稳态时 1F1B，显存占用低（及时释放激活值）
```

**特点**：
- 显存占用低（前向完成后立即反向，释放激活值）
- 气泡比 GPipe 小
- 实现复杂度中等

**非交错 1F1B**：
- 每个 GPU 分配连续的层（如 GPU 0: Layer 1-8, GPU 1: Layer 9-16）
- 简单但气泡较大

### Interleaved 1F1B（交错 1F1B）

**核心思想**：每个 GPU 分配多个非连续的层块（model chunk），微批次多次遍历流水线[^megatron-2020-interleaved]。

```
非交错 1F1B（V=1）：
GPU 0: Layer 1-8
GPU 1: Layer 9-16
GPU 2: Layer 17-24

Interleaved 1F1B（V=2）：
GPU 0: Layer 1-4, 17-20
GPU 1: Layer 5-8, 21-24
GPU 2: Layer 9-12, 25-28

每个 GPU 有 2 个 model chunk，微批次遍历流水线 2 次
```

**气泡减少**：
- 气泡比例 = `(1/V) * (D - 1) / (M + D - 1)`
- `V=2` 时，气泡减少一半
- `V=4` 时，气泡减少到 1/4

**代价**：
- 通信开销增加（每个微批次需要遍历流水线 V 次）
- 实现复杂度高（需要协调多个 model chunk）

**调度策略**：
- 当多个微批次准备好时，优先处理较早的微批次（"depth first"）
- 确保流水线稳定流动

---

## 性能对比

| 调度策略 | 显存占用 | 气泡比例 | 通信开销 | 实现复杂度 |
|----------|----------|----------|----------|------------|
| GPipe | 高 | 中 | 低 | 低 |
| 1F1B（非交错） | 低 | 中 | 中 | 中 |
| 1F1B（交错，V=2） | 中 | 低 | 高 | 高 |
| 1F1B（交错，V=4） | 中 | 很低 | 很高 | 很高 |

**选择建议**：
- **显存受限**：使用 1F1B（非交错）
- **GPU 数量多（气泡大）**：使用 Interleaved 1F1B（V=2 或 V=4）
- **网络带宽充足**：可以增加 V 值减少气泡
- **网络带宽受限**：使用较小的 V 值或非交错 1F1B

---

## 与其他并行方式的组合

大模型训练通常组合多种并行策略：

```
3D Parallel = Data Parallel (DP) + Pipeline Parallel (PP) + Tensor Parallel (TP)
```

**组合方式**：
- **DP**：处理不同 batch，同步梯度
- **PP**：模型按层切分，微批次流水线
- **TP**：层内切分（如注意力矩阵分片）

**示例**：8 卡 GPU 训练 7B 模型
- 2 个 GPU 组成 PP 组（Layer 1-16, Layer 17-32）
- 每个 PP 组内 2 个 GPU 进行 TP（注意力矩阵分片）
- 2 个 PP 组组成 DP（处理不同 batch）

---

## 实现细节

### 梯度累积

流水线并行中，微批次的梯度需要累积到目标 batch size 后再更新参数：

```python
# 伪代码
for microbatch in microbatches:
    loss = model(microbatch)
    loss.backward()  # 梯度累积

# 所有微批次完成后更新参数
optimizer.step()
optimizer.zero_grad()
```

### 检查点保存

流水线并行的检查点需要保存：
- 每个 stage 的模型权重
- 优化器状态
- 训练状态（step、epoch、dataloader offset）

**分布式检查点**：
- 每个 GPU 保存自己的分片
- 避免单点 I/O 瓶颈

---

## 常见问题

### 为什么需要微批次？

如果不切分微批次，流水线并行的气泡会非常大。微批次让不同 GPU 可以同时处理不同阶段，提高 GPU 利用率。

### Interleaved 1F1B 的通信开销为什么更高？

因为每个微批次需要遍历流水线 V 次，每次遍历都需要在 GPU 间传输激活值和梯度。V 越大，通信次数越多。

### 如何选择 V 值？

- V 值越大，气泡越小，但通信开销越大
- 通常选择 V=2 或 V=4
- 取决于网络带宽和 GPU 数量

---

## 参考资料

[^gpipe-2019]: Huang et al. *GPipe: Efficient Training of Giant Neural Networks Using Pipeline Parallelism*. 2019. https://arxiv.org/pdf/1811.06965
[^megatron-2020-1f1b]: Narayanan et al. *Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM*. 2020. https://arxiv.org/pdf/2104.04473
[^megatron-2020-interleaved]: Narayanan et al. *Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM*. 2020. https://arxiv.org/pdf/2104.04473
