# AGENTS.md — 项目约定

## 项目概述

个人 AI 前沿知识库。知识文档用中文编写，代码和配置用英文。

## 内容偏好

维护者是技术人员，知识库的价值在于记录**技术方案上的革新**，而非功能罗列。

### 写作原则

1. **重技术方案，轻功能清单**：不要罗列"支持 Agent"、"支持 MCP"、"上下文感知补全"这类行业通用能力。重点写：它在技术实现上做了什么**不一样**的事？用了什么独到的架构/算法/工程手段？
2. **去重复化**：所有产品/项目共有的通用特性（如"支持多模型"、"代码补全"、"Chat 对话"）不在每个文档里重复。如需说明共性，集中在品类概述文档中写一次。
3. **应用型内容的写法**：先写内化的技术方案（它解决了什么技术问题、用了什么方法），再写为特定目标采用的亮眼工程细节（巧妙的系统设计、性能优化、取舍决策）。
4. **知识导向，非实现导向**：记录"这个东西为什么值得知道"，而不是"怎么用它"。比如一个 GitHub 热门 repo，应该提炼它在技术上出彩的部分（新颖的架构思路、解决了什么难题、关键的工程决策），而不是搬运 README。

### 产品档案（docs/coding-agents/）写法指南

产品文档应聚焦于**技术区分度**：

- **属性表 + 一句话定位**：保留，用于快速识别
- **核心能力**：只写该产品**独有或领先**的能力，跳过行业标配功能
- **技术要点**：这是最重要的部分——写清楚架构差异、工程亮点、独到的技术决策
- **定价**：保留，简明即可
- ~~通用功能~~：不写"支持代码补全"、"支持 Chat"等所有同类产品都有的东西

### 开源项目 / Trending Repos 写法指南

评估一个开源项目是否值得收录时，关注：

- 是否引入了新颖的技术方案或架构思路？
- 是否有出彩的工程细节（性能优化、系统设计、算法创新）？
- 是否解决了已知难题的新方法？

收录时提炼知识点，不搬运 README。格式：问题 → 方案 → 为什么巧妙。

## 目录约定

- `docs/foundations/` — 基础理论（稳定知识，低频更新）
- `docs/applied/` — 应用技术（工程方法，中频更新）
- `docs/research/` — 前沿研究（快速演进，高频更新）
- `docs/coding-agents/` — 编码 Agent 产品档案（每个产品一个文件，聚焦技术底座和区分度）
- `docs/landscape/` — 行业全景（模型跟踪）
- `journal/YYYY/MM/DD/<source>.md` — 每日 RSS 原始素材，按订阅源拆分（脚本自动生成）
- `docs/resources.md` — 精选资源汇总
- `scripts/` — 自动化脚本
- `scripts/scrapers/` — 网页爬虫（每个网站一个独立脚本）

### 新增品类目录的约定

当出现一个新的产品品类需要收录多个产品档案时：

1. 在 `docs/` 下新建**扁平的品类目录**，命名格式 `<品类名>/`（如 `docs/search-agents/`、`docs/data-tools/`）
2. 不嵌套子目录（不要 `docs/products/coding-agents/`），保持一层
3. 品类目录内每个产品一个 `.md` 文件，写法同上述产品档案指南
4. 在本节目录约定中登记新目录
5. 如有品类共性（所有同类产品都具备的通用能力），在 `docs/applied/` 下写一篇品类概述文档，各产品档案不重复

## Markdown 规范

- 所有知识文档必须有 YAML frontmatter（title, description, created, updated, tags）
- 日报用简化 frontmatter（date, type, source, category）
- 每次修改知识文档时更新 `updated` 字段
- 参考资料统一放在文档末尾的 `## 参考资料` 区

### 来源标识（Source Citation）

用 Markdown 脚注标记段落信息的出处。格式约定：

#### 脚注 key 命名规则

`来源简写-年份` 或 `来源简写-年份-关键词`，全小写，连字符分隔。

| 来源类型 | key 示例 |
|----------|----------|
| 论文 | `arxiv-2025-attention` |
| 厂商博客 | `openai-2025-gpt5`, `google-2025-gemini` |
| 个人博客 | `willison-2025-agents` |
| 官方文档 | `pytorch-docs-compile` |

#### 行内引用

在段落末尾或关键句后加脚注标记：

```markdown
Transformer 的核心是自注意力机制，通过 Q/K/V 矩阵计算 token 间的关联权重[^vaswani-2017]。
近期研究表明线性注意力可以将复杂度降至 O(n)[^arxiv-2025-linear-attn]。
```

#### 参考资料区定义

在文档末尾 `## 参考资料` 下定义所有脚注，格式统一为：

