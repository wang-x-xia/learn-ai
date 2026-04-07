# AI 基础设施 (AI Infrastructure)

> 从硬件加速器到推理优化，AI 基础设施决定了大模型能否高效训练和部署。本文档梳理当前 AI 基础设施的核心技术栈。

---

## 1. 概述

### AI 基础设施全栈

```
┌──────────────────────────────────────┐
│           应用层 (Applications)       │
│    ChatGPT, Claude, Gemini, Agent    │
├──────────────────────────────────────┤
│         框架层 (Frameworks)           │
│    PyTorch, JAX, Transformers        │
├──────────────────────────────────────┤
│        优化层 (Optimization)          │
│   vLLM, TensorRT, Flash Attention    │
├──────────────────────────────────────┤
│       编排层 (Orchestration)          │
│    Kubernetes, Ray, DeepSpeed        │
├──────────────────────────────────────┤
│        硬件层 (Hardware)              │
│   NVIDIA GPU, Google TPU, AMD MI     │
└──────────────────────────────────────┘
```

---

## 2. 硬件加速

### 2.1 NVIDIA GPU

| GPU | 架构 | HBM | 显存带宽 | FP16 算力 | 特点 |
|-----|------|-----|----------|-----------|------|
| **H100 SXM** | Hopper | 80GB HBM3 | 3.35 TB/s | 989 TFLOPS | 当前主力训练卡 |
| **H200** | Hopper | 141GB HBM3e | 4.8 TB/s | 989 TFLOPS | H100 加大显存版 |
| **B100** | Blackwell | 192GB HBM3e | 8 TB/s | ~1800 TFLOPS | 新一代架构 |
| **B200** | Blackwell | 192GB HBM3e | 8 TB/s | ~2250 TFLOPS | Blackwell 旗舰 |
| **GB200** | Blackwell | 384GB (双芯) | 16 TB/s | ~4500 TFLOPS | Grace CPU + 2×B200 |
| **RTX 4090** | Ada | 24GB GDDR6X | 1 TB/s | 330 TFLOPS | 消费级推理 |
| **RTX 5090** | Blackwell | 32GB GDDR7 | 1.8 TB/s | - | 消费级新旗舰 |

**关键洞察**: 显存带宽是 LLM 推理的主要瓶颈（内存带宽受限 / memory-bound），而非计算能力。

### 2.2 AMD GPU

| GPU | 显存 | 特点 |
|-----|------|------|
| **MI300X** | 192GB HBM3 | 性价比高，生态逐步完善 |
| **MI350** | 288GB HBM3e | 下一代产品 |

### 2.3 Google TPU

| TPU | 特点 |
|-----|------|
| **TPU v5e** | 成本优化版，适合推理和中小规模训练 |
| **TPU v6e (Trillium)** | 最新一代，性能大幅提升 |

TPU 是 Gemini、PaLM 等 Google 模型的训练基础。

### 2.4 其他加速器

| 加速器 | 厂商 | 特点 |
|--------|------|------|
| **Groq LPU** | Groq | 确定性推理，极低延迟 |
| **Cerebras CS-3** | Cerebras | 晶圆级芯片，超大模型直接放入 |
| **Apple Silicon** | Apple | M 系列芯片统一内存，本地推理 |
| **Gaudi 3** | Intel | Habana Labs 加速器 |

---

## 3. 模型训练基础设施

### 3.1 分布式训练策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **数据并行 (DP)** | 每个 GPU 复制完整模型，分配不同数据 | 模型能放入单卡 |
| **张量并行 (TP)** | 将单个算子/层分割到多卡 | 单层参数过大 |
| **流水线并行 (PP)** | 将不同层分配到不同卡 | 层数多的模型 |
| **Expert 并行 (EP)** | MoE 模型中不同专家分配到不同卡 | MoE 模型 |
| **ZeRO** | 分片优化器状态/梯度/参数 | 大模型通用 |

### 3.2 训练框架

| 框架 | 厂商 | 特点 |
|------|------|------|
| **DeepSpeed** | Microsoft | ZeRO 优化，广泛使用 |
| **Megatron-LM** | NVIDIA | 3D 并行，大规模训练 |
| **FSDP** | PyTorch | 原生全分片数据并行 |
| **Alpa** | 研究项目 | 自动并行化 |
| **Colossal-AI** | HPC-AI Tech | 大模型训练套件 |

### 3.3 训练集群网络

```
GPU 间通信层级：
  同卡内: NVLink (900 GB/s, 4th gen)
  同节点: NVSwitch (全互连)
  跨节点: InfiniBand (400 Gbps, NDR)
  跨集群: RoCE / 以太网
```

### 3.4 Flash Attention

