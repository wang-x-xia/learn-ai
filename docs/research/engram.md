---
title: Engram
description: 条件记忆模块——通过现代化 N-gram embeddings 实现 O(1) 知识查找，与 MoE 条件计算形成互补稀疏性轴。适用于静态高频模式（实体、公式、API），无法动态更新，需与 RAG 配合处理动态外部知识。
created: 2026-04-27
updated: 2026-04-28
tags:
  - deepseek
  - conditional-memory
  - n-gram
  - moe
  - sparsity
  - long-context
  - rag
review: 2026-04-28
---

# Engram

??? note "背景知识"
    - **Transformer Embedding**：将 token 映射为高维向量，是模型处理文本的第一步 → [详见](../foundations/transformer.md)
    - **MoE (Mixture of Experts)**：多个小 FFN 中选择性激活，实现稀疏计算 → [详见](../foundations/transformer.md#moe)
    - **RAG (检索增强生成)**：从外部知识库检索文档注入上下文 → [详见](../applied/rag.md)
    - **N-gram**：连续 N 个 token 的组合，用于文本的局部模式匹配

> 原文：Cheng et al. *Conditional Memory via Scalable Lookup: A New Axis of Sparsity for Large Language Models*. 2026[^engram-2026]。本文提炼论文中的核心技术方案与设计权衡。

---

## Engram 如何工作

Engram 给模型内置一个静态 N-gram 字典，存储固化的知识，在前几层通过判断当前上下文是否与这些知识相似，如果相似就将知识权重并入当前状态，从而提升模型效果。

### 核心目标

**问题**：标准 Transformer 在前几层需要消耗大量计算来重建静态知识。例如识别 "大数据" 需要多个早期层逐步组合特征，本质是昂贵的运行时静态查找表重建。

**方案**：Engram 将这些静态知识预先存储在 embedding 表中，在前几层直接判断当前上下文是否与这些知识相似，如果相似就将知识权重并入当前状态，避免重复计算。

### Embedding 表制备

Engram 的 embedding 表通过端到端训练学习得到（使用 Adam 优化器，学习率比模型其他参数高 5×）。查询时需要额外的投影层：将通用 tokenizer 的原始 token IDs 通过 NFKC 规范化、小写等规则映射到压缩 IDs，对 128k tokenizer 可减少 23% 的有效词汇表规模，提升语义密度。Engram-27B 使用 5.7B 参数的 embedding 表，Engram-40B 扩展至 18.5B。

### 推理流程

#### 1. 提取 N-gram

对输入序列中的每个位置，提取以该位置结尾的连续 token 序列（suffix N-gram）。一般 N=3，即使用 2-gram 和 3-gram。

```
输入: "大数据分析"

位置 2 ("据"):
- 2-gram: [ID_数, ID_据]
- 3-gram: [ID_大, ID_数, ID_据]
```

#### 2. 哈希查询

通过哈希函数查找对应的 embedding 向量（固化的知识）。

```
对 2-gram [ID_数, ID_据]:
hash([ID_数, ID_据]) → 索引 12345 → e_t = [0.1, 0.2, 0.3, ...]

对 3-gram [ID_大, ID_数, ID_据]:
hash([ID_大, ID_数, ID_据]) → 索引 67890 → e_t = [0.4, 0.5, 0.6, ...]
```

这些 embedding 向量是训练时学到的固化知识，编码了 "数据" 和 "大数据" 的语义。

#### 3. 按权重并入知识

用当前隐藏状态与检索到的知识计算相似度，按相似度权重并入知识。

```
当前隐藏状态: h_t = [0.5, 0.6, 0.7, ...]  ← 模型对当前上下文的内部理解
检索到的知识: e_t = [0.1, 0.2, 0.3, ...]  ← 固化的 "数据" 知识

计算相似度权重:
α = σ(h_t · e_t)  ← α ∈ [0,1]

按权重并入:
h_new = h_t + α · e_t
```

如果当前上下文确实在讲 "数据"，α 接近 1，知识被充分并入；如果不是，α 接近 0，知识被抑制。

### 配置参数

| 参数 | 典型值 | 说明 |
|------|--------|------|
| N-gram 阶数 N | 3 | 使用 2-gram + 3-gram |
| 哈希头数 K | 8 | 每个 N-gram 用 8 个哈希头减少冲突 |
| Engram 所在层 | 如第 2 层和第 15 层 | 早期插入可卸载局部模式重建，但需权衡上下文查询质量（详见论文 Section 6.2） |
| embedding 维度 | 1280 | 固化知识的向量维度 |
| embedding 表共享 | 全局共享 | 不同层的 Engram 使用同一个 embedding 表，避免重复存储相同知识 |

---

## Engram vs RAG vs Fine Tuning

| 维度 | Engram | RAG | Fine Tuning |
|------|--------|-----|-------------|
| **知识存储** | 模型内部（embedding 表） | 外部系统（向量库） | 模型内部（权重） |
| **知识更新** | 重新训练 | 直接更新文档 | 重新训练 |
| **推理成本** | 极低（确定性查找） | 中等（检索+生成） | 无额外成本 |
| **知识时效性** | 训练时固定 | 实时更新 | 训练时固定 |
| **适用场景** | 静态高频（API、公式） | 动态外部（新闻、文档） | 领域适配、风格迁移 |

---

## 参考资料

[^engram-2026]: Cheng et al. *Conditional Memory via Scalable Lookup: A New Axis of Sparsity for Large Language Models*. 2026. https://github.com/deepseek-ai/Engram
