# AI Agent 智能体

> AI Agent 是 2024-2026 年最热门的 AI 方向之一。从简单的聊天机器人进化为能够自主规划、使用工具、执行复杂任务的智能体。

---

## 1. 概述

### 什么是 AI Agent

AI Agent (智能体) 是一个以大语言模型为"大脑"，能够**自主感知环境、制定计划、使用工具、执行行动**的系统。与传统的单轮问答不同，Agent 能够：

- 分解复杂任务为多个步骤
- 调用外部工具（搜索、代码执行、API 等）
- 根据执行结果动态调整计划
- 维护长期记忆

### Agent 核心公式

```
Agent = LLM (推理引擎) + Memory (记忆) + Tools (工具) + Planning (规划)
```

### 为什么 Agent 如此重要

- **从对话到行动**: LLM 不再只是回答问题，而是直接完成任务
- **复杂任务自动化**: 将多步骤工作流自动化
- **连接真实世界**: 通过工具调用与外部系统交互
- **自主改进**: 通过反思和反馈不断优化执行

---

## 2. Agent 架构

### 2.1 ReAct 模式 (Reasoning + Acting)

[ReAct (Yao et al., 2022)](https://arxiv.org/abs/2210.03629) 是最经典的 Agent 架构，交替进行推理和行动：

```
Thought: 我需要查找今天的天气
Action: search("今天北京天气")
Observation: 北京今天晴，最高温度 25°C
Thought: 我已获得天气信息，可以回答用户了
Action: respond("北京今天晴天，最高温 25°C")
```

### 2.2 Plan-and-Execute

先制定完整计划，再逐步执行：

```
Plan:
  1. 搜索相关论文
  2. 阅读论文摘要
  3. 总结关键发现
  4. 生成报告

Execute:
  Step 1: [执行搜索] → 找到 5 篇相关论文
  Step 2: [阅读摘要] → 提取关键信息
  Step 3: [总结] → 归纳 3 个主要发现
  Step 4: [生成报告] → 输出 Markdown 报告
```

### 2.3 Reflexion (自我反思)

[Reflexion (Shinn et al., 2023)](https://arxiv.org/abs/2303.11366) 让 Agent 从失败中学习：

```
尝试 → 失败 → 反思（为什么失败？）→ 改进策略 → 重新尝试
```

### 2.4 记忆系统

| 记忆类型 | 实现方式 | 用途 |
|----------|----------|------|
| **短期记忆** | 上下文窗口 | 当前对话/任务上下文 |
| **长期记忆** | 向量数据库 | 持久化知识和经验 |
| **情景记忆** | 结构化存储 | 过往交互经验 |
| **工作记忆** | 临时缓冲区 | 当前任务的中间状态 |

**最新研究** (2026 年 4 月 arXiv):

- **MemMachine**: 保留真实信息的记忆系统，防止 Agent 记忆失真
- **SuperLocalMemory V3.3**: 受生物学启发的遗忘机制 + 认知量化 + 多通道检索
- **Memory Intelligence Agent**: 智能记忆管理的多Agent系统

---

## 3. 主流 Agent 框架

### 框架对比

| 框架 | 厂商 | 语言 | 特点 | 适用场景 |
|------|------|------|------|----------|
| **LangChain** | LangChain | Python/JS | 生态最全，组件丰富 | 通用 Agent 开发 |
| **LangGraph** | LangChain | Python/JS | 基于图的工作流 | 复杂多步骤流程 |
| **AutoGen** | Microsoft | Python | 多 Agent 对话框架 | 多 Agent 协作 |
| **CrewAI** | CrewAI | Python | 角色扮演 Agent | 团队协作模拟 |
| **Semantic Kernel** | Microsoft | C#/Python | 企业级 AI 集成 | .NET 生态 |
| **Dify** | Dify | Python | 低代码 AI 平台 | 快速原型开发 |
| **Coze** | 字节跳动 | - | 低代码 Bot 平台 | 快速构建 Bot |

### LangGraph 示例

```python
from langgraph.graph import StateGraph, MessagesState
from langchain_openai import ChatOpenAI

# 定义 Agent 状态和节点
def agent_node(state: MessagesState):
    llm = ChatOpenAI(model="gpt-5")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def tool_node(state: MessagesState):
    # 执行工具调用
    ...

# 构建图
graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge("agent", "tools")
graph.add_edge("tools", "agent")
```

### 商业 Agent 产品

| 产品 | 厂商 | 说明 |
|------|------|------|
| **Codex** | OpenAI | GPT-5.3-Codex 驱动，按需定价 (2026.4) |
| **Claude Code** | Anthropic | 端到端编程Agent，企业版可用 |
| **Claude Cowork** | Anthropic | 协作式 AI 助手 |
| **Google Antigravity** | Google | Agent 开发平台 |
| **Assistants API** | OpenAI | 自定义 Agent 构建 API |

---

## 4. Agent 协议与通信

### MCP (Model Context Protocol)

Anthropic 提出的**工具连接协议**，定义了 LLM 与外部工具/数据源之间的标准化接口：

```
LLM ←→ MCP Server ←→ 外部工具/数据
         ├── 文件系统
         ├── 数据库
         ├── API 服务
         └── 其他 MCP Server
```

特点：
- 标准化的工具描述和调用格式
- Server-Client 架构
- 支持资源 (Resources)、工具 (Tools)、提示 (Prompts)
- 被 Claude、Cursor、Windsurf 等广泛采用

### A2A (Agent-to-Agent Protocol)

Google 提出的 **Agent 间通信协议**：
- Agent 发现和能力声明
- 任务委派和结果返回
- 与 MCP 互补（MCP 是 Agent-工具通信，A2A 是 Agent-Agent 通信）

### ANX Protocol (2026 年 4 月)

最新的开源 Agent 交互协议，在四个维度对比了 MCP、A2A 等现有协议：
- **工具使用 (Tooling)**
- **发现机制 (Discovery)**
- **安全性 (Security)**
- **多 Agent SOP 协作**

### Function Calling

各厂商 API 的原生工具调用机制：

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "获取指定城市的天气",
    "parameters": {
      "type": "object",
      "properties": {
        "city": { "type": "string", "description": "城市名" }
      },
      "required": ["city"]
    }
  }
}
```

---

## 5. 代码 Agent

代码 Agent 是目前最成熟的 Agent 应用领域。

### 主流产品

| 产品 | 类型 | 特点 |
|------|------|------|
| **GitHub Copilot** | IDE 插件 | 实时代码补全和建议 |
| **Cursor** | AI-native IDE | 深度集成 AI 的编辑器 |
| **Devin** | 自主编程 Agent | 端到端完成编程任务 |
| **Claude Code** | CLI 编程 Agent | 终端中的编程助手 |
| **OpenAI Codex** | 云端编程 Agent | GPT-5.3-Codex 驱动 |
| **Windsurf** | AI-native IDE | Codeium 出品 |
| **Cline** | VS Code 插件 | 开源 Agent |
| **Aider** | CLI 工具 | 开源 Git 集成 Agent |

### 编程 Agent 能力层次

```
Level 0: 代码补全 (Tab 补全)
Level 1: 代码生成 (从注释/描述生成代码)
Level 2: 代码编辑 (理解上下文，修改现有代码)
Level 3: 项目级理解 (理解整个代码库，跨文件修改)
Level 4: 自主编程 (从需求到完成，包括调试和测试)
```

### 评估基准

| 基准 | 说明 |
|------|------|
| **SWE-bench** | 真实 GitHub Issue 修复 |
| **SWE-bench Verified** | 人工验证的子集 |
| **HumanEval** | Python 函数生成 |
| **MBPP** | Python 编程题 |
| **LiveCodeBench** | 动态更新的编程基准 |

---

## 6. 搜索 Agent

### 主流产品

| 产品 | 特点 |
|------|------|
| **Perplexity AI** | AI 原生搜索引擎，引用来源 |
| **Google AI Overviews** | 搜索结果中的 AI 摘要 |
| **ChatGPT Browse** | ChatGPT 的实时搜索 |
| **Bing Chat** | Microsoft 搜索 + AI |

### 最新研究

**"Search, Do not Guess"** (2026 年 4 月 arXiv):
- 教小语言模型成为有效的搜索 Agent
- 核心思想: 让模型在不确定时主动搜索，而非猜测
- 对轻量级搜索增强系统有重要指导意义

---

## 7. 安全与对齐

### 主要风险

| 风险 | 说明 | 缓解措施 |
|------|------|----------|
| **提示注入** | 恶意输入操纵 Agent 行为 | 输入清洗、权限隔离 |
| **工具滥用** | Agent 误用或过度使用工具 | 权限控制、操作审批 |
| **信息泄露** | 敏感数据通过 Agent 传出 | 数据分类、输出过滤 |
| **无限循环** | Agent 陷入循环执行 | 超时机制、步骤限制 |
| **供应链攻击** | 恶意工具或数据源 | 来源验证、沙箱执行 |

### 最新安全研究 (2026.4)

- **ShieldNet**: 针对 Agent 系统供应链注入的网络级防护
- **AI Trust OS**: 自主 AI 可观测性和零信任合规的持续治理框架

### 安全最佳实践

```
1. 最小权限原则: Agent 只拥有完成任务所需的最少权限
2. 人类审批: 关键操作需人类确认
3. 沙箱执行: 工具调用在隔离环境中运行
4. 日志审计: 记录所有 Agent 行为用于审计
5. 速率限制: 防止 Agent 过度调用外部服务
```

---

## 8. 发展趋势

### 8.1 多 Agent 系统

多个 Agent 协作完成复杂任务：
- **角色分工**: 不同 Agent 扮演不同角色（研究员、程序员、审核员）
- **层级结构**: Manager Agent 分配和协调子 Agent
- **协作模式**: 对话式、管道式、竞争式

### 8.2 自主计算机使用

Agent 直接操作计算机界面：
- Claude Computer Use
- 基于截图理解的 GUI 操控
- Browser Agent (浏览网页完成任务)

### 8.3 长运行持久 Agent

**Springdrift** (2026.4 arXiv): 可审计的持久运行时，具备：
- 基于案例的记忆
- 规范性安全保障
- 环境自我感知

### 8.4 个性化 Agent

- 学习用户偏好和工作习惯
- 维护个人知识库
- 主动提供建议和帮助

### 8.5 Agent 基础设施成熟

- 标准化协议 (MCP、A2A)
- 评估和监控工具
- 安全防护框架
- 商业化部署方案

---

## 参考资料

- Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", 2022 - [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning", 2023 - [arXiv:2303.11366](https://arxiv.org/abs/2303.11366)
- Wang et al., "A Survey on Large Language Model based Autonomous Agents", 2023 - [arXiv:2308.11432](https://arxiv.org/abs/2308.11432)
- MCP Specification: https://spec.modelcontextprotocol.io/
- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
