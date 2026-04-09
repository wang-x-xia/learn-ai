---
title: "Continue"
description: 以 Config-as-Code 和可扩展上下文系统为核心设计理念的开源 AI 编码助手，原生支持 VS Code 与 JetBrains 双平台。
created: 2026-04-08
updated: 2026-04-08
tags: [product, coding, vscode, jetbrains, open-source]
---

# Continue

> 以 Config-as-Code 和可扩展上下文系统为核心设计理念的开源 AI 编码助手，原生支持 VS Code 与 JetBrains 双平台。

| 属性 | 值 |
|------|-----|
| 厂商 | Continue.dev (YC 孵化) |
| 形态 | VS Code / JetBrains 扩展 |
| 开源 | 是，Apache 2.0 ([GitHub](https://github.com/continuedev/continue)) |
| 技术栈 | TypeScript (VS Code), Kotlin (JetBrains) |
| 官网 | [continue.dev](https://continue.dev/) |

## 技术亮点

- **Config-as-Code**：所有行为——模型选择、上下文源、slash 命令、补全策略——均通过 `~/.continue/config.json` 或项目级 `.continuerc.json` 声明。配置即代码，可纳入版本控制、团队共享、CI 校验。这与 GUI 配置的工具在设计哲学上有根本差异。
- **Context Providers 抽象层**：可扩展的上下文插件系统。内置代码库索引、文档、URL、终端输出等 provider，也可自行编写 provider 将任意数据源（内部 wiki、数据库 schema、监控指标等）注入模型上下文。这是一个干净的抽象边界，将"上下文从哪来"与"模型怎么用"解耦。
- **双 IDE 原生实现**：同时维护 TypeScript（VS Code）和 Kotlin（JetBrains）两套原生插件，而非简单移植。两端各自利用宿主 IDE 的原生 API，体验一致但实现独立。
- **无代理服务器**：API 调用直连提供商，不经过 Continue 后端。与 Cline 家族的架构选择一致，但两者独立演化。

## 定价

- 完全免费开源，仅按模型 API 用量付费。

## 参考资料

- [Continue 官网](https://continue.dev/)
- [GitHub 仓库](https://github.com/continuedev/continue)
