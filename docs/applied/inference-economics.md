---
title: 推理经济性 (Inference Economics)
description: 租公有云 GPU 卖推理是否赚钱？从 GPU 小时成本、模型吞吐、API 定价三个维度拆解推理服务的盈利模型。
created: 2026-04-13
updated: 2026-05-07
tags: [inference, economics, gpu, pricing, cost]
review: 2026-05-07
---

# 推理经济性 (Inference Economics)

> 核心问题：**如果以租借公有云 GPU 为主要运营成本，推理服务能否盈利？**
>
> 结论：取决于架构和运营效率。Dense 大模型（70B+）以常规 TP 部署在 GPU 市场价下亏损；小模型暴利；**MoE 模型 + 大规模 Expert Parallelism 可以实现数倍利润**（DeepSeek 实证：成本利润率 545%）。关键不在于模型大不大，而在于每张 GPU 实际处理多少参数、batch 能做多大。

---

## 1. 分析框架

推理服务的盈亏取决于三个变量的乘积关系：

```
利润/hr = (API 单价 × 有效吞吐) − GPU 租赁成本

其中：
  有效吞吐 = 聚合吞吐(tok/s) × 利用率 × 3600
  聚合吞吐 取决于模型大小、GPU 数量、优化栈
  利用率   取决于流量波动（实际 20%-60%）
```

下面分别量化每个变量。

---

## 2. GPU 租赁成本

### 2.1 超大规模云 vs GPU 市场

GPU 云市场存在明显的两层定价：超大规模云（AWS/Azure/GCP）价格含配套 CPU/RAM/网络/SLA，比 GPU 市场（Lambda/CoreWeave/RunPod）贵 3-5 倍。

| GPU | 超大规模云 ($/hr)[^cloud-pricing-2026] | GPU 市场 ($/hr) | 倍数 |
|-----|---------------------------------------|----------------|------|
| **H100 80GB SXM** | $11 – $12 | $2.0 – $3.3 | ~4x |
| **H200 141GB** | $12 – $14 | $3.0 – $4.0 | ~3.5x |
| **A100 80GB** | $3.7 – $5.1 | $1.1 – $2.2 | ~2.5x |

超大规模云是按实例计费（如 AWS p5.48xlarge = 8×H100，$98.32/hr），上表为折算到单 GPU 的价格。GPU 市场为裸 GPU 租赁，无企业级 SLA。

### 2.2 自有硬件的折算成本

头部厂商（OpenAI、Anthropic、Google）不租卡——它们通过长期预留合同或自建集群获得远低于市场价的算力：

| 方式 | 折算 $/hr/H100 | 与 GPU 市场比 |
|------|-----------------|---------------|
| 3 年预留合同 | ~$1.5 – $2.0 | 0.6x |
| 自有硬件（3 年折旧 + 电力 + 冷却） | ~$0.8 – $1.2 | 0.4x |
| GPU 市场按需 | $2.0 – $3.3 | 1x（基线） |

**这个差距是头部厂商盈利的核心前提。**

---

## 3. 模型吞吐量

吞吐量受模型大小、GPU 数量和优化栈三重影响。以下数据基于 vLLM / TensorRT-LLM 的公开 benchmark[^vllm-benchmark][^trtllm-benchmark]。

### 3.1 典型吞吐（output tokens/s，聚合值）

**常规部署（Tensor Parallelism，单节点内）**：

| 模型规模 | 硬件 | 优化 | 聚合吞吐 |
|----------|------|------|----------|
| 7-20B | 1×H100 | TRT-LLM FP8, batch=64+ | 8,000 – 14,000 tok/s |
| 70B | 4×H100 TP=4 | vLLM, batch=32 | 400 – 800 tok/s |
| 70B | 8×H100 TP=8 | TRT-LLM FP8, batch=128+ | 1,500 – 3,000 tok/s |
| MoE ~600B (激活 ~100B) | 8×H100 | EP+TP | 600 – 1,000 tok/s |

**大规模 Expert Parallelism（DeepSeek 实测）**[^deepseek-inference-2025]：

| 阶段 | 部署规模 | 策略 | 单 GPU 吞吐 |
|------|---------|------|-------------|
| Prefill | 4 节点 32 GPU | EP32 + DP32，每卡 9 个路由专家 | ~73.7K input tok/s |
| Decode | 18 节点 144 GPU | EP144 + DP144，每卡 2 个路由专家 | ~14.8K output tok/s |

DeepSeek 的单 GPU decode 吞吐（14.8K tok/s）是常规 TP=8 部署 MoE 模型的 **15-25 倍**。原因：EP144 下每张 GPU 只放 2 个路由专家（参数极少），batch 可以做到极大，将 decode 从内存带宽瓶颈推向计算效率区。

