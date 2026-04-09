---
title: "Kilo Code"
description: Cline/Roo Code 的下游分支，在继承全部基础能力之上增加了多模式工作流和快照回滚。
created: 2026-04-08
updated: 2026-04-08
tags: [product, coding, vscode, agent, open-source]
review:
---

# Kilo Code

> Cline/Roo Code 的下游分支，在继承全部基础能力之上增加了多模式工作流和快照回滚。

| 属性 | 值 |
|------|-----|
| 厂商 | Kilo Code（社区驱动） |
| 形态 | VS Code 扩展（兼容 Cursor、Windsurf 等 fork） |
| 开源 | 是，Apache 2.0 ([GitHub](https://github.com/kilocode-ai/kilocode)) |
| 技术栈 | TypeScript, React（Webview UI） |
| 谱系 | Claude Dev → Cline → Roo Code → **Kilo Code** |
| 官网 | [kilocode.ai](https://kilocode.ai/) |

## 技术亮点

以下仅列出相对上游 Cline 的增量差异；基础架构（原生 tool calling、本地直连、Webview UI）均继承自 Cline。

- **多模式工作流（Code / Architect / Ask / Debug）**：每个模式拥有独立的系统提示词和工具权限集。例如 Architect 模式可禁用文件写入只做方案设计，Debug 模式可自动附加错误上下文。本质上是用"角色 × 工具权限矩阵"实现同一 Agent 的多种行为约束。
- **Checkpoint / 快照系统**：Agent 执行过程中自动创建快照，用户可一键回滚到任意检查点。这是对"Agent 失控"问题的工程化安全网——无需手动 git stash，直接恢复文件系统状态。

## 定价

- 扩展完全免费开源，仅按模型 API 用量付费。

## 参考资料

- [Kilo Code 官网](https://kilocode.ai/)
- [GitHub 仓库](https://github.com/kilocode-ai/kilocode)
