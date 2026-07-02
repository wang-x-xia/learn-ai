# AGENTS.md — 项目约定

## 项目概述

个人 AI 前沿知识库。

## 构建 & 验证

任何commit之前，必须确保以下两个命令没有任何warning和error：

```bash
# 构建站点，同时校验文档是否符合zensical的规范
uv run zensical build --strict   
# 检查本项目特别定义的规范，自动修复可修复项
uv run scripts/validate_docs.py --auto-fix
```

推送 `main` 后 GitHub Actions 自动构建部署（`.github/workflows/deploy-pages.yml`）。

## 原则

- 知识文档用中文编写，使用Markdown格式。代码和配置用英文。

以下原则针对代码和配置：

- 新增依赖用 `uv add <pkg>`，不要使用 PEP 723 inline script metadata——项目统一通过 `pyproject.toml` 管理依赖，避免声明分散。

**不要碰：**

- `uv.lock` — 自动生成，不要手动编辑
- `.github/workflows/` — CI 配置，除非维护者要求

## 知识库文档原则

- **聚焦技术原理**：优先展示在技术实现上有哪些创新。
- **去重复化**：通用特性不需要在每个文档里重复。如需说明共性，集中在品类概述文档中写一次。积极地链接其他文档，而不是复制粘贴。
- **弱化用法**：只有在技术实现举例的时候，考虑展示具体的使用方法。在绝大多数情况下，当技术理念比较简单时，不需要特别强调用法上的创新。
- **先讲直觉，再给形式化**：每个核心概念先用类比或具体例子建立直觉，再给出数学定义和公式。公式用 LaTeX 格式，行内用 `$` 包裹，块级用 `$$` 包裹，尽量避免不必要的形式化。
- **善用 Mermaid 图表和对比表**：流程用 Mermaid 可视化，方案对比用精炼的表格（含"权衡"列），避免大段文字叙述。
- **简化历史演进**：技术脉络只需一句话交代前置工作的不足，然后聚焦当前最重要的突破点。
- **单文件精简**：知识库用于快速回忆重点，细节通过引用外部链接达成。单文件**内容行数**（不计 frontmatter 和 `## 参考资料` 以下部分）不超过 **500 行**，超出时应拆分或精简。

### Frontmatter

每个 `.md` 文件必须有 YAML frontmatter。

```yaml
title: "文档标题"
description: "文档描述"
created: "2025-10-15"
updated: "2025-10-15"
# 最后一次review的时间，Review 过程中不要更新 `review` 日期，等维护者确认 review 完成后再更新。
# 使用 uv run scripts/review_status.py 查看项目内所有文档的review状态。
review: "2025-10-15"
# 可选，review未完全完成时的备注。review全部完成后删除此字段。
review_note: ""
tags:
  # 必须使用 YAML 列表格式（连字符缩进），禁止使用 JSON 数组格式（会导致 Zensical 构建警告）。
  - multimodal
  - vision-language
  - reasoning
```

索引页只需 `title`, `description`。

### 背景知识规范（可选）

每篇知识文档在 `# 标题` 之后、正文之前，放一个**可折叠 admonition** 快速铺垫前置概念，至多6条：

```markdown
??? note "背景知识"
    - **概念 A**：一句话解释 → [详见](相对路径)
    - **概念 B**：一句话解释 → [详见](相对路径)
```

## 产品档案（可选）

对于产品、框架、开源库等，背景知识之后，可以添加如下的章节用来展示产品的基本信息：

```markdown
# 产品档案

| 属性 | 值 |
|------|-----|
| 厂商 | ... |
| 形态 | ... |
| 开源 | 是/否 |
| GitHub | [链接](url) |
| 官网 | [链接](url) |
```

属性表字段按需增减（如框架可加"语言"列，产品可加"定价"段落）。

### 来源标识（脚注）

在文末用以下章节标记来源出处：

```markdown
## 参考资料

[^vaswani-2017]: Vaswani et al. *Attention Is All You Need*. 2017. https://arxiv.org/abs/1706.03762
```

使用`来源简写-年份-关键词`作为引用的key，全小写连字符分隔（如 `arxiv-2025-attention`、`openai-2025-gpt5`）。
每个 `[^key]` 引用**必须**有对应的 `[^key]: ...` 定义。

### 交叉引用

文档间链接使用相对路径。添加新章节或修改标题时，搜索全库检查是否有其他文档链接到旧锚点。

### mkdocs.yml 维护

每新增一个 `.md` 文件，必须同时在 `mkdocs.yml` 的 `nav:` 中添加对应条目，以及更新对应的 `index.md`。

**顶级 nav 条目数 ≤ 5**：`nav:` 的第一级列表项不得超过 5 个（超过的话页面会不好看）。新增内容应归入现有顶级分类的子节。

## 目录结构与收录范围

```
learn-ai/
├── docs/                            # 知识文档（Zensical 源文件）
│   ├── foundations/                 # 稳定核心知识（Transformer、KV Cache、SSM、多模态）
│   ├── agent/                      # Agent 技术栈（执行循环、记忆、工具、协议、Skills）
│   ├── applied/                    # 通用 AI 应用技术（提示工程、RAG、浏览器自动化）
│   ├── ai-personal-software/       # AI 个人软件产品档案
│   ├── agent-workflow/             # Agent Workflow 框架产品档案
│   ├── embodied-algorithm/         # 具身算法（VLA、世界模型）
│   ├── embodied-infrastructure/    # 具身基础设施（数据、仿真、中间件）
│   ├── infrastructure/             # 系统基础设施 & 经济性（中频更新）
│   ├── hardware/                   # 硬件产品档案
│   ├── research/                   # 前沿研究（高频更新）
│   ├── model/                      # 模型档案（重要模型深度分析）
│   └── libraries/                  # 开源库产品档案
├── exam/                            # 考试评测脚本（非知识库内容）
├── how-to-learn/                    # 学习方法笔记（非知识库内容）
├── idea/                            # 想法草稿与探索（非知识库内容）
├── scripts/                         # 自动化脚本
├── mkdocs.yml                       # 站点配置 & 导航（Zensical 可直接读取）
└── pyproject.toml                   # Python 依赖
```

