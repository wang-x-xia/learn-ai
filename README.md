# Learn AI

个人 AI 前沿知识库。系统梳理 AI 核心技术，每日自动追踪社区与行业动态。

---

## 知识体系

### 基础理论 — *what*

| 主题 | 说明 |
|------|------|
| [大语言模型](docs/foundations/large-language-models.md) | Transformer、Scaling Laws、主流模型对比、MoE、推理模型 |
| [多模态 AI](docs/foundations/multimodal-ai.md) | 视觉语言模型、文生图/视频、音频语音、世界模型 |
| [训练与对齐](docs/foundations/training-and-alignment.md) | SFT、LoRA/QLoRA、RLHF、DPO、Constitutional AI |

### 应用技术 — *how*

| 主题 | 说明 |
|------|------|
| [提示工程](docs/applied/prompt-engineering.md) | CoT、Few-shot、提示框架 (CRISPE/CO-STAR/DSPy)、安全防御 |
| [检索增强生成 (RAG)](docs/applied/rag.md) | 分块/嵌入/向量库/检索策略、GraphRAG、Agentic RAG |
| [AI Agent 智能体](docs/applied/ai-agents.md) | ReAct、框架生态、MCP/A2A 协议、代码 Agent |
| [AI 基础设施](docs/applied/infrastructure.md) | GPU/TPU、推理优化、量化压缩、MLOps、成本优化 |

### 前沿研究 — *what's next*

| 主题 | 说明 |
|------|------|
| [推理与规划](docs/research/reasoning-and-planning.md) | Test-time compute、PRM、o-series、DeepSeek-R1 |
| [AI 安全与治理](docs/research/safety-and-governance.md) | 可解释性、全球监管、人机协作 |
| [新兴前沿方向](docs/research/emerging-frontiers.md) | AI for Science、世界模型、小模型、长上下文、多智能体 |

### 行业全景 & 每日动态

| 主题 | 说明 |
|------|------|
| [模型动态跟踪](docs/landscape/model-tracker.md) | 闭源/开源模型发布追踪、评估排行 |
| [每日日报](journal/) | 自动生成的 AI 行业日报（按年/月/日归档） |
| [精选资源](docs/resources.md) | 论文、API 平台、开发工具、社区资讯 |

---

## 目录结构

```
learn-ai/
├── docs/
│   ├── foundations/          # 基础理论 (相对稳定)
│   │   ├── large-language-models.md
│   │   ├── multimodal-ai.md
│   │   └── training-and-alignment.md
│   ├── applied/              # 应用技术 (工程方法)
│   │   ├── prompt-engineering.md
│   │   ├── rag.md
│   │   ├── ai-agents.md
│   │   └── infrastructure.md
│   ├── research/             # 前沿研究 (快速演进)
│   │   ├── reasoning-and-planning.md
│   │   ├── safety-and-governance.md
│   │   └── emerging-frontiers.md
│   ├── products/             # 产品档案
│   ├── landscape/            # 行业全景 (高频更新)
│   │   └── model-tracker.md
│   └── resources.md          # 精选资源汇总
├── journal/                  # 每日动态 (自动生成)
│   └── YYYY/MM/DD.md
├── scripts/
│   └── daily_update.py       # 日更脚本
├── mkdocs.yml                # GitHub Pages 站点配置
└── .github/workflows/
    └── deploy-pages.yml      # GitHub Pages 自动部署
```

---

## 每日更新

GitHub Actions 每天 UTC 00:00 自动拉取 RSS 写入 `journal/`：

- **数据源**: arXiv cs.AI/cs.CL、OpenAI Blog、DeepMind Blog、Latent Space、Sebastian Raschka、Simon Willison
- **输出**: `journal/YYYY/MM/DD.md` — 按论文/厂商动态/社区分类的原始条目
- **RSS 源配置**: `scripts/daily_update.py` 顶部的 `RSS_FEEDS`

整理流程（人+LLM）见 [AGENTS.md](AGENTS.md#llm-整理流程手动触发)。

```bash
# 手动拉取
uv run scripts/daily_update.py

# 拉取过去 48 小时
uv run scripts/daily_update.py --hours 48
```

---

## Frontmatter 规范

每个 Markdown 文件使用 YAML frontmatter 记录元数据：

```yaml
---
title: 文档标题
description: 一句话描述
created: 2026-04-07
updated: 2026-04-07
tags: [tag1, tag2]
---
```

日报使用简化格式：

```yaml
---
date: 2026-04-07
type: daily
---
```

---

## License

MIT