[Flash Attention (Dao et al., 2022)](https://arxiv.org/abs/2205.14135) 是现代 LLM 训练的基础优化：

- IO 感知的精确注意力计算
- 减少 HBM 访问次数
- 节省 2-4 倍显存
- 加速 1.5-3 倍
- Flash Attention 3: 进一步优化，利用 Hopper 架构特性

---

## 4. 模型推理与部署

### 4.1 推理优化技术

| 技术 | 说明 | 加速效果 |
|------|------|----------|
| **KV-Cache** | 缓存历史 key/value，避免重复计算 | 必须有 |
| **Continuous Batching** | 动态批处理，不等最长请求 | 2-5x 吞吐 |
| **PagedAttention** | 虚拟内存管理 KV-Cache | 减少显存碎片 |
| **Speculative Decoding** | 小模型预测+大模型验证 | 2-3x 加速 |
| **Prefix Caching** | 缓存共享前缀的 KV-Cache | 减少延迟 |
| **Chunked Prefill** | 分块处理长输入 | 减少首 token 延迟 |

### 4.2 推理框架

| 框架 | 厂商 | 特点 | 适用场景 |
|------|------|------|----------|
| **vLLM** | UC Berkeley | PagedAttention，高吞吐 | 生产级推理服务 |
| **TGI** | Hugging Face | 简单易用，容器化 | 快速部署 |
| **TensorRT-LLM** | NVIDIA | 深度优化 NVIDIA 硬件 | 最高性能 |
| **Ollama** | Ollama | 一键本地运行 | 开发/个人使用 |
| **llama.cpp** | ggerganov | 纯 CPU 推理，GGUF 格式 | CPU/边缘设备 |
| **SGLang** | LMSYS | 结构化生成优化 | 结构化输出 |
| **MLC-LLM** | CMU | 跨平台优化 | 移动端/浏览器 |

### 4.3 vLLM 示例

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    tensor_parallel_size=2,  # 双卡张量并行
    gpu_memory_utilization=0.9,
)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
)

outputs = llm.generate(["什么是人工智能？"], sampling_params)
```

### 4.4 Ollama 快速上手

```bash
# 安装并运行模型
ollama run llama3.1

# API 调用
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "什么是机器学习？"
}'
```

---

## 5. 模型压缩与量化

### 5.1 量化方法

| 方法 | 精度 | 工具 | 特点 |
|------|------|------|------|
| **GPTQ** | INT4/INT8 | AutoGPTQ | 训练后量化，广泛支持 |
| **AWQ** | INT4 | AutoAWQ | 激活感知量化，效果好 |
| **GGUF** | Q2-Q8 | llama.cpp | CPU 友好，灵活精度 |
| **bitsandbytes** | INT4/INT8 | Hugging Face | 集成好，QLoRA 基础 |
| **FP8** | FP8 | TensorRT-LLM | Hopper+架构原生支持 |
| **SmoothQuant** | INT8 | - | 平滑激活分布 |

### 5.2 量化对性能的影响

```
FP16 (基线)  ████████████████████ 100% 质量, 100% 显存
INT8         ███████████████████░  98% 质量,  50% 显存
INT4 (GPTQ)  ██████████████████░░  95% 质量,  25% 显存
INT4 (AWQ)   ███████████████████░  96% 质量,  25% 显存
Q4_K_M       ██████████████████░░  94% 质量,  25% 显存
```

### 5.3 知识蒸馏 (Knowledge Distillation)

用大模型（教师）训练小模型（学生）：

```
教师模型 (GPT-5) → 生成高质量数据/软标签
                          ↓
学生模型 (小模型) → 学习教师的输出分布
```

代表案例：
- DeepSeek-R1 → 蒸馏为 1.5B-70B 多种规格
- Gemma 4 受益于 Gemini 的知识蒸馏

### 5.4 剪枝 (Pruning)

移除模型中不重要的参数：
- **非结构化剪枝**: 移除单个权重
- **结构化剪枝**: 移除整个头/层/通道
- **SparseGPT**: 大模型的高效一次性剪枝

---

## 6. 云平台与 MLOps

### 6.1 云 AI 平台

| 平台 | 厂商 | 特点 |
|------|------|------|
| **Amazon Bedrock** | AWS | 多模型统一 API，无服务器 |
| **Amazon SageMaker** | AWS | 全流程 ML 平台 |
| **Vertex AI** | Google Cloud | Gemini 生态，AutoML |
| **Azure OpenAI Service** | Microsoft | GPT 系列独家云托管 |
| **Azure AI Foundry** | Microsoft | AI 应用构建平台 |
| **Microsoft Foundry** | Microsoft | Anthropic Claude 接入 |
| **阿里云百炼** | 阿里 | 通义千问生态 |
| **火山引擎** | 字节跳动 | 豆包模型平台 |

### 6.2 MLOps 工具

| 工具 | 用途 |
|------|------|
| **MLflow** | 实验追踪、模型注册、部署 |
| **Weights & Biases** | 实验追踪、可视化 |
| **Neptune** | 实验追踪 |
| **BentoML** | 模型服务化 |
| **Seldon** | 模型部署和监控 |
| **KubeFlow** | Kubernetes 上的 ML 流水线 |

### 6.3 模型注册与版本

```
模型版本管理:
  v1.0 (基础模型)
    └── v1.1 (LoRA 微调 - 客服场景)
    └── v1.2 (LoRA 微调 - 代码场景)
  v2.0 (全量微调)
    └── v2.1 (DPO 对齐)
