# docs/embodied-infrastructure/ — 具身基础设施

具身智能的数据、仿真与系统基础设施。

## 文件列表

| 文件 | 主题 |
|------|------|
| `embodied-data-types.md` | 具身智能数据类型（通用四元组：图像、本体感知、动作、语言指令） |
| `embodied-normalization.md` | 具身智能数据归一化（z-score / min-max / 分位数方案、delta actions 陷阱、per-timestep 归一化） |
| `embodied-data-pipeline.md` | 具身智能数据管线（领域特有问题：硬件碎片化、动作空间异构、采集即标注，各阶段跨框架解法对比） |
| `lerobot-dataset-v3.md` | LeRobot Dataset v3 可扩展存储架构（存储-API 解耦、多 episode 聚合、关系型元数据） |
| `simulation.md` | 具身仿真（GPU 并行 vs CPU 高保真、接触力学建模、Sim-to-Real Gap 跨越策略） |
| `ros2.md` | ROS 2 机器人分布式软件框架（DDS 通信层、去中心化发现、通信原语、QoS、Executor 调度） |
| `dds.md` | DDS 数据分发服务（Data-Centric 模型、DCPS 实体、自动发现、QoS 策略、机器人集成形态） |
| `embodied-synthetic-data.md` | 具身智能合成数据（仿真扩增 / H2R 视频合成 / LLM 驱动生成三条路线、各方案核心权衡） |

## 收录哪些内容

- 具身数据采集与标注方法
- 数据类型、归一化、数据管线
- 数据集存储架构
- 仿真到现实迁移（Sim-to-Real、域随机化）
- 机器人中间件与通信协议（ROS 2、DDS）
- 触觉/力觉等新型传感模态

## 不收录

- **机器人基础模型（VLA、世界模型）** → `embodied-algorithm/`
- **通用视觉/多模态模型**（无物理交互场景）→ `foundations/multimodal-ai.md`
- **纯强化学习理论**（无具身落地场景）→ 跳过
- **产品评测/对比清单** → 跳过
