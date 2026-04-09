# docs/applied/ — 应用技术

工程方法与实践，中频更新。

## 文件列表

| 文件 | 主题 |
|------|------|
| `ai-agents.md` | AI Agent 智能体（框架、协议、趋势） |
| `agent-hooks.md` | Agent 生命周期钩子 |
| `subagents.md` | Subagent / 多 Agent 架构 |
| `prompt-engineering.md` | 提示工程 |
| `rag.md` | 检索增强生成 |
| `infrastructure.md` | 硬件 / 推理 / 部署基础设施 |

## 收录哪些内容

- Agent 框架 / 协议 → `ai-agents.md`
- Agent 生命周期钩子 → `agent-hooks.md`
- Subagent / 多 Agent 架构 → `subagents.md`
- 提示技巧 / 框架 → `prompt-engineering.md`
- RAG 新方法 → `rag.md`
- 硬件 / 推理 / 部署 → `infrastructure.md`

## Frontmatter 要求

```yaml
---
title: 文档标题
description: 一句话描述
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
review: YYYY-MM-DD
---
```

六个字段必填（`review` 留空表示从未 review）。每次修改内容时更新 `updated`，每次阅读审校后更新 `review`。
