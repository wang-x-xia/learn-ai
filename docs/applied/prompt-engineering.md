---
title: 提示工程 (Prompt Engineering)
description: 从手工技巧到系统设计思维——提示工程如何适应 Agent 时代的 AI 交互范式。
created: 2026-04-07
updated: 2026-05-07
tags: [prompt-engineering, cot, few-shot, dspy, agents]
review: 2026-05-07
---

# 提示工程 (Prompt Engineering)

> 提示工程是与 LLM 高效交互的艺术和科学。随着模型能力提升和 Agent 系统兴起，提示工程从"手工打磨技巧"演变为"系统设计思维"——关注如何通过提示定义 Agent 行为、工具使用和协作模式。

---

## 1. 概述

### 什么是提示工程

提示工程 (Prompt Engineering) 是设计和优化输入给 LLM 的文本（提示/Prompt），以引导模型生成期望输出的技术。

### 为什么重要（2024-2025 年视角）

随着模型能力提升和应用范式转变，提示工程的重要性发生了变化：

| 维度 | 2022-2023 年（早期） | 2024-2025 年（当前） |
|------|---------------------|---------------------|
| **核心场景** | 直接对话、单轮任务 | Agent 编排、工具调用、多步推理 |
| **技能门槛** | 高（需要掌握 CoT、Few-shot 等技巧） | 低（模型更"听话"，自然语言即可） |
| **边际收益** | 10x 性能提升 | 1.2x 性能提升 |
| **关注点** | 提示词本身 | Agent 行为定义、工具描述、协作协议 |
| **固化方式** | 手工编写 | 系统提示、产品化配置（Skills、GPTs） |

### 与其他方法的关系（更新）

```
提示工程 (交互设计基础)
    ↓ 
Agent 编排 (LangGraph、MAF、AutoGen)
    ↓
工具调用 (Function Calling、MCP)
    ↓
RAG (需要外部知识时)
    ↓
微调 (需要特定行为/风格时)
```

**关键变化**：提示工程不再是一个独立的"优化手段"，而是 Agent 系统的**基础设施**——通过提示定义 Agent 的行为边界、工具使用策略和协作模式。

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

## 10. 发展趋势与 Agent 时代的新角色

### 10.1 为什么提示工程"热度下降"？

2024-2025 年，提示工程作为独立技术话题的讨论热度显著下降，主要原因：

1. **模型能力提升，指令遵循增强**
   - GPT-4.5、Claude 3.5/4、Gemini 2.0 等模型在指令遵循能力上有显著提升
   - 以前需要精心设计的 CoT 提示词，现在模型自己就能主动推理
   - 以前需要复杂的格式约束，现在模型能更好地理解结构化输出要求
   - **结果**：简单的自然语言指令就能得到不错的结果

2. **Agent 和工具调用成为主流**
   - 开发范式从"提示词工程"转向"Agent 编排"
   - 通过 Function Calling 调用外部 API/数据库，而非依赖提示词中的知识
   - 多 Agent 系统通过协作解决问题，而非单一超级提示词
   - **结果**：工程师关注点从"如何写好提示词"转移到"如何设计 Agent 架构"

3. **系统提示词的最佳实践被固化**
   - 模型厂商在系统提示词中内置了常见最佳实践
   - 平台层提供预设的提示词模板（Anthropic Skills、OpenAI GPTs）
   - 企业级应用使用统一的提示词模板库
   - **结果**：提示词工程变成"配置"而非"工程"，可见度降低

4. **注意力转移到更高层抽象**
   - Agent 编排（LangGraph、MAF、AutoGen）
   - 记忆系统（RAG、向量数据库）
   - 工具生态（MCP、OpenAPI）
   - 推理优化（KV Cache、量化、蒸馏）
   - **结果**：这些更高层技术能带来更大杠杆效应，吸引更多关注

5. **边际收益递减**
   - 早期（2022-2023）：精心设计的提示词能带来 10x 性能提升
   - 现在（2024-2025）：精心设计的提示词可能只带来 1.2x 提升
   - **机会成本**：同样的时间投入在 Agent 设计或 RAG 系统上，收益更大

6. **产品化工具降低门槛**
   - ChatGPT Custom Instructions、GPTs
   - Claude Skills
   - 低代码平台（Dify、Coze）
   - **结果**：用户通过 UI 配置就能实现以前需要提示词工程才能做到的效果

### 10.2 提示工程会消亡吗？

**不会，但角色发生了转变**：

| 角色 | 2022-2023 年 | 2024-2025 年 |
|------|-----------|-----------|
| **形态** | 手工打磨提示词 | 系统设计思维 |
| **场景** | 直接对话优化 | Agent 行为定义 |
| **技能** | 掌握 CoT、Few-shot | 理解 Agent 架构 |
| **固化** | 代码中的字符串 | Skills、GPTs、配置文件 |
| **价值** | 直接提升输出质量 | 定义系统边界和行为 |

