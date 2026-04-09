---
title: "Cursor"
description: Anysphere 出品的 AI 代码编辑器，VS Code fork，以自研补全模型和代理架构见长。
created: 2026-04-08
updated: 2026-04-08
tags: [product, anysphere, coding, ide, agent]
---

# Cursor

> Anysphere 出品的 AI 代码编辑器，VS Code fork，以自研补全模型和代理架构见长。

| 属性 | 值 |
|------|-----|
| 厂商 | Anysphere |
| 形态 | 桌面 IDE（macOS / Windows / Linux） |
| 开源 | 否（基于 VS Code 开源 fork，AI 层闭源） |
| 技术栈 | Electron, TypeScript, React |
| 底座模型 | GPT-4o, Claude Sonnet, Gemini 2.5 Pro, `cursor-small`（自研） |
| 官网 | [cursor.com](https://www.cursor.com/) |

## 技术亮点

- **自研 `cursor-small` 补全模型**：专门为低延迟 Tab 补全微调的小模型。与直接调用通用 LLM 做补全不同，Cursor 选择训练一个专用模型来优化延迟和补全质量之间的平衡——这是一个有意义的工程取舍。
- **AI Proxy 架构**：所有 LLM 调用统一经由 Cursor 代理服务器路由，实现计量、缓存和隐私控制。这种集中式路由设计使得模型切换、A/B 测试和成本优化成为可能，是其基础设施层面的关键决策。
- **代码库向量索引**：打开项目时自动构建 embedding 索引，驱动语义搜索。工程难点在于增量更新策略和大规模代码库的处理效率。
- **Background Agents（Beta）**：在云端沙箱中异步执行任务，用户可在本地继续工作。将 Agent 运行环境与用户编辑环境分离，是一种值得关注的架构尝试。
- **VS Code fork 策略**：选择 fork VS Code 而非做插件，获得了对编辑器体验的深度控制权，代价是需要持续跟踪上游变更的维护负担。

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| Hobby | 免费 | 50 次高级模型请求/月 |
| Pro | $20/月 | 500 次快速请求/月，无限补全 |
| Business | $40/人/月 | 团队管理、SSO |

## 参考资料

- [Cursor 官网](https://www.cursor.com/)
- [Cursor 文档](https://docs.cursor.com/)
