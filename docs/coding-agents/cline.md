---
title: "Cline"
description: Cline fork 家族的架构原型——定义了"VS Code 扩展 + LLM 原生工具调用 = 自主编码 Agent"这一模式。
created: 2026-04-08
updated: 2026-04-08
tags: [product, coding, vscode, agent, open-source]
review:
---

# Cline

> Cline fork 家族的架构原型——定义了"VS Code 扩展 + LLM 原生工具调用 = 自主编码 Agent"这一模式。

| 属性 | 值 |
|------|-----|
| 厂商 | 社区（Saoud Rizwan 发起） |
| 形态 | VS Code 扩展 |
| 开源 | 是，Apache 2.0 ([GitHub](https://github.com/cline/cline)) |
| 技术栈 | TypeScript, React（Webview UI） |
| 官网 | [cline.bot](https://cline.bot/) |

## 技术亮点

- **Fork 谱系始祖**：Claude Dev → **Cline** → Roo Code → Kilo Code。Cline 定义了整条产品线的架构范式：将 LLM 通过原生工具调用变为自主编码 Agent 的 VS Code 扩展。后续分支在此基础上做增量创新。
- **原生 function calling 驱动的 Tool-use 架构**：文件读写、终端执行、搜索等操作均通过模型原生 function/tool calling 触发，而非 prompt 工程拼接指令。这一设计决策让工具调用的可靠性直接取决于模型的 tool-use 能力，是与 prompt-based 方案的根本区别。
- **本地直连，无后端服务器**：API 请求从扩展直接发往模型提供商，不经过任何中间服务器。隐私与延迟优势明显。
- **Webview ↔ Extension Host 通信**：React 侧栏 UI 通过 `postMessage` 与 VS Code Extension Host 双向通信。这是所有 fork 继承的 UI 架构模板。

## 定价

- 完全免费开源，仅按模型 API 用量付费。

## 参考资料

- [Cline 官网](https://cline.bot/)
- [GitHub 仓库](https://github.com/cline/cline)
