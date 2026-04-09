---
title: "Transformer 架构"
description: "Transformer 架构深度解析——自注意力机制、前馈网络与 MoE。"
created: 2026-04-08
updated: 2026-04-09
tags: [transformer, attention, moe]
review:
---

# Transformer 架构

> Transformer 是当前几乎所有前沿语言模型的底层架构。本文档聚焦其核心机制的技术原理和设计权衡，不涉及具体模型。
>
> 相关文档：[KV Cache 与推理优化](./kv-cache.md) | [Mamba 与状态空间模型](./mamba-and-ssm.md) | [大语言模型概览](./large-language-models.md)

???+ tip "推荐视频：3Blue1Brown 直观讲解 Transformer"

    <div class="video-wrapper">
      <iframe src="https://www.youtube.com/embed/wjZofJX0v4M" title="3Blue1Brown - Attention in Transformers, visually explained" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
    </div>

---

## 1. 架构原理

Transformer 由 Vaswani 等人在 2017 年提出[^vaswani-2017]，用**纯注意力机制**替代了 RNN 的循环结构。

``` mermaid
graph TB
    Input["输入 Tokens"] --> Emb["Token Embedding\n+ 位置编码"]
    Emb --> Block

    subgraph Block ["Transformer Block × N"]
        direction TB
        Attn["Multi-Head\nSelf-Attention"]
        Attn --> AN1["Add & Norm"]
        AN1 --> FFN["前馈网络\n(FFN / MoE)"]
        FFN --> AN2["Add & Norm"]
    end

    Block --> Out["输出概率分布\n(Softmax)"]
```

每个 Transformer Block 重复堆叠 N 次（GPT-3 有 96 层，Llama-3-70B 有 80 层）。一个 Block 内部的完整流程：

```
输入 x
  │
  ├──→ Self-Attention(x) ──→ + ──→ Norm ──→ y     ① 交流：token 之间交换信息
  │                          ↑
  └──────────────────────────┘  （残差连接：把原始输入加回来，防止信息丢失）
                                   
  ├──→ FFN(y) ──→ + ──→ Norm ──→ 输出               ② 思考：每个 token 独立做非线性变换
  │               ↑
  └───────────────┘  （残差连接）
```

- **Self-Attention**：每个 token 从其他 token 收集相关信息（"交流"阶段）。输出和输入维度相同，比如 `(4×128)` 进 `(4×128)` 出
- **Add & Norm**：把 Attention 的输出和原始输入相加（残差连接），再做归一化。残差连接保证信息不会在深层网络中丢失
- **FFN**：对每个 token 的向量独立做非线性变换（"思考"阶段）。这是模型存储知识的主要位置——研究表明事实知识主要记忆在 FFN 的权重里

**为什么要堆叠很多层？** 每一层都在上一层的基础上进一步精炼表示。浅层捕获简单模式（词性、局部搭配），深层捕获复杂模式（语义、长距离依赖、推理链条）。类似人的理解过程——先看懂字面意思，再理解言外之意。

经过所有 Block 后，每个位置的向量都融合了上下文信息。最终每个位置预测"下一个 token 是什么"：

```
输入:   我    喜欢    吃    苹果
         ↓      ↓     ↓      ↓
       ┌──── Transformer Blocks × N ────┐
         ↓      ↓     ↓      ↓
预测:   喜欢    吃    苹果    。
```

训练时所有位置同时算 loss；推理时只看最后一个位置的输出，采样出下一个 token，追加到序列末尾，重复这个过程——这就是**自回归生成**。

---

## 2. 自注意力机制

一个 Transformer Block 里有很多个 Attention 单元（称为"头"），每个头负责捕获一种小的统计模式——比如"动词后面的名词要关注"、"相隔 5 个词的两个代词经常相关"。单个头学到的模式人类往往看不懂，但几十个头组合起来，就涌现出了对语言的整体理解。

每个头做的事情可以用一句话概括：**对序列中的每个 token，根据它与其他 token 的相关度做加权求和，得到一个融合了上下文信息的新表示。**

用一个简化的例子来理解——假设某个头学会了"通过动词判断名词含义"：

``` mermaid
graph LR
    subgraph s1 ["「我 喜欢 吃 苹果」"]
        我 -.-|低| apple1["苹果 → 水果"]
        喜欢 -.-|低| apple1
        吃 ===|高| apple1
    end

    subgraph s2 ["「苹果 发布 了 新手机」"]
        发布 ===|高| apple2["苹果 → 公司"]
        了 -.-|低| apple2
        新手机 ===|高| apple2
    end
```

具体来说，每个 token 的 embedding 经过三个不同的线性投影（即乘以三个学习到的权重矩阵 W_Q、W_K、W_V），得到三个向量：

- **Query（Q）**：「我在找什么？」—— 当前 token 发出的查询，表达它需要从上下文中获取什么信息
- **Key（K）**：「我是什么？」—— 每个 token 的标签，用于被其他 token 的 Query 匹配
- **Value（V）**：「我能提供什么？」—— 匹配成功后实际传递的信息内容

Q 和 K 的点积衡量两个 token 的相关度（匹配分数），经 softmax 归一化后作为权重，对 V 做加权求和：

