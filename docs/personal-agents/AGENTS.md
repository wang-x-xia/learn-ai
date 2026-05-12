# docs/personal-agents/ — 个人 AI Agent 产品档案

每个产品一个 `.md` 文件，聚焦**技术区分度**。

## 收录范围

通用型个人 AI Agent——不限于编码场景，强调跨会话学习、自主任务执行、多平台接入。
与 `coding-agents/` 的区别：编码 Agent 专精代码生成/修复，本目录收录的产品定位为**通用个人助手**。

## 写法指南

- **属性表 + 一句话定位**：保留，用于快速识别
- **技术亮点**：只写该产品**独有或领先**的架构设计，跳过通用能力（如"支持多模型"、"对话式交互"）
- 不写教程代码，不搬运 README

## 模板

```markdown
---
title: "产品名"
description: 一句话定位
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: product, vendor-name, personal-agent
review:
---

# 产品名

> 一句话定位（厂商 + 核心定位 + 最大区分点）

| 属性 | 值 |
|------|-----|
| 厂商 | ... |
| 语言 | ... |
| 开源 | 是/否 |
| GitHub | [链接](url) |
| 官网 | [链接](url) |

## 技术亮点

- **亮点一**：（只写该产品独有或领先的架构设计）
- **亮点二**：...

## 参考资料

[^key]: Author. "Title". Year. URL
```

## 品类共性

个人 Agent 的共性概念在 `docs/applied/` 下的品类概述文档中集中说明：

- 执行循环 → `docs/applied/ai-agents.md`
- 记忆系统 → `docs/applied/memory-systems.md`
- 工具接入 → `docs/applied/agent-tools.md`
- Agent Skills → `docs/applied/agent-skills.md`
