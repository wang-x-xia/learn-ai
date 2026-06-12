---
title: "具身智能数据管线：领域特有问题与方案"
description: "具身智能数据管线相比通用闭环系统的特殊挑战——硬件碎片化、动作空间异构、采集即标注，以及 LeRobot、OpenPI、Octo、RT-2/OXE、Isaac Lab 等框架在各阶段的解法对比。"
created: "2026-06-12"
updated: "2026-06-12"
tags:
  - embodied
  - dataset
  - robotics
  - data-infrastructure
review: "2026-06-12"
---

# 具身智能数据管线：领域特有问题与方案

??? note "背景知识"
    - **ML 数据管线**：通用阶段模型、开环 vs 闭环的根本差异、双向变换一致性 → [详见](../infrastructure/data-pipeline.md)
    - **具身智能数据类型**：机器人学习的事实标准四元组——图像、本体感知、动作、语言指令 → [详见](embodied-data-types.md)
    - **数据归一化**：z-score / min-max / 分位数方案及 delta actions 陷阱 → [详见](embodied-normalization.md)
    - **OpenPI 三层 Transform**：RepackTransform → data_transforms → model_transforms 的分层数据管线 → [详见](openpi.md)
    - **LeRobot Dataset v3**：多 episode 聚合存储、关系型元数据索引 → [详见](lerobot-dataset-v3.md)

---

具身智能的数据管线是[闭环管线](../infrastructure/data-pipeline.md)的一种——前向把传感器信号变成模型张量，逆向把模型输出变回关节指令。具身管线的核心挑战是**碎片化**：数百种机器人硬件、无统一通信协议、动作空间维度和语义千差万别。

```
传感器  → ⓪采集  → ①Schema → ②坐标 → ③模态  → ④归一化 → ⑤时序 → ⑥表示 → ⑦Batch → 模型
原始数据    & 标注    映射     变换    预处理           窗口    转换    & 设备
执行器  ←          ←①逆映射←       ←③逆处理←④反归一化←      ←⑥逆转换←⑦Unbatch← 模型
```

本文聚焦各阶段中**具身领域特有**的问题和框架解法。通用的管线阶段定义和开环/闭环差异 → [详见 ML 数据管线](../infrastructure/data-pipeline.md)。

---

## ⓪ 数据获取 — 三条路径各有瓶颈

具身数据有三种主要获取方式，各自解决不同的规模-质量权衡：

| 方式 | 规模 | 数据质量 | 核心瓶颈 |
|------|------|----------|----------|
| **真机遥操作** | 低（每小时几十 episode） | 最高（真实物理） | 人力成本——采集过程本身就是标注（动作由编码器录制） |
| **仿真生成** | 极高（GPU 并行，百万级 episode/天） | 受 sim-to-real gap 限制 | 物理保真度——接触力学、视觉、传感器噪声的差距 |
| **互联网视频** | 海量 | 无动作标签 | 需额外推断动作——τ₀-World Model 用视频+机器人数据联合训练解决此问题 → [详见](tau-0-wm.md) |

### 真机遥操作：采集即标注

与 CV/NLP 的"先采集再标注"不同，遥操作时关节编码器实时录制的动作序列就是模仿学习的 ground truth——**采集过程本身就是标注**。任务语言指令由操作员填写，episode 边界由按键切分。

核心瓶颈是**采集贵**而非标注贵。应对策略：

- **联合采集**：Open X-Embodiment 22 个机构贡献 1M+ 轨迹[^google-2024-oxe]
- **降低硬件门槛**：LeRobot 支持 SO-100（~\$3K）等廉价臂[^lerobot-2026]

### 仿真生成：规模化的代价是 Sim-to-Real Gap

仿真是唯一能做到百万级 episode 的路径。GPU 并行仿真（Isaac Lab 单卡 4096+ 环境）让数据生成成本趋近于零，但仿真数据训练的策略能否迁移到真机取决于 sim-to-real gap 的控制。主要 gap 来源及应对 → [详见具身仿真文档](simulation.md)。

存储格式设计 → [详见 LeRobot Dataset v3](lerobot-dataset-v3.md)。

---

## ① Schema 映射 — 硬件碎片化的直接后果

机器人硬件高度碎片化——同一个腕部相机，在 ALOHA 叫 `observation.images.top`，在 DROID 叫 `exterior_image_1_left`，在 LIBERO 叫 `image`。没有统一的传感器命名标准，策略模型需要固定输入 key。

| 解法 | 代表 | 做法 | 权衡 |
|------|------|------|------|
| **Key 重映射 + 固定槽位** | OpenPI | RepackTransform 做 key 重命名 → `XXXInputs` 类组装成固定位置结构 → 模型按**位置**而非名称读取 | 最严格——错放相机会让预训练先验失效；但迁移效果最好 |
| **Tokenizer 屏蔽** | Octo | 每种模态独立 Tokenizer，缺失模态 zero-pad + attention mask | 最灵活——任意传感器组合均可；但浪费算力 |
| **标准格式入库前转** | RT-2/OXE | 入库前转成 RLDS 统一 Schema | 一次性成本——入库麻烦但训练零开销 |
| **不做统一** | ROS 2 / robomimic | 用户自行编写映射代码 | 灵活但不可复用 |

