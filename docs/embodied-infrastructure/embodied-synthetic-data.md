---
title: "具身智能合成数据"
description: "机器人操作数据的三类合成方法——仿真扩增、Human-to-Robot 视频合成、LLM 驱动生成式仿真，以及各方案的核心权衡。"
created: "2026-06-24"
updated: "2026-06-24"
tags:
  - embodied
  - robotics
  - synthetic-data
  - data-augmentation
review: "2026-06-24"
---

# 具身智能合成数据

??? note "背景知识"
    - **具身智能数据类型**：机器人学习的通用四元组（图像、本体感知、动作、语言指令） → [详见](embodied-data-types.md)
    - **MANO**：参数化 3D 人手模型（778 顶点），用形状参数 β（10 维）和姿态参数 θ（45 维）表示任意手部的形状和关节弯曲
    - **逆运动学（IK）**：给定末端执行器目标位姿，求解满足约束的关节角度序列
    - **具身仿真**：GPU 并行仿真 vs CPU 高保真的技术权衡，Sim-to-Real Gap 跨越策略 → [详见](simulation.md)

---

## 为什么需要合成数据

机器人操作数据稀缺且昂贵——即便最大的开源数据集（Open X-Embodiment）也仅约 1 万小时，远不及语言/视觉领域的数据规模。合成数据是弥合这个规模差距的核心手段，目前有三条主要技术路线：

| 路线 | 数据来源 | 核心思路 | 代表 |
|------|---------|---------|------|
| **仿真扩增** | 少量机器人演示 | 分解演示→变换物体位姿/场景→重组 | MimicGen、RoboCasa |
| **Human-to-Robot** | 人类视频 | 手部估计→重定向→去手修复→渲染合成 | H2R、Masquerade、Qwen-RobotManip |
| **LLM 驱动生成** | LLM 自动生成 | LLM 提议任务→生成场景→求解轨迹 | RoboGen、GenSim2 |

---

## 路线一：仿真扩增——从少量演示到大规模数据集

不涉及跨域迁移，而是在仿真器内部将少量真实演示扩增为大规模数据集。

### MimicGen：物体中心的演示重组

MimicGen 的核心思路是将演示分解为**物体中心的操作片段**，然后根据新场景中物体的位姿变化重新拼接[^mimicgen-2023]：

1. 收集少量人类遥操演示（如 200 条）
2. 将每条演示分解为一系列「接近物体 → 操作物体 → 移动到目标」片段
3. 对新场景（物体位置/姿态不同），将每个片段根据当前物体位姿做坐标变换，拼接成新轨迹
4. 机器人执行新轨迹并记录数据

200 条演示 → 50K+ 条合成演示，覆盖 18 个任务。关键限制：依赖仿真器的特权信息（物体位姿 ground truth），且变换仅限于同一类任务内的空间变化——无法生成全新任务。

### RoboCasa：程序化场景 + MimicGen 扩增

RoboCasa 在 MimicGen 基础上叠加了**程序化场景生成**：2,500+ 厨房场景、3,200+ 3D 物体、365 个任务，最新版本（RoboCasa365）积累 2,200+ 小时机器人数据。场景多样性由 AI 生成的 3D 资产和程序化布局提供，任务定义由 LLM 辅助生成[^robocasa-2024]。

仿真扩增的核心权衡：**场景多样性高、动作标注精确**（物理引擎直接产出），但受限于 Sim-to-Real Gap——视觉外观、接触力学、物体物理属性与真实世界始终有差异。

---

## 路线二：Human-to-Robot 视频合成

从第一人称人类操作视频（Ego4D、Epic-Kitchens 等）出发，将人类演示“翻译”成机器人演示。核心挑战在于域差距——人手和机器人在外观、运动学、控制方式上完全不同。

### 通用管线：五个阶段

2025 年起，多个独立团队收敛到了一条几乎相同的管线架构[^h2r-2025][^masquerade-2025]：

```mermaid
flowchart LR
    A["第一人称<br/>人类视频"] --> B["① 手部估计<br/>（MANO）"]
    B --> C["② 运动重定向<br/>（手→夹爪/灵巧手）"]
    C --> D["③ 去手修复<br/>（分割+修复）"]
    D --> E["④ 机器人放置<br/>（IK 可达性搜索）"]
    E --> F["⑤ 渲染合成<br/>（深度引导）"]
    F --> G["多形态<br/>机器人演示"]
```

