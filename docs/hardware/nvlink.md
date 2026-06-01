---
title: NVIDIA NVLink 与 NVLink Switch
description: NVLink 高速互联协议与 NVLink Switch 交换芯片的代际演进——从点对点链路到机架级全互连 fabric 的架构设计。
created: 2026-06-01
updated: 2026-06-01
tags:
  - infrastructure
  - gpu
  - nvlink
  - nvswitch
  - nvidia
review: 2026-06-01
---

# NVIDIA NVLink 与 NVLink Switch

??? note "背景知识"
    - **PCIe**：CPU 与外设的通用总线标准，GPU 通过 PCIe 连接主机 → [详见](../infrastructure/infrastructure.md)
    - **RDMA**：远程直接内存访问，NVLink 在节点内提供类似的零拷贝 GPU 间通信
    - **单节点拓扑**：NVLink/NVLink Switch 在 DGX H100 中的实际部署方式 → [详见](../infrastructure/single-node.md)
    - **NCCL**：NVIDIA 集合通信库，自动感知 NVLink 拓扑选择最优通信路径

> NVLink 是 NVIDIA 的 GPU 间高速点对点互联协议，NVLink Switch 是配套的交换芯片。两者组合解决了一个根本问题：**PCIe 带宽不够用**——当 GPU 算力每代翻倍时，GPU 间通信带宽必须同步增长，否则多卡并行的效率会被互联瓶颈拖垮。

---

## 1. 为什么需要 NVLink

PCIe 是通用总线，设计目标是连接各种外设（网卡、SSD、GPU……），带宽演进受制于向后兼容和标准化进程。GPU 算力的增长速度远超 PCIe 带宽的迭代[^nvidia-nvlink-blog]：

| 年份 | GPU | FP16 算力 | PCIe 带宽 | NVLink 带宽 | NVLink/PCIe |
|------|-----|----------|-----------|------------|-------------|
| 2016 | P100 | 21 TFLOPS | 32 GB/s (Gen3) | 160 GB/s | **5x** |
| 2017 | V100 | 125 TFLOPS | 32 GB/s (Gen3) | 300 GB/s | **9x** |
| 2020 | A100 | 312 TFLOPS | 64 GB/s (Gen4) | 600 GB/s | **9x** |
| 2022 | H100 | 989 TFLOPS | 128 GB/s (Gen5) | 900 GB/s | **7x** |
| 2024 | B200 | ~2250 TFLOPS | 128 GB/s (Gen5) | 1800 GB/s | **14x** |

**关键洞察**：NVLink 不是 PCIe 的替代品，两者共存。NVLink 专注 GPU↔GPU 的快速路径；PCIe 仍然负责 CPU↔GPU 和外设连接。分布式训练中，节点内通信走 NVLink（快），节点间通信走 PCIe→ConnectX→网络（慢）——这个带宽悬崖直接决定了并行策略的切分方式。

---

## 2. NVLink 协议演进

### 2.1 一条 NVLink 的物理结构

"18 条 NVLink"中的**一条 (link)** 是一个双向点对点通道，内部由三层结构组成：

```
一条 NVLink (link)                          ← "18 条"的计数单位
├── TX 子链路 (sub-link) ─→ 发送方向
│   ├── 差分对 0 ─→ 物理线对，跑 PAM4 信号
│   └── 差分对 1
└── RX 子链路 (sub-link) ←─ 接收方向
    ├── 差分对 0
    └── 差分对 1
```

以 NVLink 4.0 (H100) 为例：每条 link 包含 TX/RX 两个子链路，每个子链路 2 对差分对，每对跑 50 Gbaud PAM4（每符号 2 bit，有效 100 Gb/s/对）。一条 link 的单方向带宽 = 2 对 × 100 Gb/s = 200 Gb/s = **25 GB/s**，双向合计 **50 GB/s**。18 条 × 50 GB/s = **900 GB/s**。

差分对数量逐代减少（8→4→2），但波特率和调制方式同步升级，所以单链路带宽不降反升。减少差分对意味着更少的引脚——同一 GPU 封装就能塞下更多链路（4 条→18 条），总带宽从 160 GB/s 跃升到 1800 GB/s。

**18 条链路的数据流方式**：GPU A 向 GPU B 发送数据时，不需要"选择走哪条链路"。硬件把数据切成小包（FLIT, Flow Control Digit），自动交织分发到 GPU A 连向所有 4 颗 NVLink Switch 的全部链路上**同时发送**。每颗 NVLink Switch 收到包后，经内部 crossbar 转发到 GPU B 对应的端口。GPU B 侧从 4 颗 NVLink Switch 同时收包并重组。整个过程类似内存多通道交织——18 条链路并行工作、自动负载均衡，对上层软件完全透明，NCCL 只看到一个 900 GB/s 的逻辑通道。

### 2.2 代际规格

| 代 | 年份 | GPU 架构 | 链路数/GPU | 单链路带宽 (双向) | GPU 总带宽 | 信号调制 |
|----|------|---------|-----------|-----------------|-----------|---------|
| **1.0** | 2016 | Pascal P100 | 4 | 40 GB/s | 160 GB/s | NRZ 20 Gbaud |
| **2.0** | 2017 | Volta V100 | 6 | 50 GB/s | 300 GB/s | NRZ 25 Gbaud |
| **3.0** | 2020 | Ampere A100 | 12 | 50 GB/s | 600 GB/s | NRZ 50 Gbaud |
| **4.0** | 2022 | Hopper H100 | 18 | 50 GB/s | 900 GB/s | PAM4 50 Gbaud |
| **5.0** | 2024 | Blackwell B200 | 18 | 100 GB/s | 1800 GB/s | PAM4 100 Gbaud |
| **6.0** | 2026+ | Rubin | 36 | 100 GB/s | 3600 GB/s | — |

