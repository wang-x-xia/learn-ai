---
title: LangGraph
description: LangChain 团队出品的图驱动 Agent 编排框架，用有向图建模 Agent 工作流。
created: 2026-04-10
updated: 2026-05-07
tags: [framework, langchain, agent, python, javascript]
review: 2026-05-07
---

# LangGraph

??? note "背景知识"
    - **Agent 执行循环**：思考→行动→观察的迭代 → [详见](../agent/ai-agents.md)
    - **有向图 (DAG)**：节点 + 有向边的数据结构，用于建模工作流中的步骤和转移
    - **状态机**：系统在有限状态间根据事件转移，用于控制 Agent 工作流

> LangChain 团队出品，用**有向图**（而非线性链）建模 Agent 工作流——节点是计算步骤，边是状态转移。

| 属性 | 值 |
|------|-----|
| 厂商 | LangChain |
| 语言 | Python / JavaScript |
| 开源 | 是 |
| GitHub | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) |
| 官网 | [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/)[^langgraph-docs] |

## 技术亮点

- **静态图定义 + 动态任务调度**：节点和边在构建阶段（`compile` 之前）静态定义，形成固定的图结构；运行时通过条件边和 `Send` 机制动态决定执行路径。这种设计兼顾了可验证性（静态图可分析、可可视化）和灵活性（运行时可分支），避免了一些动态图框架的复杂度和不确定性
- **图即工作流**：Agent 的执行逻辑表达为 `StateGraph`——节点是函数（agent 推理、工具调用、人类审批等），边定义状态转移和条件分支。相比线性 Chain，图天然支持循环、分支、并行，直接对应 [ReAct 循环](../agent/ai-agents.md)的 Think→Act→Observe→Think 回路
- **状态持久化（Checkpointing）**：每个节点执行后自动保存图状态快照，支持断点恢复、时间旅行（回退到任意历史节点）、人机交互中断与继续。这是 long-running Agent 的关键基础设施
- **LangChain 生态集成**：与 LangChain 的模型抽象、工具接口、向量存储无缝集成，可复用 LangChain 生态中的大量现成组件

## 执行模型

### Graph 与 Node 的关系

LangGraph 采用**静态图定义**：图是节点和边的容器，节点是 Python 函数，边定义节点间的转移关系。节点在构建阶段注册到图中，形成固定的图结构，编译后不可再修改。图本身是构建器（`StateGraph`），编译后变为可执行对象（`CompiledStateGraph`）。

### Graph 的生命周期

1. **创建**：`StateGraph(state_schema)` 初始化空的图结构
2. **构建**：通过 `add_node()`、`add_edge()`、`add_conditional_edges()` 逐步定义图结构
3. **编译**：`compile()` 验证图结构完整性，创建执行引擎（Pregel），图变为可执行状态
4. **执行**：每次 `invoke()` 或 `stream()` 创建独立执行上下文，按图结构逐步执行节点
5. **销毁**：图对象被垃圾回收，相关资源释放

编译后的图可多次调用，每次调用互不干扰。

### Node 的生命周期

节点本质上是 Python 函数，生命周期分为：

- **定义**：模块加载时函数定义一次
- **注册**：构建时通过 `add_node()` 注册到图中，获得唯一名称
- **执行**：运行时可能被多次调用（每次 `invoke` 可能触发多次），每次执行独立无状态
- **销毁**：随进程结束而消失

节点函数本身无状态，但执行时可通过 `state` 参数访问共享状态，通过闭包捕获外部配置（如 model、tools）。所有持久化状态必须存储在共享 state 中，不能存在节点内部。

### 节点触发机制

节点通过以下方式触发其他节点：

- **静态边**：`add_edge("node_a", "node_b")` 定义固定转移，`node_a` 执行后总是触发 `node_b`
- **条件边**：`add_conditional_edges("node_a", router_func, ["node_b", END])` 根据运行时状态决定触发哪个节点
- **Send 机制**：节点返回 `Send("target_node", arg)` 列表，动态批量触发目标节点（支持并发）。**Send 只能触发已注册的节点**，不能动态创建节点；可通过节点的 `destinations` 参数进一步限制可触发的目标范围。Send 主要用于 map-reduce、动态数量等确定性模式，而非随意跳转

所有触发机制都基于**channel 更新**：节点执行后产生 writes，更新的 channel 触发依赖该 channel 的节点。如果没有 channel 被更新，或更新的 channel 没有触发任何节点，执行自然结束。

### 死循环预防

LangGraph 提供多层防护机制：

- **步数限制**：通过 `recursion_limit` 配置最大执行步数，超过则抛出异常
- **超时控制**：通过 `timeout` 配置执行时间上限，节点级别或图级别均可设置
- **中断机制**：`interrupt_before`/`interrupt_after` 在指定节点暂停执行，允许人工检查和干预
- **条件边终止**：条件边函数必须包含明确的终止逻辑（返回 `END`），设计层面防止无限循环
- **Retry Policy**：限制节点重试次数，避免因错误导致的无限重试循环
- **图结构验证**：编译时检测孤立节点、不可达节点、无终止条件的循环

## 与 LangChain 的关系

LangChain 是组件库（模型、工具、检索器等标准抽象），LangGraph 是编排层（定义这些组件如何协作）。LangChain 提供"零件"，LangGraph 提供"装配图"。

## 参考资料

[^langgraph-docs]: LangChain. *LangGraph Documentation*. https://langchain-ai.github.io/langgraph/