### ① 手部估计

从每帧 RGB 图像回归 MANO 参数，得到腕部 6D 位姿和手指关节角。常用估计器：HaMeR、FrankMocap。精度瓶颈在单目深度估计——绝对 z 距离误差较大，但帧间相对运动通常可用。

### ② 运动重定向

将人手姿态映射到目标末端执行器：

- **腕部 → EEF 位姿**：人手腕部 6D 位姿直接对应机器人末端执行器的目标位姿，需要一个固定的旋转偏移（人手"正面"和夹爪"正面"朝向不同），可能需要空间缩放
- **手指 → 夹爪开合**：拇指-食指指尖距离线性映射到 `[0, 1]`
- **手指 → 灵巧手关节**：维度更接近时可直接映射关节角，但需手动标定对应关系

Qwen-RobotManip 的具体实现用虚拟指尖 $k_{vf} = 0.7 k_{index} + 0.3 k_{middle}$ 加权，再由拇指和虚拟指尖计算 EEF 位置和朝向，Savitzky-Golay 滤波平滑轨迹[^qwen-2026-robotmanip]。

每种末端执行器类型（平行夹爪 / 灵巧手 / 吸盘）需要各自的重定向器。支持 N 种形态就需要 N 套规则。

### ③ 去手修复

最终图像里应该只有机器人，不能同时出现人手（否则模型学到虚假相关）。两步走：

1. **实例分割**：用 SAM（Segment Anything Model）对每帧做手部分割，得到精确 mask。手部 mask 需略微膨胀（dilate 几像素），否则边缘残留肤色
2. **视频修复**：用 ProPainter（Qwen-RobotManip）或 E2FGVI（Mitty）等视频修复模型填充 mask 区域。视频修复优于单帧修复——手移动时被遮挡的桌面/物体在其他帧中可见，时序信息提供更好的纹理来源

**已知瓶颈**：手与物体接触时（正在抓东西），修复质量下降——被手遮挡的物体表面在相邻帧中也不可见。

### ④ 机器人放置（IK 可达性搜索）

将虚拟机器人"放"在场景中合理的位置：

1. 将 EEF 轨迹转换到世界坐标系（需相机外参或单目深度估计）
2. 在仿真器（MuJoCo / Isaac Sim）中加载机器人模型
3. 遍历候选基座位置（桌面边缘离散网格），对每个位置检查：所有 EEF 目标可达？关节角在限位内？有无自碰撞？
4. 选可达率最高、关节角变化最平滑的基座位姿

Qwen-RobotManip 用目标函数 $T_{base}^* = \arg\max_{T_{base}} \frac{1}{|K|} \sum_{k} \mathbf{1}_{[\text{IK}(T_{base}^{-1} T_{ee,k}) \text{ feasible}]}$ 做网格搜索[^qwen-2026-robotmanip]。不同机器人工作空间差异大，部分人类操作轨迹对某些形态不可达——这些 case 丢弃。

**计算优化**：先用工作空间包络快速过滤不可达候选，再对剩余做精确 IK。

### ⑤ 渲染合成

**前置准备**：对去手修复后的背景帧用单目深度估计（如 Depth Anything）生成场景深度图。

按 IK 解出的关节角序列在仿真器中逐帧渲染机器人（仿真器同时产出机器人深度图）。合成时逐像素比较两张深度图：机器人比场景近的部分显示机器人，否则显示背景——这样机器人被桌面、物体等遮挡的部分就不会穿帮。

输出的动作标注：state 来自 IK 解的关节角序列，action 来自相邻帧 EEF 位姿差值（delta pose），语言指令从原始视频标注迁移或用 VLM 自动生成。

### H2R 内部的两条子路线

上述五阶段管线属于**几何渲染路线**。2025 年下半年起出现了**扩散生成路线**，用视频扩散模型直接做人→机器人的视频翻译：

| 维度 | 几何渲染路线 | 扩散生成路线 |
|------|------------|------------|
| **代表** | H2R、Masquerade、Qwen-RobotManip | H2R-Grounder、Mitty、MimicDreamer |
| **合成方式** | 仿真渲染 + 深度合成 | 视频扩散模型生成 |
| **视觉质量** | 受限于渲染器（硬阴影、简单材质） | 接近真实（扩散先验） |
| **动作标注** | 直接产出（IK 解） | 需额外步骤提取 |
| **计算成本** | 低（CPU 即可） | 高（需 GPU 推理） |
| **可控性** | 高（精确控制机器人位姿） | 低（扩散模型可能产生物理不合理的姿态） |
| **规模化** | 容易（已验证 25K+ h） | 尚未大规模验证 |

