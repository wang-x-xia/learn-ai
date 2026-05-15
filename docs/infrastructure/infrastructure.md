---
title: AI 基础设施 (AI Infrastructure)
description: 从硬件加速器到网络协议，AI 基础设施决定了大模型能否高效训练和部署。本文档梳理当前 AI 基础设施的核心技术栈。
created: 2026-04-07
updated: 2026-05-11
tags:
  - infrastructure
  - gpu
  - network
  - nvlink
  - infiniband
  - roce
  - nvme-of
review: 2026-05-15
---

# AI 基础设施 (AI Infrastructure)

??? note "背景知识"
    - **GPU (Graphics Processing Unit)**：图形处理器，通过大规模并行计算单元加速 AI 训练和推理
    - **带宽 (Bandwidth)**：单位时间内数据传输量，决定训练/推理的数据吞吐能力
    - **延迟 (Latency)**：数据从源到目的的传输时间，影响实时性要求高的任务
    - **RDMA (Remote Direct Memory Access)**：远程直接内存访问，绕过 CPU 实现零拷贝网络传输
    - **PCIe (Peripheral Component Interconnect Express)**：计算机扩展总线标准，用于连接 GPU、网卡等设备

> 从硬件加速器到网络协议，AI 基础设施决定了大模型能否高效训练和部署。本文档梳理当前 AI 基础设施的核心技术栈。

---

## 1. 概述

### AI 基础设施网络分层

```
1. 节点内通信 (Intra-node)
   └── GPU 间互联技术
       ├── 互联协议：NVLink / HCCS / Infinity Fabric
       ├── 交换芯片：NVSwitch (NVIDIA) / 无交换芯片 (华为)
       ├── 带宽范围：300-900 GB/s
       ├── 拓扑：全互连 (Full-Mesh) 或 点对点
       └── 代表产品：NVLink 4.0、HCCS v2

2. 超节点互联 (Supernode)
   └── 跨节点高速互联
       ├── 互联技术：UB 灵衡 / NVLink-Network
       ├── 交换层级：L1/L2 两级交换 / 外部 NVLink Switch
       ├── 延迟：150-200 ns（接近节点内）
       ├── 规模：256-384 GPU/NPU
       └── 特性：跨节点统一内存域、单跳低延迟

3. 节点间计算通信 (Inter-node compute)
   └── 高速网络 fabric
       ├── 网卡 (NIC)
       │   ├── 协议：InfiniBand / RoCE v2 / Ethernet
       │   ├── 带宽：200-400 Gb/s
       │   ├── 接口：PCIe Gen5
       │   ├── 特性：RDMA、零拷贝、in-network computing
       │   └── 代表产品：ConnectX-7、内置 RoCE 网卡
       ├── 交换机
       │   ├── 端口：32-64 端口
       │   ├── 聚合带宽：25-51 Tb/s
       │   ├── 拓扑支持：Fat-Tree、Dragonfly、Torus
       │   └── 代表产品：Quantum QM9700、CloudEngine 系列
       └── 网络拓扑：Rail-optimized Fat-Tree

4. 存储网络 (Storage)
   └── 存储访问网络
       ├── 协议：InfiniBand / RoCE v2 / Ethernet / NVMe-oF
       ├── 网卡：同计算网络或专用存储网卡
       ├── 交换机：同计算网络或专用存储交换机
       ├── GPU 直接访问：GPUDirect Storage (绕过 CPU bounce buffer)
       └── 连接：高性能存储系统、并行文件系统
```

**工程权衡**：计算网络和存储网络可以复用同一套 fabric 以降低成本，通过 QoS 隔离流量。分开部署能提供更好的性能隔离，但成本更高。

---

## 2. 硬件加速组件

### 2.1 节点内通信技术对比

GPU/NPU 间互联技术决定了单节点内多卡协同训练的效率。

| 技术 | 厂商 | 带宽 | 拓扑 | 交换芯片 | 代表产品 |
|------|------|------|------|----------|----------|
| **NVLink 4.0** | NVIDIA | 900 GB/s | 全互连 | NVSwitch 3.0 | H100/H200 |
| **HCCS v2** | 华为 | 392 GB/s | Full-Mesh | 无 | 昇腾 910B |
| **Infinity Fabric** | AMD | - | - | - | MI300X |

