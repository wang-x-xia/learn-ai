---
title: Agent Workflow 框架档案
description: 主流 Agent Workflow 框架的技术档案，聚焦架构差异与设计权衡。
---

# Agent Workflow 框架档案

每个框架一个文件，聚焦**技术区分度**——架构差异、核心抽象、独到的设计决策。跳过所有框架共有的通用能力。

Agent 的共性概念（执行循环、记忆、协议）见[应用技术](../agent/ai-agents.md)。

<div class="grid cards" markdown>

- :material-graph-outline: **[LangGraph](langgraph.md)**

    ---

    LangChain · Python/JS · 基于图的 Agent 工作流

- :material-source-branch: **[Ruflo](ruflo.md)**

    ---

    RuvNet · TypeScript · Claude Code 的外挂式 Agent 控制平面

- :material-microsoft: **[Microsoft Agent Framework](maf.md)**

    ---

    Microsoft · C#/Python · 生产级 AI Agent 与多 Agent 工作流

- :material-palette: **[Dify](dify.md)**

    ---

    Dify · Python/TS · 可视化 AI 应用平台

- :material-eye-check: **[NeMo Agent Toolkit](nemo-agent-toolkit.md)**

    ---

    NVIDIA · Python · 跨框架 Agent 可观测性与安全运行时

</div>

## 横向对比

| 维度 | LangGraph | Ruflo | MAF | Dify | NeMo Agent Toolkit |
|------|-----------|-------|-----|------|--------------------|
| **抽象层次** | 编排框架 | 编排框架 | 编排框架 | 可视化平台 | 元框架 |
| **执行模型** | 静态图 + 动态调度 | CLI 编排控制平面 | 双模式（Functional / Graph） | 可视化工作流 + Graphon 引擎 | YAML 配置驱动函数编排 |
| **状态管理** | 图状态持久化 + Checkpointing | 向量记忆层 + Session 快照 | 步骤级 Checkpointing | Graph JSON + 节点级状态 | 参数覆盖 + 热更新 |
| **语言** | Python / JS | TypeScript | C# / Python | Python / TS | Python |
| **适用场景** | 复杂多步 Agent 编排 | 多拓扑 Agent 协调 | 企业级工作流 | 低代码 AI 应用搭建 | 跨框架统一编排 |
| **核心权衡** | 灵活但学习曲线陡 | 功能丰富但生态较小 | 类型安全但绑定 .NET 生态 | 易上手但定制灵活性有限 | 统一抽象但增加间接层 |
