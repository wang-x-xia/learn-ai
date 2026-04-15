---
title: Hermes Agent
description: Nous Research 的自进化个人 AI Agent，核心区分点是闭环学习循环——自动创建 Skill、使用中自我改进、跨会话知识持久化。
created: 2026-04-10
updated: 2026-04-15
tags: [product, nous-research, personal-agent, agent, skills, memory]
review: 2026-04-15
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

**Skill 管理机制**（系统 prompt 指导 Agent 自主判断）：

创建触发场景：
- 完成复杂任务（5+ tool calls）
- 修复棘手错误后找到正确路径
- 发现非平凡工作流
- 困难/迭代任务完成后

改进机制：
- 使用 Skill 时发现问题（过时、缺失步骤、命令错误）→ **立即**用 `skill_manage(action='patch')` 更新
- 不等用户提醒，发现就改

本质上没有自动评估/反馈循环，完全靠 Agent 自主判断在使用中发现问题并修复。

- **主动知识持久化**：Agent 会 nudge 自己将有价值的信息写入[长期记忆](../applied/memory-systems.md)，而非等用户指示
- 兼容 [agentskills.io](https://agentskills.io) 开放标准

### 2. RL 训练集成

Hermes 同时是一个**训练数据生成平台**：

- **Atropos RL 环境**：[Atropos](https://github.com/NousResearch/atropos)（1K stars）是 Nous Research 的 LLM RL 框架，通过环境微服务收集和评估 LLM 轨迹。Hermes 内置 [tinker-atropos](https://github.com/NousResearch/tinker-atropos) submodule 作为集成层
- **轨迹压缩**：将冗长的多轮交互压缩为高质量训练样本
- **批量轨迹生成**：配合 `batch_runner.py` 和 `datagen-config-examples/` 批量生产 tool-calling 训练数据

> **注意**：Atropos RL 训练需要自托管模型（vLLM/SGLang 加载 LoRA），商业 API 用户无法使用此功能。

**工作流程**：

```
用户使用 Hermes Agent → 生成交互轨迹 → 送入 Atropos RL 环境 → 训练 tool-calling 专精模型 → 反哺 Hermes Agent
```

**实测效果**（Tool Calling）：

| 任务类型 | Base Model | With Atropos RL |
|---------|------------|-----------------|
| Parallel Tasks | 10% | 46%（4.6x） |
| Simple Tasks | 21% | 51.75%（2.5x） |

模型输出：[DeepHermes-ToolCalling-Specialist-Atropos](https://huggingface.co/NousResearch/DeepHermes-ToolCalling-Specialist-Atropos)

**与 Honcho 的关系**：Honcho 负责用户记忆（输入侧），Atropos 负责 RL 训练（训练侧），两者独立。

### 3. Honcho 辩证用户建模

[Honcho](../libraries/honcho.md) 是 plastic-labs 开源的记忆库。Hermes 用它做**辩证用户建模**——通过多轮交互逐步构建和修正对用户的理解模型，跨会话累积。本质是让 Agent 构建一个"用户心智模型"而非"用户偏好列表"。Honcho 不绑定特定模型或框架，可以独立使用。

---

## 演进历史

Hermes Agent 早期曾用 ClawdBot、MoltBot 等名称[^hermes-github]。项目提供 `hermes claw migrate` 一键迁移工具，方便从 [OpenClaw](https://github.com/openclaw/openclaw)（354K stars）迁移。

OpenClaw 同样支持 Skills 系统、多渠道接入、IDE 集成等能力。两者核心差异在于 Hermes 多了**学习循环**（Skill 使用中改进）和** Honcho 用户建模**，但对普通用户来说实际体验差异不大。

---

## 参考资料

[^hermes-github]: NousResearch. *Hermes Agent*. https://github.com/NousResearch/hermes-agent