### 2.3 物理层各代参数

| 代 | 差分对/子链路 | 波特率 | 调制 | 单方向带宽/链路 |
|----|-------------|--------|------|---------------|
| 1.0 | 8 | 20 Gbaud | NRZ | 20 GB/s |
| 2.0 | 8 | 25 Gbaud | NRZ | 25 GB/s |
| 3.0 | **4** | 50 Gbaud | NRZ | 25 GB/s |
| 4.0 | **2** | 50 Gbaud | **PAM4** | 25 GB/s |
| 5.0 | 2 | **100 Gbaud** | PAM4 | **50 GB/s** |

配合 2.1 节的结构图阅读：每行的"差分对/子链路"就是树状图中一个子链路下面挂了几对差分对[^hotchips-nvswitch]。

---

## 3. NVLink Switch：从点对点到交换 Fabric

### 3.1 为什么需要 NVLink Switch

没有 NVLink Switch 时，GPU 间只能用 NVLink 做点对点直连。对于 8 张 GPU 的全互连，需要 $C(8,2) = 28$ 条链路——而早期 GPU 只有 4-6 条 NVLink，远远不够。结果是部分 GPU 对必须走 PCIe 中转，出现"快/慢路径"的 NUMA 效应。

NVLink Switch 的解决方案：**把 NVLink 从点对点协议变成交换网络**。每张 GPU 只需将自己的全部 NVLink 连到 NVLink Switch，由其内部的 crossbar 提供任意 GPU 对之间的全速通信。连接数从 $O(n^2)$ 降到 $O(n)$。

### 3.2 NVLink Switch 代际规格

| 代 | 年份 | 系统 | 端口数 | 单芯片带宽 (双向) | 每系统数量 | 制程 / 晶体管 |
|----|------|------|--------|------------------|-----------|------------|
| **1st** | 2018 | DGX-2 (16x V100) | 18 | 900 GB/s | 12 (6/baseboard) | 12nm / 2B |
| **2nd** | 2020 | DGX A100 (8x A100) | — | — | 6 | — |
| **3rd** | 2022 | DGX H100 (8x H100) | **64** | **3.2 TB/s** | **4** | **4N / 25.1B** |
| **4th** | 2024 | GB200 NVL72 | **72** | **14.4 TB/s** | 机架级 switch tray | — |

**3rd 代（H100）的关键突破**[^hotchips-nvswitch]：
- **SHARP (Scalable Hierarchical Aggregation and Reduction Protocol)**：在交换芯片内完成 AllReduce 归约，减少网络实际传输量
- **NVLink Network 端口**：64 端口中，约 36 个连节点内 GPU，剩余端口可通过 OSFP 线缆连到外部 NVLink Switch，实现**跨节点 NVLink 域**

### 3.3 NVLink Switch 内部架构

每颗 NVLink Switch 的核心是一个**全连接 crossbar**——N×N 端口的无阻塞交叉开关：

- 任意输入端口的数据可以路由到任意输出端口，无需排队等待
- 所有端口对可以同时满速通信（非阻塞）
- 多颗 NVLink Switch 并联时，每张 GPU 向每颗芯片各接入若干链路，流量跨芯片并行传输

以 DGX H100 为例：8 GPU × 18 NVLink = 144 条链路，需要 4 颗 64 端口 NVLink Switch 才能容纳（[详见单节点拓扑](../infrastructure/single-node.md)）。

---

## 4. 从节点级到机架级：NVLink 域的扩展

NVLink 最初只存在于单节点内部。从 H100 起，NVLink Switch 的端口开始"走出节点"：

| 阶段 | 系统 | NVLink 域规模 | 实现方式 |
|------|------|-------------|---------|
| **节点内** (2018-) | DGX-2, A100, H100 | 8-16 GPU | NVLink Switch 芯片在服务器内 |
| **跨节点** (2022-) | DGX H100 SuperPOD | **256 GPU** | 节点内 NVLink Switch 的空闲端口 → OSFP 线缆 → 外部 NVLink Switch (1U 机架设备，双芯片 128 端口) |
| **机架级** (2024-) | GB200 NVL72 | **72 GPU (单机架)** | NVLink Switch 从服务器移到独立 switch tray，9 个 switch tray 全互连 72 GPU |

**GB200 NVL72 的架构变化**：NVLink Switch 不再装在服务器内，而是放在独立的机架级 switch tray 中。72 张 GPU 通过 NVLink 5.0 连接到 9 个 switch tray，形成一个 130 TB/s 聚合带宽的全互连域——整个机架表现得像一台巨大的单机[^nvidia-nvlink-page]。

**设计权衡**：NVLink 域越大，需要走传统网络（InfiniBand/Ethernet）的通信比例越小，集合通信效率越高。但 NVLink 域的扩展受限于 NVLink Switch 端口数和物理线缆距离（铜缆 ~2m，光缆可更远），成本也随域规模非线性增长。

---

## 参考资料

[^nvidia-nvlink-blog]: NVIDIA. *How NVLink Will Enable Faster, Easier Multi-GPU Computing*. https://developer.nvidia.com/blog/how-nvlink-will-enable-faster-easier-multi-gpu-computing/
[^hotchips-nvswitch]: Alexander Ishii, Ryan Wells. *The NVLink-Network Switch*. Hot Chips 34, 2022. https://hc34.hotchips.org/assets/program/conference/day2/Network%20and%20Switches/NVSwitch%20HotChips%202022%20r5.pdf
[^nvidia-nvlink-page]: NVIDIA. *NVLink & NVSwitch*. https://www.nvidia.com/en-gb/data-center/nvlink/
