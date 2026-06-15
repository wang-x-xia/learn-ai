# docs/embodied-algorithm/ — 具身算法

机器人基础模型与学习算法。

## 文件列表

| 文件 | 主题 |
|------|------|
| `openvla-oft.md` | OpenVLA-OFT VLA 微调方法论（并行解码、MLP action head 连续回归、L1 loss、FiLM 语言调制） |
| `openpi.md` | OpenPI 具身基础模型微调框架（双专家架构、三层 Transform 管线、位置语义化观测结构） |
| `tau-0-wm.md` | τ₀-World Model 统一视频-动作世界模型（异构数据监督掩码、6D rotation、Propose-Evaluate-Revise） |
| `starvla.md` | StarVLA 模块化 VLA 研究平台（Backbone–Action Head 解耦、四种动作解码范式、StarVLA-α 极简基线消融） |

## 收录哪些内容

- 机器人基础模型（VLA、通用操控策略）
- 世界模型（视频-动作联合生成）
- 感知-决策-控制架构

## 不收录

- **数据类型/归一化/管线/存储** → `embodied-infrastructure/`
- **仿真环境、机器人中间件** → `embodied-infrastructure/`
- **通用视觉/多模态模型**（无物理交互场景）→ `foundations/multimodal-ai.md`
- **纯强化学习理论**（无具身落地场景）→ 跳过
- **产品评测/对比清单** → 跳过
