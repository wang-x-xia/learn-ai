---
title: "扩散模型 (Diffusion Models)"
description: "扩散模型原理——DDPM、Latent Diffusion、DiT 与 Flow Matching。"
created: 2026-04-28
updated: 2026-05-06
tags: [diffusion, latent-diffusion, dit, flow-matching]
review: 2026-04-29
review_note: review 了 DDPM 部分（第1章），修正了前向过程命名，重写了章节结构，添加了 DDIM
---

# 扩散模型 (Diffusion Models)

> 扩散模型是当前图像、视频、音频生成的主流技术路线。本文档聚焦其核心原理和关键改进。
>
> 相关文档：[多模态 AI](./multimodal-ai.md) | [Transformer 架构](./transformer.md)

---

## 1. DDPM (Denoising Diffusion Probabilistic Models)

DDPM 是扩散模型的基础架构，通过学习去噪来生成图像。

### 1.1 核心思想

**学习去噪**：从纯噪声逐步还原成清晰信号。DDPM 将这个过程形式化为一个前向加噪、反向去噪的概率模型。[^ho-2020-ddpm]

**两阶段过程**：

```
前向（构建训练数据）：
  清晰图 x₀ → 加一点噪声 → x₁ → 加噪声 → x₂ → ... → x_T (纯噪声)

反向（训练模型）：
  纯噪声 x_T → 去一点噪声 → x_{T-1} → 去噪声 → ... → x₀ (生成图)
```

> 注：上图是概念性展示。实际训练时使用重参数化技巧，从 $x_0$ 一步计算得到任意 $x_t$，无需逐步迭代。

**直觉类比**：
- 前向过程：像"毁掉"一张图，一步步加噪声直到完全模糊
- 反向过程：训练神经网络学会"修复"，从模糊图猜原图长什么样
- 生成时从纯噪声开始，一步步"修复"成清晰图

### 1.2 推理流程（从纯噪声生成）

从纯噪声 $x_T$ 开始，每步去噪后重新添加噪声（用 $\sigma_t$），保持扩散过程的随机性，逐步得到 $x_{T-1}, x_{T-2}, ..., x_0$（生成图）。

**$\sigma_t$ 的作用**：
- 重新添加噪声的标准差参数，通常 $\sigma_t = \sqrt{\beta_t}$
- 保持扩散过程的随机性，避免推理过程完全确定性
- 确保生成的样本具有多样性

### 1.3 DDPM 的局限性

- 采样速度慢：需要多步去噪（通常 1000 步）
- 在像素空间扩散：计算量大，高分辨率图像生成困难

---

## 2. 关键改进

### 2.1 DDIM (Denoising Diffusion Implicit Models)

通过修改推理过程实现加速，可以用更少的步数达到类似质量。[^song-2020-ddim]

**核心改进**：
- DDPM 需要 1000 步采样，DDIM 可以用 50 步达到类似质量
- 实现非马尔可夫采样，跳过中间步骤
- 推理过程可以是确定性的（可设置），便于一致性和可控性

**与 Flow Matching 的关联**：
- 两者都致力于解决 DDPM 采样速度慢的问题
- DDIM 通过修改离散扩散模型的推理过程来实现加速
- Flow Matching 通过学习连续向量场来实现更高效的采样
- DDPM → DDIM → Flow Matching 是扩散模型从离散到连续的演进路径；如果想先建立一条完整主线，可以配合综述型讲解视频一起看。[^youtube-2024-diffusion]

### 2.2 Latent Diffusion

在 VAE 潜空间而非像素空间做扩散，计算量降低数十倍。[^rombach-2022-ldm]

```
图像 → VAE 编码器 → 潜空间向量（压缩 30-50 倍）→ 扩散模型
潜空间向量 → VAE 解码器 → 图像
```

**优势**：
- 潜空间维度小，计算量大幅降低
- 保留语义信息，生成质量更高

