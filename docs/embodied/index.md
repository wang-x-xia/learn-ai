---
title: 具身智能
description: 具身智能——机器人学习、仿真环境、视觉-语言-动作模型与物理世界交互。
---

# 具身智能

AI 与物理世界交互的技术前沿，涵盖机器人基础模型、仿真到现实迁移、感知-决策-控制全栈。

<div class="grid cards" markdown>

- :material-format-list-bulleted-type: **[具身智能数据类型](embodied-data-types.md)**

    ---

    机器人学习的事实标准四元组——视觉观测、本体感知、动作序列、语言指令的通用模式与各框架差异

- :material-chart-bell-curve: **[具身智能数据归一化](embodied-normalization.md)**

    ---

    z-score、min-max、分位数三种归一化方案的公式与权衡，delta actions 陷阱，per-timestep 归一化，动作离散化

- :material-robot: **[OpenPI 微调框架](openpi.md)**

    ---

    Physical Intelligence 开源 VLA 模型框架——双专家架构、三层 Transform 数据管线、位置语义化的固定观测结构

- :material-database: **[LeRobot Dataset v3](lerobot-dataset-v3.md)**

    ---

    存储-API 解耦、多 episode 文件聚合、关系型元数据索引，解决百万级 episode 可扩展性

- :material-earth: **[τ₀-World Model](tau-0-wm.md)**

    ---

    5B 视频-动作统一世界模型——视频扩散骨干联合生成未来帧与动作序列，异构数据模态级监督掩码，推理时 Propose-Evaluate-Revise

</div>