---

## 路线三：LLM 驱动的生成式仿真

用 LLM 自动化整个数据生成流程——从任务提议到场景生成到轨迹求解：

- **RoboGen**[^robogen-2024]：LLM 提议任务 → 生成仿真场景（放置资产、配置空间关系）→ 分解为子任务 → 自动选择学习方法（RL / 运动规划 / 轨迹优化）→ 生成训练监督信号。全自动循环可无限重复。
- **GenSim2**[^gensim2-2025]：用多模态 + 推理 LLM 生成包含铰接物体的复杂任务，规划器和 RL 求解器在物体类别内泛化。可生成 100 个铰接任务 × 200 个物体，合成数据用于零样本 sim-to-real 迁移或与真实数据共训（+20%）。

这条路线的优势是**任务多样性理论上无限**（LLM 可以不断提出新任务），但生成的任务质量和物理合理性难以保证，且依赖精心设计的 prompt 工程。

---

## 全景对比

| 方法 | 路线 | 数据来源 | 合成方式 | 规模 | 核心权衡 |
|------|------|---------|---------|------|------|
| **MimicGen**[^mimicgen-2023] | 仿真扩增 | 少量机器人演示 | 物体位姿变换+重组 | 50K episodes | 标注精确，但受限于同任务空间变化 |
| **RoboCasa**[^robocasa-2024] | 仿真扩增 | 程序化场景+遥操 | MimicGen + 域随机化 | 2,200+ h | 场景多样性高，但 Sim-to-Real Gap |
| **Masquerade**[^masquerade-2025] | H2R | 人类视频 | 几何渲染 | EPIC-Kitchens | 轻量管线，仅用于视觉预训练 |
| **H2R**[^h2r-2025] | H2R | 人类视频 | 几何渲染 | Ego4D+SSv2 | 有 CLIP 质量评估，仅用于编码器预训练 |
| **H2R-Grounder** | H2R | 人类视频 | Wan 2.2 扩散 | — | 视觉质量高，但无动作标注 |
| **Mitty** | H2R | 人类视频 | DiT 扩散 | EPIC-Kitchens | 端到端，无中间表示损失 |
| **MimicDreamer** | H2R | 人类视频 | 扩散+IK | 人类演示 | 视觉+视角+动作三维对齐 |
| **Qwen-RobotManip**[^qwen-2026-robotmanip] | H2R | 人类视频 | 几何渲染+深度 | **25K h × 15 形态** | 规模最大，与对齐框架深度耦合 |
| **RoboGen**[^robogen-2024] | LLM 生成 | LLM 自动生成 | RL/规划/优化 | 无限循环 | 任务多样性无限，但质量难控 |
| **GenSim2**[^gensim2-2025] | LLM 生成 | LLM 自动生成 | 规划+RL | 100 任务×200 物体 | 支持铰接物体，已验证 sim-to-real |

---

## 参考资料

[^mimicgen-2023]: Mandlekar et al. *MimicGen: A Data Generation System for Scalable Robot Learning using Human Demonstrations*. CoRL 2023. https://mimicgen.github.io
[^robocasa-2024]: Nasiriany et al. *RoboCasa: Large-Scale Simulation of Everyday Tasks for Generalist Robots*. RSS 2024. https://robocasa.ai
[^h2r-2025]: Chen et al. *H2R: A Human-to-Robot Data Augmentation for Robot Pre-training from Videos*. 2025. https://arxiv.org/abs/2505.11920
[^masquerade-2025]: Lepert et al. *Masquerade: Simple and Lightweight Image Augmentation for Vision-Language-Action Models via Robot Rendering*. 2025.
[^robogen-2024]: Wang et al. *RoboGen: Towards Unleashing Infinite Data for Automated Robot Learning via Generative Simulation*. ICML 2024.
[^gensim2-2025]: Hua et al. *GenSim2: Scaling Robot Data Generation with Multi-modal and Reasoning LLMs*. 2025.
[^qwen-2026-robotmanip]: Qwen Team. *Qwen-RobotManip Technical Report: Alignment Unlocks Scale for Robotic Manipulation Foundation Models*. 2026. https://arxiv.org/abs/2606.17846
