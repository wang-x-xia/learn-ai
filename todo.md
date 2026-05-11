# Docs 目录重组计划

## 现状分析

### 当前结构

```
docs/
├── foundations/        # 基础理论 — 6 篇
├── applied/            # 应用技术 — 14 篇 ← 问题所在
├── research/           # 前沿研究 — 3 篇
├── model/              # 模型档案 — 2 篇
├── coding-agents/      # 编码 Agent — 1 篇 (claude-code)
├── personal-agents/    # 个人 Agent — 2 篇
├── agent-workflow/     # Agent 框架 — 5 篇
├── libraries/          # 开源库   — 1 篇 (honcho)
├── index.md
└── resources.md
```

当前 nav 有 **7 个顶级 tab**（首页、基础理论、应用技术、前沿研究、模型档案、产品档案、精选资源），过于分散。

### 核心问题

1. **`applied/` 成了 14 篇的大杂烩**，混合 Agent 技术栈 (7)、通用 AI 技术 (4)、基础设施 (3)
2. **顶级 nav 过多** — 7 个 tab 让导航杂乱，需要精简到 ≤5 个

---

## 重组方案

### 一、目录变更

#### 变更 1：创建 `agent/` — 从 applied/ 拆出 Agent 技术栈

| 原路径 | 新路径 |
|--------|--------|
| `applied/ai-agents.md` | `agent/ai-agents.md` |
| `applied/memory-systems.md` | `agent/memory-systems.md` |
| `applied/agent-tools.md` | `agent/agent-tools.md` |
| `applied/agent-skills.md` | `agent/agent-skills.md` |
| `applied/agent-protocols.md` | `agent/agent-protocols.md` |
| `applied/agent-hooks.md` | `agent/agent-hooks.md` |
| `applied/subagents.md` | `agent/subagents.md` |

新建 `agent/index.md` + `agent/AGENTS.md`。

#### 变更 2：创建 `infrastructure/` — 从 applied/ 拆出基础设施

| 原路径 | 新路径 |
|--------|--------|
| `applied/infrastructure.md` | `infrastructure/infrastructure.md` |
| `applied/lustre.md` | `infrastructure/lustre.md` |
| `applied/inference-economics.md` | `infrastructure/inference-economics.md` |

新建 `infrastructure/index.md` + `infrastructure/AGENTS.md`。

#### 变更 3：`applied/` 瘦身

保留 4 篇：`thinking-mode.md`、`prompt-engineering.md`、`rag.md`、`browser-automation.md`。
更新 `applied/index.md` + `applied/AGENTS.md`。

#### 变更 4：产品档案不动

`coding-agents/`、`personal-agents/`、`agent-workflow/`、`libraries/` 保持现状。

### 二、Nav 精简为 4 个顶级 tab

精选资源从独立 tab 降为首页子页面。合并后的顶级 tab：

```yaml
nav:
  - 首页:
    - index.md
    - 精选资源: resources.md

  - 基础理论:
    - foundations/index.md
    - Transformer 架构: foundations/transformer.md
    - KV Cache 与推理优化: foundations/kv-cache.md
    - Mamba 与 SSM: foundations/mamba-and-ssm.md
    - 多模态 AI: foundations/multimodal-ai.md
    - 扩散模型: foundations/diffusion-models.md
    - 从规则到表示学习: foundations/representation-learning.md

  - 应用技术:
    - Agent 技术栈:
      - agent/index.md
      - AI Agent 智能体: agent/ai-agents.md
      - Agent 记忆系统: agent/memory-systems.md
      - Agent 工具接入: agent/agent-tools.md
      - Agent Skills: agent/agent-skills.md
      - Agent 间协议: agent/agent-protocols.md
      - Agent Hooks: agent/agent-hooks.md
      - Subagent 实践: agent/subagents.md
    - 通用技术:
      - applied/index.md
      - Thinking Mode: applied/thinking-mode.md
      - 提示工程: applied/prompt-engineering.md
      - 检索增强生成 (RAG): applied/rag.md
      - AI 浏览器自动化: applied/browser-automation.md
    - 基础设施:
      - infrastructure/index.md
      - AI 基础设施: infrastructure/infrastructure.md
      - Lustre 并行文件系统: infrastructure/lustre.md
      - 推理经济性: infrastructure/inference-economics.md

  - 研究、模型与产品:
    - 前沿研究:
      - research/index.md
      - 可解释性: research/interpretability.md
      - AI 安全与治理: research/safety-and-governance.md
      - Engram: research/engram.md
    - 模型档案:
      - model/index.md
      - Claude Mythos Preview: model/claude-mythos.md
      - DeepSeek-V4: model/deepseek-v4.md
    - 编码工具:
      - coding-agents/index.md
      - Claude Code: coding-agents/claude-code.md
    - 开源库:
      - libraries/index.md
      - libraries/honcho.md
    - Agent Workflow:
      - agent-workflow/index.md
      - LangGraph: agent-workflow/langgraph.md
      - Ruflo: agent-workflow/ruflo.md
      - Microsoft Agent Framework: agent-workflow/maf.md
      - Dify: agent-workflow/dify.md
      - NeMo Agent Toolkit: agent-workflow/nemo-agent-toolkit.md
    - 个人 Agent:
      - personal-agents/index.md
      - Hermes Agent: personal-agents/hermes-agent.md
      - OpenClaw: personal-agents/openclaw.md
```

