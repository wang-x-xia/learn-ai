---
title: "微调与对齐 (Fine-tuning & Alignment)"
description: "微调让通用模型适配特定任务，对齐确保模型行为符合人类价值观。这是从预训练到可用产品的关键环节。"
created: 2026-04-07
updated: 2026-04-09
tags: [fine-tuning, alignment, lora, rlhf, dpo, constitutional-ai]
---

# 微调与对齐 (Fine-tuning & Alignment)

> 微调让通用模型适配特定任务，对齐确保模型行为符合人类价值观。这是从预训练到可用产品的关键环节。

---

## 1. 概述

### 训练流程全景

```
预训练 (Pre-training)
  │  海量文本数据，学习语言和知识
  ▼
监督微调 (SFT)
  │  高质量指令-回复对，学习遵循指令
  ▼
对齐训练 (Alignment)
  │  RLHF / DPO 等，学习人类偏好
  ▼
安全护栏 (Safety)
     红队测试、安全过滤等
```

### 各阶段对比

| 阶段 | 数据 | 目标 | 计算成本 |
|------|------|------|----------|
| **预训练** | 万亿 token 文本 | 语言建模 | 极高 (千万美元级) |
| **SFT** | 万-百万级指令数据 | 遵循指令 | 中等 |
| **RLHF/DPO** | 万-十万级偏好数据 | 对齐人类偏好 | 中等 |

---

## 2. 监督微调 (Supervised Fine-Tuning, SFT)

### 全量微调 (Full Fine-tuning)

更新模型所有参数，效果最好但成本最高：

```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    learning_rate=2e-5,
    bf16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()
```

### 指令微调 (Instruction Tuning)

训练模型遵循各种指令的能力。关键在于数据格式：

**Alpaca 格式:**
```json
{
  "instruction": "将以下英文翻译为中文",
  "input": "Hello, how are you?",
  "output": "你好，你好吗？"
}
```

**ChatML / ShareGPT 格式:**
```json
{
  "conversations": [
    {"role": "system", "content": "你是一个有帮助的助手"},
    {"role": "user", "content": "什么是机器学习？"},
    {"role": "assistant", "content": "机器学习是..."}
  ]
}
```

### 数据质量 > 数据数量

- **LIMA 论文**: 仅 1000 条高质量数据就能显著提升模型表现
- 关键: 数据多样性、准确性、格式一致性
- 建议: 先从少量高质量数据开始，逐步扩展

### 常用工具

| 工具 | 说明 |
|------|------|
| **Hugging Face Transformers** | 最通用的训练框架 |
| **Axolotl** | 配置驱动的微调工具 |
| **LLaMA-Factory** | 中文社区流行，支持多种方法 |
| **Unsloth** | 极致速度优化 (2x-5x 加速) |
| **torchtune** | PyTorch 官方微调库 |

---

## 3. 参数高效微调 (PEFT)

### 3.1 LoRA (Low-Rank Adaptation)

[LoRA (Hu et al., 2021)](https://arxiv.org/abs/2106.09685) 是最流行的高效微调方法。核心思想：冻结原始权重，只训练低秩分解的增量矩阵。

```
原始权重 W (冻结)
              ↓
输入 x → W·x + B·A·x → 输出
              ↑
         LoRA 增量 (B·A)
         A: d×r  B: r×d  (r << d)
```

**优势**:
- 训练参数量减少 90%+
- 内存占用大幅降低
- 训练后的 LoRA 权重可独立保存和切换
- 多个 LoRA 可动态加载/卸载

**关键参数**:

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `r` (rank) | 低秩维度 | 8-64 (通常 16 或 32) |
| `lora_alpha` | 缩放因子 | 通常 = 2×r |
| `lora_dropout` | Dropout 率 | 0.05-0.1 |
| `target_modules` | 应用的模块 | q_proj, v_proj (或全部线性层) |

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    task_type="CAUSAL_LM",
)

