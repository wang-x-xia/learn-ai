---
title: Agent 工具接入
description: Agent 获得外部能力的基础机制——Function Calling 和 MCP 的技术方案与设计要点。
created: 2026-04-10
updated: 2026-04-10
tags: [agents, tools, mcp, function-calling]
review: 2026-04-10
---

# Agent 工具接入

??? note "背景知识"
    - **Agent 执行循环**：思考→行动→观察的迭代，Act 步骤需要调用外部工具 → [详见](ai-agents.md)
    - **JSON Schema**：描述 JSON 数据结构的标准格式，用于定义工具的参数签名
    - **RPC (远程过程调用)**：跨进程/网络调用函数的通信模式

> Agent [执行循环](ai-agents.md)的 Act 步骤需要外部能力。Function Calling 和 MCP 是两个基础层——前者定义"怎么调用"，后者定义"怎么发现和连接"。更高层的能力编排见 [Agent Skills](agent-skills.md)。

---

## 1. Function Calling

各厂商 API 的原生工具调用机制，是所有上层方案的基础。

**核心流程**：模型输出结构化的函数调用请求（函数名 + 参数），宿主程序执行后将结果注入上下文，成为下一轮推理的 Observation。

**设计要点**：

- 函数描述的质量直接影响调用准确率（本质上是 [prompt engineering](prompt-engineering.md)）
- 并行函数调用（parallel function calling）减少循环轮次
- 模型需要在"调用工具"和"直接回答"之间做判断

---

## 2. MCP（Model Context Protocol）

Anthropic 提出的 Agent—工具连接协议[^mcp-spec]，将工具的**发现、描述、调用**标准化。

**解决的问题**：Function Calling 只定义了"怎么调用一个函数"，没有定义"怎么发现有哪些函数可用"。每个工具提供者要为每个 Agent 写一套适配——MCP 用统一协议消除了 M×N 集成问题。

**架构**：

```
Agent（MCP Client）←→ MCP Server ←→ 外部资源
                        ├── Resources（只读数据源）
                        ├── Tools（可执行操作）
                        └── Prompts（提示模板）
```

**技术要点**：

- **Server-Client 架构**：每个 MCP Server 封装一组相关能力（如 GitHub Server 封装仓库操作），Agent 作为 Client 连接多个 Server
- **三种原语**：Resources（只读数据）、Tools（可执行操作）、Prompts（可复用提示模板）
- **传输层**：支持 stdio（本地进程）和 Streamable HTTP（远程服务）

---

## 参考资料

[^mcp-spec]: Anthropic. *Model Context Protocol Specification*. https://spec.modelcontextprotocol.io/
