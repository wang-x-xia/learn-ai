# 提示工程 (Prompt Engineering)

> 提示工程是与 LLM 高效交互的艺术和科学。通过精心设计的提示，可以在不修改模型的情况下极大提升输出质量。

---

## 1. 概述

### 什么是提示工程

提示工程 (Prompt Engineering) 是设计和优化输入给 LLM 的文本（提示/Prompt），以引导模型生成期望输出的技术。

### 为什么重要

- **零成本**: 不需要训练或微调
- **即时生效**: 修改提示立即看到效果
- **灵活性**: 同一模型适配不同任务
- **性价比**: 在大多数场景下效果足够好

### 与其他方法的关系

```
提示工程 (简单、快速、零成本)
    ↓ 不够用时
RAG (需要外部知识时)
    ↓ 不够用时
微调 (需要特定行为/风格时)
    ↓ 不够用时
预训练 (需要全新能力时)
```

---

## 2. 基础技巧

### 2.1 Zero-shot Prompting

直接给出任务描述，不提供示例：

```
将以下文本翻译成英文：
"人工智能正在改变世界"
```

### 2.2 Few-shot Prompting

提供几个示例来引导模型：

```
将中文翻译成英文：

中文：今天天气很好
英文：The weather is nice today

中文：我喜欢编程
英文：I love programming

中文：人工智能正在改变世界
英文：
```

### 2.3 System Prompt (系统提示)

设定模型的角色和行为：

```
System: 你是一位资深的 Python 开发者，专注于代码质量和最佳实践。
        回答时请：
        1. 提供简洁高效的代码
        2. 解释关键决策
        3. 指出潜在的陷阱

User: 如何实现一个线程安全的单例模式？
```

### 2.4 输出格式控制

明确指定期望的输出格式：

```
分析以下客户评价的情感，以 JSON 格式返回结果：

评价："这个产品太棒了，物流也很快！"

请严格按照以下格式输出：
{
  "sentiment": "positive/negative/neutral",
  "confidence": 0.0-1.0,
  "keywords": ["关键词1", "关键词2"]
}
```

### 2.5 采样参数

| 参数 | 范围 | 说明 |
|------|------|------|
| **Temperature** | 0-2 | 越高越随机/创意，越低越确定/精确 |
| **Top-p** | 0-1 | 核采样，限制候选 token 的累积概率 |
| **Top-k** | 1-∞ | 限制候选 token 数量 |
| **Max tokens** | - | 最大输出长度 |
| **Frequency penalty** | -2 到 2 | 降低重复 token 的概率 |

```
确定性任务 (数学、代码): temperature=0, top_p=1
创意任务 (写作、头脑风暴): temperature=0.7-1.0
平衡场景: temperature=0.3-0.5
```

---

## 3. 高级技巧

### 3.1 Chain-of-Thought (CoT) 思维链

