---
title: DeepSeek-V4
description: 首个原生百万 token 上下文的开源 MoE 模型——混合压缩注意力架构将 1M 推理 FLOPs 降至 V3.2 的 27%，KV Cache 缩至 10%。
created: 2026-04-27
updated: 2026-04-27
tags: [deepseek, moe, long-context, sparse-attention, muon, fp4, architecture]
review:
---

> 原文：DeepSeek-AI. *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*. 2026[^deepseek-v4-2026]。本文提炼论文中的核心技术方案与设计权衡。

---

## 核心定位

DeepSeek-V4 系列是 DeepSeek 继 V3 → V3.2 后的**架构换代**——核心目标不是"更大"，而是**在百万 token 上下文下把推理成本打下来**。两个型号：

| 型号 | 总参数 | 活跃参数 | 上下文 | 精度 |
|------|--------|----------|--------|------|
| V4-Flash | 284B | 13B | 1M | FP4+FP8 混合 |
| V4-Pro | 1.6T | 49B | 1M | FP4+FP8 混合 |

**效率跃升**：在 1M token 上下文下，V4-Pro 的单 token 推理 FLOPs 仅为 V3.2 的 **27%**，KV Cache 仅为 **10%**；V4-Flash 更极端——FLOPs 降至 **10%**，KV Cache 降至 **7%**。

---

## 架构创新

V4 保留了 V3 的 DeepSeekMoE + Multi-Token Prediction 框架，引入三项关键升级：

### 1. 混合注意力：CSA + HCA

这是 V4 最核心的架构突破。传统 Attention 在超长序列下 FLOPs 和 KV Cache 都呈二次增长；V4 用两种互补的压缩注意力**交替堆叠**来打破瓶颈：

**Compressed Sparse Attention (CSA)** — 压缩 + 稀疏双管齐下：

1. **Token 级 KV 压缩**：每 $m$ 个 token 的 KV 条目通过可学习的加权求和压缩成 1 个条目（V4-Pro $m=4$），序列长度直接降为 $1/m$
2. **Lightning Indexer 稀疏选择**：对压缩后的 KV 条目，每个 query 只选 top-k 个做注意力（V4-Pro $k=1024$），不做全量注意力
3. **Shared Key-Value MQA**：选出的 KV 条目同时充当 key 和 value，用 Multi-Query Attention 做最终计算
4. **滑动窗口补充**：额外保留最近 $n_\text{win}=128$ 个 token 的原始 KV，维持局部细粒度依赖

**Heavily Compressed Attention (HCA)** — 更激进的压缩 + 密集注意力：

- 压缩率 $m'=128$（CSA 的 32 倍），但对压缩后的 KV 做**密集注意力**（不做稀疏选择）
- 同样附带滑动窗口

**设计权衡**：CSA 和 HCA 交替出现在不同 Transformer 层。CSA 保留更多细节（压缩比低）但靠稀疏省计算；HCA 压缩更狠但保留全局密集注意力。两者互补——CSA 处理需要精细检索的场景，HCA 处理全局语义理解。

### 2. Manifold-Constrained Hyper-Connections (mHC)

**解决的问题**：标准 Hyper-Connections (HC) 能解耦残差宽度与隐层维度，提供额外的缩放轴，但在深层堆叠时频繁出现数值不稳定。

**核心方案**：将残差映射矩阵 $B^l$ 约束到**双随机矩阵流形**（Birkhoff 多面体）上：

- 谱范数 $\|B^l\|_2 \leq 1$，保证残差变换非扩张，前向和反向传播都数值稳定
- 集合 $\mathcal{M}$ 对乘法封闭，深层堆叠不会发散
- 通过 Sinkhorn-Knopp 算法（20 次迭代）将裸参数投影到流形上
- 输入/输出映射用 Sigmoid 约束为非负有界，避免信号抵消

V4 的 mHC 扩展因子 $n_\text{hc}=4$，即残差流宽度是隐层维度的 4 倍。

### 3. Muon 优化器

V4 用 Muon 替代 AdamW 作为大多数模块的优化器（Embedding、预测头、RMSNorm 仍用 AdamW）。

**核心思路**：对梯度动量做**近似正交化**（Newton-Schulz 迭代逼近 $U V^T$），使更新方向更"干净"。