**关键洞察**：同一个 MoE 模型，用 8 卡 TP 部署和用 144 卡 EP 部署，单 GPU 吞吐差一个数量级以上。**并行策略的选择比模型大小更决定经济性。**

### 3.2 为什么利用率低

LLM decode 阶段是**显存带宽受限**（memory-bound），不是计算受限：

| 指标 | H100 SXM |
|------|----------|
| 显存带宽 | 3.35 TB/s |
| FP16 算力 | 989 TFLOPS |
| Decode 算术强度 | ~1-2 FLOPs/byte |
| 饱和算力所需强度 | ~50+ FLOPs/byte |

结果：decode 时 GPU 计算核心大部分空闲，瓶颈在"读模型权重"上。批处理能摊薄这个成本——batch=1 时每个 token 都要完整读一遍权重，batch=64 时 64 个 token 共享一次权重读取。

生产环境实际利用率：

| 场景 | GPU 利用率 | 原因 |
|------|-----------|------|
| 批处理/离线 | 70-90% | 持续有请求填充 |
| 实时 API | 15-40% | 流量波动，低谷时 GPU 空转 |
| 旗舰模型 API | 10-30% | 用量少、请求零散 |

---

## 4. API 定价现状（2026.4 实时数据）

### 4.1 主流模型定价

以下价格全部来自官网实时抓取[^openai-pricing][^anthropic-pricing][^google-pricing][^together-pricing]。

| 模型 | 输入 ($/M tok) | 输出 ($/M tok) | 档位 |
|------|---------------|---------------|------|
| Claude Opus 4.6 | $5.00 | $25.00 | 顶级推理 |
| GPT-5.4 | $2.50 | $15.00 | 旗舰 |
| Claude Sonnet 4.6 | $3.00 | $15.00 | 旗舰 |
| Gemini 3.1 Pro | $2.00 | $12.00 | 旗舰 |
| GPT-5.4 mini | $0.75 | $4.50 | 中档 |
| Claude Haiku 4.5 | $1.00 | $5.00 | 中档 |
| Gemini 3 Flash | $0.50 | $3.00 | 轻量 |
| GPT-5.4 nano | $0.20 | $1.25 | 轻量 |
| Gemini 3.1 Flash-Lite | $0.25 | $1.50 | 轻量 |
| DeepSeek V3.1 (Together) | $0.60 | $1.70 | 开源 |
| Llama 3.3 70B (Together) | $0.88 | $0.88 | 开源 |

### 4.2 价格崩塌趋势

| 时间 | 旗舰模型 output 价格 | 等效能力 |
|------|----------------------|----------|
| 2023.3 GPT-4 发布 | $60/M | 基线 |
| 2024.5 GPT-4o | $15/M | >GPT-4 |
| 2025.4 GPT-4.1 | $8/M | >>GPT-4 |
| 2026.4 GPT-5.4 | $15/M | >>>GPT-4 |

旗舰模型名义价格两年内跌了 4 倍，但能力提升远超 4 倍——**单位智能的价格在指数级下降**。

开源模型更剧烈：Llama 70B 级 API 已跌至 $0.88/M output，是 GPT-4 发布价的 **1/68**。

### 4.3 隐藏的利润杠杆

| 机制 | 原理 | 节省 |
|------|------|------|
| **Prompt Caching** | 缓存命中时只收 1/10 价格，但边际成本近零 | 输入成本 -90% |
| **Batch API** | 异步处理，允许高利用率调度 | 全价 -50% |
| **Flex Processing** | 低优先级，填充 GPU 空闲时段 | 全价 -50% |

对提供方来说，缓存命中和 Batch/Flex 请求几乎是纯利润——它们填充了原本空闲的 GPU。

---

## 5. 盈亏测算

### 5.1 四个典型场景

以 GPU 市场价（H100 ~$2.50/hr）为成本基准。

#### 场景 A：开源 70B（Llama 3.3 70B）

```
成本：8×H100 = $20/hr
吞吐：2,000 tok/s（TRT-LLM FP8）× 50% 利用率 = 1,000 tok/s
收入：3.6M tok/hr × $0.88/M = $3.17/hr
利润：-$16.83/hr ❌
```

**即使利用率 100% 也亏 $13.66/hr。** 价格战已把 70B 开源模型推到成本线以下。

#### 场景 B：旗舰闭源（Sonnet 4.6 级）

```
成本：8×H100 = $20/hr
吞吐：800 tok/s（MoE ~600B）× 40% 利用率 = 320 tok/s
收入：1.15M tok/hr × $15/M = $17.28/hr
利润：-$2.72/hr（≈打平）
```

利用率达到 ~47% 才能打平。旗舰模型在 GPU 市场价下**勉强盈亏平衡**。

#### 场景 C：顶级推理模型（Opus 级）

