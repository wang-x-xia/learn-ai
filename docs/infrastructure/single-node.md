---
title: AI 服务器单节点拓扑
description: 单机 8 卡 AI 服务器的硬件结构——NVLink Switch 全互连、PCIe 桥接、Rail-aligned 网络模块。以 NVIDIA DGX/HGX 产品序列为参考。
created: 2026-06-01
updated: 2026-06-01
tags:
  - infrastructure
  - gpu
  - nvlink
  - nvswitch
  - pcie
review: 2026-06-01
---

# AI 服务器单节点拓扑

??? note "背景知识"
    - **NVLink / NVLink Switch**：NVIDIA GPU 间高速互联协议与交换芯片，提供非阻塞全互连 → [详见](../hardware/nvlink.md)
    - **PCIe (Peripheral Component Interconnect Express)**：计算机扩展总线标准，连接 CPU、GPU、网卡等设备
    - **ConnectX**：NVIDIA ASIC SmartNIC 产品线，提供 RDMA 和网络卸载 → [详见](../hardware/nvidia-connectx.md)
    - **Rail-aligned 拓扑**：每个 GPU 索引映射到独立网络平面，减少交换机层拥塞 → [详见](infrastructure.md)

> 以 NVIDIA DGX/HGX 产品序列为参考[^nvidia-dgx-h100]，梳理单节点内 CPU、GPU、网络的连接方式与设计权衡。下文以 Hopper 一代参数为基准，Blackwell 的变化见第 4 节。

---

## 1. 三条数据通路

节点内存在三条带宽差异巨大的数据通路，这直接决定了分布式训练的通信策略：

| 通路 | 带宽 | 倍数 | 用途 |
|------|------|------|------|
| **GPU↔GPU (NVLink+NVLink Switch)** | 900 GB/s 双向/对 | 1x | 张量并行、梯度同步 |
| **GPU↔CPU (PCIe Gen5 x16)** | ~64 GB/s 双向 | ~1/14 | 数据加载、控制面 |
| **GPU↔网络 (PCIe→ConnectX)** | ~50 GB/s (400 Gb/s) | ~1/18 | 节点间通信 |

**关键设计决策**：NVLink 比 PCIe 快 **~14 倍**，这意味着节点内 GPU 间通信必须走 NVLink Switch 全互连，绝不经过 PCIe/CPU 中转。NCCL 等通信库会自动感知这一拓扑，优先使用 NVLink 路径。

### GPU 全互连拓扑

8 张 GPU 通过多颗 NVLink Switch 实现**非阻塞全互连**——任意两张 GPU 之间都有等带宽直连，无需多跳。设计遵循两条原则：

1. **每颗 NVLink Switch 连接所有 GPU**：GPU 间通信在 NVLink Switch 内部经 crossbar 一跳完成，所有 GPU 对的带宽完全对称。
2. **尽可能多的 NVLink Switch，用满 GPU 的 NVLink 端口**：GPU 的 NVLink 端口均匀分配到多颗 NVLink Switch 上，任意 GPU 对的通信同时经过所有 NVLink Switch 并行传输，聚合带宽随 NVLink Switch 数量线性增长。NVLink Switch 上未被 GPU 占用的剩余端口可用于 NVLink Network 跨节点互联。

两条原则的结果就是"非阻塞"——不管哪些 GPU 对在同时通信，都不会互相抢占带宽（[NVLink Switch 架构详见](../hardware/nvlink.md)）。

---

## 2. 网络模块与 Rail-aligned 设计

Hopper 一代的网络模块设计解决了一个工程难题：如何在有限的 PCIe 通道下让每张 GPU 都有独立的高速网络出口。

### 网络模块封装

- 8 张 ConnectX-7 单口卡封装到 **2 个网络模块**（每模块 4 张）
- 网络模块安装在 interposer board 上，一端连 CPU 的 PCIe 根端口，另一端连 GPU 托盘
- **DensiLink 线缆**从 ConnectX-7 直连到机箱背面的 **4 个 OSFP 接口**（每 OSFP 出 2 个端口）

### 每 GPU 一张网卡 (Rail Alignment)

**为什么要 1:1 映射？** 集群中所有节点的 GPU 0 连到同一条 Rail（同一组 Leaf Switch），GPU 1 连到另一条 Rail……这样 AllReduce 等集合通信的流量天然分散到 8 个独立网络平面，避免交换机层拥塞。

---

## 3. 四种网络 Fabric

单节点对外有四种不同用途的网络连接，物理隔离不同类型的流量：

| Fabric | 网卡 | 速率 | 用途 |
|--------|------|------|------|
| **Compute** | 8x ConnectX-7 单口 | 400G IB/Eth | GPU 间跨节点通信（NCCL） |
| **Storage** | 2x ConnectX-7 双口 | 400G Eth/IB | 数据集加载、checkpoint |
| **In-band Mgmt** | 同 Storage 复用 | — | 节点监控、编排调度 |
| **Out-of-band** | 1x 1GbE BMC (RJ45) | 1G | 硬件管理 (IPMI/Redfish) |

**设计权衡**：计算 fabric 和存储 fabric 物理分离确保训练通信不会被数据加载抢占带宽。小规模部署可以复用同一 fabric 通过 QoS 隔离，但大规模集群（如 DGX SuperPOD）始终分开部署。

---

## 4. 演进：Hopper → Blackwell

| 指标 | Hopper | Blackwell |
|------|--------|-----------|
| GPU-GPU 带宽 | 900 GB/s | **1800 GB/s** (2x) |
| NVLink 聚合带宽 | 4.8 TB/s | **14.4 TB/s** (3x) |
| NVLink Switch | 4x 第四代 | 4x **第五代** |
| 计算网卡 | 8x ConnectX-7 (400G) | 8x **ConnectX-8 SuperNIC (800G)** |
| 基础设施卸载 | 无 | **BlueField-3 DPU** |

Blackwell 的关键架构变化：计算网卡从 ConnectX-7 升级为 ConnectX-8 SuperNIC（[详见](../hardware/nvidia-connectx.md)），并新增 BlueField-3 DPU（[详见](../hardware/nvidia-bf.md)）负责基础设施卸载。

---

## 参考资料

[^nvidia-dgx-h100]: NVIDIA. *DGX H100/H200 User Guide*. https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html
