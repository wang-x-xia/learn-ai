---
title: "Claude Code"
description: Anthropic 出品的终端编程 Agent，直接在命令行中完成端到端编码任务。
created: 2026-04-08
updated: 2026-04-08
tags: [product, anthropic, coding, cli, agent]
---

# Claude Code

> Anthropic 出品的终端编程 Agent，直接在命令行中完成端到端编码任务。

| 属性 | 值 |
|------|-----|
| 厂商 | Anthropic |
| 形态 | CLI / VS Code & JetBrains 扩展 / Web |
| 开源 | 是 ([GitHub](https://github.com/anthropics/claude-code)) |
| 技术栈 | TypeScript, Node.js, ink (React for CLI) |
| 底座模型 | Claude Sonnet 4/4.6（默认）、Opus 4/4.6（复杂任务）、Haiku 3.5（轻量子任务） |
| 官网 | [docs.anthropic.com/claude-code](https://docs.anthropic.com/en/docs/claude-code/overview) |

## 技术亮点

- **Subagent 并行架构**：为独立子任务派生并行 Agent（[博客](https://claude.com/blog/subagents-in-claude-code)）。这是 Agentic 编码中的架构创新——主 Agent 将任务分解后，子 Agent 各自拥有独立上下文窗口并发执行，最终结果汇总。解决了单一 Agent 串行瓶颈问题，也让 1M token 上下文窗口在长会话中得到更有效的分配
- **Agentic Loop 与上下文管理**：核心循环为 Think → Tool Use → Observe → Think（ReAct 模式）。真正值得关注的是其在 1M 上下文窗口内的会话管理策略——长任务中如何剪枝、压缩、分配上下文是 Agent 工程的核心难题，Claude Code 依靠超长窗口 + Subagent 分治来应对
- **CLAUDE.md 约定**：通过项目根目录的 `CLAUDE.md` 文件为 Agent 注入上下文和指令（构建命令、代码规范、架构约束等）。设计哲学是用一个纯文本文件替代复杂配置系统——零学习成本，版本可控，团队共享。这一模式已被 Codex（`AGENTS.md`）等工具效仿
- **Headless / SDK 模式**：`@anthropic-ai/claude-code` 作为可编程库暴露，同一个 Agent 既能交互式运行，也能以无头模式嵌入 CI/CD pipeline。架构意义在于：Agent 不再局限于人机交互，可以无人值守地执行代码审查、测试修复等任务
- **细粒度权限模型**：文件写入、命令执行、网络访问等工具调用可独立审批或预授权。这是自主 Agent 安全架构的关键设计——在 Auto Mode（无需逐步审批）下尤为重要，用户可精确划定 Agent 的自主边界
- **ink (React for CLI)**：技术栈选择 ink 框架，将 React 的组件化渲染模型引入终端 UI。使得复杂的交互状态（多 Agent 并行输出、权限弹窗、流式响应）可以用声明式组件管理

## 定价

- CLI 工具免费开源，按 Anthropic API 用量计费
- 也可通过 Claude Pro ($20/月) / Max ($100-200/月) 订阅使用

## 参考资料

- [Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code/overview)
- [GitHub 仓库](https://github.com/anthropics/claude-code)