**效果：** 首页 | 基础理论 | 应用技术 | 研究、模型与产品 — 共 4 个 tab，≤5 限制。

### 三、校验规则 — 限制顶级 nav ≤5

在 `validate_docs.py` 中新增检查：解析 `mkdocs.yml`，校验顶级 nav 条目数 ≤ 5。
超出时报 ERROR，阻断 CI。

---

## 执行步骤

### 1. 文件移动
- [ ] 创建 `docs/agent/` 和 `docs/infrastructure/` 目录
- [ ] 移动 7 个 Agent 文件到 `agent/`
- [ ] 移动 3 个基础设施文件到 `infrastructure/`

### 2. 新建文件
- [ ] 创建 `agent/index.md`
- [ ] 创建 `agent/AGENTS.md`
- [ ] 创建 `infrastructure/index.md`
- [ ] 创建 `infrastructure/AGENTS.md`

### 3. 更新交叉引用

需要更新的交叉引用（按影响统计）：

| 被移动文件 | 引用次数 | 涉及目录 |
|------------|---------|----------|
| `applied/ai-agents.md` | 15+ | agent-workflow/, personal-agents/, coding-agents/, applied/ 内部 |
| `applied/memory-systems.md` | 6+ | personal-agents/, libraries/, agent-workflow/ |
| `applied/agent-tools.md` | 5+ | agent-workflow/ |
| `applied/agent-skills.md` | 5+ | agent-workflow/, personal-agents/ |
| `applied/agent-hooks.md` | 3+ | agent-workflow/ |
| `applied/subagents.md` | 3+ | personal-agents/ |
| `applied/infrastructure.md` | 2+ | applied/lustre (→ infrastructure/lustre) |

- [ ] 更新 `agent/` 内文件的相互引用
- [ ] 更新 `agent-workflow/*.md` 中指向旧 applied/ 的链接
- [ ] 更新 `personal-agents/*.md` 中的链接
- [ ] 更新 `coding-agents/*.md` 中的链接
- [ ] 更新 `libraries/*.md` 中的链接
- [ ] 更新 `research/*.md` 中的链接
- [ ] 更新 `docs/index.md` 中的链接
- [ ] 更新 `infrastructure/` 内文件的相互引用

### 4. 更新配置 & 校验
- [ ] 更新 `mkdocs.yml` nav 为上述 4-tab 结构
- [ ] 更新 `applied/index.md`（移除已迁走的条目）
- [ ] 更新 `applied/AGENTS.md`（更新收录范围）
- [ ] 更新根 `AGENTS.md` 中的目录约定
- [ ] `validate_docs.py` 新增顶级 nav ≤5 检查

### 5. 验证
- [ ] `uv run mkdocs build --strict` 构建通过
- [ ] `uv run scripts/validate_docs.py` 校验通过（含新 nav 规则）
- [ ] 所有交叉引用无死链
