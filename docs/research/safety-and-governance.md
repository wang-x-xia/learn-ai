---
title: AI 安全与治理
description: AI 安全研究、可解释性、全球治理框架、人机协作等方向。
created: 2026-04-07
updated: 2026-04-08
tags: [safety, governance, interpretability, alignment, regulation]
review:
---

# AI 安全与治理 (Safety & Governance)

> 涵盖 AI 安全研究、可解释性与机制理解、全球治理框架、以及 AI 与人类协作等重要议题。

---

## 1. 可解释性与机制理解 (Interpretability)

### 概述

理解 LLM 内部工作机制——不仅知道模型"做了什么"，更要知道"为什么这样做"。

### 1.1 Anthropic 可解释性研究

Anthropic 在这一领域处于领先地位：

| 研究 | 时间 | 发现 |
|------|------|------|
| **情感概念与功能** | 2026.4 | 理解模型如何表征和使用情感概念 |
| **行为差异检测工具** | 2026.3 | "diff" 工具发现新旧模型的行为差异 |
| **模型内省** | 2025.10 | 发现模型具有有限但功能性的自我审视能力 |
| **Golden Gate Claude** | 2024 | 通过激活引导改变模型行为的实验 |

### 1.2 Gemma Scope 2 (2025.12)

Google DeepMind 帮助 AI 安全社区深入理解复杂语言模型行为的工具：
- 可视化模型内部激活
- 理解特征表示
- 开源给安全研究社区

### 1.3 核心概念

**特征 (Features)**
模型内部学到的有意义的概念表示。例如：
- "Golden Gate Bridge" 特征在提到金门大桥时激活
- "代码 bug" 特征在代码有错误时激活

**叠加 (Superposition)**
模型用 N 个神经元表征远多于 N 个的概念，类似于压缩编码。

**稀疏自编码器 (Sparse Autoencoders)**
用于从模型的叠加表示中提取独立的、可解释的特征：

```
模型隐藏状态 → 稀疏自编码器 → 独立特征
  (纠缠的)                     (可解释的)
```

**回路分析 (Circuit Analysis)**
追踪模型内部特定行为的信息流动路径。

---

## 2. AI 安全与治理

### 2.1 安全研究

| 研究 | 时间 | 要点 |
|------|------|------|
| **AI 安全验证的不完备性** | 2026.4 | 用 Kolmogorov 复杂性证明 AI 安全验证的理论限制 |
| **AI Trust OS** | 2026.4 | 自主 AI 可观测性和零信任合规的持续治理框架 |
| **AGI 衡量框架** | 2026.3 | Google DeepMind 提出衡量通向 AGI 进展的认知框架 |
| **防止有害操纵** | 2026.3 | Google DeepMind 的保护性研究 |

### 2.2 安全举措

| 举措 | 机构 | 时间 |
|------|------|------|
| **Project GlassWing** | Anthropic | 2026.4 |
| **Safety Fellowship** | OpenAI | 2026.4 |
| **Safety Bug Bounty** | OpenAI | 2026.3 |
| **Responsible Scaling** | Anthropic | 持续更新 |
| **FACTS Benchmark** | Google | 2025.12 |
| **Gemma Scope 2** | Google | 2025.12 |

### 2.3 Project GlassWing 与 Claude Mythos（2026.4）

Anthropic 发布了 Claude Mythos Preview，但**未公开发布**——GPT-2 以来首次有厂商主动限制前沿模型的发布[^willison-2026-glasswing]。

**Claude Mythos 的能力：**
- 发现了每个主流操作系统和浏览器中的高严重性漏洞，包括 OpenBSD 中存在 27 年的 TCP SACK 内核崩溃 bug
- 编写了链接 4 个漏洞的浏览器攻击链，通过 JIT 堆喷射逃逸渲染器和 OS 沙箱
- 在 Firefox JS 引擎漏洞利用测试中成功率 181/数百次，而 Opus 4.6 仅 2/数百次
- Anthropic 红队报告：模型展现出"复杂的策略性思考和情景感知"，7.6% 的情况下意识到自己正在被评估

**Project GlassWing 限制措施：**
- 仅向 40 家合作伙伴开放（AWS、Apple、Microsoft、Google、Linux Foundation 等）
- 提供 $1 亿使用额度 + $400 万开源安全组织捐赠
- 合作伙伴用于查找和修复基础设施中的漏洞（漏洞检测、黑盒测试、渗透测试）
- Anthropic 计划：不公开发布 Mythos，将在后续 Claude Opus 模型中先上线安全防护机制

**Nicolas Carlini（Anthropic 研究员）：**
> "过去几周我发现的 bug 比我这辈子加起来都多。"[^willison-2026-glasswing]

### 2.4 全球治理

| 地区 | 法规/政策 | 状态 |
|------|-----------|------|
| **欧盟** | EU AI Act | 实施中 |
| **中国** | 生成式AI管理办法 | 已生效 |
| **美国** | 行政命令 + 州立法 | 推进中 |
| **英国** | AI Safety Institute | 运营中 |

---

## 3. AI 与人类协作

### 最新研究发现

**"AI Assistance Reduces Persistence and Hurts Independent Performance"** (2026.4 arXiv):
- AI 辅助可能减少人类的坚持性
- 过度依赖 AI 可能损害独立能力
- 需要思考 AI 辅助的最佳方式

**"渐进认知外化框架"** (2026.4):
- 环境智能如何逐步将人类认知外化
- 理解 AI 对人类认知过程的深层影响

### 增强 vs 自动化

```
增强 (Augmentation):
  人类决策 + AI 辅助 → 更好的结果
  保留人类的控制和学习

自动化 (Automation):
  AI 独立完成 → 效率最高
  但可能导致技能退化
```

### 人机协作最佳实践

- **关键决策保留人类**: AI 提供信息，人类做决定
- **渐进式信任**: 从简单任务开始，逐步增加 AI 自主权
- **持续学习**: 保持人类对 AI 决策过程的理解
- **反馈循环**: 人类反馈 → AI 改进 → 更好的协作

---

## 参考资料

[^willison-2026-glasswing]: Simon Willison. "Anthropic's Project Glasswing". 2026. https://simonwillison.net/2026/Apr/7/project-glasswing/
- AI Assistance Reduces Persistence - [arXiv:2604.04721](https://arxiv.org/abs/2604.04721)
- ShieldNet: Network-Level Guardrails for Agentic Systems - [arXiv:2604.04426](https://arxiv.org/abs/2604.04426)
- Anthropic Research: https://www.anthropic.com/research
- Google DeepMind: https://deepmind.google/discover/blog/