```
成本：16×H100 = $40/hr（更大模型）
吞吐：400 tok/s × 30% 利用率 = 120 tok/s
收入：0.43M tok/hr × $25/M = $10.80/hr
利润：-$29.20/hr ❌
```

单价最高但吞吐最低、利用率最差，反而**亏损最严重**。

#### 场景 D：小模型（GPT-5.4 nano / Flash-Lite 级）

```
成本：1×H100 = $2.50/hr
吞吐：8,000 tok/s × 60% 利用率 = 4,800 tok/s
收入：17.28M tok/hr × $1.25/M = $21.60/hr
利润：+$19.10/hr ✅ 毛利率 88%
```

小模型单卡服务、吞吐极高，**即使单价低也能靠量暴利**。

#### 场景 E：MoE + 大规模 EP（DeepSeek V3/R1 实测）

DeepSeek 官方公布了 2025.2.27-28 的 24 小时生产数据[^deepseek-inference-2025]：

```
部署规模：平均 226.75 节点（8×H800），峰值 278 节点
成本：226.75 × 8 GPU × $2/hr × 24h = $87,072/天

产出：
  输入 608B tokens（其中 56.3% 命中 KV Cache 磁盘缓存）
  输出 168B tokens

收入（全按 R1 定价）：
  输入缓存命中：342B × $0.14/M = $47,880
  输入缓存未命中：266B × $0.55/M = $146,300
  输出：168B × $2.19/M = $367,920
  合计：$562,027/天

利润：$562,027 - $87,072 = +$474,955/天 ✅
成本利润率：545%
```

即使考虑到实际收入低于理论值（V3 定价更低、部分免费流量、夜间折扣），利润率仍然极高。

**与场景 A-C 的关键差异**：

| 差异点 | 场景 A-C（常规部署） | 场景 E（DeepSeek EP） |
|--------|---------------------|-----------------------|
| 并行策略 | TP=4-8（单节点内） | EP144（跨 18 节点） |
| 每卡参数量 | 全部权重或 1/8 | 仅 2 个路由专家 |
| 单卡 decode 吞吐 | 200-3,000 tok/s | **14,800 tok/s** |
| KV Cache 缓存 | 无磁盘缓存 | **56.3% 磁盘命中** |
| 利用率管理 | 固定部署 | **昼夜弹性调度**（闲时还给训练） |

### 5.2 盈亏汇总

| 档位 | 代表模型 | output 单价 | 租云卡盈利？ | 关键条件 |
|------|---------|-------------|-------------|----------|
| 小模型 (8-20B) | GPT-5.4 nano | $1.25/M | **暴利 (毛利 ~88%)** | 单卡高吞吐 |
| Dense 70B | Llama 70B | $0.88/M | **亏损** | 价格低于成本线 |
| MoE 大模型 + 大规模 EP | DeepSeek R1 | $2.19/M | **暴利 (利润率 545%)** | EP144 + 磁盘缓存 + 弹性调度 |
| 旗舰闭源（常规部署） | Sonnet 4.6 | $15/M | **勉强打平** | 吞吐低、利用率不稳定 |
| 顶级推理 (dense) | Opus 4.6 | $25/M | **亏损** | 模型太大、吞吐太低 |

---

## 6. 结构性洞察

### 6.1 为什么各家都在出 mini/nano/lite

小模型是推理业务唯一稳赚的产品线。2025-2026 年各家密集发布轻量模型不是偶然：

| 厂商 | 轻量产品线 | output 价格 |
|------|-----------|-------------|
| OpenAI | GPT-5.4 nano | $1.25/M |
| Google | Gemini 3.1 Flash-Lite | $1.50/M |
| Anthropic | Claude Haiku 4.5 | $5.00/M |
| Mistral | Mistral Small | $0.30/M |

这些模型 8-20B 参数，单卡即可跑出 8,000+ tok/s——是旗舰模型吞吐的 10 倍以上。

### 6.2 MoE + 大规模 EP：推理经济性的核心技术决策

MoE 本身只是必要条件——DeepSeek V3 有 671B 总参数、256 个专家、每次激活 8 个（37B）。但真正决定经济性的是**部署时的并行策略**：

| 部署方式 | 每卡负载 | 单卡 decode 吞吐 | 经济性 |
|----------|---------|-----------------|--------|
| TP=8（1 节点） | 全模型 1/8 权重 | 600-1,000 tok/s | 亏损（场景 B） |
| EP144（18 节点） | 仅 2 个路由专家 | **14,800 tok/s** | **暴利（场景 E）** |

为什么 EP 能带来 15 倍吞吐提升[^deepseek-inference-2025]：

1. **每卡参数极少**（2 个专家 ≈ 5B 参数）→ 权重读取快，decode 不再被显存带宽卡死
2. **batch 可以做到极大**（144 路 DP 汇聚的请求分发到每张卡）→ 矩阵乘法效率高
3. **双 batch 流水线**隐藏跨节点通信开销——一个 batch 算的时候，另一个 batch 在传输
4. **Prefill/Decode 分离**——Prefill 用 EP32（计算密集），Decode 用 EP144（带宽敏感），各自最优配置