[Wei et al., 2022](https://arxiv.org/abs/2201.11903) 让模型逐步推理：

**不用 CoT:**
```
Q: 一个农场有 15 只鸡和 8 头牛，一共有多少条腿？
A: 62
```

**使用 CoT:**
```
Q: 一个农场有 15 只鸡和 8 头牛，一共有多少条腿？
A: 让我一步步来算：
   1. 鸡有 2 条腿，15 只鸡 = 15 × 2 = 30 条腿
   2. 牛有 4 条腿，8 头牛 = 8 × 4 = 32 条腿
   3. 总共 = 30 + 32 = 62 条腿
   答案是 62。
```

### 3.2 Zero-shot CoT

不需要示例，只需加一句魔法咒语：

```
Q: 一个农场有 15 只鸡和 8 头牛，一共有多少条腿？

Let's think step by step.
(让我们一步一步地思考。)
```

### 3.3 Self-Consistency

[Wang et al., 2022](https://arxiv.org/abs/2203.11171): 多次采样，选择最一致的答案：

```
同一个问题 → 采样 5 次不同推理路径
  路径 1: 答案 = 42
  路径 2: 答案 = 42
  路径 3: 答案 = 38
  路径 4: 答案 = 42
  路径 5: 答案 = 42

多数投票 → 最终答案 = 42 (4/5)
```

### 3.4 Tree of Thoughts (ToT)

[Yao et al., 2023](https://arxiv.org/abs/2305.10601): 树状探索多种思路：

```
问题
├── 思路 A → 评估(好) → 继续探索
│   ├── A1 → 评估(好) → ✓ 选择
│   └── A2 → 评估(差) → 剪枝
├── 思路 B → 评估(一般) → 继续但低优先
└── 思路 C → 评估(差) → 剪枝
```

### 3.5 ReAct Prompting

结合推理 (Reasoning) 和行动 (Acting):

```
Question: 谁是2024年诺贝尔物理学奖得主？

Thought: 我需要搜索最新的诺贝尔奖信息。
Action: Search("2024 Nobel Prize Physics")
Observation: 2024年诺贝尔物理学奖授予了 John Hopfield 和 Geoffrey Hinton。
Thought: 我已经找到了答案。
Answer: 2024年诺贝尔物理学奖授予了 John Hopfield 和 Geoffrey Hinton，以表彰他们在人工神经网络方面的基础性发现。
```

### 3.6 结构化输出

使用 JSON Mode 或 Schema 约束输出：

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": "以 JSON 格式回答"},
        {"role": "user", "content": "分析'我很开心'的情感"}
    ]
)
```

---

## 4. 提示框架

### 4.1 CRISPE 框架

| 元素 | 说明 | 示例 |
|------|------|------|
| **C**apacity | 角色/能力 | "你是一位资深数据科学家" |
| **R**ole | 具体角色 | "专注于 NLP 领域" |
| **I**nsight | 背景信息 | "我们在做一个情感分析项目" |
| **S**tatement | 具体任务 | "请分析以下评论的情感" |
| **P**ersonality | 风格 | "用简洁专业的语言回答" |
| **E**xperiment | 限制 | "给出 3 个不同的方案" |

### 4.2 CO-STAR 框架

```
C - Context (背景): 任务的背景信息
O - Objective (目标): 需要完成什么
S - Style (风格): 期望的写作/回答风格
T - Tone (语气): 正式/非正式/友好/专业
A - Audience (受众): 目标读者是谁
R - Response (回复): 期望的格式和长度
```

### 4.3 DSPy 框架

[DSPy](https://github.com/stanfordnlp/dspy) 将提示工程**程序化**：

```python
import dspy

class SentimentAnalysis(dspy.Signature):
    """分析文本的情感倾向"""
    text: str = dspy.InputField(desc="待分析的文本")
    sentiment: str = dspy.OutputField(desc="positive/negative/neutral")
    confidence: float = dspy.OutputField(desc="置信度 0-1")

# 自动优化提示
teleprompter = dspy.BootstrapFewShot(metric=accuracy)
optimized = teleprompter.compile(SentimentAnalysis, trainset=examples)
```

---

## 5. 场景化提示技巧

### 5.1 代码生成

```
### 好的提示:
用 Python 实现一个 LRU Cache 类，要求：
- 支持 get(key) 和 put(key, value) 操作
- 两个操作的时间复杂度都是 O(1)
- 当缓存满时，淘汰最近最少使用的键
- 使用 OrderedDict 实现
- 包含类型提示和文档字符串

### 不好的提示:
写一个缓存
```

### 5.2 数据提取

```
从以下文本中提取结构化信息。

文本：
"张三，男，35岁，现任ABC科技有限公司高级工程师，
2015年毕业于清华大学计算机科学专业。"

请按以下 JSON 格式提取：
{
  "name": "",
  "gender": "",
  "age": 0,
  "company": "",
  "position": "",
  "education": {
    "school": "",
    "major": "",
    "graduation_year": 0
  }
}
```

### 5.3 文本总结

```
请用 3 个要点总结以下文章，每个要点不超过 30 字。
要求：
- 抓住核心论点
- 避免冗余信息
- 使用客观语言

文章：
[文章内容]
```

### 5.4 推理与分析

```
你是一位逻辑分析专家。请分析以下论点的逻辑缺陷：

论点："所有成功的企业家都很勤奋。张三很勤奋，所以张三一定会成为成功的企业家。"

请：
1. 识别逻辑谬误的类型
2. 解释为什么这个推理是错误的
3. 给出一个正确的推理形式
```

---

## 6. 提示优化

### 6.1 迭代优化流程

```
初始提示 → 测试 → 分析失败案例 → 改进提示 → 再测试 → ...
```

### 6.2 优化策略

| 策略 | 说明 |
|------|------|
| **添加示例** | Few-shot 通常比 Zero-shot 效果好 |
| **分解任务** | 复杂任务拆成多步 |
| **明确约束** | 清晰说明不要什么 |
| **添加角色** | 设定专业角色提升质量 |
| **格式指定** | JSON/Markdown/表格等 |
| **增加上下文** | 提供更多背景信息 |

### 6.3 自动化提示优化

| 工具 | 说明 |
|------|------|
| **DSPy** | 程序化提示优化 |
| **OPRO** | LLM 自我优化提示 |
| **PromptBreeder** | 进化算法优化提示 |
| **APE** | 自动提示工程 |

### 6.4 评估提示质量

```python
# 简单评估框架
def evaluate_prompt(prompt_template, test_cases, model):
    results = []
    for test in test_cases:
        prompt = prompt_template.format(**test['input'])
        response = model.generate(prompt)
        score = compare(response, test['expected'])
        results.append(score)
    return sum(results) / len(results)
```

---

## 7. 多模态提示

### 图像理解

```
[上传一张图片]

请分析这张图片：
1. 描述图中的主要内容
2. 识别所有文字
3. 如果是图表，提取关键数据
4. 给出你的解读
```

### 结合图文

```
[上传一张建筑设计图]

作为一名建筑师，请评估这个设计方案：
- 空间利用率
- 采光和通风
- 结构可行性
- 改进建议
```

---

## 8. 安全考虑

### 提示注入防御

```python
# 不安全的做法
prompt = f"回答用户的问题：{user_input}"

# 更安全的做法
prompt = f"""你是一个客服助手，只回答关于产品的问题。
如果用户的问题与产品无关，礼貌地拒绝并引导回正题。

用户问题：{sanitize(user_input)}

请按规定回答："""
```

### 防御策略

| 策略 | 说明 |
|------|------|
| **输入清洗** | 过滤特殊字符和已知攻击模式 |
| **指令隔离** | 系统指令和用户输入明确分离 |
| **输出过滤** | 检查输出是否包含敏感信息 |
| **权限最小化** | 限制模型可访问的工具和数据 |
| **监控审计** | 记录和分析异常对话 |

---

## 9. 实践案例

### 案例 1: 代码审查提示优化

**Before (基础提示):**
```
审查这段代码
```

**After (优化后):**
```
作为一位高级代码审查者，请审查以下 Python 代码。
关注以下方面：
1. 代码正确性和潜在 Bug
2. 性能问题
3. 安全漏洞
4. 代码风格和可读性
5. 改进建议

对每个问题，请给出：
- 严重级别 (Critical/Major/Minor/Info)
- 问题位置 (行号)
- 问题描述
- 修复建议

代码：
[代码内容]
```

### 案例 2: 数据分析

**Before:**
```
分析这个数据
```

**After:**
```
你是一位数据分析师。请对以下销售数据进行分析：

[数据表格]

请提供：
1. 关键指标摘要（总销售额、增长率、TOP5产品）
2. 趋势分析（环比、同比）
3. 异常检测（是否有异常波动）
4. 可行的业务建议（至少3条）

以 Markdown 表格和要点列表的格式输出。
```

---

## 10. 发展趋势

### 10.1 提示工程是否会消亡？

随着模型越来越强，简单的提示就能获得好结果。但：
- 复杂任务仍需要精心设计的提示
- 系统级提示 (System Prompt) 变得更重要
- 提示工程演变为"AI 交互设计"

### 10.2 程序化提示 (DSPy)

从手工编写提示 → 程序化定义和自动优化：
- 定义输入输出 Schema
- 自动搜索最优提示
- 版本控制和 A/B 测试

### 10.3 模型特定策略

不同模型对提示的响应不同：
- GPT 系列: 遵循详细指令好
- Claude: 理解细微语境好
- Gemini: 多模态指令好
- 开源模型: 通常需要更明确的指令

### 10.4 Agent Prompt Design

为 Agent 系统设计提示成为新挑战：
- 工具使用提示
- 多步骤规划提示
- 错误恢复提示

---

## 参考资料

- Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", 2022 - [arXiv:2201.11903](https://arxiv.org/abs/2201.11903)
- Wang et al., "Self-Consistency Improves Chain of Thought Reasoning", 2022 - [arXiv:2203.11171](https://arxiv.org/abs/2203.11171)
- Yao et al., "Tree of Thoughts", 2023 - [arXiv:2305.10601](https://arxiv.org/abs/2305.10601)
- Yao et al., "ReAct: Synergizing Reasoning and Acting", 2022 - [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- DSPy: https://github.com/stanfordnlp/dspy
- Prompt Engineering Guide: https://www.promptingguide.ai/