**关键差异**：
- **NVLink + NVSwitch**：非阻塞交换芯片，任意 GPU 间 900 GB/s 直连，适合大模型张量并行[^nvidia-nvlink]
- **HCCS**：点对点互联，无交换芯片，总带宽 392 GB/s，依赖软件优化弥补硬件差距[^huawei-hccs]

### 2.2 超节点互联技术

| 技术 | 厂商 | 规模 | 延迟 | 交换层级 | 代表产品 |
|------|------|------|------|----------|----------|
| **UB 灵衡** | 华为 | 384 NPU | 150-200 ns | L1/L2 两级交换 | CloudMatrix 384 |
| **NVLink-Network** | NVIDIA | 256 GPU | - | 外部 NVLink Switch | - |

**UB 灵衡**：华为超节点技术，通过两级交换实现 384 NPU 跨节点统一内存域，单跳时延 150-200 ns。

### 2.3 节点间网卡对比

网卡负责节点间的高速数据传输，协议选择影响集群扩展性和成本。

| 协议 | 带宽 | 延迟 | 成本 | 生态 | 代表产品 |
|------|------|------|------|------|----------|
| **InfiniBand NDR** | 400 Gb/s | 极低 | 高 | 专有生态 | ConnectX-7 |
| **RoCE v2** | 200-400 Gb/s | 低 | 中 | 以太网生态 | 内置 RoCE 网卡 |
| **Ethernet** | 100-400 Gb/s | 中 | 低 | 通用生态 | 标准以太网网卡 |

**关键差异**：
- **InfiniBand**：专为 HPC/AI 设计，最低延迟，支持 in-network computing（SHARP），但成本高，生态封闭
- **RoCE v2**：基于以太网的 RDMA，平衡性能和成本，支持 NVMe-oF over RDMA 实现低延迟存储访问，华为昇腾内置网卡，NVIDIA 需外接 ConnectX
- **Ethernet**：通用性强，成本最低，支持 NVMe-oF over TCP，适合现有以太网基础设施，但延迟较高

### 2.4 交换机对比

交换机构建集群网络拓扑，端口密度和聚合带宽决定集群规模上限。

| 类型 | 端口 | 聚合带宽 | 拓扑支持 | 成本 | 代表产品 |
|------|------|----------|----------|------|----------|
| **InfiniBand 交换机** | 64×400G | 51.2 Tb/s | Fat-Tree, Dragonfly | 高 | Quantum QM9700 |
| **以太网交换机** | 64×400G | 25.6 Tb/s | Spine-Leaf, Clos | 中 | CloudEngine, Spectrum-4 |
| **智能网卡 (SmartNIC)** | - | - | - | 高 | BlueField-3 DPU |

**关键差异**：
- **InfiniBand 交换机**：专为 AI/HPC 优化，支持自适应路由、SHARP in-network computing，但成本高
- **以太网交换机**：通用性强，生态成熟，RoCE v2 可达到接近 InfiniBand 的性能，成本更低
- **智能网卡**：卸载网络、存储、安全功能，释放 CPU 资源，适合超大规模集群

### 2.5 计算芯片对比

计算芯片是 AI 基础设施的核心，算力、显存、互联带宽共同决定训练/推理性能。

| 芯片 | 厂商 | 架构 | 显存 | 显存带宽 | FP16 算力 | 互联 |
|------|------|------|------|----------|-----------|------|
| **H100 SXM** | NVIDIA | Hopper | 80GB HBM3 | 3.35 TB/s | 989 TFLOPS | NVLink 4.0 |
| **H200** | NVIDIA | Hopper | 141GB HBM3e | 4.8 TB/s | 989 TFLOPS | NVLink 4.0 |
| **B200** | NVIDIA | Blackwell | 192GB HBM3e | 8 TB/s | ~2250 TFLOPS | NVLink 5.0 |
| **昇腾 910B** | 华为 | Da Vinci | 64GB HBM2e | ~1.2 TB/s | ~600 TFLOPS | HCCS v2 |
| **MI300X** | AMD | CDNA 3 | 192GB HBM3 | 5.3 TB/s | ~1300 TFLOPS | Infinity Fabric |

**关键洞察**：显存带宽是 LLM 推理的主要瓶颈（内存带宽受限 / memory-bound），而非计算能力。

### 2.6 NVMe over Fabrics (NVMe-oF)

NVMe-oF 将 NVMe 存储协议扩展到网络，实现远程存储访问。它定义了如何通过网络访问 NVMe 设备，支持多种传输层。

#### NVMe-oF 与传输层的关系