```markdown
## 参考资料

[^vaswani-2017]: Vaswani et al. *Attention Is All You Need*. 2017. https://arxiv.org/abs/1706.03762
[^arxiv-2025-linear-attn]: Zhang et al. *Linear Attention Revisited*. 2025. https://arxiv.org/abs/2501.xxxxx
[^openai-2025-gpt5]: OpenAI. "Introducing GPT-5". 2025. https://openai.com/blog/gpt-5
```

#### 整段引用

如果某一整段内容来自单一来源，可以在段首用粗体标注来源，避免每句都打脚注：

```markdown
**[来源: OpenAI Blog][^openai-2025-gpt5]** GPT-5 在推理基准上相比前代提升了 40%。
模型采用了全新的 MoE 架构……
```

## 日更脚本

- 入口：`scripts/daily_update.py`
- 只做一件事：拉 RSS + 爬虫 → 按订阅源写入 `journal/YYYY/MM/DD/<source>.md`
- 依赖管理：统一在 `pyproject.toml`，通过 `uv` 管理
- 所有源统一在 `scripts/feeds.yaml` 登记，按分类（papers / industry / community）组织
  - 只有 `verified: true` 的源会被拉取
  - `type: rss`（默认）— 标准 RSS/Atom 源，配置 url 即可
  - `type: scrape` — 网页爬虫，爬取逻辑在 `scripts/scrapers/<slug>.py` 独立维护
  - 添加新 RSS 源后先跑 `uv run scripts/daily_update.py --hours 1` 验证，再把 `verified` 改为 `true`
  - 添加新爬虫源：在 `scripts/scrapers/` 下新建 `<slug>.py`（暴露 `NAME`, `SLUG`, `CATEGORY`, `scrape()`），然后在 `feeds.yaml` 登记
- 运行：`uv run scripts/daily_update.py` 或 `uv run scripts/daily_update.py --hours 48`

## LLM 整理流程（手动触发）

脚本只负责拉取原始素材到 journal/。后续整理由人+LLM 协作完成：

### 1. 阅读当日素材

打开 `journal/YYYY/MM/DD/` 目录，浏览各订阅源的原始条目文件。

### 2. 更新 docs/landscape/model-tracker.md

如果有新模型发布或重大更新：
- 在对应的闭源/开源表格中添加新行
- 在 `## 最近更新` 下追加条目
- 更新 frontmatter 的 `updated` 字段

### 3. 更新知识文档

如果有值得纳入知识体系的内容，更新对应文件：

| 素材类型 | 归入文件 |
|----------|----------|
| Transformer 架构演进 | `docs/foundations/transformer.md` |
| SSM/Mamba/替代架构 | `docs/foundations/mamba-and-ssm.md` |
| 新模型发布/Scaling/评估 | `docs/foundations/large-language-models.md` |
| 多模态新进展 | `docs/foundations/multimodal-ai.md` |
| 训练/对齐新方法 | `docs/foundations/training-and-alignment.md` |
| 提示技巧/框架 | `docs/applied/prompt-engineering.md` |
| RAG 新方法 | `docs/applied/rag.md` |
| Agent 框架/协议 | `docs/applied/ai-agents.md` |
| 硬件/推理/部署 | `docs/applied/infrastructure.md` |
| 推理模型进展 | `docs/research/reasoning-and-planning.md` |
| 安全/治理/可解释性 | `docs/research/safety-and-governance.md` |
| 其他前沿方向 | `docs/research/emerging-frontiers.md` |

### 4. 更新 docs/resources.md

如果发现值得长期收藏的论文、工具或博客，添加到 `docs/resources.md` 对应分类下。

### 筛选标准

素材进入知识库的门槛（按优先级）：

1. **技术方案革新**：新架构、新算法、新训练方法 → 高优先
2. **工程亮点**：巧妙的系统设计、性能突破、独到的取舍决策 → 高优先
3. **解决已知难题的新方法** → 中优先
4. 纯功能发布（"我们也支持 X 了"）→ 跳过，除非背后有独到的技术实现
5. 通用知识、行业共识 → 跳过，不重复记录

### 提示词参考

让 LLM 帮忙整理时可以这样说：

> 阅读 journal/2026/04/07/ 目录下的今日素材，帮我：
> 1. 用技术视角筛选出最值得关注的 5 条——关注技术方案创新和工程亮点，跳过纯功能发布和通用知识
> 2. 判断哪些应该更新到知识文档中
> 3. 直接帮我更新对应的文件（记得更新 frontmatter 的 updated 字段，遵循"内容偏好"中的写作原则）

## 构建 & 验证

- 无构建步骤，纯 Markdown 仓库
- 日更脚本测试：`uv run scripts/daily_update.py --hours 1`