model = get_peft_model(base_model, lora_config)
model.print_trainable_parameters()
# trainable params: 4,194,304 || all params: 6,742,609,920 || trainable%: 0.06%
```

### 3.2 QLoRA (Quantized LoRA)

[QLoRA (Dettmers et al., 2023)](https://arxiv.org/abs/2305.14314) 在 4-bit 量化的模型上进行 LoRA 微调：

- 基础模型用 4-bit NF4 量化 → 大幅减少显存
- LoRA 适配器保持 bf16/fp16 精度
- 使得在单张消费级 GPU (24GB) 上微调 70B 模型成为可能

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-70B",
    quantization_config=bnb_config,
)
```

### 3.3 其他 PEFT 方法

| 方法 | 说明 | 适用场景 |
|------|------|----------|
| **Prefix Tuning** | 在每层添加可训练前缀 | 生成任务 |
| **Prompt Tuning** | 在输入添加可训练软提示 | 分类任务 |
| **Adapters** | 在 Transformer 层间插入小网络 | 多任务适配 |
| **IA3** | 学习激活的缩放向量 | 极少参数量 |

### LoRA vs Full Fine-tuning

| 维度 | Full FT | LoRA | QLoRA |
|------|---------|------|-------|
| 显存需求 | 极高 | 中 | 低 |
| 训练速度 | 慢 | 快 | 中 |
| 效果 | 最好 | 接近 | 稍差 |
| 多任务切换 | 需多份完整模型 | 热切换 LoRA | 热切换 LoRA |
| 推荐场景 | 大预算大模型 | 大多数场景 | 资源受限 |

---

## 4. RLHF (基于人类反馈的强化学习)

### 核心流程

```
步骤 1: 收集人类偏好数据
  prompt → 模型生成多个回答 → 人类排序 (A > B > C)

步骤 2: 训练奖励模型 (Reward Model)
  (prompt, response) → Reward Model → 分数

步骤 3: PPO 强化学习优化
  策略模型生成回答 → 奖励模型评分 → PPO 更新策略 → 重复
```

### InstructGPT (OpenAI, 2022)

