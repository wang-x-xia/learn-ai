# docs/agent-workflow/ — Agent Workflow 框架档案

每个框架一个 `.md` 文件，聚焦**Workflow 技术区分度**。

## 写法指南

- **属性表 + 一句话定位**：保留，用于快速识别
- **技术亮点**：只写该框架**独有或领先**的架构设计，跳过所有框架共有的能力（如"支持多模型"、"支持工具调用"）
- 不写教程代码，不搬运 README

## 模板

```markdown
---
title: "框架名"
description: 一句话定位
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [framework, vendor-name, agent]
review:
---

# 框架名

> 一句话定位（厂商 + 核心定位 + 最大区分点）

| 属性 | 值 |
|------|-----|
| 厂商 | ... |
| 语言 | ... |
| 开源 | 是/否 |
| GitHub | [链接](url) |
| 官网 | [链接](url) |

## 技术亮点

- **亮点一**：（只写该框架独有或领先的架构设计）
- **亮点二**：...

## 参考资料

[^key]: Author. "Title". Year. URL
```

## 品类共性

Agent Workflow 框架的共性概念（执行循环、记忆系统、协议）在 `docs/applied/` 下的品类概述文档中集中说明：

- 执行循环 → `docs/applied/ai-agents.md`
- 记忆系统 → `docs/applied/memory-systems.md`
- 工具接入 → `docs/applied/agent-tools.md`
- Agent Skills → `docs/applied/agent-skills.md`
- Agent 间协议 → `docs/applied/agent-protocols.md`
