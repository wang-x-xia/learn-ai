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

- :material-pipe: **[具身智能数据管线](embodied-data-pipeline.md)**

    ---

    从采集到模型消费的 8 个阶段——Schema 映射、坐标变换、模态预处理、归一化、时序窗口、表示转换、Batch 化、噪声注入，以及 LeRobot / OpenPI / Octo / RT-2 等框架的解法对比

- :material-robot: **[OpenPI 微调框架](openpi.md)**

    ---

    Physical Intelligence 开源 VLA 模型框架——双专家架构、三层 Transform 数据管线、位置语义化的固定观测结构

- :material-database: **[LeRobot Dataset v3](lerobot-dataset-v3.md)**

    ---

    存储-API 解耦、多 episode 文件聚合、关系型元数据索引，解决百万级 episode 可扩展性

- :material-earth: **[τ₀-World Model](tau-0-wm.md)**

    ---

    5B 视频-动作统一世界模型——视频扩散骨干联合生成未来帧与动作序列，异构数据模态级监督掩码，推理时 Propose-Evaluate-Revise

- :material-cube-outline: **[具身仿真](simulation.md)**

    ---

    GPU 并行仿真 vs CPU 高保真的技术权衡——接触力学建模、Sim-to-Real Gap 四种来源、域随机化 / 系统辨识 / Teacher-Student 蒸馏三种跨越策略

- :material-robot-industrial: **[ROS 2](ros2.md)**

    ---

    机器人分布式软件框架——DDS 通信层、去中心化发现、节点/话题/服务/动作四种通信原语、QoS 策略、Executor 调度模型

- :material-lan: **[DDS 数据分发服务](dds.md)**

    ---

    以数据为中心的发布/订阅标准——DCPS 实体模型、去中心化发现协议、22+ 种 QoS 策略，及在机器人系统中的三种集成形态

</div>