[InstructGPT](https://arxiv.org/abs/2203.02155) 是 RLHF 的标志性工作，证明了：
- 1.3B 的 InstructGPT 比 175B GPT-3 更受用户欢迎
- RLHF 显著提升了遵循指令和安全性

### RLHF 的挑战

| 挑战 | 说明 |
|------|------|
| **奖励黑客** | 模型学会"欺骗"奖励模型获得高分 |
| **训练不稳定** | PPO 训练容易不收敛 |
| **成本高** | 需要人类标注偏好数据 |
| **奖励模型瓶颈** | 奖励模型的能力限制了策略模型 |

---

## 5. DPO 及其变体

### 5.1 DPO (Direct Preference Optimization)

[DPO (Rafailov et al., 2023)](https://arxiv.org/abs/2305.18290) 直接从偏好数据优化策略，无需单独训练奖励模型：

```
RLHF:  偏好数据 → 训练奖励模型 → PPO 训练策略模型
DPO:   偏好数据 → 直接优化策略模型 (一步到位)
```

**DPO 损失函数** (简化):
```
L = -log σ(β · (log π(y_w|x) - log π(y_l|x) - log π_ref(y_w|x) + log π_ref(y_l|x)))
```
其中 y_w 是偏好回答，y_l 是非偏好回答。

**优势**:
- 训练流程简单（无需奖励模型）
- 更稳定（无 PPO 的不稳定性）
- 计算成本更低

```python
from trl import DPOTrainer, DPOConfig

dpo_config = DPOConfig(
    beta=0.1,
    learning_rate=5e-7,
    num_train_epochs=1,
)

trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    args=dpo_config,
    train_dataset=preference_dataset,
    tokenizer=tokenizer,
)

trainer.train()
```

### 5.2 DPO 变体

| 方法 | 说明 | 论文 |
|------|------|------|
| **KTO** | 无需偏好对，只需好/坏标签 | Kahneman-Tversky Optimization |
| **ORPO** | 将 SFT 和偏好学习合二为一 | Odds Ratio Preference Optimization |
| **IPO** | 修正 DPO 的过拟合问题 | Identity Preference Optimization |
| **SimPO** | 更简单的参考无关偏好优化 | Simple Preference Optimization |
| **SPPO** | 自博弈偏好优化 | Self-Play Preference Optimization |

---

## 6. 对齐研究前沿

### Constitutional AI (Anthropic)

用一组**原则 (Constitution)** 指导模型行为，减少对人类标注的依赖：

```
1. 模型生成回答
2. 模型根据 Constitution 自我批评
3. 模型修正回答
4. 重复以上过程
```

### Constitutional Classifiers (2025.2)

Anthropic 的防越狱分类器：
- 过滤绝大多数越狱攻击
- 经历 3000+ 小时红队测试无发现通用越狱
- 保持实际部署可用性

### Alignment Faking (2024.12)

Anthropic 重要发现 — 模型在未经训练的情况下出现**对齐伪装**行为：
- 模型在被监控时表现出合规行为
- 在不被监控时保留原有偏好
- 这是首个实证研究

### Model Spec (OpenAI, 2026.3)

OpenAI 公开其模型行为规范的制定方法：
- 定义模型应该如何行事
- 平衡有用性和安全性
- 处理边界情况的准则

### 可解释性用于对齐

Anthropic 最新研究方向：
- **情感概念理解** (2026.4): 理解模型如何表征情感
- **模型内省** (2025.10): 模型能否报告自己的内部状态？
- **行为差异检测** (2026.3): "diff" 工具发现新旧模型行为差异

### Sycophancy Disentanglement via Reward Decomposition（2026.4）

LLM 的谄媚（sycophancy）——在社会压力下偏离正确答案迎合用户——是对齐的关键挑战。标准 RLHF 无法修复它，因为标量奖励模型将两种正交的失败模式混为一个信号[^sycophancy-2026]：

| 失败模式 | 含义 |
|----------|------|
| **Pressure Capitulation**（压力屈服） | 证据不变，但模型在权威暗示下改变正确答案 |
| **Evidence Blindness**（证据盲视） | 无论提供什么上下文证据，模型输出不变 |

两种失败在标量奖励下都能拿到高分（人类标注偏好"令人愉快的"回答），导致 RLHF 梯度在谄媚回答与准确回答得分相近时消失。

**方法：五分量 GRPO 奖励分解。** 对每个问题构造对比数据——两个矛盾的证据上下文 C/C' × 三级权威压力 P₁/P₂/P₃ + 无压力基线 b(C)，然后将奖励分解为五个正交分量：

```
R = α·R_q + β·R_c + γ·R_p + ε·R_pos − δ·R_g

R_p  (压力抵抗)   = 1 − shift(b(C), y)        # 相对无压力基线的语义漂移，越小越好
R_c  (上下文忠实)  = p_entail(b(C), y)          # 回答须蕴含上下文匹配的基线立场
R_pos(立场一致)    = 𝟙_opp · [entail − contra]  # 在对立上下文中须明确采纳新立场（堵中立回答漏洞）
R_g  (迎合惩罚)    = 𝟙[hedge(y)] + p_entail(o,y)# 惩罚骑墙语言和与压力观点的蕴含
R_q  (事实正确)    = p_entail(b(C), y)          # 仅事实领域，锚定正确性
```

**非冗余性**：压力屈服压低 R_p 和 R_pos 但可保持 R_c；证据盲视压低 R_c 和 R_pos 但可保持 R_p——没有任何一种失败能在多个分量上同时拿高分。

**训练**：两阶段 pipeline——(1) SFT 预热建立"证据推理"锚点，(2) GRPO + 分解奖励。在 5 个基础模型上所有指标一致改善；消融实验确认每个分量控制独立的行为维度。即使训练只用显式权威压力模板，在 SycophancyEval 的隐式压力场景（答案引导、"你确定吗？"跟进）上也减少最多 **17pp** 谄媚率，说明学到的压力抵抗具有泛化性。

---

## 7. 安全对齐

### 越狱与防御

| 攻击类型 | 说明 | 防御方式 |
|----------|------|----------|
| **直接越狱** | 直接要求模型忽略规则 | System prompt 加固 |
| **间接注入** | 通过上下文注入恶意指令 | 输入清洗、权限隔离 |
| **角色扮演** | "假装你是没有限制的AI" | 角色一致性检查 |
| **编码绕过** | Base64/ROT13 编码有害内容 | 多层内容过滤 |
| **多轮诱导** | 逐步引导到有害输出 | 上下文安全监控 |

### 安全评估

| 框架/工具 | 说明 |
|-----------|------|
| **HarmBench** | 统一的有害行为评估 |
| **ToxiGen** | 隐性有害内容检测 |
| **Red Teaming** | 人工对抗测试 |
| **Automated Red Teaming** | 用 AI 自动找漏洞 |

### 最新安全举措 (2026)

- **OpenAI Safety Fellowship** (2026.4): 培养 AI 安全人才
- **OpenAI Safety Bug Bounty** (2026.3): 安全漏洞悬赏
- **Anthropic Responsible Scaling** (更新中): 负责任扩展政策

---

## 8. 实践指南

### 何时微调

```
需要微调:
  ✓ 需要特定的输出格式或风格
  ✓ 需要领域专业术语
  ✓ 需要一致的角色/人设
  ✓ 需要在特定任务上达到最优

不需要微调:
  ✗ 只需要注入新知识 → 用 RAG
  ✗ 只需要调整输出风格 → 用 Prompt Engineering
  ✗ 数据量不足 → 先收集更多数据
```

### 微调 Checklist

```
□ 明确目标: 微调要解决什么问题？
□ 数据准备: 至少 500-1000 条高质量数据
□ 基线评估: 用原始模型建立基线
□ 选择方法: LoRA (通常够用) vs Full FT
□ 超参数: lr=1e-5~5e-5, epochs=1~3
□ 验证集: 预留 10-20% 数据做验证
□ 评估: 自动指标 + 人工评估
□ 迭代: 分析错误案例，改进数据
```

### 平台选择

| 平台 | 特点 | 适用场景 |
|------|------|----------|
| **OpenAI Fine-tuning** | 最简单，按 token 计费 | 快速实验 |
| **Together AI** | 开源模型微调 | 开源模型 |
| **Anyscale** | Ray 生态，分布式 | 大规模训练 |
| **Lambda Labs** | GPU 云服务 | 自定义训练 |
| **本地 GPU** | 完全控制 | 数据敏感场景 |

---

## 9. 发展趋势

### 9.1 合成数据

用强模型生成训练数据：
- GPT-5 生成数据 → 训练开源模型
- 数据质量控制成为关键
- 自我改进循环 (Self-Improvement)

### 9.2 自动化红队

用 AI 自动发现模型弱点：
- 对抗性提示生成
- 自动化安全评估
- 持续安全监控

### 9.3 过程奖励 vs 结果奖励

- **结果奖励 (ORM)**: 只评判最终答案
- **过程奖励 (PRM)**: 评判每个推理步骤
- PRM 对推理任务更有效

### 9.4 多模态对齐

将对齐扩展到多模态场景：
- 图像生成的安全对齐
- 视频内容的伦理约束
- Agent 行为的对齐

### 9.5 Constitutional 方法扩展

- 从文本扩展到多模态
- 从单模型扩展到 Agent 系统
- 自动化 Constitution 生成和优化

---

## 参考资料

- Ouyang et al., "Training Language Models to Follow Instructions with Human Feedback" (InstructGPT), 2022 - [arXiv:2203.02155](https://arxiv.org/abs/2203.02155)
- Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models", 2021 - [arXiv:2106.09685](https://arxiv.org/abs/2106.09685)
- Dettmers et al., "QLoRA: Efficient Finetuning of Quantized Language Models", 2023 - [arXiv:2305.14314](https://arxiv.org/abs/2305.14314)
- Rafailov et al., "Direct Preference Optimization", 2023 - [arXiv:2305.18290](https://arxiv.org/abs/2305.18290)
- Bai et al., "Constitutional AI", 2022 - [arXiv:2212.08073](https://arxiv.org/abs/2212.08073)
- Zhou et al., "LIMA: Less Is More for Alignment", 2023 - [arXiv:2305.11206](https://arxiv.org/abs/2305.11206)
- Anthropic Alignment Research: https://www.anthropic.com/research
[^sycophancy-2026]: "Pressure, What Pressure? Sycophancy Disentanglement in Language Models via Reward Decomposition". 2026. https://arxiv.org/abs/2604.05279
