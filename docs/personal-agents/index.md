---
title: 个人 AI Agent
description: 通用型个人 AI Agent 产品档案——聚焦跨会话学习、自主任务执行、多平台接入等技术区分度。
---

# 个人 AI Agent

> 通用型个人 AI Agent——不限于编码场景，强调跨会话学习、自主任务执行、多平台接入。与[编码 Agent](../coding-agents/index.md) 的区别：编码 Agent 专精代码生成/修复，本目录收录的产品定位为**通用个人助手**。

---

## 产品列表

<div class="grid cards" markdown>

- :material-assistant: **[Hermes Agent](hermes-agent.md)**

    ---

    Nous Research · 闭环学习循环：自动创建 Skill → 使用中自我改进 → 跨会话持久化

</div>

## 横向对比

| 维度 | Hermes Agent | OpenClaw |
|------|-------------|----------|
| **核心差异化** | 闭环学习循环（自动创建/改进 Skill） | Heartbeat 主动汇报 + 多 Agent 隔离路由 |
| **记忆方案** | Honcho 辩证用户建模 | 多 Agent 独立记忆隔离 |
| **Skill 生态** | 运行时自动生成 Skill | ClawHub 市场 + 社区共享 |
| **RL 训练** | Atropos 环境集成（4.6x 并行任务提升） | 无 |
| **适用场景** | 需要持续学习和个性化的长期助手 | 需要多 Agent 协作和后台任务的场景 |

## 品类共性

个人 Agent 的核心机制在应用技术文档中集中说明：

- [AI Agent 执行循环](../applied/ai-agents.md)
- [记忆系统](../applied/memory-systems.md)
- [工具接入](../applied/agent-tools.md)
- [Agent Skills](../applied/agent-skills.md)
