# AGENTS.md — 项目约定

## 项目概述

个人 AI 前沿知识库。知识文档用中文编写，代码和配置用英文。

- 站点使用 MkDocs Material 生成，推送 `main` 后由 GitHub Actions 自动部署到 GitHub Pages
- 依赖管理统一使用 `uv`，Python 版本要求 `>=3.12`

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
│   ├── foundations/             # 基础理论（低频更新）
│   ├── applied/                # 应用技术（中频更新）
│   ├── research/               # 前沿研究（高频更新）
│   ├── coding-agents/          # 编码 Agent 产品档案
│   └── landscape/              # 行业全景（模型跟踪）
├── journal/                     # 每日 RSS 原始素材（脚本自动生成）
├── scripts/                     # 自动化脚本
├── mkdocs.yml                   # 站点配置 & 导航
└── pyproject.toml               # Python 依赖
```

每个子目录都有自己的 `AGENTS.md`，记录该目录的文件列表、收录范围和特殊约定。

### 文件命名

- **知识文档**：`kebab-case.md`（如 `ai-agents.md`、`prompt-engineering.md`）
- **Python 脚本**：`snake_case.py`（如 `daily_update.py`）
- **journal 文件**：`<source-slug>.md`，由脚本自动生成

---

## Markdown 规范

### Frontmatter

每个 `.md` 文件必须有 YAML frontmatter。知识文档要求六个字段（`title`、`description`、`created`、`updated`、`tags`、`review`），索引页只需 `title` + `description`。各目录的具体要求见对应的 `AGENTS.md`。

`review` 字段记录维护者最后一次阅读/审校该文档的日期（`YYYY-MM-DD`），留空表示从未 review。Review 过程中不要更新 `review` 日期，等维护者确认 review 完成后再更新。用 `uv run scripts/review_status.py` 查看待 review 清单。

### 来源标识（脚注）

用 Markdown 脚注标记出处，不要用无序列表。

**Key 命名**：`来源简写-年份-关键词`，全小写连字符分隔（如 `arxiv-2025-attention`、`openai-2025-gpt5`）。

**行内引用**：`...关联权重[^vaswani-2017]。`

**参考资料区**：在文档末尾 `## 参考资料` 下定义所有脚注：

```markdown
## 参考资料

[^vaswani-2017]: Vaswani et al. *Attention Is All You Need*. 2017. https://arxiv.org/abs/1706.03762
```

每个 `[^key]` 引用**必须**有对应的 `[^key]: ...` 定义。

### 交叉引用

文档间链接使用相对路径。添加新章节或修改标题时，搜索全库检查是否有其他文档链接到旧锚点。

---

## mkdocs.yml 维护

每新增一个 `.md` 文件，必须同时在 `mkdocs.yml` 的 `nav:` 中添加对应条目，以及更新对应的 `index.md`。

---

## 日更脚本

入口：`scripts/daily_update.py`。详细用法和订阅源配置见 `scripts/AGENTS.md`。

```bash
uv run scripts/daily_update.py              # 默认拉取 48h
uv run scripts/daily_update.py --hours 1    # 验证新源
```

---

## LLM 整理流程（手动触发）

脚本只负责拉取原始素材到 `journal/`。后续整理由人 + LLM 协作完成：

1. 阅读 `journal/YYYY/MM/DD/` 当日素材
2. 按筛选标准挑选值得收录的内容
3. 更新对应知识文档（各目录的 `AGENTS.md` 有文件-主题映射表）
4. 如有新模型，更新 `docs/landscape/model-tracker.md`
5. 如有精选资源，添加到 `docs/resources.md`

---

## 构建 & 验证

```bash
uv run mkdocs serve              # 本地预览
uv run mkdocs build --strict     # 严格构建（CI 使用，警告视为错误）
uv run scripts/validate_docs.py  # 检查 frontmatter 和脚注规范
uv run scripts/review_status.py  # 查看待 review 清单
uv run scripts/daily_update.py --hours 1   # 日更脚本验证
```

推送 `main` 后 GitHub Actions 自动构建部署（`.github/workflows/deploy-pages.yml`）。
