---
title: "具身智能数据类型：观测-动作四元组"
description: "机器人学习的事实标准数据结构——视觉观测、本体感知、动作序列、语言指令的通用模式与各框架差异。"
created: "2026-06-11"
updated: "2026-06-11"
tags:
  - embodied
  - robotics
  - dataset
  - vla
review: "2026-06-11"
---

# 具身智能数据类型：观测-动作四元组

??? note "背景知识"
    - **VLA（Vision-Language-Action）模型**：融合视觉、语言理解和动作生成的多模态模型，直接从图像和语言指令输出机器人控制信号
    - **Open X-Embodiment**：Google DeepMind 主导的大规模机器人数据集联盟，汇聚 1M+ 轨迹、22 种机器人形态、60+ 子数据集[^oxe-2023]
    - **RLDS**：Reinforcement Learning Datasets，Google 提出的强化学习数据集生态，Open X-Embodiment 的底层格式标准[^rlds-2021]
    - **LeRobot Dataset v3**：Hugging Face 的机器人数据格式，用 Parquet + MP4 替代 RLDS 的 TFRecord → [详见](lerobot-dataset-v3.md)

---

无论框架（RT-2、Octo、OpenVLA、OpenPI、Diffusion Policy）还是数据标准（RLDS、LeRobot、HDF5），机器人学习的训练样本都由同一组时序信号组成。各框架在细节上有差异，但核心四元组是稳定的[^oxe-2023][^rlds-2021]：

```
一条训练样本 = (视觉观测, 本体感知, 动作, 语言指令)
```

---

## 视觉观测（Images）

RGB 图像是模型理解场景的主要输入。不同框架使用的摄像头数量和分辨率不同，但摄像头角色是统一的：

| 角色 | 典型名称 | 安装位置 | 作用 |
|------|---------|---------|------|
| **第三人称视角** | base / top / head / exterior | 固定支架或头部 | 全局空间布局、物体位置 |
| **腕部摄像头** | wrist / gripper / eye-in-hand | 末端执行器 | 近景精确定位、抓取点对齐 |

### 各框架摄像头配置

| 框架 / 平台 | 摄像头数 | 配置 | 分辨率 |
|------------|---------|------|--------|
| RT-2 | 1 | 头部摄像头 | 320×320 |
| Octo | 2 | 主视角 + 腕部 | 256×256 / 128×128 |
| OpenVLA | 1 | 主视角 | 224×224 |
| ALOHA | 3 | 顶部 + 左腕 + 右腕 | 480×640 |
| CALVIN | 4 | 2 RGB + 2 深度 | 200×200 / 84×84 |
| OpenPI | 3（固定槽位） | 外部 + 左腕 + 右腕 | 任意，内部 resize 到 224×224 |

缺失的摄像头通常用零数组填充 + mask 标记为无效，模型跳过该输入。

深度图、点云、触觉图像等模态在部分框架中作为可选输入，但 RGB 是唯一普遍必需的视觉模态。

---

## 本体感知（Proprioceptive State）

机器人自身的低维状态向量，通常包含：

| 信号 | 典型维度 | 值域 | 说明 |
|------|---------|------|------|
| **关节角度**（qpos） | 6–7 per arm | 弧度（rad） | 各关节当前位置 |
| **关节速度**（qvel） | 6–7 per arm | rad/s | 可选，部分框架不使用 |
| **夹爪位置** | 1 per gripper | \[0, 1\]（开 → 闭） | 夹爪开合度 |
| **末端位姿**（EEF） | 6–7 | 米 + 弧度/四元数 | 笛卡尔空间位置和姿态 |

### 关节空间 vs 笛卡尔空间

这是最重要的表示选择之一：

| 表示 | 内容 | 维度（7-DoF 单臂） | 优势 | 劣势 |
|------|------|-------------------|------|------|
| **关节空间** | 各关节角度 | 7 | 无奇异性，直接控制 | 不直观 |
| **笛卡尔空间** | 末端 xyz + 旋转 + 夹爪 | 7 | 直观，任务空间泛化好 | 逆运动学奇异性 |

ALOHA / ACT 系列使用关节空间；RT-2 / OpenVLA / BridgeData 使用笛卡尔空间的末端位姿增量。**两种表示在数据层面都是一个 float32 向量，区别在于物理含义和数值分布**。

### 并非所有框架都使用本体感知

| 框架 | 是否使用 state | 说明 |
|------|--------------|------|
| RT-2 | 否 | 仅图像 + 语言 → 动作 |
| OpenVLA（base） | 否 | 同上 |
| Octo | 可选 | 微调时可加入 |
| ALOHA / ACT | 是 | 关节角度必需 |
| OpenPI | 是 | state 是核心输入之一 |
| Diffusion Policy | 是 | 通常需要 state 输入 |

---

## 动作（Actions）

模型的输出目标。训练时作为监督信号提供，推理时由模型预测。

### 动作表示

与 state 类似，动作也分关节空间和笛卡尔空间两种表示，且有绝对 / 增量之分：