**OpenPI 的位置语义绑定**是最值得注意的设计：模型在预训练时将每个输入位置与固定语义绑定（第 0 槽 = 全局相机、第 1 槽 = 左腕相机……），权重烧入了这种映射。微调时放反相机位置 = 预训练先验完全失效 → [详见 OpenPI](openpi.md)。

---

## ② 坐标变换 — 纯学习框架普遍跳过

| 解法 | 代表 | 做法 |
|------|------|------|
| **全局变换树** | ROS 2 | `tf2` 维护实时坐标变换树。痛点：单个缺失变换中断整棵树 |
| **仿真器内置** | Isaac Lab / ManiSkill | 仿真器统一世界坐标系，观测函数直接输出目标坐标系下的值 |
| **跳过** | OpenPI / Octo / robomimic | 假定输入已在正确坐标系——职责推给数据采集环节 |

纯学习框架普遍将坐标系一致性视为**数据质量要求**而非管线职责——只有 ROS 2 因其中间件定位而系统性地处理坐标变换。

---

## ③ 模态预处理 — 缺失模态是跨机器人泛化的刚需

各模态的预处理本身不特殊（图像 resize、文本 tokenize……），但**缺失模态处理**是具身领域的独有需求——不同机器人的相机数量、有无力觉传感器各不相同：

| 解法 | 代表 | 做法 | 权衡 |
|------|------|------|------|
| **Zero-pad + attention mask** | Octo | block-wise masked attention 自动忽略 zero-pad 位置 | 灵活但浪费算力 |
| **image_mask 显式标记** | OpenPI | 缺失相机填零数组 + `image_mask=False` | 模型显式知道哪些输入是真实的 |
| **不支持** | robomimic、Isaac Lab | 假定所有传感器都在——换机器人就要改代码 | |

---

## ④ 归一化 — 具身领域的特殊陷阱

归一化方案本身（min-max / z-score / 分位数）不是具身特有的，但具身领域有两个独有陷阱：

**陷阱一：Delta actions 的归一化顺序**。先差分再归一化 vs 先归一化再差分，数学结果不同，物理含义完全不同 → [详见归一化文档](embodied-normalization.md)。

**陷阱二：跨机器人训练的量纲差异**。不同机器人的关节范围、末端工作空间完全不同——RT-2/OXE 的做法是 per-dataset 独立归一化后再混合训练。

| 方案 | 代表 | 权衡 |
|------|------|------|
| Min-Max → \[-1, 1\] | RT-2、robomimic | 兼容 tanh；对异常值极度敏感 |
| Gaussian (z-score) | Isaac Lab、Octo | 稍鲁棒但无界 |
| 分位数截断 | LeRobot | 对异常值最鲁棒 |
| Per-dataset 独立 | RT-2/OXE | 解决跨机器人量纲差异 |

---

## ⑤ 时序窗口 — Action Chunk 与实时控制的矛盾

策略模型输出 action chunk（多步动作序列）可提升时间一致性，但带来**延迟问题**——大模型单次推理 100-500ms，远超 30Hz 控制周期的 33ms 预算。

| 解法 | 代表 | 做法 |
|------|------|------|
| **Delta timestamps** | LeRobot | `[-0.2, -0.1, 0.0]` 配置历史窗口；episode 边界自动 padding |
| **固定窗口 + chunk** | Octo | 2 帧历史 + 4 步 action chunk |
| **大 chunk + ensembling** | ACT | 100 步 chunk，temporal ensembling 平滑重叠区 |
| **Per-term 环形缓冲** | Isaac Lab | 每个观测 term 独立 `history` 长度 |

**Real-Time Chunking (RTC)** 是 LeRobot 对延迟问题的工程解法：机器人执行 chunk N 时异步生成 chunk N+1，用 flow-matching guidance 保证重叠区连续性，实现 30+ Hz 控制频率（尽管单次推理需 100-500ms）[^lerobot-2026]。

---

## ⑥ 表示转换 — 具身管线最复杂、最易出错的阶段

具身的动作空间从 2-DoF 夹爪到 30+ DoF 人形全身，且同一任务可以用关节空间、末端空间、绝对/相对等完全不同的表示——变换类型多、有状态、前向逆向必须严格对称。

| 转换类型 | 做法 | 代表 |
|----------|------|------|
| 绝对 → 相对 (delta) | $a_t^{rel} = a_t^{abs} - s_t$ | LeRobot `RelativeActionsStep`、Octo、OpenPI |
| 关节 → 末端执行器 | FK / IK（基于 URDF） | LeRobot `RobotKinematics`、ManiSkill |
| 连续 → 离散 token | 256 bins 量化或 DCT + BPE | RT-2（256-bin）、Pi0-FAST（DCT + BPE） |
| 旋转表示转换 | axis-angle → 6D continuous | robomimic、τ₀-World Model |
| Zero-padding | 不足 action_dim 补零，推理截断 | OpenPI（默认 32 维） |

