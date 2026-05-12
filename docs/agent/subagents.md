---
title: Subagent 实践：从架构到工程模式
description: Subagent 是解决单一 Agent 串行瓶颈与上下文膨胀的核心架构模式。本文从技术原理、调用机制到反模式，系统梳理 subagent 的工程实践。
created: 2026-04-09
updated: 2026-05-08
tags:
  - agent
  - subagents
  - multi-agent
  - context-management
  - parallel-execution
review: 2026-05-08
---

# Subagent 实践：从架构到工程模式

??? note "背景知识"
    - **Agent 执行循环**：思考→行动→观察的迭代过程 → [详见](ai-agents.md)
    - **上下文窗口**：LLM 单次能处理的最大 token 数，超出则信息丢失
    - **工具权限**：Agent 可调用的工具集合及其读写权限 → [详见](agent-tools.md)
    - **并发 vs 串行**：并行执行多个独立子任务 vs 顺序执行，影响延迟和资源开销

> Subagent 是解决单一 Agent 串行瓶颈与上下文膨胀的核心架构模式——将主 Agent 的任务分治到独立上下文窗口中并发执行，只回传结果摘要。

---

## 1. 为什么需要 Subagent

单一 Agent 在长会话中面临两个根本性工程问题：

1. **上下文膨胀**：每次文件读取、工具调用、探索性推理都累积在同一个上下文窗口中，导致响应变慢、token 成本攀升、注意力稀释
2. **串行瓶颈**：多个独立子任务只能排队执行，无法利用并行性

Subagent 的核心思想：**隔离 + 并发 + 摘要回传**。

```
主 Agent (保持干净的上下文)
  ├── Subagent A (独立上下文) → 返回摘要
  ├── Subagent B (独立上下文) → 返回摘要  ← 并发执行
  └── Subagent C (独立上下文) → 返回摘要
```

类比：Subagent 之于 Agent 会话，就像浏览器标签页之于主窗口——在独立空间追踪支线任务，不污染主线程[^claude-blog-2026]。

---

## 2. 架构原理

### 2.1 上下文隔离模型

每个 subagent 拥有**独立的上下文窗口**，具备以下特性：

| 特性 | 说明 |
|------|------|
| **独立上下文** | 不继承主会话的历史、已读文件、推理过程 |
| **独立权限** | 可配置不同的工具访问权限（只读 / 读写 / 受限 Bash） |
| **独立模型** | 可指定不同模型（如用 Haiku 做轻量探索，Opus 做复杂推理） |
| **结果回传** | 完成后只将摘要/结论返回主会话，不回传原始上下文 |

这解决了 Agent 工程中的核心难题——1M token 上下文窗口在长会话中如何有效分配：主 Agent 保持精简上下文用于决策，子任务的探索性上下文消耗被隔离在 subagent 中[^claude-code-product]。

### 2.2 不可嵌套约束

Subagent **不能再生成 subagent**（防止无限递归）。这是一个关键的架构约束：

- 如果需要多级委派，由主 Agent 串联多个 subagent（chain 模式）
- 如果需要 subagent 间通信，使用 Agent Teams（跨会话协调，更重更贵）

### 2.3 前台 vs 后台执行

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| **前台** | 阻塞主会话，权限提示直接传递给用户 | 需要交互确认的任务 |
| **后台** | 并发运行，启动前预授权所有需要的权限，运行中自动拒绝未授权操作 | 独立的探索/修改任务 |

后台 subagent 的权限预授权机制是关键设计：在启动时一次性确认权限边界，运行中不再打断用户。如果后台 subagent 因权限不足失败，可以用前台模式重试[^anthropic-docs-2026]。

---

## 3. 内置 Subagent 类型（以 Claude Code 为例）

Claude Code 是目前 subagent 架构最成熟的落地实现，其内置类型体现了典型的分工设计[^anthropic-docs-2026]：

| 类型 | 模型 | 工具权限 | 用途 |
|------|------|----------|------|
| **Explore** | Haiku（快、便宜） | 只读（无 Write/Edit） | 代码搜索、文件发现、架构探索 |
| **Plan** | 继承主会话 | 只读 | Plan Mode 下的前置调研 |
| **General-purpose** | 继承主会话 | 全部工具 | 复杂多步任务、需要读写的操作 |

设计亮点：

- **Explore 用 Haiku 而非 Sonnet/Opus**：搜索探索是高频低复杂度任务，用小模型显著降低成本和延迟
- **Explore 分三档彻底度**：`quick`（精准查找）、`medium`（均衡探索）、`very thorough`（全面分析），由主 Agent 根据任务判断
- **Plan subagent 的递归防护**：Plan Mode 下需要调研代码库，但 subagent 不能嵌套，所以 Plan subagent 只做调研，不做规划

