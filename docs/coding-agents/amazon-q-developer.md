---
title: "Amazon Q Developer"
description: AWS 的 AI 编码助手（原 CodeWhisperer），核心差异在于 Agent 驱动的大规模代码迁移和 AWS 生态深度绑定。
created: 2026-04-08
updated: 2026-04-08
tags: [product, aws, amazon, coding, ide, agent]
review:
---

# Amazon Q Developer

> AWS 的 AI 编码助手（原 CodeWhisperer），核心差异在于 Agent 驱动的大规模代码迁移和 AWS 生态深度绑定。

| 属性 | 值 |
|------|-----|
| 厂商 | Amazon (AWS) |
| 形态 | IDE 扩展（VS Code / JetBrains）、CLI、AWS Console 集成 |
| 开源 | 否 |
| 技术栈 | TypeScript (VS Code 扩展), Java/Kotlin (JetBrains), AWS 后端 |
| 底座模型 | Amazon 自研模型 + Claude (via Bedrock) |
| 官网 | [aws.amazon.com/q/developer](https://aws.amazon.com/q/developer/) |

## 技术亮点

- **Agent 驱动的代码转换**：自动化大规模迁移（Java 8→17、.NET Framework→.NET Core）。这是一个真正困难的问题——需要理解框架差异、API 映射、跨整个代码库的依赖解析。Agent 方式处理代码迁移在架构上有独到之处。
- **参考追踪与许可证归因**：标记与开源代码相似的建议，附带许可证信息，方法类似 Copilot。
- **Bedrock 多模型后端**：通过 Amazon Bedrock 路由到不同模型。
- **AWS 生态绑定**：生成 CloudFormation/CDK 模板、Lambda 函数，理解 AWS 架构。这是深度领域知识内嵌于产品中——与 CloudWatch、CodeCatalyst 等深度整合。

坦率地说，除代码转换 Agent 和 AWS 生态绑定外，Amazon Q Developer 在技术独特性上相对有限。

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| Free | 免费 | 有限补全和 Chat 额度 |
| Pro | $19/人/月 | 更高额度，安全扫描，Agent 转换 |

## 参考资料

- [Amazon Q Developer](https://aws.amazon.com/q/developer/)
- [文档](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/what-is.html)
