---
title: "Sourcegraph Cody"
description: Sourcegraph 的 AI 编码助手，核心差异在于用代码图谱（而非 embedding 检索）驱动上下文，是架构层面的根本不同。
created: 2026-04-08
updated: 2026-04-08
tags: [product, sourcegraph, coding, ide, open-source]
review:
---

# Sourcegraph Cody

> Sourcegraph 的 AI 编码助手，核心差异在于用代码图谱（而非 embedding 检索）驱动上下文，是架构层面的根本不同。

| 属性 | 值 |
|------|-----|
| 厂商 | Sourcegraph |
| 形态 | VS Code / JetBrains 扩展、Web (sourcegraph.com) |
| 开源 | 客户端 Apache 2.0 ([GitHub](https://github.com/sourcegraph/cody))；Sourcegraph 后端 source-available |
| 技术栈 | TypeScript (VS Code), Kotlin (JetBrains) |
| 底座模型 | 多模型：Claude Sonnet, GPT-4o, Gemini, Mixtral + Sourcegraph 自研补全模型 |
| 官网 | [sourcegraph.com/cody](https://sourcegraph.com/cody) |

## 技术亮点

- **代码图谱驱动的上下文检索**：这是 Cody 的核心差异化。多数竞品（Copilot、Cursor 等）使用 embedding 相似性搜索来检索上下文——本质上是把代码当文本处理。Cody 基于 Sourcegraph 的代码搜索引擎，理解符号索引、依赖关系图、跨仓库引用。这提供的是结构精确的上下文，而非语义相似的文本。这是解决上下文检索问题的一种根本不同的技术路径。
- **多仓库理解**：企业场景下可同时理解数百个关联仓库。这依赖于图谱方法——embedding 检索在跨仓库引用场景下的扩展性不佳。当代码分散在数百个仓库中且互相依赖时，图谱索引可以追踪这些引用关系，而 embedding 只能给出"看起来相似"的代码片段。
- **Context Window 智能管理**：在有限的模型上下文窗口内，智能选择最相关的上下文片段。由于 Cody 拥有更丰富的代码图谱信息，其选择算法比纯基于 embedding 相似度排序的方案更为精细——可以基于依赖关系、调用链路等结构信息做优先级判断。
- **StarCoder 微调补全模型**：自研的快速补全模型，基于 StarCoder 微调，可自托管部署，针对低延迟补全场景优化。

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| Free | 免费 | 有限补全和 Chat |
| Pro | $9/月 | 无限补全和 Chat |
| Enterprise | 自定义 | 多仓库索引、私有部署 |

## 参考资料

- [Sourcegraph Cody](https://sourcegraph.com/cody)
- [GitHub 仓库](https://github.com/sourcegraph/cody)
