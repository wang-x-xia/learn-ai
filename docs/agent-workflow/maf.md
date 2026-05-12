---
title: Microsoft Agent Framework
description: Microsoft 的生产级 AI Agent 框架，融合 AutoGen 和 Semantic Kernel，以图-based Workflow 编排和多源 Skills 架构支持企业级多 Agent 系统。
created: 2026-04-10
updated: 2026-05-07
tags:
  - framework
  - microsoft
  - agent
  - csharp
  - python
  - enterprise
  - workflow
review: 2026-05-07
---

# Microsoft Agent Framework

??? note "背景知识"
    - **Agent 执行循环**：思考→行动→观察的迭代 → [详见](../agent/ai-agents.md)
    - **Agent Skills**：声明式能力描述，告诉 Agent 遇到特定问题该怎么做 → [详见](../agent/agent-skills.md)
    - **有向图工作流**：用节点和边建模 Agent 的执行步骤与状态转移

> Microsoft 出品的生产级 AI Agent 框架，是 Semantic Kernel 和 AutoGen 的继任者。核心定位是**构建生产就绪的 AI Agent 和多 Agent 工作流**——以图-based Workflow 实现显式编排，以多源 Skills 架构统一知识管理。

| 属性 | 值 |
|------|-----|
| 厂商 | Microsoft |
| 语言 | C# / Python |
| 开源 | 是 |
| GitHub | [microsoft/agent-framework](https://github.com/microsoft/agent-framework) |
| 官网 | [learn.microsoft.com/agent-framework](https://learn.microsoft.com/en-us/agent-framework/)[^maf-docs] |
| 状态 | Preview（Semantic Kernel v1.x 仍支持） |

> **注**：Semantic Kernel 已演进为 Microsoft Agent Framework (MAF)。Semantic Kernel v1.x 仍会继续维护（修复关键 bug 和安全问题），但新功能主要在 MAF 中开发。详见 [迁移指南](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-semantic-kernel)。[^maf-migration]

## 技术亮点

- **图-based Workflow 编排**：不同于 Semantic Kernel 的隐式函数调用，MAF 提供显式的图结构编排，支持 sequential、concurrent、handoff、group collaboration 等模式，配合 checkpointing 实现长时间运行和 human-in-the-loop 场景的状态持久化。这是 MAF 相比前代最核心的架构革新
- **多源 Skills 架构**：统一的技能系统支持从文件系统（SKILL.md）、内联代码、类库三种来源定义 Skills，通过抽象基类 `AgentSkill`、`AgentSkillResource`、`AgentSkillScript` 实现统一管理。文件-based Skills 支持自定义 script executor（如 Python/shell），程序化 Skills 支持进程内执行。这种设计让 Agent 可以灵活发现和使用领域知识，而无需重写代码
- **生产级状态管理**：Session-based state management 配合 checkpointing，支持长时间运行 Agent 的暂停、恢复、time-travel。这是 Semantic Kernel 企业级能力的延续和增强
- **DevUI 交互式开发**：内置交互式开发者界面，用于 Agent 开发、测试、调试 workflows，填补了传统 SDK 开发的体验空白[^maf-devui]

## 执行模型

MAF 的执行模型基于 Executor 和 Edge 的图结构编排[^maf-workflows]。

### 双模式架构

MAF 提供两种 Workflow 模式，满足不同复杂度的需求：

- **Functional 模式**：用普通 Python async 函数写 workflow，没有图概念，用原生控制流（`if`/`else`、`asyncio.gather`）实现分支和并行。适合简单场景和快速原型
- **Graph-based 模式**：使用 Executor 和 Edges 的图结构编排，支持显式的状态转移和条件路由。适合复杂的多 Agent 协作和长时间运行场景

### Graph-based 模式的核心概念

#### Executor 与 WorkflowContext

Executor 是 MAF 中的计算单元，有两种定义方式[^maf-executors]：

1. **自定义 Executor 子类**：继承 `Executor` 类，用 `@handler` 装饰器标记异步方法
2. **函数式 Executor**：用 `@executor` 装饰器直接装饰异步函数

WorkflowContext 是执行上下文，提供两个关键方法：
- `ctx.send_message(result)`：向下游 Executor 发送消息
- `ctx.yield_output(result)`：产生工作流最终输出

WorkflowContext 支持泛型参数：
- `WorkflowContext[T_Out]`：向下游发送 T_Out 类型的消息
- `WorkflowContext[Never, str]`：不发送消息，但产生 str 类型的最终输出
- `WorkflowContext[str, str]`：既发送 str 消息，又产生 str 最终输出

#### 类型系统

MAF 提供两种类型声明方式：

1. **类型内省**：从函数签名自动推断输入输出类型
2. **显式类型参数**：在 `@handler(input=str, output=int, workflow_output=bool)` 中显式声明。这是"全有或全无"模式——一旦提供任何显式参数，就完全禁用内省

显式类型参数适用于：
- 接受联合类型（`str | int`）而不需要复杂的类型注解
- 函数签名使用 `Any` 或基类型以保持灵活性
- 将运行时类型路由与静态类型注解解耦

#### Edge 与条件路由

Edge 连接 Executor，定义消息流转路径。MAF 支持多种 Edge 类型：

- **静态边**：`add_edge(A, B)` 定义固定转移，A 执行后总是触发 B
- **条件边**：`add_edge(A, B, condition=predicate)` 根据上游输出决定是否激活边。条件函数接收上游输出，返回布尔值
- **Switch-case 边组**：基于分类器输出选择分支
- **多选边组**：动态选择一个或多个目标（子集 fan-out）

条件路由常用于 Agent 响应的分类场景，如根据 Agent 的结构化输出（`DetectionResult.is_spam`）决定路由到不同的处理流程[^maf-edge-condition]。

### Workflow 的生命周期

1. **创建**：通过 `WorkflowBuilder(start_executor=executor)` 初始化
2. **构建**：通过 `add_edge()` 逐步定义图结构
3. **编译**：`build()` 创建可执行的 `Workflow` 对象
4. **执行**：`await workflow.run(initial_input)` 执行工作流，返回事件集合
5. **销毁**：工作流对象被垃圾回收

### Checkpointing 与状态持久化

MAF 支持多层次的 Checkpointing：

- **步骤级 Checkpointing**：`@step` 装饰器为每个步骤提供 checkpointing 和可观测性
- **工作流级 Checkpointing**：支持暂停、恢复、时间旅行（回退到任意历史状态）
- **持久化存储**：支持 `CosmosCheckpointStorage` 等持久化后端，实现跨会话的状态恢复

Checkpointing 与 Human-in-the-loop 深度集成：工作流可在 checkpoint 处暂停，等待人工审批后继续执行。

### Human-in-the-loop

MAF 提供多种 HITL 模式：

- **交互式请求/响应**：通过 `ctx.request_info()` 与人类交互
- **审批请求**：Agent 在执行过程中创建审批请求，等待人工批准后继续
- **声明式工具**：当 Agent 调用客户端工具（`func=None`）时，工作流暂停，调用者提供结果

### 与 LangGraph 的对比

| 维度 | LangGraph | MAF |
|------|----------|-----|
| 图定义 | 静态图（compile 前定义） | 双模式：functional（无图）+ graph-based（动态构建） |
| 节点定义 | Python 函数 | Executor 子类或 @executor 装饰函数 |
| 状态管理 | 共享 state 对象 | WorkflowContext + send_message/yield_output |
| 条件路由 | add_conditional_edges + router_func | add_edge + condition predicate |
| 并行 | Send 机制（批量触发） | functional 模式用 asyncio.gather |
| 类型系统 | 无显式类型系统 | 支持类型内省和显式类型参数 |
| Checkpointing | 自动保存快照 | @step 装饰器 + 持久化存储 |

## 参考资料

[^maf-docs]: Microsoft. *Microsoft Agent Framework Documentation*. https://learn.microsoft.com/en-us/agent-framework/
[^maf-migration]: Microsoft. *Semantic Kernel and Microsoft Agent Framework*. 2025-10-07. https://devblogs.microsoft.com/agent-framework/semantic-kernel-and-microsoft-agent-framework
[^maf-devui]: Microsoft Agent Framework README. *DevUI: Interactive developer UI*. https://github.com/microsoft/agent-framework
[^maf-workflows]: Microsoft Agent Framework. *Workflows Getting Started Samples*. https://github.com/microsoft/agent-framework/tree/main/python/samples/03-workflows
[^maf-executors]: Microsoft Agent Framework. *Executors and Edges Sample*. https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/_start-here/step1_executors_and_edges.py
[^maf-edge-condition]: Microsoft Agent Framework. *Edge Condition Sample*. https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/control-flow/edge_condition.py