---

## 4. 自定义 Subagent 配置

自定义 subagent 是**带 YAML frontmatter 的 Markdown 文件**，body 即 system prompt[^anthropic-docs-2026]：

```markdown
---
name: security-reviewer
description: Reviews code changes for security vulnerabilities,
  injection risks, auth issues, and sensitive data exposure.
  Use proactively before commits touching auth, payments, or user data.
tools: Read, Grep, Glob
model: sonnet
---

You are a security-focused code reviewer. Analyze the provided
changes for:
- SQL injection, XSS, and command injection risks
- Authentication and authorization gaps
- Sensitive data in logs, errors, or responses
- Insecure dependencies or configurations

Return a prioritized list of findings with file:line references
and a recommended fix for each.
```

**核心字段**：
- `name`：唯一标识（小写+连字符）
- `description`：**关键**——主 Agent 据此决定何时自动委派
- `tools`：工具白名单（省略则继承所有）
- `disallowedTools`：工具黑名单
- `model`：指定模型（`sonnet` / `opus` / `haiku` / `inherit`）
- `permissionMode`：权限模式（`default` / `auto` / `dontAsk` 等）
- `mcpServers`：独立配置 MCP 服务器
- `memory`：持久化记忆作用域（`user` / `project` / `local`）

**作用域优先级**：Managed settings（组织级） > `--agents` CLI 参数 > `.claude/agents/`（项目级） > `~/.claude/agents/`（用户级） > Plugin `agents/` 目录。同名 subagent 高优先级覆盖低优先级。

**工具权限**：`tools`（白名单）和 `disallowedTools`（黑名单）可组合使用。MCP 服务器可内联定义在 subagent 中，仅对该 subagent 可见，避免主会话上下文被不必要的工具描述占用。

**持久化记忆**：启用后 subagent 自动维护 `MEMORY.md`，每次启动时加载前 200 行或 25KB，从过去的审查中积累模式识别能力。

---

## 5. 触发机制

**自然语言调用**：直接在对话中描述，主 Agent 自动判断是否委派：

```
Use subagents to explore this codebase in parallel:
1. Find all API endpoints and summarize their purposes
2. Identify the database schema and relationships
3. Map out the authentication flow
Return a summary of each, not the full file contents.
```

有效的提示结构：明确定义独立任务 → 显式请求并行 → 指定返回格式。

**@-mention 精确调用**：`@"security-reviewer (agent)"` 强制使用指定 subagent，而非让主 Agent 自行选择。

---

## 6. 反模式：何时不该用 Subagent

| 反模式 | 问题 | 替代方案 |
|--------|------|----------|
| **顺序强依赖任务** | 步骤 B 需要步骤 A 的完整输出，subagent 间无法直接通信 | 在主会话中串行执行 |
| **同文件并行编辑** | 两个 subagent 同时编辑同一文件会产生冲突 | 保持在一个上下文中处理 |
| **小任务** | 委派的开销（新建上下文、预授权）超过任务本身 | 直接在主会话中完成 |
| **定义过多专家 Agent** | Agent 选择器面临太多候选，自动委派变得不可靠 | 团队收敛到少量精心设计的 subagent |
| **需要 subagent 间协调** | Subagent 只向主会话汇报，不能相互通信 | 使用 Agent Teams（跨会话协调） |

**经验法则**：当任务需要探索 10+ 个文件，或涉及 3+ 个独立子任务时，subagent 的收益明显[^claude-blog-2026]。

---

## 7. Subagent vs Agent Teams

| 维度 | Subagent | Agent Teams |
|------|----------|-------------|
| **执行范围** | 单一会话内 | 跨独立会话 |
| **通信方式** | 只向主会话返回结果 | Agent 间可以互相通信 |
| **上下文** | 共享同一会话的 token 预算 | 每个 Agent 有完全独立的上下文 |
| **成本** | 较低（共享会话基础设施） | 较高（每个 Agent 是独立会话） |
| **适用场景** | 任务分解、并行探索、独立审查 | 持续协作、需要 Agent 间协调的工作流 |

---

## 参考资料

[^claude-blog-2026]: Anthropic. "How and when to use subagents in Claude Code". 2026. https://claude.com/blog/subagents-in-claude-code
[^anthropic-docs-2026]: Anthropic. "Create custom subagents - Claude Code Docs". 2026. https://docs.anthropic.com/en/docs/claude-code/sub-agents
[^claude-code-product]: Claude Code 产品技术分析，见本库 `docs/coding-agents/claude-code.md`
