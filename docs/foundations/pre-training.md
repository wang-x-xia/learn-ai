---
title: "预训练：为什么 Transformer 离不开它"
description: "预训练对 Transformer 的关键意义——归纳偏置权衡、数据阈值效应与理论解释。"
created: 2026-06-24
updated: 2026-06-24
tags:
  - transformer
  - pre-training
  - inductive-bias
  - transfer-learning
review: 2026-06-24
---

# 预训练：为什么 Transformer 离不开它

??? note "背景知识"
    - **Transformer 架构**：纯注意力机制的序列建模架构，无内置视觉/局部性先验 → [详见](./transformer.md)
    - **归纳偏置 (Inductive Bias)**：模型架构内置的先验假设，如 CNN 的平移等变性、局部感受野
    - **表示学习**：模型自动从原始数据中学习有用的特征表示 → [详见](./representation-learning.md)
    - **迁移学习 (Transfer Learning)**：在一个任务上学到的知识复用到其他任务

> CNN 和 RNN 从随机初始化训练就能达到不错的效果，但 Transformer 必须经过大规模预训练才能发挥威力。这不是巧合，而是架构设计的必然结果。
>
> 相关文档：[Transformer 架构](./transformer.md) | [从规则到表示学习](./representation-learning.md)

---

## 1. 核心矛盾：通用性 vs 数据饥渴

Transformer 的核心特点是**几乎没有领域先验**——它不预设"相邻像素更相关"（CNN 的卷积核）或"序列有时序依赖"（RNN 的循环结构）。这种通用性是一把双刃剑。

类比：CNN 像一个已经学过"看图基本功"的画家——构图、透视、配色的基础已经内化了，给他几百张范画就能画得不错。Transformer 像一个完全的白纸新手——天赋极高，但什么基础都没有，需要看上亿张画才能悟出门道。一旦悟了，反而画得比科班出身的更好，因为他没有被固定套路限制。

| 架构 | 内置归纳偏置 | 小数据表现 | 大数据上限 | 权衡 |
|------|-------------|-----------|-----------|------|
| **CNN** | 平移等变性、局部感受野 | 好——先验帮助快速收敛 | 受限——先验限制了表达空间 | 用上限换起点 |
| **RNN** | 时序依赖、隐状态传递 | 中等——适合序列但梯度问题多 | 受限——长距离依赖困难 | 用上限换结构 |
| **Transformer** | 几乎为零（仅位置编码） | 差——严重过拟合 | 最高——从数据中学出比先验更好的模式 | 用起点换上限 |

---

## 2. 关键实验证据

### ViT：90M 图片的分水岭

ViT (Vision Transformer) 论文[^vit-2021]做了一个决定性的控制实验，在 JFT-300M 数据集的不同规模子集上训练 ViT 和 ResNet，**不加额外正则化**，直接比较模型的本征性质：

| 预训练数据量 | ViT-B/32 vs ResNet50 |
|---|---|
| **9M** | ViT **远不如** ResNet |
| **30M** | 差距缩小 |
| **90M** | ViT **开始超过** ResNet |
| **300M** | ViT 明显优于 ResNet |

论文原话：

> *"Vision Transformers overfit more than ResNets with comparable computational cost on smaller datasets... This result reinforces the intuition that the convolutional inductive bias is useful for smaller datasets, but for larger ones, learning the relevant patterns directly from data is sufficient, even beneficial."*[^vit-2021]

在完整数据集对比中，ViT 在仅 1.3M 图片的 ImageNet 上输给 CNN，在 14M 的 ImageNet-21k 上持平，在 300M 的 JFT-300M 上才全面超越。

**历史注脚**：2017 年 YouTube-8M 视频分类竞赛中，尽管 *Attention Is All You Need* 已发表，但没有 Transformer 方案获胜——冠军清一色是 CNN + LSTM/GRU 架构。直到 ViT 论文揭示了大规模预训练的阈值效应，Transformer 在视觉领域才站稳脚跟。

### TrOCR：预训练模型初始化的决定性作用

TrOCR[^trocr-2021] 用纯 Transformer（ViT 编码器 + RoBERTa 解码器）替代传统的 CNN+RNN OCR 方案，消融实验表明预训练模型初始化、数据增强、两阶段预训练各自都带来显著提升。论文明确指出：

