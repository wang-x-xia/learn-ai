# docs/foundations/ — 基础理论

稳定的核心知识，低频更新。

## 文件列表

| 文件 | 主题 |
|------|------|
| `transformer.md` | Transformer 架构 |
| `large-language-models.md` | LLM 概览、Scaling、评估 |
| `mamba-and-ssm.md` | SSM / Mamba / 替代架构 |
| `multimodal-ai.md` | 多模态 AI |
| `training-and-alignment.md` | 训练与对齐 |

## 收录哪些内容

- Transformer 架构演进 → `transformer.md`
- SSM / Mamba / 替代架构 → `mamba-and-ssm.md`
- 新模型发布 / Scaling / 评估方法 → `large-language-models.md`
- 多模态新进展 → `multimodal-ai.md`
- 训练 / 对齐新方法 → `training-and-alignment.md`

## Frontmatter 要求

```yaml
---
title: 文档标题
description: 一句话描述
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
review: YYYY-MM-DD
---
```

六个字段必填（`review` 留空表示从未 review）。每次修改内容时更新 `updated`，每次阅读审校后更新 `review`。
