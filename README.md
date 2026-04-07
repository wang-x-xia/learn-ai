# Learn AI - AI 前沿知识库

> 一份精心整理的 AI 前沿知识合集，涵盖大语言模型、多模态AI、智能体、RAG、微调对齐等核心领域。
> 
> 最后更新：2026 年 4 月

---

## 目录

| # | 主题 | 说明 |
|---|------|------|
| 01 | [大语言模型 (LLMs)](docs/01-large-language-models.md) | GPT-5、Claude、Gemini、Llama、DeepSeek 等主流模型对比与关键技术 |
| 02 | [多模态 AI](docs/02-multimodal-ai.md) | 视觉语言模型、文生图、文生视频、音频、世界模型 |
| 03 | [AI Agent 智能体](docs/03-ai-agents.md) | Agent 架构、框架、协议、代码 Agent、多智能体系统 |
| 04 | [检索增强生成 (RAG)](docs/04-rag.md) | RAG 架构、向量数据库、检索策略、高级 RAG 技术 |
| 05 | [微调与对齐](docs/05-fine-tuning-and-alignment.md) | SFT、LoRA、RLHF、DPO、对齐研究前沿 |
| 06 | [提示工程](docs/06-prompt-engineering.md) | 基础与高级提示技巧、模板框架、实践案例 |
| 07 | [AI 基础设施](docs/07-ai-infrastructure.md) | GPU/TPU、训练推理优化、量化压缩、云平台 |
| 08 | [前沿研究方向](docs/08-emerging-research.md) | 推理模型、AI for Science、可解释性、世界模型、AI 安全 |

---

## AI 格局概览 (2026)

当前 AI 领域正处于快速发展期，主要玩家及其最新进展：

### 闭源模型

| 厂商 | 最新模型 | 亮点 |
|------|----------|------|
| **OpenAI** | GPT-5、GPT-5.3 Instant、GPT-5.3-Codex | 2026年3月融资 $122B；Sora 视频生成；Codex 按需定价 |
| **Anthropic** | Claude Opus 4、Sonnet 4、Haiku | Claude Code / Cowork；对齐伪装研究；Constitutional Classifiers |
| **Google DeepMind** | Gemini 3.1 Pro/Flash/Flash-Lite、Deep Think | Gemini Robotics；Genie 3 世界模型；SIMA 2 游戏智能体 |

### 开源模型

| 厂商 | 最新模型 | 亮点 |
|------|----------|------|
| **Meta** | Llama 4 系列 | 开源旗舰，广泛社区支持 |
| **Google** | Gemma 4 (2026.4) | 开源 Gemma 系列最新版 |
| **Mistral** | Mistral Large、Mixtral | 欧洲 AI 代表，MoE 架构先驱 |
| **DeepSeek** | DeepSeek-V3、DeepSeek-R1 | 推理模型标杆，开源 MoE |
| **阿里 (Qwen)** | Qwen2.5 系列 | 中文最强开源模型之一 |

### 关键趋势

- **推理时计算 (Test-time Compute)**: o1/o3、R1、Deep Think 等"思考"模型崛起
- **AI Agent**: 从单纯聊天到能执行复杂任务的智能体
- **多模态融合**: 文本、图像、音频、视频的原生统一
- **小而精模型**: 在保持性能的同时追求效率
- **AI 安全与治理**: 全球监管框架加速成型

---

## 如何使用

1. **系统学习**: 按照目录从 01 到 08 依次阅读，建立完整的 AI 知识体系
2. **专题查阅**: 根据兴趣或工作需要，直接跳转到相应专题
3. **实践参考**: 各文档中包含代码示例、工具推荐和最佳实践

```bash
# 克隆本仓库
git clone <repo-url>

# 直接用 Markdown 阅读器浏览
# 推荐：VS Code + Markdown Preview Enhanced 插件
```

---

## 参考资源

### 论文与研究
- [arXiv (cs.AI)](https://arxiv.org/list/cs.AI/recent) - AI 领域最新论文
- [arXiv (cs.CL)](https://arxiv.org/list/cs.CL/recent) - 计算语言学论文
- [arXiv (cs.LG)](https://arxiv.org/list/cs.LG/recent) - 机器学习论文
- [Papers With Code](https://paperswithcode.com/) - 论文+代码+基准

### 模型与工具
- [Hugging Face](https://huggingface.co/) - 模型、数据集、Spaces
- [OpenAI Platform](https://platform.openai.com/) - OpenAI API
- [Anthropic Console](https://console.anthropic.com/) - Claude API
- [Google AI Studio](https://aistudio.google.com/) - Gemini API

### 社区与资讯
- [The Batch (deeplearning.ai)](https://www.deeplearning.ai/the-batch/) - Andrew Ng 的 AI 周报
- [AI News (Sebastian Raschka)](https://magazine.sebastianraschka.com/) - 深度技术解读
- [Latent Space Podcast](https://www.latent.space/) - AI 工程播客

---

## Contributing

欢迎贡献！如果你发现内容有误或想补充新知识：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/new-topic`)
3. 提交更改 (`git commit -m 'Add new topic'`)
4. 推送到分支 (`git push origin feature/new-topic`)
5. 创建 Pull Request

---

## License

MIT License - 自由使用和分享