**行业趋势**：跨机器人泛化场景中 **delta EE（末端增量）** 已成主流——Octo、RT-2、OpenPI 都默认使用。原因：delta 动作有隐式安全边界，且跨机器人语义一致（"向右移 2cm"对任何臂含义相同）。

### 双向一致性的具身实现

双向变换一致性是所有闭环管线的通用难题（→ [详见通用分析](../infrastructure/data-pipeline.md)），具身领域的主要实现模式：

| 模式 | 代表 | 做法 |
|------|------|------|
| **可逆 Transform 栈** | OpenPI | output transforms 按 input transforms 的**逆序**自动应用；frozen dataclass 保证不可变 |
| **双管线显式分离** | LeRobot | `PolicyProcessorPipeline` 的 `forward()` / `inverse()` 路径，Step 声明 I/O 合约 |
| **不做显式保证** | robomimic、ROS 2 | 前向/逆向散落在不同代码路径 |

---

## ⑧ 噪声注入 — Sim-to-Real Gap 的管线层应对

仿真数据过于"干净"，策略迁移到真机后对传感器噪声不鲁棒：

| 解法 | 代表 | 做法 |
|------|------|------|
| **Per-term 噪声配置** | Isaac Lab | `ObservationManager` 每个 term 配置高斯/传感器噪声模型 |
| **Per-key 增强** | robomimic | crop、color jitter 等 randomizer 按 key 配置 |
| **域随机化** | Isaac Lab | 纹理、光照、物理参数随机化（仿真器层） |

大多数纯学习框架（OpenPI、Octo、LeRobot）不将噪声注入视为管线显式阶段。

---

## 关注点分离：硬件管线 vs 模型管线

管线阶段中有些是**硬件相关**的（标定、坐标变换），有些是**模型相关**的（归一化、tokenization）。两者是否分离，决定了换机器人时要改多少代码：

| 模式 | 代表 | 做法 | 换机器人代价 |
|------|------|------|:----------:|
| **显式双管线** | LeRobot | `RobotProcessorPipeline`（硬件，CPU）+ `PolicyProcessorPipeline`（模型，GPU） | 只换 Robot 管线 |
| **Manager 分层** | Isaac Lab | `ObservationManager`（环境侧）+ Agent normalizer（JIT 进模型） | 改环境配置 |
| **不分离** | robomimic / Octo / ROS 2 | 变换逻辑在 dataset class 或训练脚本里 | 多处改动 |

在具身领域这种分离是刚需——同一策略可能需要部署到关节数、相机配置完全不同的机器人上。

---

## 各框架覆盖阶段总览

| 阶段 | ROS 2 | Isaac Lab | OpenPI | robomimic | Octo | RT-2/OXE | LeRobot |
|------|:-----:|:---------:|:------:|:---------:|:----:|:--------:|:-------:|
| ⓪ 采集 & 标注 | 部分 | 仿真 | - | - | - | RLDS | 遥操作全栈 |
| ① Schema 映射 | - | - | Repack + Inputs | registry | config | RLDS 预转 | Step |
| ② 坐标变换 | tf2 | 仿真器内 | - | - | - | - | - |
| ③ 模态预处理 | 用户写 | modifiers | Layer ②③ | process_obs | tokenizer | 统一格式 | Step |
| ④ 归一化 | - | empirical | Layer ③ | per-key | gaussian | per-dataset | Step |
| ⑤ 时序窗口 | - | history buffer | - | - | 固定窗口 | - | delta_ts |
| ⑥ 表示转换 | - | Controller | Layer ②③ | rotation | delta EE | 256-bin | Step |
| ⑦ Batch/设备 | - | 向量化 | 隐式 | DataLoader | DataLoader | DataLoader | Step |
| ⑧ 噪声注入 | - | noise cfg | - | randomizer | - | - | - |

**没有任何框架把所有阶段都显式建模为独立可组合的步骤**。LeRobot 覆盖最广（⓪①③④⑤⑥⑦），但缺坐标变换和噪声注入。OpenPI 把 ①③④⑥ 压缩成 3 层但不可细粒度拆分。这反映了当前领域仍在探索最佳抽象粒度。

---

## 参考资料

[^google-2024-oxe]: Open X-Embodiment Collaboration. *Open X-Embodiment: Robotic Learning Datasets and RT-X Models*. 2024. https://arxiv.org/abs/2310.08864
[^lerobot-2026]: Cadène et al. *LeRobot: End-to-End Learning for Real-World Robotics in a Million Lines of Code*. ICLR 2026. https://github.com/huggingface/lerobot
