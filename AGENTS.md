# AGENTS.md — 项目约定

## 项目概述

个人 AI 前沿知识库。系统梳理 AI 核心技术，每日自动追踪社区与行业动态。

- **知识文档**用中文编写，**代码和配置**用英文
- 站点使用 MkDocs Material 生成，推送 `main` 后由 GitHub Actions 自动部署到 GitHub Pages
- 依赖管理统一使用 `uv`，Python 版本要求 `>=3.12`

## 技术栈

| 工具 | 用途 | 配置位置 |
|------|------|----------|
| **uv** | Python 依赖管理 & 脚本运行 | `pyproject.toml` |
| **MkDocs Material** | 静态站点生成 | `mkdocs.yml` |
| **GitHub Actions** | 推送 main 后自动构建部署 | `.github/workflows/deploy-pages.yml` |
| **feedparser / httpx / beautifulsoup4** | RSS 拉取 & 网页爬取 | `pyproject.toml` (dependencies) |

---

## 内容偏好

维护者是技术人员，知识库的价值在于记录**技术方案上的革新**，而非功能罗列。

### 写作原则

1. **重技术方案，轻功能清单**：不要罗列"支持 Agent"、"支持 MCP"、"上下文感知补全"这类行业通用能力。重点写：它在技术实现上做了什么**不一样**的事？用了什么独到的架构/算法/工程手段？
2. **去重复化**：所有产品/项目共有的通用特性（如"支持多模型"、"代码补全"、"Chat 对话"）不在每个文档里重复。如需说明共性，集中在品类概述文档中写一次。
3. **应用型内容的写法**：先写内化的技术方案（它解决了什么技术问题、用了什么方法），再写为特定目标采用的亮眼工程细节（巧妙的系统设计、性能优化、取舍决策）。
4. **知识导向，非实现导向**：记录"这个东西为什么值得知道"，而不是"怎么用它"。比如一个 GitHub 热门 repo，应该提炼它在技术上出彩的部分（新颖的架构思路、解决了什么难题、关键的工程决策），而不是搬运 README。
5. **跨文档去重**：同一主题只在**一个**权威位置展开。其他涉及该主题的文档用一行摘要 + 交叉链接指过去，不复制段落。

### 筛选标准

素材进入知识库的门槛（按优先级）：

1. **技术方案革新**：新架构、新算法、新训练方法 → 高优先
2. **工程亮点**：巧妙的系统设计、性能突破、独到的取舍决策 → 高优先
3. **解决已知难题的新方法** → 中优先
4. 纯功能发布（"我们也支持 X 了"）→ 跳过，除非背后有独到的技术实现
5. 通用知识、行业共识 → 跳过，不重复记录

---

## 目录约定

```
learn-ai/
├── docs/                        # 知识文档（MkDocs 源文件）
│   ├── index.md                 # 站点首页
│   ├── resources.md             # 精选资源汇总
│   ├── foundations/             # 基础理论（稳定知识，低频更新）
│   ├── applied/                # 应用技术（工程方法，中频更新）
│   ├── research/               # 前沿研究（快速演进，高频更新）
│   ├── coding-agents/          # 编码 Agent 产品档案
│   └── landscape/              # 行业全景（模型跟踪）
├── journal/                     # 每日 RSS 原始素材（脚本自动生成）
│   └── YYYY/MM/DD/<source>.md
├── scripts/
│   ├── daily_update.py          # 日更脚本入口
│   ├── feeds.yaml               # 订阅源清单
│   └── scrapers/                # 网页爬虫（每个网站一个独立脚本）
│       ├── __init__.py          # 自动发现 & 分发
│       ├── anthropic.py
│       ├── claude_blog.py
│       └── github_trending.py
├── mkdocs.yml                   # MkDocs 站点配置 & 导航
├── pyproject.toml               # Python 依赖
└── .github/workflows/
    └── deploy-pages.yml         # GitHub Pages 自动部署
```

### 各目录说明

| 目录 | 内容 | 更新频率 |
|------|------|----------|
| `docs/foundations/` | Transformer、LLM、SSM/Mamba、多模态、训练对齐 | 低 |
| `docs/applied/` | Agent、Agent Hooks、Subagent、Prompt Engineering、RAG、基础设施 | 中 |
| `docs/research/` | 推理与规划、安全治理、新兴前沿 | 高 |
| `docs/coding-agents/` | 编码 Agent 产品档案（每个产品一个文件） | 随产品更新 |
| `docs/landscape/` | 模型动态跟踪 | 有新模型时 |
| `journal/` | RSS/爬虫原始素材，按日期和来源拆分 | 每日 |

### 文件命名

- **知识文档**：`kebab-case.md`（如 `ai-agents.md`、`prompt-engineering.md`）
- **Python 脚本**：`snake_case.py`（如 `daily_update.py`、`github_trending.py`）
- **journal 文件**：`<source-slug>.md`（如 `arxiv-cs-ai.md`、`simon-willison.md`），由脚本自动生成

