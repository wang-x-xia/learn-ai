---
title: "OneVL：双模态 Latent CoT 的视觉-语言-动作框架"
description: "OneVL 通过双模态辅助解码器将 Emu3.5 的视觉 tokenizer 与 Qwen3-VL 的语言模型集成，实现了首个超越显式 CoT 的 latent CoT 方法"
created: "2025-01-19"
updated: "2025-01-19"
tags: ["multimodal", "vision-language", "cot", "reasoning", "architecture"]
review: "2025-01-19"
---

| 属性 | 值 |
|------|-----|
| **开发者** | Xiaomi Research |
| **开源协议** | Apache 2.0 |
| **GitHub** | [xiaomi-research/onevl](https://github.com/xiaomi-research/onevl) |
| **论文** | [arXiv:2604.18486](https://arxiv.org/abs/2604.18486) |
| **模型权重** | [HuggingFace](https://huggingface.co/collections/xiaomi-research/onevl-models/) |

**一句话定位**：首个在驾驶任务上超越显式 CoT 的 latent CoT 方法，通过双模态辅助解码器将 Emu3.5 视觉 tokenizer 与 Qwen3-VL 语言模型集成，实现 answer-only 延迟下的最优性能。

---

??? note "背景知识"
    - **VLA（Vision-Language-Action）模型**：融合视觉、语言和动作的多模态模型，用于具身智能任务
    - **Chain-of-Thought（CoT）推理**：通过显式的推理链提升模型性能，但会增加推理延迟
    - **Latent CoT**：将推理过程压缩到 latent space 中以减少延迟，但通常性能不如显式 CoT
    - **Emu3**[^github-2024-emu3]：BAAI 提出的基于 next-token prediction 的多模态模型，使用统一的视觉 tokenizer
    - **Qwen3-VL**[^github-2025-qwen3-vl]：阿里巴巴推出的视觉-语言模型，具有强大的多模态理解能力

---

## 核心问题：Latent CoT 的性能困境

在自动驾驶轨迹预测任务中，Chain-of-Thought（CoT）推理能显著提升准确性，但其自回归性质带来的延迟成本对于实时部署是不可接受的。Latent CoT 方法试图通过将推理压缩到连续隐状态中来减少延迟，但**在驾驶任务上一致性地表现不佳，甚至不如不使用 CoT 的基线**。

OneVL 论文[^arxiv-2026-onevl]指出，这一根本性缺陷的原因是：**纯语言 latent 表示压缩的是世界的符号化抽象，而非实际驾驶的因果动力学**。一个只压缩语言的 latent 向量仅仅是在压缩对世界的抽象描述，而非底层的物理结构。

## 技术亮点

### 双模态辅助解码器架构

OneVL 的核心创新在于引入**双模态辅助解码器**，同时约束 latent space 的语义和物理维度：

- **语言辅助解码器**：从语言 latent hidden states 重构人类可读的 CoT 文本，将 bottleneck 建立在语义意图上（场景解释、对象分析、驾驶决策）
- **视觉辅助解码器**：从视觉 latent hidden states 预测未来帧的视觉 tokens（t+0.5s 和 t+1.0s），作为 **world model 监督信号**，将 bottleneck 建立在物理场景动力学上

两个解码器共同约束 latent space，使其同时编码语义意图和物理动力学，这是 OneVL 能够超越显式 CoT 的关键。

### Emu3.5 与 Qwen3-VL 的深度集成

OneVL 不是简单地将两个模型拼接，而是通过精心设计的接口将 Emu3.5 的视觉能力嵌入到 Qwen3-VL 的语言理解框架中：

```
输入图像 → Emu3.5 IBQ (131k codebook) → 视觉 tokens → Qwen3-VL 扩展词汇表 → 轨迹预测
                                                              ↓
                                                        latent tokens
                                                              ↓
                                            ┌─────────────────┴─────────────────┐
                                            ↓                                   ↓
                                    语言辅助解码器                      视觉辅助解码器
                                    (重构 CoT 文本)                    (预测未来帧 tokens)
                                            ↓                                   ↓
                                    可解释的推理                        物理场景动力学
```

#### 视觉 Tokenizer 层
直接使用 Emu3.5 的 **IBQ（Index-Based Quantization）** 模型作为视觉 tokenizer，利用其预训练的 131k codebook，无需从头训练视觉量化模块。

#### 词汇表扩展策略
扩展 Qwen3-VL 的 tokenizer 以支持 131k 个视觉 tokens：
- **视觉令牌格式**：`<<|visual token XXXXXX|>`（6 位数字，共 131k 个）
- **令牌 ID 范围**：从 151674 开始
- **实现方式**：避免使用 Qwen3-VL 的 `added_tokens` 机制（慢），直接操作 `model.vocab`（快），用 NUL byte（`\x00`）作为占位符，后处理中替换为真实视觉令牌 ID

#### 视觉 Token Embedding 初始化
新增的视觉 token embedding 不是随机初始化，而是从训练好的检查点中加载，基于 Emu3.5 的预训练知识。

### Prefill Inference 策略

- **训练时**：辅助解码器监督 latent tokens 的学习
- **推理时**：丢弃辅助解码器，latent tokens 预填充到上下文，单次并行处理
- **效果**：推理延迟与 answer-only 相当，但性能超越显式 CoT

这种策略使得 OneVL 在保持推理效率的同时，获得了超越显式 CoT 的性能。

### 三阶段渐进式训练

为确保主模型、语言辅助解码器和视觉辅助解码器能够稳定地联合优化，OneVL 采用三阶段训练流程：

1. **Stage 0（主模型预热）**：训练主模型端到端进行轨迹预测，在每个训练样本中嵌入 latent tokens
2. **Stage 1（辅助解码器预热）**：冻结主模型，单独训练辅助解码器与稳定的 latent 表示对齐
3. **Stage 2（联合端到端微调）**：解冻所有组件，同时训练，两个解码器的梯度回流到主模型，形成良性循环

分阶段训练是必需的——消融实验显示，没有分阶段训练性能会崩溃到 67.13。

## 为什么值得知道

### 首个超越显式 CoT 的 Latent CoT 方法

OneVL 是**首个在所有基准测试中超越显式 CoT 的 latent CoT 方法**：

| 基准测试 | OneVL | 显式 CoT | 提升 |
|---------|-------|---------|------|
| NAVSIM PDM-score | 88.84 | 88.29 | +0.55 |
| ROADWork ADE | 12.49 | 13.18 | -5.2% |
| Impromptu ADE | 1.34 | 1.42 | -5.6% |
| APR1 ADE | 2.62 | 2.99 | -12.4% |

同时保持 answer-only 的推理速度，在 NAVSIM 和 ROADWork 上同时实现了最低延迟和最佳指标。

### 模型集成的工程范例

OneVL[^github-2025-onevl]展示了如何巧妙地集成两个不同的预训练模型：

- **不重新训练视觉 tokenizer**：直接使用 Emu3.5 预训练的 IBQ
- **最小化架构修改**：仅扩展词汇表和添加辅助解码器
- **统一检查点管理**：所有权重存储在同一 safetensors 文件中，通过前缀区分

这种集成策略为其他多模态模型融合提供了参考。

### 压缩驱动泛化的验证

OneVL 的实验结果验证了一个重要假设：**通过合适的监督信号（world model），压缩后的表示可以比 verbose 的 token-by-token 推理更具泛化性**。这对 latent CoT 的研究方向具有重要启示。

## 局限性

1. **架构复杂度**：双模态辅助解码器增加了训练和部署的复杂度
2. **内存需求**：推理时如需使用辅助解码器，需要 ≥16GB VRAM
3. **领域特定**：当前专注于自动驾驶场景，泛化到其他 VLA 任务需验证

## 参考资料

[^arxiv-2026-onevl]: Jinghui Lu et al. *Xiaomi OneVL: One-Step Latent Reasoning and Planning with Vision-Language Explanation*. arXiv:2604.18486. 2026. https://arxiv.org/abs/2604.18486
[^github-2025-onevl]: Xiaomi Research. *OneVL: One-Step Latent Reasoning and Planning with Vision-Language Explanations*. GitHub. 2025. https://github.com/xiaomi-research/onevl
[^github-2024-emu3]: BAAI. *Emu3: Next-Token Prediction is All You Need*. GitHub. 2024. https://github.com/baaivision/Emu3
[^github-2025-qwen3-vl]: Qwen Team. *Qwen3-VL: The Most Powerful Vision-Language Model in the Qwen Series*. GitHub. 2025. https://github.com/QwenLM/Qwen3-VL