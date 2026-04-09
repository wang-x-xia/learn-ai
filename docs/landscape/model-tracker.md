---
title: 模型动态跟踪
description: 追踪主流 AI 模型的最新发布、更新和关键变化。本文件由日更脚本自动维护。
created: 2026-04-07
updated: 2026-04-09
tags: [models, landscape, tracker]
review:
---

# 模型动态跟踪

> 本文件追踪主流 AI 模型的发布和更新动态，分为闭源模型与开源模型两部分。由日更脚本自动维护，也可手动补充。

---

## 闭源模型

| 模型 | 厂商 | 发布时间 | 上下文窗口 | 亮点 |
|------|------|----------|------------|------|
| **Muse Spark** | Meta (MSL) | 2026.4 | - | MSL 全新架构栈首个前沿模型，闭源托管，Instant/Thinking 双模式 |
| **Claude Mythos Preview** | Anthropic | 2026.4 | - | 超强网络安全能力，受限发布（Project GlassWing） |
| **Claude Opus 4.6** | Anthropic | 2026.3 | 1M | 1M 上下文 GA |
| **Claude Sonnet 4.6** | Anthropic | 2026.3 | 1M | 1M 上下文 GA |
| **GPT-5.3-Codex** | OpenAI | 2026.4 | 128K+ | 专为代码优化，支持按需定价 |
| **GPT-5.3 Instant** | OpenAI | 2026.3 | 128K+ | 更快速、更经济 |
| **Gemini 3.1 Flash** | Google | 2026.3 | 1M+ | 高速推理，自然语音 |
| **Gemini 3.1 Flash-Lite** | Google | 2026.3 | 1M+ | 大规模部署优化 |
| **Gemini 3.1 Pro** | Google | 2026.2 | 1M+ | 长上下文，复杂任务 |
| **Gemini 3 Deep Think** | Google | 2026.2 | - | 科学研究与数学推理 |
| **GPT-5** | OpenAI | 2025 | 128K+ | 多模态原生，强推理能力 |
| **Claude Opus 4** | Anthropic | 2025 | 200K | 最强推理，深度分析 |
| **Claude Sonnet 4** | Anthropic | 2025 | 200K | 性能与速度平衡 |
| **Claude Haiku 3.5** | Anthropic | 2025 | 200K | 快速响应，成本最低 |

## 开源模型

| 模型 | 厂商 | 参数量 | 发布时间 | 亮点 |
|------|------|--------|----------|------|
| **GLM-5.1** | Z.ai (智谱) | 754B | 2026.4 | MIT 协议，1.51TB，主打长周期任务 |
| **Gemma 4** | Google | 多规格 | 2026.4 | 开源高效率 |
| **DeepSeek-R1** | DeepSeek | 671B | 2025.1 | 开源推理模型标杆 |
| **DeepSeek-V3** | DeepSeek | 671B(37B active) | 2024 | MoE 架构，卓越性价比 |
| **Llama 4** | Meta | 多规格 | 2025 | 开源旗舰，社区生态最强 |
| **Llama 3.1** | Meta | 8B/70B/405B | 2024 | 广泛使用 |
| **Mistral Large** | Mistral | 未公开 | 2024 | 欧洲 AI 代表 |
| **Mixtral 8x7B** | Mistral | 46.7B(12.9B active) | 2024 | MoE 架构先驱 |
| **Qwen2.5** | 阿里 | 0.5B-72B | 2024 | 中文最强开源之一 |

## 最近更新

### 2026-04-09

- **Muse Spark** 发布：Meta Superintelligence Labs（MSL）全新架构栈的首个前沿模型。闭源托管（非开源权重），提供 Instant 和 Thinking 两种模式，未来将增加 Contemplating（长推理）模式。基准与 Opus 4.6、Gemini 3.1 Pro 和 GPT-5.4 相当，长周期 Agent 任务仍有差距[^willison-2026-muse-spark]

### 2026-04-08

- **Claude Mythos Preview** 发布（受限）：Anthropic 最新旗舰模型，网络安全能力远超 Opus 4.6，仅通过 Project GlassWing 向 40 家安全合作伙伴开放[^anthropic-2026-glasswing]
- **GLM-5.1** 发布：智谱 Z.ai 发布 754B 参数开源模型（MIT 协议），主打长周期任务[^willison-2026-glm51]
- **Claude Opus 4.6 / Sonnet 4.6**：1M 上下文窗口正式 GA（2026.3.13）[^claude-2026-1m-context]

---

## 评估基准

> 详细的基准说明见 [大语言模型 § 评估基准](../foundations/large-language-models.md#5-评估基准)。

## 参考资料

[^anthropic-2026-glasswing]: Anthropic. "Project Glasswing". 2026. https://www.anthropic.com/glasswing
[^willison-2026-glm51]: Simon Willison. "GLM-5.1: Towards Long-Horizon Tasks". 2026. https://simonwillison.net/2026/Apr/7/glm-51/
[^willison-2026-muse-spark]: Simon Willison. "Meta's new model is Muse Spark". 2026. https://simonwillison.net/2026/Apr/8/muse-spark/
[^claude-2026-1m-context]: Claude Blog. "1M context is now generally available for Opus 4.6 and Sonnet 4.6". 2026. https://claude.com/blog/1m-context-ga
