---
title: NVIDIA ConnectX 系列
description: ConnectX SmartNIC 的代际演进与核心技术——从 CX-5 到 CX-8，RDMA 引擎、GPUDirect、In-Network Computing 的架构设计。
created: 2026-06-01
updated: 2026-06-01
tags:
  - infrastructure
  - network
  - rdma
  - infiniband
  - roce
  - nvidia
review: 2026-06-01
---

# NVIDIA ConnectX 系列

??? note "背景知识"
    - **RDMA (Remote Direct Memory Access)**：远程直接内存访问，绕过 CPU 实现零拷贝网络传输 → [详见](../infrastructure/infrastructure.md)
    - **InfiniBand / RoCE v2**：AI 集群的两大 RDMA 协议选择 → [详见](../infrastructure/infrastructure.md)
    - **PCIe**：CPU 与外设的总线标准，ConnectX 通过 PCIe 连接主机
    - **BlueField DPU**：在 ConnectX 网络前端上集成 Arm SoC 的基础设施处理器 → [详见](nvidia-bf.md)

> ConnectX 是 NVIDIA（原 Mellanox）的 ASIC SmartNIC 产品线[^nvidia-connectx-7]。它不是简单的"网口"，而是一颗集成了大量硬件加速引擎的专用芯片，负责 AI 集群中节点间通信的关键路径。

---

## 1. 架构定位：ASIC SmartNIC

ConnectX 的核心设计选择是 **ASIC 路线**——没有通用 CPU 核，所有功能由硬件固化的加速引擎实现：

- **优势**：最高能效比、最低延迟、最小芯片面积，适合功能明确的网络卸载
- **局限**：灵活性受限于 ASIC 预定义的功能集，无法运行自定义基础设施服务

与 BlueField DPU 的对比：ConnectX 是 BlueField 的"网络前端"子集。BlueField 在 ConnectX 基础上增加了 Arm CPU 核和可编程数据面加速器（[详见](nvidia-bf.md)）。

---

## 2. 代际演进

| 代 | 年份 | 最大速率 | PCIe | InfiniBand | 关键突破 | 典型部署 |
|----|------|---------|------|------------|---------|---------|
| **CX-5** | 2017 | 100 Gb/s | Gen 3/4 | EDR | RDMA、NVMe-oF 卸载、SR-IOV | 早期 AI 集群 |
| **CX-6** | 2019 | 200 Gb/s | Gen 4 | HDR | **In-Network Computing (SHARP)**、Multi-Host | DGX A100 |
| **CX-6 Dx** | 2020 | 200 Gb/s | Gen 4 | — | 硬件 **IPsec/TLS/MACsec** 加密卸载 | 安全合规场景 |
| **CX-7** | 2022 | **400 Gb/s** | **Gen 5** | **NDR** | ASAP2、GPUDirect Storage、全协议加密 | **DGX H100** |
| **CX-8** | 2025 | **800 Gb/s** | Gen 5 | **XDR** | SuperNIC 级 AI 优化、Direct Data Placement | **HGX B300** |

**带宽翻倍节奏**：每代约 2 年、带宽翻倍，与 InfiniBand 标准演进同步（EDR→HDR→NDR→XDR）[^fs-connectx-comparison]。

---

## 3. 核心技术能力

### 3.1 RDMA 引擎

ConnectX 的核心价值——硬件实现 RDMA 协议栈，绕过主机 CPU 和操作系统：

- **InfiniBand Verbs**：原生 IB RDMA，延迟 ~1 μs
- **RoCE v2 (RDMA over Converged Ethernet)**：在标准以太网上实现 RDMA 语义，需要 PFC/ECN 配合
- **零拷贝**：NIC DMA 引擎直接在本端内存和远端内存间传输数据，无 CPU 参与

### 3.2 GPUDirect 技术族

| 技术 | 数据路径 | 解决的问题 |
|------|---------|-----------|
| **GPUDirect RDMA** | 远端 NIC → 本端 NIC → **GPU HBM** | 跳过 CPU 内存的 bounce buffer |
| **GPUDirect Storage** | NVMe/NVMe-oF → **GPU HBM** | 训练数据直通 GPU，不经 CPU |
| **GPUDirect P2P** | GPU HBM ↔ GPU HBM (跨 PCIe) | 非 NVLink 场景的 GPU 间直传 |

GPUDirect RDMA 对 AI 训练至关重要：AllReduce 的梯度数据从 GPU HBM 出发，经 ConnectX 发送到远端节点的 ConnectX，再直接写入远端 GPU HBM——全程不经过任何 CPU 内存。

### 3.3 ASAP2 (Accelerated Switching and Packet Processing)

CX-7 引入的硬件级 OVS (Open vSwitch) 卸载：

- 将虚拟交换规则下沉到 NIC 硬件，匹配和转发在芯片内完成
- 主机 CPU 不再处理每个数据包的转发决策
- 云场景下可节省 20-30% 的 CPU 开销

### 3.4 In-Network Computing (SHARP)

NVIDIA 的独特竞争优势——在 **交换机侧** 完成集合通信的归约操作：

- AllReduce 的 SUM 操作在 Quantum 交换机内完成，而非在端侧
- 减少网络中实际传输的数据量（N 份梯度 → 1 份结果）
- 需要 ConnectX + Quantum 交换机配合，仅限 InfiniBand 生态

---

## 4. 在 AI 训练中的角色

在 NCCL 集合通信框架中，ConnectX 是"节点的出口"：

```
节点内 AllReduce（快）          节点间 AllReduce（慢但并行）
GPU0─┐                         Node0:GPU0 ─CX7─→ ┌─Leaf Switch 0─┐ ←─CX7─ Node1:GPU0
GPU1─┤ NVLink Switch            Node0:GPU1 ─CX7─→ │ Leaf Switch 1 │ ←─CX7─ Node1:GPU1
GPU2─┤ 900 GB/s                Node0:GPU2 ─CX7─→ │ Leaf Switch 2 │ ←─CX7─ Node1:GPU2
...  ┘                         ...                └───────────────┘        ...
```

**Ring/Tree AllReduce 的两阶段**：
1. **节点内**：8 张 GPU 通过 NVLink Switch 做本地规约（~900 GB/s，极快）
2. **节点间**：每张 GPU 通过各自的 ConnectX-7 在对应 Rail 上与其他节点的同号 GPU 通信（~50 GB/s，8 条 Rail 并行）

Rail-aligned 设计确保 8 条 Rail 的流量互不干扰，充分利用网络带宽[^cuda-h100-lesson9]（[详见](../infrastructure/single-node.md)）。

---

## 参考资料

[^nvidia-connectx-7]: NVIDIA. *ConnectX-7 Product Brief*. https://www.nvidia.com/en-eu/networking/infiniband-adapters/
[^fs-connectx-comparison]: FS.com. *NVIDIA ConnectX NIC Series Overview and Comparison*. https://www.fs.com/blog/nvidia-connectx-nic-series-overview-and-comparison-21170.html
[^cuda-h100-lesson9]: Prateek Shukla. *Multi-GPU Topology on H100 — Lesson 9*. https://cudacourseh100.github.io/pages/lesson-9.html