> *"The Transformer structures are competent to extract visual features well **after pre-training**."*[^trocr-2021]

没有预训练的纯 Transformer 在 OCR 上无法与 CNN 方案竞争；接入预训练后直接超越 SOTA。

---

## 3. 为什么预训练能补上归纳偏置的缺失

预训练对 Transformer 的作用可以从三个层面理解：

``` mermaid
graph LR
    subgraph 没有预训练
        R["随机初始化"] --> Bad["大量等价的\n局部最优解\n（多数泛化差）"]
    end

    subgraph 有预训练
        P["预训练权重"] --> Good["参数被锁定在\n'语言/视觉有意义'\n的区域"]
        Good --> FT["微调：在好的盆地内\n快速收敛到优解"]
    end
```

### 优化层面：引导到更好的损失盆地

Erhan et al.[^erhan-2010] 通过大量实验证明：预训练是一种**非典型正则化**——不是通过加惩罚项，而是通过约束优化起点来限制可达的局部最优解。预训练将参数初始化到一个支持更好泛化的损失盆地（basin of attraction），效果在更深的网络和更少的标注数据时更显著。

这对 Transformer 尤其重要：没有归纳偏置的深层网络面临的局部最优解数量远多于 CNN，随机初始化几乎必然落入泛化差的区域。

### 统计层面：大词汇表天然提供"多样性"

Zhang et al.[^zhang-2022] 解决了一个理论空白：已有多任务预训练理论要求任务数远大于嵌入维度（如 768），但 NLP 预训练通常只有**一个任务**（语言建模）。他们提出**类别多样性**（diversity of classes）——NLP 的语言建模任务有约 30K 个 BPE 类别，远大于嵌入维度，这种类别多样性等价于多任务预训练的效果，单任务预训练就足以学出高质量表示。

### 表示层面：交叉熵目标天然产出可迁移的特征

Saunshi et al.[^saunshi-2021] 从数学上证明：一个在交叉熵目标上 $\epsilon$-最优的语言模型，在下游分类任务上能达到 $\mathcal{O}(\sqrt{\epsilon})$ 的误差。预测下一个词需要理解语法、语义、世界知识——这些理解被压缩进了表示向量，而这些向量对下游任务天然有用。

---

## 4. 与 CNN/RNN 的对比：为什么它们不那么依赖预训练

| 维度 | CNN/RNN | Transformer | 结论 |
|------|---------|-------------|------|
| **归纳偏置** | 强先验约束搜索空间 | 几乎无约束 | Transformer 需要预训练来替代先验 |
| **随机初始化质量** | 先验保证了起点在合理区域 | 起点几乎是随机的 | 预训练提供"好起点" |
| **参数效率** | 共享卷积核 / 循环权重 → 参数少 | 全连接注意力 → 参数多 | 参数多 + 无先验 = 更容易过拟合 |
| **数据需求** | ImageNet (1.3M) 足够训练好的 CNN | 需要 90M+ 才超过 CNN | 预训练弥补了数据需求差距 |
| **上限** | 受先验假设约束 | 理论上无约束 | 预训练 + 大数据释放了 Transformer 的上限 |

CNN 内置的卷积核本质上是一种"免费的预训练"——它提前告诉模型"关注局部特征、平移不变"。Transformer 没有这个免费午餐，必须用真正的预训练来从数据中学出等价甚至更好的先验。

---

## 参考资料

[^vit-2021]: Dosovitskiy et al. *An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale*. ICLR 2021. https://arxiv.org/abs/2010.11929
[^trocr-2021]: Li et al. *TrOCR: Transformer-based Optical Character Recognition with Pre-trained Models*. AAAI 2023. https://arxiv.org/abs/2109.10282
[^erhan-2010]: Erhan et al. *Why Does Unsupervised Pre-training Help Deep Learning?* JMLR 2010. https://www.jmlr.org/papers/v11/erhan10a.html
[^zhang-2022]: Zhang et al. *Pre-training with a Single Task Can Be as Good as Multi-task Pre-training*. 2022. https://arxiv.org/abs/2209.03447
[^saunshi-2021]: Saunshi et al. *A Mathematical Exploration of Why Language Models Help Solve Downstream Tasks*. 2021. https://arxiv.org/abs/2010.03648
