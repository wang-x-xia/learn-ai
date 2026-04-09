---
title: "Gemini Code Assist"
description: Google 的 AI 编码助手，核心差异在于 Gemini 原生长上下文窗口和 Google Cloud 生态绑定。
created: 2026-04-08
updated: 2026-04-08
tags: [product, google, coding, ide]
review:
---

# Gemini Code Assist

> Google 的 AI 编码助手，核心差异在于 Gemini 原生长上下文窗口和 Google Cloud 生态绑定。

| 属性 | 值 |
|------|-----|
| 厂商 | Google |
| 形态 | IDE 扩展（VS Code / JetBrains）、Cloud Shell、Google Cloud Console |
| 开源 | 否 |
| 技术栈 | TypeScript (VS Code 扩展), Google Cloud 后端 |
| 底座模型 | Gemini 2.5 Pro / Flash |
| 官网 | [cloud.google.com/gemini/docs/codeassist](https://cloud.google.com/gemini/docs/codeassist/overview) |

## 技术亮点

- **Gemini 1M+ 原生长上下文**：无需分块或 RAG，直接将大规模代码库放入单次 prompt。这在技术上有实际意义——避免了检索环节的信息损失，模型一次性看到完整上下文。
- **Full Codebase Awareness（Enterprise）**：可索引组织级跨仓库代码库，提供跨仓库上下文理解。
- **Jules 异步 Agent**：Google 另推出的异步编码 Agent，从 GitHub Issue 出发自主完成编码并提交 PR。

除长上下文优势和 Google Cloud 绑定外，技术独特性有限。

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| 个人 | 免费 | 有限额度 |
| Standard | $19/人/月 | 团队使用 |
| Enterprise | $45/人/月 | 代码定制、组织代码库索引 |

## 参考资料

- [Gemini Code Assist](https://cloud.google.com/gemini/docs/codeassist/overview)