### 2.3 DiT (Diffusion Transformer)

用 Transformer 替代 UNet 作为去噪骨干，更好地 scale——Sora 的核心架构。[^peebles-2023-dit]

**优势**：
- Transformer 的 scaling law 适用，参数量增加效果持续提升
- 全局注意力，长距离依赖建模更好

### 2.4 Flow Matching

学习一个随时间变化的向量场（time varying vector field），实现从噪声到数据的连续变换。

**核心概念**：
- **向量场 v_t(x)**：在时刻 t，位置 x 的粒子应该往哪个方向移动
- **随时间变化**：同一个位置在不同时刻的向量可能不同
- **连续变换**：通过沿着向量场积分，从噪声逐步"流"到数据

**与 DDPM 的区别**：
- DDPM：离散的逐步去噪，每步有固定的噪声调度
- Flow Matching：连续的向量场，学习平滑变换路径

**优势**：
- 采样步数更少，速度更快
- 更稳定的训练过程

---

## 3. 应用场景

| 模态 | 代表模型 | 特点 |
|------|----------|------|
| 图像 | Stable Diffusion, DALL-E 3 | Latent Diffusion 主流 |
| 视频 | Sora, Runway Gen-3 | 3D patch + 时间一致性 |
| 音频 | AudioLDM, MusicGen | 在频谱或潜空间扩散 |

**视频生成的特殊挑战**：

| 挑战 | 具体问题 | 图像生成无此问题 |
|------|----------|-----------------|
| 帧间一致性 | 同一个人不能变脸、物体不能突然消失 | 单帧无时间维度 |
| 物理合理 | 重力、碰撞、流体运动要符合物理规律 | 静态图像无物理约束 |
| 镜头运动平滑 | 相机运动不能抖动、跳变 | 无相机运动 |

**技术手段**：
- **3D 注意力**：空间+时间联合 attention（Sora 的做法）。将视频切成时空立方体（如 2 帧×16×16），一次编码空间+时间
- **Temporal super-resolution**：先生成低帧率（如 8fps），再插帧到高帧率（24fps/30fps）
- **运动先验**：利用光流（optical flow）等运动信息指导生成，保证运动连贯

**核心差异**：
- 图像生成：2D 空间去噪，关注单帧质量
- 视频生成：3D 时空去噪，关注帧间连贯性和物理合理性

---

## 4. 与自回归对比

| 维度 | 扩散模型 | 自回归（GPT） |
|------|----------|---------------|
| 生成方式 | 整体去噪，并行处理 | 逐 token 顺序生成 |
| 适用模态 | 图像/音频/视频（连续） | 文本（离散） |
| 采样速度 | 慢（需要多步去噪） | 慢（需要顺序生成） |
| 质量控制 | 通过条件引导（文本、图像等） | 通过 prompt 引导 |

**为什么图像不用自回归？**
- 图像像素太多（224×224×3 = 15万），逐像素预测太慢
- 连续空间的自回归效果不如扩散

**为什么文本不用扩散？**
- 文本天然离散，自回归更合适
- 扩散模型在离散空间效果不好

---

## 参考资料

[^youtube-2024-diffusion]: *Diffusion Models | From DDPM to Flow Matching*. 2024. https://www.youtube.com/watch?v=iv-5mZ_9CPY

[^ho-2020-ddpm]: Ho et al. *Denoising Diffusion Probabilistic Models*. 2020. https://arxiv.org/abs/2006.11239

[^song-2020-ddim]: Song et al. *Denoising Diffusion Implicit Models*. 2020. https://arxiv.org/abs/2010.02502

[^rombach-2022-ldm]: Rombach et al. *High-Resolution Image Synthesis with Latent Diffusion Models*. 2022. https://arxiv.org/abs/2112.10752

[^peebles-2023-dit]: Peebles & Xie. *Scalable Diffusion Models with Transformers*. 2023. https://arxiv.org/abs/2212.09748
