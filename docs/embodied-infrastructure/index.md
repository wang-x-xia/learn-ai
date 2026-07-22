---
title: 具身基础设施
description: 具身智能基础设施——数据类型与归一化、数据管线、数据集存储、仿真环境、机器人中间件。
---

# 具身基础设施

具身智能的数据、仿真与系统基础设施，从数据采集到机器人通信全栈。

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

- :material-database: **[LeRobot Dataset v3](lerobot-dataset-v3.md)**

    ---

    存储-API 解耦、多 episode 文件聚合、关系型元数据索引，解决百万级 episode 可扩展性

- :material-rocket-launch: **[lerobot-lancedb](lerobot-lancedb.md)**

    ---

    LeRobotDataset 的 Lance 后端——JPEG bytes / mp4 Blob V2 两种 layout，2-5x 训练吞吐提升且 bit-exact 对齐上游

- :material-cube-outline: **[具身仿真](simulation.md)**

    ---

    GPU 并行仿真 vs CPU 高保真的技术权衡——接触力学建模、Sim-to-Real Gap 四种来源、域随机化 / 系统辨识 / Teacher-Student 蒸馏三种跨越策略

- :material-robot-industrial: **[ROS 2](ros2.md)**

    ---

    机器人分布式软件框架——DDS 通信层、去中心化发现、节点/话题/服务/动作四种通信原语、QoS 策略、Executor 调度模型

- :material-lan: **[DDS 数据分发服务](dds.md)**

    ---

    以数据为中心的发布/订阅标准——DCPS 实体模型、去中心化发现协议、22+ 种 QoS 策略，及在机器人系统中的三种集成形态

- :material-movie-filter: **[具身智能合成数据](embodied-synthetic-data.md)**

    ---

    机器人操作数据的三类合成方法——仿真扩增（MimicGen/RoboCasa）、H2R 视频合成、LLM 驱动生成式仿真，以及各方案的核心权衡

</div>
