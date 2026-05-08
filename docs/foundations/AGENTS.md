# docs/foundations/ — 基础理论

稳定的核心知识，低频更新。

## 文件列表

| 文件 | 主题 |
|------|------|
| `transformer.md` | Transformer 架构 |
| `kv-cache.md` | KV Cache 与推理优化 |
| `mamba-and-ssm.md` | SSM / Mamba / 替代架构 |
| `multimodal-ai.md` | 多模态 AI |
| `representation-learning.md` | 从规则到表示学习 |

## 收录哪些内容

- Transformer 架构演进 → `transformer.md`
- KV Cache、推理优化（GQA、Prefill/Decode、压缩权衡）→ `kv-cache.md`
- SSM / Mamba / 替代架构 → `mamba-and-ssm.md`
- 多模态数据特征与技术路线 → `multimodal-ai.md`
- ML 范式演进（规则系统 → 特征工程 → 表示学习）→ `representation-learning.md`

## 不收录

- **产品/模型清单**（各厂商模型对比、评估基准表）→ 跳过
- **教程/代码示例**（Python 微调代码、工具使用指南）→ 不属于基础理论
- **训练/对齐流程**（SFT、RLHF、DPO 等）→ 已拆除，如有技术方案革新可在 `research/` 收录

## 写作方式

- 每个概念：先用类比/具体例子建立直觉 → 再给形式化定义
- 复杂机制配可跟算的数值示例（如 SSM 一维状态更新、KV Cache 逐步计算）
- 章节按"数据/问题特征 → 技术问题 → 解法与权衡"组织
- 方案对比用精炼表格（必须包含"权衡"列）
- 流程用 Mermaid 图可视化