```

---

## 7. 开发工具生态

### 7.1 Hugging Face 生态

```
Hugging Face 生态系统
├── Hub: 模型/数据集/Spaces 托管 (100万+模型)
├── Transformers: 模型加载和推理
├── PEFT: 参数高效微调
├── TRL: 对齐训练 (RLHF/DPO)
├── Datasets: 数据处理
├── Accelerate: 分布式训练
├── Evaluate: 评估指标
├── TGI: 推理服务
├── Diffusers: 扩散模型
└── Gradio: 快速搭建 Demo
```

### 7.2 PyTorch vs JAX

| 维度 | PyTorch | JAX |
|------|---------|-----|
| 开发者 | Meta | Google |
| 编程范式 | 命令式 (eager) | 函数式 (functional) |
| 调试 | 更容易 | 相对困难 |
| 生态 | 最丰富 | 快速增长 |
| 编译优化 | torch.compile | XLA (原生) |
| 分布式 | DDP/FSDP | pjit/xmap |
| 主要用户 | 大多数开源模型 | Google/DeepMind |

### 7.3 ONNX

ONNX (Open Neural Network Exchange) 提供模型格式标准化：
- 跨框架模型转换
- 硬件无关的优化
- ONNX Runtime 提供高效推理

---

## 8. 成本优化

### 8.1 GPU 定价参考 (云)

| GPU | 按需价格 (≈$/hr) | 预留价格 | 适用 |
|-----|-------------------|----------|------|
| H100 SXM | $3-4 | $1.5-2 | 训练 |
| A100 80GB | $2-3 | $1-1.5 | 训练/推理 |
| L4 | $0.5-0.8 | $0.3-0.5 | 推理 |
| T4 | $0.3-0.5 | $0.2-0.3 | 轻量推理 |

*价格因云厂商和地区而异*

### 8.2 成本优化策略

| 策略 | 说明 | 节省比例 |
|------|------|----------|
| **Spot/抢占式实例** | 使用闲置 GPU 资源 | 60-80% |
| **量化推理** | INT4/INT8 减少 GPU 需求 | 50-75% |
| **模型蒸馏** | 用小模型替代大模型 | 70-90% |
| **批处理** | 合并请求提高吞吐 | 30-50% |
| **缓存** | 缓存常见查询结果 | 20-40% |
| **Auto-scaling** | 按需扩缩容 | 30-50% |
| **混合部署** | 高峰用云+基线用自有GPU | 20-40% |

### 8.3 Serverless 推理

| 平台 | 特点 |
|------|------|
| **AWS Lambda + SageMaker** | 按调用计费 |
| **Google Cloud Functions** | 轻量推理 |
| **Modal** | 专为 ML 设计的 serverless |
| **Replicate** | 一键部署开源模型 |
| **Together AI** | 开源模型推理 API |

---

## 9. 发展趋势

### 9.1 定制芯片竞赛

- NVIDIA 持续主导 (H100→B100→B200)
- AMD 追赶 (MI300X→MI350)
- Google TPU 在自家生态中深耕
- 创业公司 (Groq, Cerebras) 找差异化路线
- 大厂自研芯片 (Amazon Trainium, Microsoft Maia)

### 9.2 边缘 AI / 端侧推理

- Apple Intelligence (M 系列芯片 + 小模型)
- Google Gemini Nano (手机端运行)
- Qualcomm AI Engine
- 小模型+量化 = 手机/笔记本上运行 LLM

### 9.3 能效与可持续性

- LLM 训练的碳排放问题
- 更高效的硬件和算法
- 绿色数据中心
- 推理优化减少能耗

### 9.4 推理时计算扩展

- 推理时投入更多计算获得更好结果
- 推理基础设施变得更重要
- 动态计算分配 (简单问题少算，复杂问题多算)

### 9.5 AI 基础设施民主化

- Ollama / llama.cpp 让个人可以运行 LLM
- 更便宜的 GPU 云服务
- 开源推理框架降低门槛
- 模型量化让消费级硬件可用

---

## 参考资料

- Dao et al., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness", 2022 - [arXiv:2205.14135](https://arxiv.org/abs/2205.14135)
- Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention" (vLLM), 2023 - [arXiv:2309.06180](https://arxiv.org/abs/2309.06180)
- Rajbhandari et al., "ZeRO: Memory Optimizations Toward Training Trillion Parameter Models" (DeepSpeed), 2019 - [arXiv:1910.02054](https://arxiv.org/abs/1910.02054)
- Frantar et al., "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers", 2022 - [arXiv:2210.17323](https://arxiv.org/abs/2210.17323)
- vLLM: https://github.com/vllm-project/vllm
- Ollama: https://ollama.com/
