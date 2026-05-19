---
title: 训练范式演进
description: 从 CPU 单卡到 GPU 单卡再到分布式训练的技术演进——以 MNIST 为例
created: 2026-05-18
updated: 2026-05-18
tags:
  - gpu
  - infrastructure
  - history
review: 2025-01-19
---

??? note "背景知识"
    - **反向传播**：通过链式法则计算梯度，更新模型参数的核心算法
    - **GPU 显存层次**：HBM（高带宽显存）、SRAM（片上缓存）的层次结构影响数据访问模式

## GPU 加速训练（单卡时代）

GPU 的出现改变了训练范式。GPU 有数千个核心，擅长大规模矩阵运算。以 PyTorch 训练 MNIST 为例：

```python
import torch
import torch.nn as nn
import torch.optim as optim

# 1. 数据加载（CPU 内存）
train_dataset = MNIST(root='./data', train=True, download=True)
train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32)

# 2. 模型定义（CPU 内存）
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)
optimizer = optim.SGD(model.parameters(), lr=0.01)

# 3. 将模型移动到 GPU（CPU → GPU 显存）
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)  # 参数从 CPU 内存拷贝到 GPU 显存

for epoch in range(10):
    for batch_images, batch_labels in train_loader:
        # 4. 数据传输（CPU 内存 → GPU 显存，通过 PCIe）
        batch_images = batch_images.to(device)
        batch_labels = batch_labels.to(device)

        # 5. 前向传播（GPU 计算，数据在 GPU 显存）
        logits = model(batch_images.view(-1, 784))
        loss = nn.CrossEntropyLoss()(logits, batch_labels)

        # 6. 反向传播（GPU 计算，梯度在 GPU 显存）
        optimizer.zero_grad()
        loss.backward()  # 自动计算梯度

        # 7. 参数更新（GPU 计算，参数在 GPU 显存）
        optimizer.step()

# 8. 保存模型参数（GPU 显存 → CPU 内存 → 磁盘）
torch.save(model.state_dict(), 'model_weights.pt')
# 内部流程：
# 1. state_dict() 收集所有参数张量（仍在 GPU 显存）
# 2. torch.save() 将张量拷贝到 CPU 内存（通过 PCIe）
# 3. 序列化为字节流并写入磁盘

# 加载模型（磁盘 → CPU 内存 → GPU 显存）
loaded_model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)
loaded_model.load_state_dict(torch.load('model_weights.pt'))  # 磁盘 → CPU 内存
loaded_model.to(device)  # CPU 内存 → GPU 显存
```

### CPU 和 GPU 的分工

| 操作 | 执行位置 | 数据位置 | 说明 |
|------|----------|----------|------|
| 数据加载 | CPU | CPU 内存 | 从磁盘读取数据，解码图像 |
| 数据预处理 | CPU | CPU 内存 | 归一化、数据增强 |
| 模型定义 | CPU | CPU 内存 | 构建计算图 |
| 模型参数传输 | CPU → GPU | CPU 内存 → GPU 显存 | `.to(device)` 触发 PCIe 传输 |
| batch 数据传输 | CPU → GPU | CPU 内存 → GPU 显存 | 每个 batch 都需要传输 |
| 前向传播 | GPU | GPU 显存 | 矩阵乘法、激活函数 |
| 反向传播 | GPU | GPU 显存 | 自动微分计算梯度 |
| 参数更新 | GPU | GPU 显存 | SGD/Adam 更新参数 |
| 模型保存 | GPU → CPU → 磁盘 | GPU 显存 → CPU 内存 → 磁盘 | 训练完成后持久化参数 |
| 模型加载 | 磁盘 → CPU → GPU | 磁盘 → CPU 内存 → GPU 显存 | 推理时加载参数 |

### 数据传输路径

```
磁盘 → CPU 内存 → PCIe 总线 → GPU 显存
 ↓        ↓          ↓          ↓
读取    预处理     传输(瓶颈)   计算
```

### PCIe 传输瓶颈

- PCIe 3.0 x16 带宽约 16 GB/s
- PCIe 4.0 x16 带宽约 32 GB/s
- GPU 计算（如 A100）可达 312 TFLOPS，远超数据传输能力
- 因此需要异步数据加载：GPU 计算 batch N 时，CPU 提前加载 batch N+1

---

## 前向与后向的依赖关系

反向传播依赖前向传播的中间结果（激活值），这带来了显存占用问题：

```python
# 以一个简单的 2 层 MLP 为例
class SimpleMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        # 前向传播
        h1 = self.fc1(x)        # 激活值 1：需要保存用于反向传播
        a1 = torch.relu(h1)    # 激活值 2：需要保存用于反向传播
        out = self.fc2(a1)     # 激活值 3：需要保存用于反向传播
        return out

# 反向传播时的依赖链
loss.backward()
# ↓ 需要计算 ∂loss/∂fc2
#   ↓ 需要 a1（前向传播保存的激活值）
# ↓ 需要计算 ∂loss/∂fc1
#   ↓ 需要 h1（前向传播保存的激活值）
#   ↓ 需要 x（输入数据）
```

### 显存占用公式

```
总显存 = 模型参数 + 激活值 + 梯度 + 优化器状态

- 模型参数：FP16 存储权重
- 激活值：前向传播的所有中间结果（与 batch size 成正比）
- 梯度：反向传播计算的梯度（与参数量相同）
- 优化器状态：Adam 的动量、方差（通常是参数的 2-3 倍）
```

### 为什么需要分布式训练

单卡训练的瓶颈：
1. **显存限制**：大模型（如 GPT-3，175B 参数）单卡放不下
   - 175B 参数 × 2 bytes (FP16) = 350 GB，远超单卡显存（A100 80 GB）
2. **计算速度**：训练大模型需要数月，需要多卡加速
3. **数据规模**：万亿级 token 数据集，需要分布式数据加载

因此发展出数据并行、模型并行、流水线并行等分布式训练策略[^distributed-training]。

---

## 参考资料

[^distributed-training]: 分布式训练基础设施 → [详见](./distributed-training.md)
