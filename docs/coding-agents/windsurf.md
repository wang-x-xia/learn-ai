---
title: "Windsurf"
description: Codeium 出品的 AI IDE，2025 年被 OpenAI 以 ~$3B 收购。
created: 2026-04-08
updated: 2026-04-08
tags: [product, codeium, openai, coding, ide, agent]
---

# Windsurf

> Codeium 出品的 AI IDE，2025 年被 OpenAI 以 ~$3B 收购。

| 属性 | 值 |
|------|-----|
| 厂商 | Codeium → OpenAI (2025 收购) |
| 形态 | 桌面 IDE（macOS / Windows / Linux） |
| 开源 | 否（基于 VS Code 开源 fork，AI 层闭源） |
| 技术栈 | Electron, TypeScript |
| 底座模型 | GPT-4o, Claude Sonnet, Gemini + Codeium 自研补全模型 |
| 官网 | [windsurf.com](https://windsurf.com/) |

## 技术亮点

- **Cascade 引擎的响应式感知**：与 Cursor Composer 等 Agent 的核心区别在于，Cascade 采用事件驱动架构——订阅 IDE 状态变更（终端输出、lint 错误等）并自动响应，而非仅在用户主动提示时才行动。
- **Codeium 自研补全模型**：快速补全基于自研小模型，而非简单包装 OpenAI API——这是 Codeium 最初的核心产品。
- **被 OpenAI 收购（~$3B）**：战略意义大于当前技术意义，未来可能意味着与 OpenAI 模型的深度整合。

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| Free | 免费 | 有限 AI 功能额度 |
| Pro | $15/月 | 无限补全，高级模型请求 |
| Team | $30/人/月 | 团队管理 |

## 参考资料

- [Windsurf 官网](https://windsurf.com/)
