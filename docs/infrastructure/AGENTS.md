# docs/infrastructure/ — 基础设施

AI 系统的物理层与运营层，中频更新。

## 文件列表

| 文件 | 主题 |
|------|------|
| `infrastructure.md` | 硬件 / 网络 / 部署基础设施 |
| `lustre.md` | Lustre 并行文件系统（HPC/AI 超算存储） |
| `3fs.md` | 3FS 分布式文件系统（DeepSeek AI 训练存储） |
| `inference-economics.md` | 推理经济性（GPU 成本、API 定价、盈亏模型） |

## 收录哪些内容

- GPU 加速器、互联拓扑（NVLink / InfiniBand / RoCE）→ `infrastructure.md`
- HPC/AI 存储系统 → `lustre.md`、`3fs.md`
- 推理成本核算 / API 定价模型 → `inference-economics.md`

## 不收录

- **推理引擎软件**（vLLM、TensorRT-LLM 等具体实现）→ 如有技术突破收录到对应知识文档
- **云服务商对比** → 跳过
