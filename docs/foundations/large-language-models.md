---
title: "大语言模型 (Large Language Models)"
description: "大语言模型是当前 AI 革命的核心驱动力。本文档系统梳理 LLM 的关键技术、主流模型和发展趋势。"
created: 2026-04-07
updated: 2026-04-08
tags: [llm, scaling-laws, moe]
review:
---

# 大语言模型 (Large Language Models)

> 大语言模型是当前 AI 革命的核心驱动力。本文档系统梳理 LLM 的关键技术、主流模型和发展趋势。

---

## 1. 概述

### 什么是大语言模型

大语言模型 (LLM) 是基于 **Transformer 架构**、在海量文本数据上预训练的深度神经网络模型。它们通过**自回归 (autoregressive)** 方式逐 token 生成文本，能够完成对话、写作、编程、推理等复杂任务。

### 底层架构

当前主流 LLM 基于 **Decoder-only Transformer**——用因果掩码的自注意力机制进行自回归生成。近年来 **Mamba/SSM**（状态空间模型）作为线性复杂度的替代方案兴起，混合架构也在探索中。

> 架构详解见 [Transformer 架构](./transformer.md) 和 [Mamba 与状态空间模型](./mamba-and-ssm.md)。

### Scaling Laws

模型性能与三个关键因素的幂律关系：

- **参数量 (Parameters)**: 模型大小
- **数据量 (Data)**: 训练数据规模
- **计算量 (Compute)**: 训练所用 FLOPs

**Kaplan et al. (2020)** 首次提出 Scaling Laws，**Chinchilla (2022)** 修正了最优的数据-参数比例关系：训练 token 数应约为参数量的 20 倍。

---

## 2. 主流模型

> 完整的模型列表与最新发布动态见 [模型动态跟踪](../landscape/model-tracker.md)。

当前 LLM 市场由 OpenAI、Anthropic、Google 三家闭源厂商领跑，开源生态以 Meta Llama、DeepSeek、Mistral、Qwen 为代表。

### OpenAI 发展历程

```
GPT-1 (2018) → GPT-2 (2019) → GPT-3 (2020) → GPT-3.5 (2022) 
    → GPT-4 (2023.3) → GPT-4o (2024.5) → o1 (2024.9) 
    → GPT-5 (2025) → o3 (2025) → GPT-5.3 (2026.3)
```

OpenAI 在 2026 年 3 月完成了 **$122B** 融资，为 AI 史上最大规模融资。

### Anthropic 研究亮点

- **Claude Mythos Preview** (2026.4): 超强网络安全能力，GPT-2 以来首个"太危险而不公开发布"的模型，受限于 Project GlassWing
- **Claude Opus/Sonnet 4.6** (2026.3): 1M 上下文窗口正式 GA
- **Alignment Faking** (2024.12): 首次实证发现模型在未经训练情况下进行对齐伪装
- **Constitutional Classifiers** (2025.2): 防御通用越狱攻击
- **可解释性研究**: 情感概念理解 (2026.4)、模型内省能力 (2025.10)

### Google DeepMind 进展

- **Gemini 3 Flash** (2025.12): 速度优先的前沿模型
- **Gemma 4** (2026.4): 字节级最强开源模型
- **FACTS Benchmark** (2025.12): 系统评估 LLM 事实性
- **AGI 认知框架** (2026.3): 衡量通向 AGI 的进展

---

## 3. 关键技术

> 注意力变体（MHA/GQA/MLA）、位置编码（RoPE/ALiBi）、归一化、FFN/激活函数、MoE 等架构层面的技术已移至 [Transformer 架构](./transformer.md)；SSM/Mamba 相关内容见 [Mamba 与状态空间模型](./mamba-and-ssm.md)。本节聚焦 LLM 特有的技术维度。

### 3.1 Tokenization

| 方法 | 说明 |
|------|------|
| **BPE (Byte-Pair Encoding)** | GPT 系列使用，逐步合并高频字节对 |
| **SentencePiece** | Google 开发，支持 BPE 和 Unigram |
| **WordPiece** | BERT 使用 |
| **Tiktoken** | OpenAI 的高效 BPE 实现 |

### 3.2 上下文窗口演进

```
4K (GPT-3) → 8K (GPT-4) → 32K → 128K (GPT-4 Turbo) 
    → 200K (Claude 3) → 1M (Gemini 1.5) → 1M GA (Claude Opus/Sonnet 4.6) → 2M+ (Gemini 3.1)
```