**混合 Newton-Schulz 迭代**：10 步分两阶段——前 8 步用激进系数 $(3.4445, -4.7750, 2.0315)$ 快速收敛，后 2 步切换到 $(2, -1.5, 0.5)$ 精确稳定在奇异值 = 1。

**工程适配**：V4 的注意力架构允许直接在 query/KV 上加 RMSNorm，天然避免注意力 logit 爆炸，因此不需要 QK-Clip 技巧。

---

## 基础设施亮点

### Fine-Grained EP Overlap

**核心洞察**：MoE 层的通信时间 < 计算时间，因此通信延迟可以被完全隐藏。

将 expert 按 wave 拆分调度：当前 wave 计算、下一 wave 传输、已完成 wave 结果发送三路并行。开源为 MegaMoE（DeepGEMM 组件），在 NVIDIA GPU 和华为昇腾 NPU 上验证，通用推理负载 **1.50-1.73x** 加速，RL rollout 等延迟敏感场景最高 **1.96x**。

**带宽阈值**：对 V4-Pro，每 GBps 互联带宽可隐藏 6.1 TFLOP/s 的计算通信。超过此阈值后继续堆带宽收益递减。

### TileLang 内核开发

V4 复杂的模型架构原本会产生数百个细粒度 ATen 算子。采用 TileLang DSL 开发一组 fused kernel 替代绝大多数，兼顾开发效率和运行性能。集成 Z3 SMT solver 做形式化整数分析，解锁向量化、barrier 插入等高级编译优化。

### Batch-Invariant & Deterministic Kernels

端到端保证：**同一 token 不论在 batch 中什么位置，输出 bitwise 一致**。用 DeepGEMM 替代 cuBLAS，放弃 split-K（但通过专项优化追回性能），Attention 反向用独立累加缓冲 + 确定性归约。这对训练 debug、loss spike 分析和 post-training 一致性至关重要。

### FP4 量化感知训练 (QAT)

- MoE expert 权重：FP32 master → FP4 量化 → 无损反量化到 FP8 做计算（FP8 E4M3 的额外指数位完全吸收 FP4 细粒度 scale）
- CSA indexer 的 QK 路径：全链路 FP4 缓存/加载/计算
- Index scores 从 FP32 降到 BF16：top-k 选择器 **2x** 加速，KV 条目召回率 **99.7%**

---

## 训练

### 预训练

| | V4-Flash | V4-Pro |
|---|---|---|
| 训练数据 | 32T tokens | 33T tokens |
| 层数 | 43 | 61 |
| 隐层维度 | 4096 | 7168 |
| Expert 数 | 1 shared + 256 routed, Top-6 | 1 shared + 384 routed, Top-6 |
| 峰值学习率 | 2.7×10⁻⁴ | 2.0×10⁻⁴ |
| 最大 batch size | 75.5M tokens | 94.4M tokens |
| 序列长度调度 | 4K → 16K → 64K → 1M | 4K → 16K → 64K → 1M |

**注意力稀疏引入**：先用密集注意力 warm up（Flash 1T tokens / Pro 更长），再在 64K 序列长度阶段引入稀疏注意力，其中 Lightning Indexer 有独立的短 warm-up 阶段。

**MoE 变化**：前 3 层 MoE 使用 Hash routing（按 token ID 确定性路由），而非可学习 router。激活函数从 Sigmoid 改为 $\sqrt{\text{Softplus}(\cdot)}$。取消了路由目标节点数限制。

**训练稳定性**：

- **Anticipatory Routing**：不用当前 token 的隐层状态做路由，改用**上一时间步**的状态，打破"异常值→路由偏斜→更大异常值"的正反馈环路
- **SwiGLU Clamping**：对 SwiGLU 激活后的值做上界截断，直接压制异常值传播

### Post-Training：先分后合

两阶段范式：

1. **Specialist Training**——分领域独立训练 expert 模型：
    - 每个目标领域（数学、代码、Agent、指令遵循等）独立训练
    - 先 SFT 建立基础能力，再用 GRPO (Group Relative Policy Optimization) 做 RL
    - 产出十余个 domain-specific expert