### 新增品类目录

当出现一个新的产品品类需要收录多个产品档案时：

1. 在 `docs/` 下新建**扁平的品类目录**，命名格式 `<品类名>/`（如 `docs/search-agents/`）
2. 不嵌套子目录（不要 `docs/products/coding-agents/`），保持一层
3. 品类目录内每个产品一个 `.md` 文件
4. 在 `mkdocs.yml` 的 `nav:` 中添加对应条目
5. 在本节目录约定中登记新目录
6. 如有品类共性，在 `docs/applied/` 下写一篇品类概述文档，各产品档案不重复

---

## Markdown 规范

### Frontmatter

每个文件必须有 YAML frontmatter。不同类型的文件要求不同：

#### 知识文档（foundations/ applied/ research/ landscape/）

```yaml
---
title: 文档标题
description: 一句话描述文档内容
created: 2026-04-07
updated: 2026-04-09
tags: [tag1, tag2, tag3]
---
```

所有五个字段必填。每次修改内容时更新 `updated` 字段。

#### 索引页（各目录的 index.md）

```yaml
---
title: 分区标题
description: 一句话描述
---
```

索引页只需 `title` 和 `description`，不需要 `created`/`updated`/`tags`。

#### 产品档案（coding-agents/ 等品类目录）

```yaml
---
title: "产品名"
description: 一句话定位
created: 2026-04-08
updated: 2026-04-08
tags: [product, vendor, coding, form-factor, agent]
---
```

`title` 用引号包裹（产品名通常是英文专有名词）。所有五个字段必填。

#### 日报（journal/）

```yaml
---
date: 2026-04-09
type: daily
source: 来源名称
category: 分类标签
---
```

日报由脚本自动生成，不需要手动编辑。

### 产品档案模板

```markdown
---
title: "产品名"
description: 一句话定位
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [product, vendor-name, coding, form-factor, agent]
---

# 产品名

> 一句话定位（厂商 + 核心形态 + 最大区分点）

| 属性 | 值 |
|------|-----|
| 厂商 | ... |
| 形态 | ... |
| 开源 | 是/否 |
| 技术栈 | ... |
| 底座模型 | ... |
| 官网 | [链接](url) |

## 技术亮点

- **亮点一**：（只写该产品独有或领先的能力，不写行业标配）
- **亮点二**：...

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| ... | ... | ... |

## 参考资料

[^key]: Author. "Title". Year. URL
```

### 来源标识（Source Citation）

用 Markdown **脚注**标记段落信息的出处（不要用无序列表）。

#### 脚注 key 命名

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
```

#### 参考资料区

在文档末尾 `## 参考资料` 下定义所有脚注：

```markdown
## 参考资料

[^vaswani-2017]: Vaswani et al. *Attention Is All You Need*. 2017. https://arxiv.org/abs/1706.03762
[^openai-2025-gpt5]: OpenAI. "Introducing GPT-5". 2025. https://openai.com/blog/gpt-5
```

**注意**：每个 `[^key]` 行内引用都**必须**有对应的 `[^key]: ...` 定义，否则 MkDocs 渲染会出错。不要用 `- Author, "Title"` 这种无序列表格式替代脚注定义。

#### 整段引用

如果某一整段内容来自单一来源，可以在段首用粗体标注来源，避免每句都打脚注：

```markdown
**[来源: OpenAI Blog][^openai-2025-gpt5]** GPT-5 在推理基准上相比前代提升了 40%。
模型采用了全新的 MoE 架构……
```

### 交叉引用

文档间的交叉链接使用相对路径：

```markdown
<!-- 同目录 -->
详见 [Subagent 实践](subagents.md)

<!-- 跨目录 -->
详见 [产品档案](../coding-agents/index.md)

<!-- 链接到具体章节（锚点 = 小写标题、空格变连字符、去掉特殊符号） -->
详见 [Transformer § Flash Attention](../foundations/transformer.md#5-flash-attentionio-感知的算法革新)
```

添加新章节或修改标题时，搜索全库检查是否有其他文档链接到旧锚点。

---

## mkdocs.yml 维护

`mkdocs.yml` 中的 `nav:` 定义了站点导航结构。**每新增一个 `.md` 文件，必须同时在 `nav:` 中添加对应条目**，否则文件不会出现在站点导航中。

```yaml
nav:
  - 首页: index.md
  - 基础理论:
    - foundations/index.md
    - Transformer 架构: foundations/transformer.md
    # ... 新增文件加在对应分区下
  - 应用技术:
    - applied/index.md
    - AI Agent 智能体: applied/ai-agents.md
    # ...
```

同时更新对应的 `index.md`（分区索引页）和 `docs/index.md`（站点首页）中的导航表格。

---

## 日更脚本

### 概述

- 入口：`scripts/daily_update.py`
- 只做一件事：拉 RSS + 爬虫 → 按订阅源写入 `journal/YYYY/MM/DD/<source>.md`
- 依赖管理：统一在 `pyproject.toml`，通过 `uv` 管理

