# docs/ai-personal-software/ — AI 个人软件产品档案

每个产品一个 `.md` 文件，聚焦**技术区分度**。

## 收录范围

面向个人开发者的 AI 软件产品——包括编码 Agent、通用个人助手等。
强调技术方案革新与工程亮点，跳过行业标配功能。

## 写法指南

- **属性表 + 一句话定位**：保留，用于快速识别
- **技术亮点**：只写该产品**独有或领先**的架构设计，跳过通用能力（如"支持多模型"、"代码补全"、"Chat 对话"）
- **定价**：保留（如适用），简明即可
- 不写教程代码，不搬运 README

## 模板

```markdown
---
title: "产品名"
description: 一句话定位
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - product
  - vendor-name
review:
---

# 产品名

> 一句话定位（厂商 + 核心形态 + 最大区分点）

| 属性 | 值 |
|------|-----|
| 厂商 | ... |
| 形态 | ... |
| 开源 | 是/否 |
| 官网 | [链接](url) |

## 技术亮点

- **亮点一**：（只写该产品独有或领先的能力，不写行业标配）
- **亮点二**：...

## 参考资料

[^key]: Author. "Title". Year. URL
```

## 品类共性

Agent 的共性概念在 `docs/agent/` 下集中说明：

- 执行循环 → `docs/agent/ai-agents.md`
- 记忆系统 → `docs/agent/memory-systems.md`
- 工具接入 → `docs/agent/agent-tools.md`
- Agent Skills → `docs/agent/agent-skills.md`