2. **On-Policy Distillation (OPD)**——合并为统一模型：
    - 学生模型在自身生成的轨迹上优化反向 KL 散度
    - **全词表 logit 蒸馏**（非 token-level KL 估计），梯度更稳定
    - 十余个 teacher 的权重 offload 到分布式存储，按需加载；只缓存最后一层 hidden states，训练时按需重算 logits

**Quick Instruction**：在输入序列末尾附加特殊 token（如 `<|action|>`、`<|query|>`、`<|title|>`），复用已计算的 KV Cache 并行完成搜索判断、intent 识别等辅助任务，省去额外小模型和重复 prefilling。

**Interleaved Thinking**：工具调用场景中**完整保留**跨轮次的推理内容（不再像 V3.2 在新用户消息时丢弃），利用 1M 上下文支撑长周期 Agent 任务的连贯思考链。

---

## 评估亮点

### 与前沿闭源模型对比（V4-Pro-Max）

| 维度 | 关键结果 |
|------|----------|
| 知识 | SimpleQA-Verified 57.9%（开源最佳，超出此前开源 20 个百分点），仍落后 Gemini-3.1-Pro (75.6%) |
| 代码竞赛 | Codeforces Rating 3206（**开源首次匹配闭源**，Codeforces 人类排名第 23），LiveCodeBench 93.5% |
| 数学推理 | HMMT 2026 Feb 95.2%，IMOAnswerBench 89.8%，Apex Shortlist 90.2% |
| 形式化数学 | Putnam-2025 达到 120/120（与 Axiom 并列完美成绩） |
| Agent | SWE-Verified 80.6%（与 Opus 4.6 持平），MCPAtlas 73.6%，Toolathlon 51.8% |
| 1M 长上下文 | MRCR 1M 83.5%（超过 Gemini-3.1-Pro 76.3%，落后 Opus 4.6 92.9%） |

### V4-Flash vs V4-Pro

- **知识任务**：Pro 明显领先（参数量优势，SimpleQA 57.9% vs 34.1%）
- **推理任务**：Flash-Max 在更大 thinking budget 下接近 Pro（HMMT 94.8% vs 95.2%）
- **Agent 任务**：简单任务两者接近，复杂高难度任务 Pro 仍有优势

### Reasoning Effort 模式

三档推理力度：Non-Think（直觉快速）、Think High（逻辑分析）、Think Max（极限推理，建议 384K+ 上下文窗口）。从 Non-Think 到 Max，HLE 从 7.7% 跃升到 37.7%，GPQA Diamond 从 72.9% 跃升到 90.1%。

---

## 设计权衡与局限

1. **架构复杂度**：为追求长上下文极致效率，V4 保留了大量"初步验证有效"的组件和技巧，导致架构相对复杂。团队承认未来需要更系统化地精简到最本质的设计
2. **训练稳定性理解不足**：Anticipatory Routing 和 SwiGLU Clamping 虽有效，但底层原理尚不充分理解
3. **知识瓶颈**：在世界知识评估（SimpleQA、GPQA）上仍落后 Gemini-3.1-Pro，说明参数量和数据质量的天花板尚未突破
4. **未来方向**：更稀疏的 Embedding 模块、低延迟长上下文推理架构、多模态能力、在线学习范式

---

## 与 V3 架构演进对比

| 维度 | DeepSeek-V3 | DeepSeek-V4 |
|------|-------------|-------------|
| 注意力 | MLA (Multi-head Latent Attention) | CSA + HCA 混合压缩注意力 |
| 残差连接 | 标准残差 | mHC（流形约束超连接） |
| 优化器 | AdamW | Muon（主）+ AdamW（辅） |
| Expert 精度 | FP8 | **FP4** + FP8 混合（QAT） |
| 上下文长度 | 128K | **1M**（原生支持） |
| 激活函数 | Sigmoid（路由） | $\sqrt{\text{Softplus}(\cdot)}$ |
| 负载均衡 | 辅助 loss-free 均衡 | 沿用 + 序列级 balance loss |
| 前几层 MoE 路由 | Dense FFN | **Hash routing**（确定性） |
| 1M token 推理 FLOPs | 基线 | **27%**（Pro）/ **10%**（Flash） |

## 参考资料

[^deepseek-v4-2026]: DeepSeek-AI. *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*. 2026. https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/DeepSeek_V4.pdf