代价：部署单元从 1 节点变成 18 节点，跨节点通信对网络要求高（InfiniBand），系统复杂度大幅增加（需要三级负载均衡：Prefill LB、Decode LB、Expert-Parallel LB）。

**这意味着同一个模型，推理系统工程的好坏可以导致 15 倍的经济性差异。** 这也解释了为什么 DeepSeek 能以极低的 API 定价实现暴利，而第三方用 vLLM 跑同一个模型却亏钱。

### 6.3 两层 KV Cache 缓存：磁盘缓存 vs 显存级路由

DeepSeek 生产数据显示 **56.3% 的输入 token 命中了 KV Cache 磁盘缓存**[^deepseek-inference-2025]。这意味着过半的 Prefill 计算被完全跳过——对应的 GPU 算力省下来可以服务更多请求。这与 API 层面的 Prompt Caching（用户侧可见的缓存折扣）不同——磁盘缓存是系统层面的优化，用户无感知，但对提供方来说是纯成本节约。

在磁盘缓存之上还有一层更快的优化——**KV Cache 感知路由**（如 NVIDIA Dynamo 的 Radix Tree 路由，详见 [AI 基础设施 §4.5](infrastructure.md)）：将请求路由到 GPU 显存中已持有匹配 KV Cache 的 Worker，连磁盘加载都省掉。

| 层级 | 缓存位置 | 命中成本 | 典型命中率 |
|------|---------|---------|-----------|
| 显存级路由 | GPU HBM | ≈零（直接复用） | 多轮对话 80-95% |
| 磁盘缓存 | SSD/NVMe | 需 PCIe 传输到 GPU | 56.3%（DeepSeek 实测） |
| 无缓存 | — | 完整 Prefill 重算 | — |

**两层可以叠加**：路由层先查显存，未命中再查磁盘，最后才重算。

不过对 DeepSeek 这类 Prefill/Decode 分离架构，显存路由的**边际收益有限**——Prefill 只用 4 节点（EP32），Decode 的 18 节点（EP144）才是成本大头。KV Cache 路由主要省 Prefill 计算，对总成本影响约 10-15%。

相反，对**不做 Prefill/Decode 分离的架构**（多数闭源厂商的现状），KV Cache 路由的价值更大——Prefill 和 Decode 共享 GPU，省掉 Prefill 计算直接释放给 Decode，TTFT 降 2x、SLA 违约减 80%（Dynamo 报告数据）。

---

## 7. 对从业者的启示

| 角色 | 结论 |
|------|------|
| **想做推理服务的创业者** | Dense 大模型租卡不赚钱；MoE + 大规模 EP 可以盈利但系统工程门槛极高；小模型是最稳的利润来源 |
| **使用 API 的开发者** | 善用 Prompt Caching 和 Batch API，选择合适档位的模型（大部分任务 mini/nano 足够） |
| **企业自建推理** | 自有硬件折算成本约 $0.8-1.2/hr/H100，比 API 调用便宜一个量级，但需要工程团队维护推理栈 |
| **模型架构设计者** | MoE 不只是训练效率的选择，更是推理经济性的决定性因素——专家数量越多、激活比例越低，EP 带来的吞吐倍增越大 |

---

## 参考资料

[^cloud-pricing-2026]: 超大规模云价格按实例折算（AWS p5.48xlarge $98.32/hr ÷ 8 GPU）；GPU 市场价参考 Lambda Labs、CoreWeave、RunPod 官网。截至 2026 年 4 月。
[^vllm-benchmark]: vLLM Project. Benchmark results. https://github.com/vllm-project/vllm
[^trtllm-benchmark]: NVIDIA. TensorRT-LLM Performance. https://github.com/NVIDIA/TensorRT-LLM
[^openai-pricing]: OpenAI. API Pricing. https://openai.com/api/pricing/ （GPT-5.4 系列，2026.4 抓取）
[^anthropic-pricing]: Anthropic. Models. https://docs.anthropic.com/en/docs/about-claude/models （Claude 4.6 系列，2026.4 抓取）
[^google-pricing]: Google. Gemini API Pricing. https://ai.google.dev/pricing （Gemini 3.x 系列，2026.4 抓取）
[^together-pricing]: Together AI. Pricing. https://www.together.ai/pricing （开源模型 API，2026.4 抓取）
[^deepseek-inference-2025]: DeepSeek. *DeepSeek-V3 / R1 推理系统概览*. 2025.3. https://zhuanlan.zhihu.com/p/27181462601 （含 2025.2.27-28 生产统计数据、EP 架构、负载均衡策略）