| 表示 | 含义 | 典型用法 |
|------|------|---------|
| **绝对关节角度** | 目标关节位置 | ALOHA、ACT |
| **关节增量** | 相对当前位置的变化量 | 部分 MuJoCo 环境 |
| **EEF 绝对位姿** | 末端目标位置 + 姿态 | 部分工业臂 |
| **EEF 增量** | 相对当前末端位姿的 delta | RT-2、OpenVLA、BridgeData |

### Action Chunking

是否一次预测多步未来动作，是各框架差异最大的设计选择之一：

| 框架 | Action Horizon | 说明 |
|------|---------------|------|
| RT-2 | 1 | 单步预测 |
| OpenVLA | 1 | 单步预测 |
| Octo | 4 | 4 步 chunk |
| Diffusion Policy | 4–16 | 可配置 |
| ALOHA / ACT | 50 | 1 秒 @50Hz |
| OpenPI | 50（默认） | 可配置 |

Action chunking 的核心权衡：chunk 越大，时间一致性越好（减少抖动），但延迟越高、对长程任务的适应性越差。实际部署中常配合 temporal ensembling（多次预测取加权平均）来平滑输出。

### 夹爪动作

夹爪通常作为动作向量的最后一维，有两种编码方式：

| 编码 | 值域 | 说明 |
|------|------|------|
| **连续** | \[0, 1\]（开 → 闭） | ALOHA、OpenPI 等 |
| **二值** | {0, 1} 或 {-1, 1} | RT-2、OpenVLA 等（离散化后） |

---

## 语言指令（Language Instruction）

自然语言任务描述，用于告诉模型"做什么"。

| 框架 | 语言输入 | 替代方案 |
|------|---------|---------|
| RT-2 | 必需 | — |
| Octo | 可选 | 目标图像作为替代 |
| OpenVLA | 必需 | — |
| OpenPI | 必需 | — |
| ALOHA / ACT | 无 | 单任务训练，无需指令 |
| Diffusion Policy | 无 | 同上 |

典型示例：`"pick up the red cup"`、`"put the banana on the plate"`。Open X-Embodiment 中约 30% 的数据集有语言标注[^oxe-2023]，缺失语言标注的数据在训练时用空字符串或默认 prompt 填充。

---

## 数据组织：Episode 与 Step

所有框架都将数据按 **episode**（一次完整操作轨迹）组织，每个 episode 包含 T 个 **step**（时间步）：

```
Episode
├─ Step 0:  {images, state, action, language_instruction, is_first=True}
├─ Step 1:  {images, state, action, language_instruction}
├─ ...
└─ Step T:  {images, state, action, language_instruction, is_last=True}
```

RLDS 格式显式定义了 `is_first` / `is_last` / `is_terminal` 标志位[^rlds-2021]。LeRobot v3 通过 episode 元数据中的起止索引隐式表达边界。

### 控制频率

| 平台 | 频率 | 说明 |
|------|------|------|
| RT-2 / RT-X | 3 Hz | 低频，每步推理时间充裕 |
| BridgeData WidowX | 5 Hz | |
| DROID Franka | 15–20 Hz | |
| ALOHA | 50 Hz | 高频，需要 action chunk 保证实时性 |

频率影响 action chunk 的时间跨度：50 步 @50Hz = 1 秒，50 步 @5Hz = 10 秒，同一模型在不同频率下的 chunk 含义完全不同。

---

## 归一化

state 和 actions 的数值范围因机器人而异（关节角度 ±π rad，末端位置 0–1 m，夹爪 0–1），训练前需要归一化到统一尺度。详细的归一化方案对比、公式、各框架选择及 delta actions 陷阱 → [详见](embodied-normalization.md)。

---

## 各框架的数据格式选择

底层存储格式各异，但语义结构（四元组 + episode 组织）是一致的：

| 格式 | 代表框架 | 视频存储 | 表格存储 | 生态 |
|------|---------|---------|---------|------|
| **RLDS** (TFRecord) | RT-2、Octo、OpenVLA、Open X-Embodiment | 逐帧 PNG/JPEG | Protocol Buffers | TensorFlow |
| **LeRobot v3** (Parquet + MP4) | OpenPI、LeRobot 生态 | H.264/AV1 视频 | Apache Parquet | HuggingFace / PyTorch |
| **HDF5** | ALOHA、robomimic、ACT | 逐帧数组 | HDF5 datasets | 通用 |
| **Zarr** | Diffusion Policy | 逐帧数组 | Zarr chunks | 通用 |

格式之间可互转：RLDS ↔ LeRobot 有官方转换工具，HDF5 → RLDS / LeRobot 也有社区脚本。选择取决于训练框架生态，不影响数据语义。

---

## 参考资料

[^oxe-2023]: Open X-Embodiment Collaboration. *Open X-Embodiment: Robotic Learning Datasets and RT-X Models*. 2023. https://arxiv.org/abs/2310.08864
[^rlds-2021]: Ramos et al. *RLDS: an Ecosystem to Generate, Share and Use Datasets in Reinforcement Learning*. 2021. https://arxiv.org/abs/2111.02767