### 运行

```bash
# 拉取过去 48h（默认）
uv run scripts/daily_update.py

# 拉取过去 24h
uv run scripts/daily_update.py --hours 24

# 只拉取指定源（用 slug 指定）
uv run scripts/daily_update.py --only simon-willison

# 快速验证新加的源（拉 1h）
uv run scripts/daily_update.py --hours 1
```

### feeds.yaml 结构

所有订阅源在 `scripts/feeds.yaml` 中登记，按分类组织：

```yaml
# 分类（顶层 key）: papers / industry / community
papers:
  - name: arXiv cs.AI          # 显示名称
    slug: arxiv-cs-ai          # 输出文件名（不含 .md）
    url: https://rss.arxiv.org/rss/cs.AI  # RSS 地址（type: rss 时必填）
    verified: true              # true = 已验证可用

industry:
  - name: Anthropic
    slug: anthropic
    type: scrape                # 网页爬虫（默认 rss）
    verified: true
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 显示名称，出现在 journal 条目的来源标签中 |
| `slug` | 是 | 输出文件名（不含 .md），也是爬虫模块的匹配 key |
| `url` | `type: rss` 时必填 | RSS/Atom 地址 |
| `type` | 否 | `rss`（默认）或 `scrape` |
| `verified` | 是 | 只有 `true` 的源才会被拉取 |

### 添加新 RSS 源

1. 在 `feeds.yaml` 对应分类下添加条目，设 `verified: false`
2. 运行 `uv run scripts/daily_update.py --hours 1 --only <slug>` 验证
3. 确认无报错后改为 `verified: true`

### 添加新爬虫源

1. 在 `scripts/scrapers/` 下新建 `<slug>.py`（文件名用 `snake_case`，SLUG 用 `kebab-case`）
2. 实现必需接口：

```python
NAME = "显示名称"           # str
SLUG = "kebab-slug"        # str，与 feeds.yaml 中的 slug 一致
CATEGORY = "industry"       # str，分类 key

def scrape(since=None) -> list[dict]:
    """
    返回条目列表。

    Args:
        since: datetime | None，只返回该时间之后的文章

    Returns:
        list[dict]，每个 dict 包含:
            - title: str      — 文章标题
            - link: str       — 文章 URL
            - summary: str    — 摘要（200 字以内）
            - published: str  — 发布日期 "YYYY-MM-DD"
            - source: str     — 来源名称（= NAME）
            - slug: str       — 来源 slug（= SLUG）
            - cat: str        — 分类 key（= CATEGORY）
    """
```

3. 在 `feeds.yaml` 中登记该源（`type: scrape`）
4. 运行 `uv run scripts/daily_update.py --hours 1 --only <slug>` 验证

`scrapers/__init__.py` 会自动发现包内所有模块（通过 `pkgutil.iter_modules`），按模块的 `SLUG` 属性建立索引。无需手动注册。

---

## LLM 整理流程（手动触发）

脚本只负责拉取原始素材到 `journal/`。后续整理由人 + LLM 协作完成。

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
| Agent 生命周期钩子 | `docs/applied/agent-hooks.md` |
| Subagent/多 Agent 架构 | `docs/applied/subagents.md` |
| 硬件/推理/部署 | `docs/applied/infrastructure.md` |
| 推理模型进展 | `docs/research/reasoning-and-planning.md` |
| 安全/治理/可解释性 | `docs/research/safety-and-governance.md` |
| 其他前沿方向 | `docs/research/emerging-frontiers.md` |
| 新编码 Agent 产品 | `docs/coding-agents/<product>.md`（新建） |

### 4. 更新 docs/resources.md

如果发现值得长期收藏的论文、工具或博客，添加到 `docs/resources.md` 对应分类下。

### 提示词参考

让 LLM 帮忙整理时可以这样说：

> 阅读 journal/2026/04/07/ 目录下的今日素材，帮我：
> 1. 用技术视角筛选出最值得关注的 5 条——关注技术方案创新和工程亮点，跳过纯功能发布和通用知识
> 2. 判断哪些应该更新到知识文档中
> 3. 直接帮我更新对应的文件（记得更新 frontmatter 的 updated 字段，遵循"内容偏好"中的写作原则）

---

## 构建 & 验证

### 本地预览站点

```bash
uv run mkdocs serve
```

浏览器打开 `http://127.0.0.1:8000` 预览。

### 严格构建（CI 使用）

```bash
uv run mkdocs build --strict
```

`--strict` 会将警告视为错误（如断链、未定义的脚注等）。GitHub Actions 使用此命令构建。

### 日更脚本验证

```bash
uv run scripts/daily_update.py --hours 1
```

### 自动部署

推送到 `main` 分支后，GitHub Actions 自动执行：
1. `uv run mkdocs build --strict` 构建站点
2. 部署到 GitHub Pages

配置见 `.github/workflows/deploy-pages.yml`。
