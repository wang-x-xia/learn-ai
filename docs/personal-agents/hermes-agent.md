---
title: Hermes Agent
description: Nous Research 的自进化个人 AI Agent，核心区分点是闭环学习循环——自动创建 Skill、使用中自我改进、跨会话知识持久化。
created: 2026-04-10
updated: 2026-04-10
tags: [product, nous-research, personal-agent, agent, skills, memory]
review:
---

# Hermes Agent

> Nous Research 出品的自进化个人 AI Agent。核心区分点不是"又一个 Agent 壳"，而是**闭环学习循环**——Agent 在使用中自动积累 Skill 和记忆，跨会话变得越来越强。

| 属性 | 值 |
|------|-----|
| 厂商 | Nous Research |
| 语言 | Python |
| 开源 | 是（MIT） |
| GitHub | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)（47K+ stars） |
| 官网 | [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com) |

---

## 技术亮点

### 1. 闭环学习循环（核心区分点）

大多数 Agent 产品是**无状态**的——每次会话重新开始，能力完全由预定义 Skill 和工具决定。Hermes Agent 的闭环设计让 Agent 从自身经验中学习：

```
完成复杂任务 → 自动提取 Skill → 下次遇到类似任务时调用
       ↑                                    ↓
       ← Skill 在使用中自我改进，不断精化 ←
```

- **自主 Skill 创建**：完成复杂任务后，Agent 自动将多步操作凝练为可复用的 [Skill](../applied/agent-skills.md)
- **使用中自我改进**：Skill 不是创建后就固定——每次执行后根据效果迭代改进
- **主动知识持久化**：Agent 会 nudge 自己将有价值的信息写入[长期记忆](../applied/memory-systems.md)，而非等用户指示
- 兼容 [agentskills.io](https://agentskills.io) 开放标准

### 2. RL 训练集成

Hermes Agent 不只是一个终端产品——它同时是一个**训练数据生成平台**：

- **Atropos RL 环境**：内置 RL 训练环境，可从 Agent 实际交互中生成训练轨迹
- **轨迹压缩**：将冗长的多轮交互压缩为高质量训练样本
- **批量轨迹生成**：配合 `batch_runner.py` 和 `datagen-config-examples/` 批量生产 tool-calling 训练数据

这形成了一个自我强化循环：用户使用 Agent → 产生轨迹数据 → 训练更好的 tool-calling 模型 → 反哺 Agent 能力。

### 3. Honcho 辩证用户建模

不同于简单记录用户偏好的方法，Hermes 使用 Honcho 框架做**辩证用户建模**——通过多轮交互逐步构建和修正对用户的理解模型，跨会话累积。本质上是让 Agent 构建一个"用户心智模型"而非"用户偏好列表"。

### 4. 单 Gateway 多平台

一个 gateway 进程同时服务 Telegram、Discord、Slack、WhatsApp、Signal，对话跨平台连续。包含语音消息转录。

### 5. Serverless 休眠

六种终端后端（Local、Docker、SSH、Daytona、Singularity、Modal）。Daytona 和 Modal 后端支持 serverless 休眠——Agent 环境空闲时 hibernate，唤醒时恢复状态，闲时接近零成本。

---

## 演进历史

Hermes Agent 早期曾用 ClawdBot、MoltBot 等名称[^hermes-github]。项目提供 `hermes claw migrate` 一键迁移工具，方便从 [OpenClaw](https://github.com/openclaw/openclaw)（独立的开源个人 AI 助手，354K stars）迁移过来。

---

## 参考资料

[^hermes-github]: NousResearch. *Hermes Agent*. https://github.com/NousResearch/hermes-agent
