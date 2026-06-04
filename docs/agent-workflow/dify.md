---
title: Dify
description: 开源的可视化 AI 应用开发平台，用拖拽式界面构建 Agent 和 RAG 工作流。
created: 2026-04-10
updated: 2026-05-07
tags:
  - framework
  - dify
  - agent
  - python
  - low-code
review: 2026-05-07
render_macros: false
---

# Dify

??? note "背景知识"
    - **Agent 执行循环**：思考→行动→观察的迭代 → [详见](../agent/ai-agents.md)
    - **RAG (检索增强生成)**：从知识库检索文档注入 LLM 上下文 → [详见](../applied/rag.md)
    - **有向图工作流**：用节点和边建模执行步骤，节点是计算单元，边是数据流

> 开源可视化 AI 应用平台——用拖拽式界面构建 Agent 和 RAG 工作流，降低 AI 应用的开发门槛。

| 属性 | 值 |
|------|-----|
| 厂商 | Dify |
| 语言 | Python / TypeScript |
| 开源 | 是 |
| GitHub | [langgenius/dify](https://github.com/langgenius/dify) |
| 官网 | [dify.ai](https://dify.ai)[^dify-docs] |

## 工作流执行

### Graph JSON 结构

工作流以 JSON 格式存储在数据库 `workflows` 表的 `graph` 字段中，核心结构如下：[^dify-graph-structure]

```json
{
  "nodes": [
    {
      "id": "node_123",
      "type": "agent",
      "data": {
        "title": "客服 Agent",
        "agent_strategy_provider_name": "dify",
        "agent_strategy_name": "function-calling",
        "agent_parameters": {...}
      },
      "position": {"x": 100, "y": 200}
    }
  ],
  "edges": [
    {
      "id": "edge_456",
      "source": "node_123",
      "target": "node_789",
      "type": "custom"
    }
  ]
}
```

### 主要节点类型

| 节点类型 | 用途 |
|---------|------|
| `start`, `end` | 工作流起点和终点 |
| `agent` | Agent 节点，支持多种策略（Function Calling、ReAct 等） |
| `llm` | LLM 调用节点 |
| `tool` | 工具调用节点 |
| `knowledge-retrieval` | 知识库检索节点 |
| `code` | 代码执行节点 |
| `if-else` | 条件分支 |
| `template-transform` | 模板转换 |
| `variable-assigner` | 变量赋值 |
| `loop`, `iteration` | 循环控制 |
| `http-request` | HTTP 请求 |
| `human-input` | 人机交互 |

[^dify-node-types]

### Agent 节点详解

#### 输入结构

**配置输入**（节点定义）：
```python
class AgentNodeData:
    agent_strategy_provider_name: str      # 策略提供者（默认 "dify"）
    agent_strategy_name: str               # 策略名称：function-calling / react / cot
    memory: MemoryConfig | None           # 记忆配置
    agent_parameters: dict[str, AgentInput]  # 参数字典（包含模型、system prompt 等）
```

**策略说明**：
- `agent_strategy_provider_name = "dify"`：使用 Dify 内置的策略实现
- `agent_strategy_name`：Agent 执行策略
  - `function-calling`：基于 Function Calling 的策略
  - `react`：ReAct 策略（推理-行动循环）
  - `cot`：Chain-of-Thought 策略

**运行时输入**（节点执行）：
```python
agent_parameters: dict[str, AgentInput]
```

参数字典，key 是参数名（如 `"system_prompt"`、`"model"`），value 是 `AgentInput` 对象。

**策略定义的参数**：
策略（如 `function-calling`）定义了自己需要的参数，常见的有：
- `system_prompt`：系统提示词（STRING 类型）
- `model`：模型配置（MODEL_SELECTOR 类型）
- `tools`：工具列表（TOOLS_SELECTOR 类型）
- `user_input`：用户输入（STRING 类型）

**AgentInput.type**（值的来源类型）：

| 类型 | 值来源 | 示例 |
|-----|-------|------|
| `constant` | 常量值 | `type="constant", value="你是一个客服"` |
| `variable` | 从工作流上下文获取变量 | `type="variable", value="{{start.user}}"` |
| `mixed` | 模板字符串（变量插值） | `type="mixed", value="你好 {{user.name}}，今天是 {{date}}"` |

**AgentInput.value**（实际值类型）：
根据参数的数据类型不同，value 可以是：
- **字符串**：用于 STRING 类型参数（如 system_prompt）
- **字典**：用于 MODEL_SELECTOR 类型参数（如 `{"provider": "openai", "model": "gpt-4o-mini", "model_type": "llm"}`）
- **列表**：用于 TOOLS_SELECTOR 类型参数
- **其他类型**：数字、布尔值等

执行时根据 `AgentInput.type` 解析：如果是 `variable` 或 `mixed`，从 `VariablePool`（工作流共享状态）中获取变量值，最终构建成 `params: dict[str, Any]` 传给策略的 `invoke()` 方法。

示例：
```python
agent_parameters: {
  "system_prompt": {              # 参数名（策略定义，STRING 类型）
    "type": "constant",           # 值的来源类型
    "value": "你是一个客服助手"   # 实际值（字符串）
  },
  "model": {                      # 参数名（策略定义，MODEL_SELECTOR 类型）
    "type": "constant",           # 值的来源类型
    "value": {                    # 实际值（字典）
      "provider": "openai",
      "model": "gpt-4o-mini",
      "model_type": "llm"
    }
  },
  "user_input": {
    "type": "variable",
    "value": "{{start.user_query}}"
  }
}
```

**策略调用参数**：
```python
strategy.invoke(
    params: dict[str, Any],              # 构建后的参数字典
    user_id: str,
    conversation_id: str | None,
    app_id: str | None,
    credentials: InvokeCredentials | None
)
```

#### 输出结构

```python
Generator[ToolInvokeMessage, None, None]
```

**消息类型**：
- `TEXT`: 纯文本响应
- `JSON`: JSON 对象（结构化数据）
- `VARIABLE`: 变量赋值（传递给下游节点）
- `LOG`: 工具调用日志
- `RETRIEVER_RESOURCES`: RAG 检索结果
- `BLOB` / `BLOB_CHUNK`: 二进制数据（流式）

**结束条件**：
1. 模型输出 `{"action": "final answer", "action_input": "..."}`
2. 达到最大迭代次数（默认上限 99 次）
3. 解析失败（无法提取有效动作）

[^dify-agent-node]

## Graphon 执行引擎

### 项目信息

| 属性 | 值 |
|------|-----|
| GitHub | [langgenius/graphon](https://github.com/langgenius/graphon) |
| 许可证 | Apache-2.0 |
| 语言 | Python |
| Stars | 40 |
| 版本 | ~=0.2.2 |

### 核心定位

Graphon 是 LangGenius（Dify 团队）开源的**图执行引擎**，专门用于编排和执行 Agent 工作流[^graphon-readme]。

### 技术亮点

- **队列驱动的事件编排**：基于队列的 `GraphEngine`，事件驱动执行
- **图解析与验证**：完整的图解析、验证和流式构建 API
- **共享运行时状态**：统一的 `GraphRuntimeState`、`VariablePool` 和工作流执行领域模型
- **内置节点实现**：提供 20+ 种内置节点类型（start、llm、tool、if-else、loop 等）
- **可插拔模型运行时**：统一的模型运行时接口，支持本地 `SlimRuntime` 和分布式运行时
- **集成协议**：HTTP、文件、工具、人机输入的标准协议
- **可扩展引擎层**：支持自定义引擎层和外部命令通道

### 与 Dify 的关系

```
Dify (应用层)
  - Web UI、Agent 管理、知识库、工具集成
  ↓ 依赖
graphon (执行引擎层)
  - 图解析、节点编排、变量系统、模型抽象
```

**设计优势**：
- **关注点分离**：graphon 专注图执行逻辑，Dify 专注应用层功能
- **可复用性**：graphon 可被其他项目独立使用
- **版本独立**：graphon 可独立迭代，不依赖 Dify 发布周期

[^dify-pyproject]

## 技术亮点

- **可视化工作流编排**：通过 Web UI 拖拽节点构建 Agent 工作流（LLM 调用、条件分支、工具调用、代码执行），无需写代码即可组装复杂流程。适合快速原型验证和非工程背景用户
- **内置 RAG 管线**：平台内集成文档上传、分块、嵌入、向量存储和检索全流程，与 Agent 工作流无缝衔接。省去自建 [RAG](../applied/rag.md) 基础设施的工程量
- **Backend-as-a-Service**：构建的应用直接暴露 API 端点，可作为后端服务集成到现有系统中
- **Graphon 执行引擎**：基于自研的图执行引擎，提供统一的节点抽象、变量系统和事件流，支持自定义节点和运行时扩展

## 参考资料

[^dify-docs]: Dify. *Dify Documentation*. https://docs.dify.ai/
[^graphon-readme]: LangGenius. *Graphon README*. https://github.com/langgenius/graphon
[^dify-graph-structure]: Dify. *api/models/workflow.py*. Workflow 模型的 `graph_dict` 属性返回解析后的 JSON 结构。https://github.com/langgenius/dify
[^dify-node-types]: Dify. *api/core/workflow/nodes/*. 节点类型实现目录。https://github.com/langgenius/dify
[^dify-agent-node]: Dify. *api/core/workflow/nodes/agent/agent_node.py*, *api/core/agent/cot_agent_runner.py*. Agent 节点实现和执行逻辑。https://github.com/langgenius/dify
[^dify-pyproject]: Dify. *api/pyproject.toml*. Dify 依赖 `graphon~=0.2.2`。https://github.com/langgenius/dify