长上下文的关键技术：
- **RoPE 频率外推**: 将 RoPE 基础频率调大（详见 [Transformer § 6](./transformer.md#6-位置编码的演进)）
- **持续预训练**: 在长文本上继续训练
- **Flash Attention**: 降低内存占用（详见 [Transformer § 5](./transformer.md#5-flash-attentionio-感知的算法革新)）
- **Ring Attention**: 分布式长序列处理

### 3.3 推理模型 (Reasoning Models)

2024-2026 年最重要的突破之一：模型在回答前先进行**深度思考**。

| 模型 | 厂商 | 特点 |
|------|------|------|
| **o1** | OpenAI | 首个商业推理模型 |
| **o3** | OpenAI | o1 的后续版本，更强推理 |
| **DeepSeek-R1** | DeepSeek | 开源推理模型标杆 |
| **Gemini Deep Think** | Google | 面向科学与数学 |
| **QED-Nano** | 研究论文 | 教小模型证明困难定理 (2026.4) |

核心技术：
- **链式思维 (Chain-of-Thought)**: 模型生成推理过程
- **Test-time Compute Scaling**: 推理时投入更多计算
- **过程奖励模型 (PRM)**: 对推理过程（而非仅结果）进行奖励
- **蒙特卡洛树搜索 (MCTS)**: 在推理空间中搜索最优路径

---

## 4. 开源 vs 闭源生态

### 开源优势
- 可本地部署，数据不出域
- 自由微调和定制
- 社区驱动创新
- 成本可控

### 闭源优势
- 通常性能更强
- 持续更新维护
- 使用简单 (API)
- 安全防护更完善

### 开源生态系统

```
Hugging Face Hub (模型、数据集、Spaces)
    ├── Transformers (训练/推理框架)
    ├── PEFT (参数高效微调)
    ├── TRL (RLHF 训练)
    ├── Datasets (数据处理)
    ├── Accelerate (分布式训练)
    └── Text Generation Inference (推理服务)
```

### 许可证对比

| 许可证 | 商用 | 代表模型 |
|--------|------|----------|
| Apache 2.0 | 完全允许 | Mistral, Qwen |
| Llama 许可证 | 有条件 (MAU<700M) | Llama 系列 |
| Gemma 许可证 | 有条件 | Gemma 系列 |
| CC-BY-NC | 仅非商用 | 部分研究模型 |

---

## 5. 评估基准

### 主要基准

| 基准 | 评估能力 | 说明 |
|------|----------|------|
| **MMLU** | 知识广度 | 57 个学科的多选题 |
| **MMLU-Pro** | 知识深度 | MMLU 的加强版 |
| **HumanEval / MBPP** | 代码生成 | Python 编程题 |
| **MATH** | 数学推理 | 竞赛级数学题 |
| **GSM8K** | 数学推理 | 小学数学应用题 |
| **ARC** | 科学推理 | 科学考试题 |
| **HellaSwag** | 常识推理 | 场景续写 |
| **GPQA** | 专家级知识 | 研究生级别的科学题 |
| **SWE-bench** | 工程能力 | 真实 GitHub Issue 修复 |
| **Chatbot Arena** | 综合对话 | 人类盲评排名 (ELO) |
| **MT-Bench** | 多轮对话 | GPT-4 评判 |
| **FACTS** | 事实性 | Google DeepMind 2025.12 发布 |

### Chatbot Arena (LMSYS)

[Chatbot Arena](https://chat.lmsys.org/) 是目前最权威的 LLM 综合评测平台：
- 用户与两个匿名模型对话并投票选择更好的
- 使用 ELO 评分系统排名
- 覆盖数十万次人类评价

---

## 6. 发展趋势

### 6.1 推理时计算 (Test-time Compute)

不只是训练更大的模型，而是让模型在推理时"思考更久"：
- 更多的推理 token = 更好的结果
- Scaling 曲线从训练转向推理

### 6.2 小而精模型

大模型的知识通过蒸馏等方式转移到小模型：
- Phi 系列 (Microsoft): 小参数量大能力
- Gemma 4 (Google): 开源高效率
- DeepSeek-R1 蒸馏版: 1.5B-70B 多种规格

### 6.3 多模态融合

LLM 从纯文本走向原生多模态：
- GPT-4o: 文本 + 图像 + 音频统一
- Gemini: 从设计之初就是多模态
- 趋势: 所有模态在统一架构中处理

### 6.4 长上下文

- 从 4K 到 2M+ tokens
- 减少了对外部检索的依赖
- 但长上下文的有效利用仍是挑战（"中间遗失"问题）

### 6.5 代码生成专精

- GPT-5.3-Codex: 专为代码优化的模型
- Claude Code: 端到端编程助手
- 编程 Agent 成为最成熟的应用场景之一

### 6.6 合成数据

- 用强模型生成训练数据给弱模型
- 对数据质量的要求越来越高
- 数据筛选和清洗变得与模型架构同等重要

---

## 参考资料

- Kaplan et al., "Scaling Laws for Neural Language Models", 2020 - [arXiv:2001.08361](https://arxiv.org/abs/2001.08361)
- Hoffmann et al., "Training Compute-Optimal Large Language Models" (Chinchilla), 2022 - [arXiv:2203.15556](https://arxiv.org/abs/2203.15556)
- Wei et al., "Chain-of-Thought Prompting", 2022 - [arXiv:2201.11903](https://arxiv.org/abs/2201.11903)
- OpenAI Blog: https://openai.com/blog
- Anthropic Research: https://www.anthropic.com/research
- Google DeepMind: https://deepmind.google/discover/blog/
