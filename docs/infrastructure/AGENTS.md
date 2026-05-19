# docs/infrastructure/ — 基础设施

AI 系统的物理层与运营层，中频更新。

## 文件列表

| 文件 | 主题 |
|------|------|
| `infrastructure.md` | 硬件 / 网络 / 部署基础设施 |
| `training-evolution.md` | 训练范式演进（CPU → GPU → 分布式） |
| `distributed-training.md` | 分布式训练的数据流、存储与并行架构 |
| `inference-stages.md` | 推理过程主要阶段（KV Cache、Prefill、Decode）及优化技术（MTP、Chunked Prefilling） |
| `lustre.md` | Lustre 并行文件系统（HPC/AI 超算存储） |
| `3fs.md` | 3FS 分布式文件系统（DeepSeek AI 训练存储） |
| `inference-economics.md` | 推理经济性（GPU 成本、API 定价、盈亏模型） |

## 收录哪些内容

- GPU 加速器、互联拓扑（NVLink / InfiniBand / RoCE）→ `infrastructure.md`
- 训练范式演进（CPU → GPU → 分布式）→ `training-evolution.md`
- 分布式训练架构（数据流、并行策略、检查点）→ `distributed-training.md`
- 推理过程主要阶段（KV Cache、Prefill、Decode）→ `inference-stages.md`
- HPC/AI 存储系统 → `lustre.md`、`3fs.md`
- 推理成本核算 / API 定价模型 → `inference-economics.md`

## 不收录

- **推理引擎软件**（vLLM、TensorRT-LLM 等具体实现）→ 如有技术突破收录到对应知识文档
- **云服务商对比** → 跳过
