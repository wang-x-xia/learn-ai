---
title: AI 个人软件
description: 面向个人开发者的 AI 软件产品档案——编码 Agent、通用个人助手等，聚焦技术区分度与架构亮点。
---

# AI 个人软件

面向个人开发者的 AI 软件产品档案，聚焦**技术区分度**——架构差异、工程亮点、独到的技术决策。跳过行业标配功能。

---

## 产品列表

<div class="grid cards" markdown>

- :material-console: **[Claude Code](claude-code.md)**

    ---

    Anthropic · CLI 编程 Agent

- :material-assistant: **[Hermes Agent](hermes-agent.md)**

    ---

    Nous Research · 闭环学习循环：自动创建 Skill → 使用中自我改进 → 跨会话持久化

- :material-robot: **[OpenClaw](openclaw.md)**

    ---

    Peter Steinberger · Heartbeat 主动汇报 + 多 Agent 隔离路由

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

Agent 的核心机制在技术文档中集中说明：

- [AI Agent 执行循环](../agent/ai-agents.md)
- [记忆系统](../agent/memory-systems.md)
- [工具接入](../agent/agent-tools.md)
- [Agent Skills](../agent/agent-skills.md)