提示工程从"显性技术"转为"隐性基础设施"，但仍然是 AI 交互的核心能力。

### 10.3 Agent 时代的提示工程

在 Agent 系统中，提示工程的新关注点：

#### Agent 行为定义

```python
# Agent 系统提示示例
agent_prompt = """你是一个数据分析 Agent。

你的职责：
- 接收用户的数据分析请求
- 决定使用哪些工具（SQL 查询、数据可视化、统计检验）
- 将复杂任务分解为可执行的步骤

工具使用规则：
- 只有在需要查询数据库时才使用 SQL 工具
- 生成图表前先确认数据完整性
- 遇到异常数据时主动标记并寻求人工确认

协作协议：
- 如果任务超出你的能力范围，向用户说明并建议替代方案
- 如果需要人工确认，使用 human-in-the-loop 机制
"""
```

#### 工具描述提示

```python
# Function Calling 的工具描述
tool_description = """执行 SQL 查询并返回结果。

使用场景：
- 用户询问具体的数据指标或统计信息
- 需要从数据库中提取结构化数据

使用规则：
- 只执行 SELECT 查询，禁止修改操作
- 查询前先检查 SQL 语法
- 结果集超过 1000 行时自动聚合

输入格式：
- query: SQL 查询语句
- database: 数据库名称（可选）

输出格式：
- success: 查询是否成功
- data: 查询结果（JSON 格式）
- error: 错误信息（如果失败）
"""
```

#### 多 Agent 协作提示

```python
# Router Agent 的路由提示
router_prompt = """你是一个任务路由 Agent。

你的职责：
- 分析用户请求的意图和领域
- 将请求路由到最合适的子 Agent

可用 Agent：
- data_agent: 数据分析和可视化
- code_agent: 代码生成和审查
- research_agent: 信息检索和总结

路由决策依据：
- 请求的关键词和语义
- 每个 Agent 的能力描述
- 上下文中的历史交互

输出格式：
- target_agent: 目标 Agent 名称
- reasoning: 路由决策的理由
- confidence: 决策的置信度 (0-1)
"""
```

### 10.4 程序化提示 (DSPy) 在 Agent 时代的价值

DSPy 从手工编写提示 → 程序化定义和自动优化，在 Agent 系统中尤为重要：

```python
import dspy

class DataAnalysisAgent(dspy.Signature):
    """数据分析 Agent 的提示定义"""
    user_request: str = dspy.InputField(desc="用户的数据分析请求")
    tool_plan: list[str] = dspy.OutputField(desc="需要使用的工具列表")
    execution_plan: str = dspy.OutputField(desc="执行步骤说明")

# 自动优化 Agent 的提示
teleprompter = dspy.BootstrapFewShot(metric=agent_success_rate)
optimized_agent = teleprompter.compile(
    DataAnalysisAgent, 
    trainset=agent_examples,
    valset=validation_cases
)
```

**价值**：
- 将 Agent 行为定义为可测试、可优化的 Schema
- 自动搜索最优的 Agent 提示策略
- 版本控制和 A/B 测试不同的 Agent 配置

### 10.5 模型特定策略（更新）

不同模型对提示的响应不同，Agent 系统需要针对性适配：

| 模型 | 特点 | Agent 设计建议 |
|------|------|---------------|
| **GPT 系列** | 遵循详细指令好 | 明确的步骤说明、工具使用规则 |
| **Claude** | 理解细微语境好 | 丰富的背景信息、 nuanced 的约束 |
| **Gemini** | 多模态指令好 | 图文结合的 Agent、视觉推理任务 |
| **开源模型** | 需要更明确的指令 | 更详细的工具描述、更多的示例 |

---

## 参考资料

### 经典论文
- Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", 2022 - [arXiv:2201.11903](https://arxiv.org/abs/2201.11903)
- Wang et al., "Self-Consistency Improves Chain of Thought Reasoning", 2022 - [arXiv:2203.11171](https://arxiv.org/abs/2203.11171)
- Yao et al., "Tree of Thoughts", 2023 - [arXiv:2305.10601](https://arxiv.org/abs/2305.10601)
- Yao et al., "ReAct: Synergizing Reasoning and Acting", 2022 - [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)

### 工具和框架
- DSPy: https://github.com/stanfordnlp/dspy
- Prompt Engineering Guide: https://www.promptingguide.ai/

### Agent 框架
- LangGraph: https://github.com/langchain-ai/langgraph
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- AutoGen: https://github.com/microsoft/autogen

### 相关文档
- Agent 智能体: [ai-agents.md](ai-agents.md)
- Agent 工具接入: [agent-tools.md](agent-tools.md)
- Agent Skills: [agent-skills.md](agent-skills.md)