```
Attention(Q, K, V) = softmax(Q · Kᵀ / √d_k) · V
```

以「我 喜欢 吃 苹果」（4 个 token，假设 d_k=128）为例，各矩阵的大小：

```
Q:  (4×128)                — 4 个 token，每个一条 128 维的 Query 向量
Kᵀ: (128×4)                — K 转置后，列数 = token 数

Q · Kᵀ = (4×4)             — 4×4 方阵，每个位置是两个 token 的匹配分数
                              ┌─────────────────────────────┐
                              │     我   喜欢   吃   苹果   │
                              │ 我  [0.30 0.30  0.25 0.15]  │
                              │ 喜欢[0.20 0.10  0.40 0.30]  │
                              │ 吃  [0.05 0.05  0.10 0.80]  │
                              │ 苹果[0.05 0.10  0.65 0.20]  │
                              └─────────────────────────────┘
                              ↑ softmax 归一化后的注意力权重（每行和为 1）

V:  (4×128)                — 4 个 token 的 Value 向量
输出: (4×4) · (4×128) = (4×128) — 每个 token 得到一条新的 128 维向量
```

从右往左拆解这个公式的每一步：

| 步骤 | 运算 | 做了什么 | 例子 |
|------|------|----------|------|
| 1 | `Q · Kᵀ` | 每个 token 的 Q 和所有 token 的 K 做点积，得到原始匹配分数 | "苹果"的 Q 和"吃"的 K 点积 = 7.4，和"我"的 K 点积 = 0.6 |
| 2 | `/ √d_k` | 除以维度的平方根，把分数缩小到合理范围 | 7.4 → 0.65，0.6 → 0.05（假设 d_k=128，√128≈11.3） |
| 3 | `softmax(...)` | 把所有分数归一化成概率（和为 1），变成注意力权重 | [0.05, 0.10, **0.65**, 0.20] → "吃"权重最高 |
| 4 | `· V` | 用这些权重对所有 token 的 V 做加权求和，得到最终输出 | 输出 = 0.05·V~我~ + 0.10·V~喜欢~ + 0.65·V~吃~ + 0.20·V~苹果~ |

最终，"苹果"这个 token 的新表示主要包含了"吃"的语义信息——模型因此理解这里的"苹果"是水果。

类比搜索引擎：你输入一个搜索词（Query），它和每个网页的标题（Key）算匹配度，然后按匹配度加权返回网页内容（Value）。区别在于 Q/K/V 都是从同一个输入学出来的，模型自己决定"问什么"和"答什么"。

除以 `√d_k` 是为了防止点积过大导致 softmax 退化成 one-hot。**Multi-Head Attention (MHA)** 将 Q/K/V 拆分成多个头并行计算，最后拼接输出。为减少推理时的 KV Cache 内存，后续出现了 GQA（分组共享 KV 头）和 MLA（低秩 KV 压缩）等变体，详见 [KV Cache 与推理优化](./kv-cache.md)。

---

## 3. 前馈网络与 MoE

### 前馈网络（FFN）

前馈网络是最基础的神经网络结构——输入向量乘以权重矩阵，过一个非线性激活函数，再投影回来：

```
FFN(x) = 激活函数(x · W₁ + b₁) · W₂ + b₂
```

"前馈"的意思是数据单向从输入流向输出，没有循环、没有回头看。在 Transformer 里，Attention 负责 token 之间"交流"（你和谁相关），FFN 负责每个 token 独立地"思考"（对收集到的信息做非线性变换）。研究发现模型记住的事实知识（比如"巴黎是法国首都"）主要存储在 FFN 的权重矩阵里。

### MoE：稀疏激活的参数扩展

Mixture of Experts 是 FFN 层的一种替换策略：与其用一个大 FFN，不如用很多个小 FFN（Expert），每次只激活其中几个：

```
标准 FFN:   x → FFN(x)
MoE FFN:    x → Router(x) → 选择 Top-K Expert → Σ(gate_i · Expert_i(x))
```

| 模型 | 总参数 | 活跃参数 | Expert 数 | Router 策略 |
|------|--------|----------|-----------|-------------|
| Mixtral 8x7B | 46.7B | 12.9B | 8, Top-2 | Token-choice |
| DeepSeek-V3 | 671B | 37B | 256, Top-8 | 辅助 loss-free 均衡 |
| Qwen2.5-MoE | 14.3B | 2.7B | 60, Top-4+4 shared | Fine-grained |

**MoE 的关键工程挑战**：

1. **负载均衡**：如果 Router 总选同几个 Expert，其他 Expert 白训练。传统方案加辅助 loss 强制均衡，但这个 loss 会干扰主任务。DeepSeek-V3 提出 **loss-free 均衡**——用动态偏置调节 Router 分数，不引入额外 loss
2. **Expert 并行**：256 个 Expert 不可能放在一张卡上，需要跨设备调度。通信开销是瓶颈
3. **Token 丢弃**：当某个 Expert 过载时需要丢弃 token，影响质量

---

## 参考资料

[^vaswani-2017]: Vaswani et al. *Attention Is All You Need*. 2017. https://arxiv.org/abs/1706.03762
