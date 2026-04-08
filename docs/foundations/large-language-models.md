---
title: "大语言模型 (Large Language Models)"
description: "大语言模型是当前 AI 革命的核心驱动力。本文档系统梳理 LLM 的关键技术、主流模型和发展趋势。"
created: 2026-04-07
updated: 2026-04-08
tags: [llm, transformer, scaling-laws, attention, moe]
---

# 大语言模型 (Large Language Models)

> 大语言模型是当前 AI 革命的核心驱动力。本文档系统梳理 LLM 的关键技术、主流模型和发展趋势。

---

## 1. 概述

### 什么是大语言模型

大语言模型 (LLM) 是基于 **Transformer 架构**、在海量文本数据上预训练的深度神经网络模型。它们通过**自回归 (autoregressive)** 方式逐 token 生成文本，能够完成对话、写作、编程、推理等复杂任务。

### 核心架构：Transformer

Transformer 由 Vaswani 等人在 2017 年论文 [*"Attention Is All You Need"*](https://arxiv.org/abs/1706.03762) 中提出，核心机制包括：

- **自注意力 (Self-Attention)**: 让模型关注输入序列中任意位置之间的依赖关系
- **多头注意力 (Multi-Head Attention)**: 并行计算多组注意力，捕获不同子空间的信息
- **位置编码 (Positional Encoding)**: 注入序列位置信息（从固定正弦编码演进到 RoPE、ALiBi 等）
- **前馈网络 (FFN)**: 每层中的非线性变换，现代模型常用 SwiGLU 激活

```
输入 Token → Embedding → [Self-Attention → FFN] × N layers → 输出概率分布
```

### Scaling Laws

模型性能与三个关键因素的幂律关系：

- **参数量 (Parameters)**: 模型大小
- **数据量 (Data)**: 训练数据规模
- **计算量 (Compute)**: 训练所用 FLOPs

**Kaplan et al. (2020)** 首次提出 Scaling Laws，**Chinchilla (2022)** 修正了最优的数据-参数比例关系：训练 token 数应约为参数量的 20 倍。

---

## 2. 主流模型对比 (截至 2026 年 4 月)

### 闭源模型

| 模型 | 厂商 | 发布时间 | 上下文窗口 | 特点 |
|------|------|----------|------------|------|
| **Claude Mythos Preview** | Anthropic | 2026.4 | - | 未公开发布，受限于 Project GlassWing |
| **Claude Opus 4.6** | Anthropic | 2026.3 | 1M | Opus 4 后续，1M 上下文 GA |
| **Claude Sonnet 4.6** | Anthropic | 2026.3 | 1M | 1M 上下文 GA |
| **GPT-5.3-Codex** | OpenAI | 2026.4 | 128K+ | 专为代码优化，支持按需定价 |
| **GPT-5.3 Instant** | OpenAI | 2026.3 | 128K+ | 更快速、更经济的版本 |
| **GPT-5** | OpenAI | 2025 | 128K+ | 多模态原生，强推理能力 |
| **o1 / o3** | OpenAI | 2024-2025 | 128K | 推理模型，"思考"后回答 |
| **Claude Opus 4** | Anthropic | 2025 | 200K | 最强推理，深度分析 |
| **Claude Sonnet 4** | Anthropic | 2025 | 200K | 性能与速度平衡 |
| **Claude Haiku 3.5** | Anthropic | 2025 | 200K | 快速响应，成本最低 |
| **Gemini 3.1 Pro** | Google | 2026.2 | 1M+ | 长上下文，复杂任务 |
| **Gemini 3.1 Flash** | Google | 2026.3 | 1M+ | 高速推理，自然语音 |
| **Gemini 3.1 Flash-Lite** | Google | 2026.3 | 1M+ | 大规模部署优化 |
| **Gemini 3 Deep Think** | Google | 2026.2 | - | 科学研究与数学推理 |

### 开源模型

| 模型 | 厂商 | 参数量 | 特点 |
|------|------|--------|------|
| **GLM-5.1** | Z.ai (智谱) | 754B | MIT 协议，1.51TB，主打长周期任务 (2026.4) |
| **Llama 4** | Meta | 多规格 | 开源旗舰，社区生态最强 |
| **Llama 3.1** | Meta | 8B/70B/405B | 仍在广泛使用 |
| **Gemma 4** | Google | 多规格 | 2026.4 最新开源，高效率 |
| **Mistral Large** | Mistral | 未公开 | 欧洲 AI 代表 |
| **Mixtral 8x7B** | Mistral | 46.7B(12.9B active) | MoE 架构先驱 |
| **DeepSeek-V3** | DeepSeek | 671B(37B active) | MoE 架构，卓越性价比 |
| **DeepSeek-R1** | DeepSeek | 671B | 开源推理模型标杆 |
| **Qwen2.5** | 阿里 | 0.5B-72B | 中文最强开源之一 |
| **Yi-Lightning** | 零一万物 | 未公开 | 中文大模型 |

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

### 3.1 注意力机制演进

| 技术 | 说明 | 代表模型 |
|------|------|----------|
| **Vanilla Attention** | O(n²) 复杂度，标准 Transformer | GPT-2/3 |
| **Multi-Query Attention (MQA)** | 多个 query 头共享 KV 头 | PaLM |
| **Grouped-Query Attention (GQA)** | 折中方案，分组共享 KV 头 | Llama 2/3 |
| **Flash Attention** | IO 感知的精确注意力算法 | 几乎所有现代模型 |
| **Ring Attention** | 跨设备分布式长序列注意力 | 长上下文模型 |
| **Sliding Window Attention** | 局部注意力窗口 | Mistral |

### 3.2 位置编码

- **RoPE (Rotary Position Embedding)**: 通过旋转矩阵编码相对位置，支持长度外推
- **ALiBi (Attention with Linear Biases)**: 线性偏置实现位置感知
- **YaRN**: RoPE 的改进版，更好的长度泛化

### 3.3 Tokenization

| 方法 | 说明 |
|------|------|
| **BPE (Byte-Pair Encoding)** | GPT 系列使用，逐步合并高频字节对 |
| **SentencePiece** | Google 开发，支持 BPE 和 Unigram |
| **WordPiece** | BERT 使用 |
| **Tiktoken** | OpenAI 的高效 BPE 实现 |

### 3.4 上下文窗口演进

```
4K (GPT-3) → 8K (GPT-4) → 32K → 128K (GPT-4 Turbo) 
    → 200K (Claude 3) → 1M (Gemini 1.5) → 1M GA (Claude Opus/Sonnet 4.6) → 2M+ (Gemini 3.1)
```

长上下文的关键技术：
- **RoPE 频率外推**: 将 RoPE 基础频率调大
- **持续预训练**: 在长文本上继续训练
- **Flash Attention**: 降低内存占用
- **Ring Attention**: 分布式长序列处理

### 3.5 Mixture of Experts (MoE)

MoE 是一种**稀疏激活**架构，在每次前向传播中只激活部分参数：

```
输入 → Router → 选择 Top-K Expert → Expert 1, Expert 3 → 加权合并 → 输出
                                      (只有被选中的 Expert 参与计算)
```

**优势**: 在相同计算预算下拥有更多参数（知识容量）

| 模型 | 总参数 | 活跃参数 | Expert 数 |
|------|--------|----------|-----------|
| Mixtral 8x7B | 46.7B | 12.9B | 8 |
| DeepSeek-V3 | 671B | 37B | 256 |
| Qwen2.5-MoE | - | - | - |

### 3.6 推理模型 (Reasoning Models)

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

- Vaswani et al., "Attention Is All You Need", 2017 - [arXiv:1706.03762](https://arxiv.org/abs/1706.03762)
- Kaplan et al., "Scaling Laws for Neural Language Models", 2020 - [arXiv:2001.08361](https://arxiv.org/abs/2001.08361)
- Hoffmann et al., "Training Compute-Optimal Large Language Models" (Chinchilla), 2022 - [arXiv:2203.15556](https://arxiv.org/abs/2203.15556)
- Wei et al., "Chain-of-Thought Prompting", 2022 - [arXiv:2201.11903](https://arxiv.org/abs/2201.11903)
- Dao et al., "FlashAttention", 2022 - [arXiv:2205.14135](https://arxiv.org/abs/2205.14135)
- Shazeer, "GLU Variants Improve Transformer", 2020 - [arXiv:2002.05202](https://arxiv.org/abs/2002.05202)
- OpenAI Blog: https://openai.com/blog
- Anthropic Research: https://www.anthropic.com/research
- Google DeepMind: https://deepmind.google/discover/blog/