NVMe-oF 是协议框架，NVMe over TCP/RDMA/FC 是具体传输实现：

```
NVMe-oF (框架/总称)
├── NVMe over RDMA  (一种实现)
├── NVMe over TCP   (一种实现)
└── NVMe over FC    (一种实现)
```

**类比**：NVMe-oF 是"汽车"，NVMe over TCP/RDMA/FC 是"燃油车/电动车/氢能车"。

#### 传输层选择

**传输层对比**（详见 2.3 节网卡对比）：
- **NVMe over RDMA**：最低延迟（微秒级），适合 AI 训练，需 RDMA 网卡
- **NVMe over TCP**：兼容性好，适合现有以太网，延迟略高，可通过 SmartNIC/DPU 卸载 TCP 协议栈降低延迟
- **NVMe over FC**：传统企业存储，与 FC SAN 兼容

#### NVMe-oF 核心功能

- **远程存储访问**：通过网络访问远程 NVMe 设备，像访问本地存储一样
- **队列管理**：保留 NVMe 原生队列机制（Admin Queue + I/O Queue），无需协议转换
- **发现机制**：Discovery Service 自动发现网络上的 NVMe 目标
- **认证与安全**：DH-HMAC-CHAP 双向认证、TLS 加密（TCP 传输层）
- **连接管理**：支持多路径、多连接提高吞吐和可靠性
- **传输层抽象**：传输层对上层透明，应用层无需关心

#### 与本地 NVMe 的对比

| 功能 | 本地 NVMe | NVMe-oF |
|------|-----------|---------|
| 队列机制 | ✅ 相同 | ✅ 相同 |
| 命令集 | ✅ 相同 | ✅ 相同 |
| 传输方式 | PCIe | 网络（RDMA/TCP/FC） |
| 发现 | PCIe 枚举 | Discovery Service |
| 认证 | 无 | ✅ DH-HMAC-CHAP |

**关键设计**：NVMe-oF 尽量保留本地 NVMe 的语义，只是把 PCIe 传输换成网络传输，应用层代码基本无需改动。

### 2.7 存储访问技术

传统存储访问路径需要经过 CPU 内存（bounce buffer），成为 I/O 瓶颈。GPUDirect Storage 提供存储到 GPU 的直接数据路径。

| 技术 | 厂商 | 带宽 | 路径 | 特性 |
|------|------|------|------|------|
| **GPUDirect Storage** | NVIDIA | 可叠加（多设备） | 存储 → GPU | 绕过 CPU bounce buffer |
| **传统方式** | - | 受限于 PCIe | 存储 → CPU → GPU | 需要 CPU 参与 |

**GPUDirect Storage 优势**：
- **直接路径**：存储设备（NVMe/NVMe-oF）的 DMA 引擎直接访问 GPU 内存
- **绕过 CPU**：避免数据在 CPU 内存中缓存，降低 CPU 开销
- **带宽叠加**：多个存储设备可同时传输，理论带宽可达 200 GB/s（DGX-2）
- **支持远程存储**：通过 NVMe-oF 访问网络存储

**适用场景**：
- 大规模数据加载（训练数据集）
- 高吞吐 I/O 工作负载
- 需要降低 CPU 占用的场景

---

## 3. 发展趋势

### 3.1 定制芯片竞赛

- NVIDIA 持续主导 (H100→B100→B200)
- AMD 追赶 (MI300X→MI350)
- Google TPU 在自家生态中深耕
- 创业公司 (Groq, Cerebras) 找差异化路线
- 大厂自研芯片 (Amazon Trainium, Microsoft Maia)

### 3.2 边缘 AI / 端侧推理

- Apple Intelligence (M 系列芯片 + 小模型)
- Google Gemini Nano (手机端运行)
- Qualcomm AI Engine
- 小模型+量化 = 手机/笔记本上运行 LLM
- Google LiteRT-LM: C++ 运行时，专为边缘设备 LLM 推理设计（2026.4 GitHub Trending，501 stars/day）

### 3.3 能效与可持续性

- LLM 训练的碳排放问题
- 更高效的硬件和算法
- 绿色数据中心
- 推理优化减少能耗

### 3.4 AI 基础设施民主化

- 更便宜的 GPU 云服务
- 开源推理框架降低门槛
- 模型量化让消费级硬件可用

---

## 参考资料

[^nvidia-nvlink]: NVIDIA. NVLink and NVSwitch 技术文档
[^huawei-hccs]: 华为. HCCS 互联技术文档
