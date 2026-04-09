---
title: Subagent 实践：从架构到工程模式
description: Subagent 是解决单一 Agent 串行瓶颈与上下文膨胀的核心架构模式。本文从技术原理、调用机制、实战模式到反模式，系统梳理 subagent 的工程实践。
created: 2026-04-09
updated: 2026-04-09
tags: [agents, subagents, multi-agent, context-management, parallel-execution]
review:
---

# Subagent 实践：从架构到工程模式

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

自定义 subagent 本质上是**带 YAML frontmatter 的 Markdown 文件**，body 部分就是 system prompt[^anthropic-docs-2026]：

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

### 4.1 作用域与优先级

| 位置 | 作用域 | 优先级 |
|------|--------|--------|
| Managed settings | 组织级 | 1（最高） |
| `--agents` CLI 参数 | 当前会话 | 2 |
| `.claude/agents/` | 当前项目（可 Git 共享） | 3 |
| `~/.claude/agents/` | 用户级（跨项目） | 4 |
| Plugin 的 `agents/` 目录 | 插件启用范围 | 5（最低） |

同名 subagent 高优先级覆盖低优先级，这为企业级管控提供了灵活性。

### 4.2 核心配置字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 唯一标识，小写+连字符 |
| `description` | 是 | **关键**——主 Agent 据此决定何时自动委派 |
| `tools` | 否 | 工具白名单（省略则继承所有） |
| `disallowedTools` | 否 | 工具黑名单（从继承列表中排除） |
| `model` | 否 | `sonnet` / `opus` / `haiku` / `inherit` / 完整模型 ID |
| `permissionMode` | 否 | `default` / `acceptEdits` / `auto` / `dontAsk` / `bypassPermissions` / `plan` |
| `mcpServers` | 否 | 为 subagent 独立配置 MCP 服务器（不影响主会话） |
| `hooks` | 否 | 生命周期钩子（PreToolUse / PostToolUse / Stop） |
| `memory` | 否 | 持久化记忆作用域：`user` / `project` / `local` |
| `skills` | 否 | 启动时注入的 Skill 内容 |
| `isolation` | 否 | 设为 `worktree` 可在独立 git worktree 中运行 |
| `maxTurns` | 否 | 最大推理轮次，防止 subagent 陷入循环 |
| `background` | 否 | `true` 则始终作为后台任务运行 |

### 4.3 工具权限控制的巧妙设计

- `tools`（白名单）和 `disallowedTools`（黑名单）可组合使用：黑名单先执行，再从剩余池中匹配白名单
- `Agent(worker, researcher)` 语法可限制 subagent 能生成哪些子类型（仅 `--agent` 模式下有效）
- MCP 服务器可以内联定义在 subagent 中，**仅对该 subagent 可见**，避免主会话上下文被不必要的工具描述占用

### 4.4 持久化记忆

Subagent 可以配置跨会话的持久记忆目录，用于积累领域知识：

| 作用域 | 存储位置 | 场景 |
|--------|----------|------|
| `user` | `~/.claude/agent-memory/<name>/` | 跨项目的通用知识 |
| `project` | `.claude/agent-memory/<name>/` | 项目专属，可 Git 共享 |
| `local` | `.claude/agent-memory-local/<name>/` | 项目专属，不入版本控制 |

启用后 subagent 会自动维护 `MEMORY.md`，每次启动时加载前 200 行或 25KB（取较小值）。这使得 subagent 可以从过去的审查中积累模式识别能力，逐渐变得更有效。

---

## 5. 触发与调用机制

Subagent 有四个层次的触发方式，从即席到全自动[^claude-blog-2026]：

### 5.1 自然语言调用

直接在对话中描述，主 Agent 自动判断是否委派：

```
Use subagents to explore this codebase in parallel:
1. Find all API endpoints and summarize their purposes
2. Identify the database schema and relationships
3. Map out the authentication flow
Return a summary of each, not the full file contents.
```

有效的提示结构：明确定义独立任务 → 显式请求并行 → 指定返回格式。

### 5.2 @-mention 精确调用

`@"security-reviewer (agent)"` 强制使用指定 subagent，而非让主 Agent 自行选择。

### 5.3 CLAUDE.md 策略驱动

将 subagent 使用规则写入项目级 `CLAUDE.md`，确保团队一致行为：

```markdown
## Code review standards
When asked to review code, ALWAYS use a subagent with READ-ONLY access
(Glob, Grep, Read only). The review should ALWAYS check for:
- Security vulnerabilities
- Performance issues
- Adherence to project patterns in /docs/architecture.md
```

### 5.4 Hooks 自动化

通过生命周期钩子实现全自动 subagent 触发，例如 Stop hook 阻止 Agent 结束直到测试通过：

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/check-tests.sh"
      }]
    }]
  }
}
```

**渐进策略**：从对话式调用开始 → 发现重复模式后抽象为自定义 subagent → 用 CLAUDE.md 固化团队规范 → 最终用 Hooks 实现全自动化[^claude-blog-2026]。

---

## 6. 实战模式

### 6.1 先调研后实现（Research → Implement）

在不熟悉的代码中添加功能前，先用 subagent 做调研，避免主会话被原始上下文淹没：

```
Before I implement user notifications, use a subagent to research:
- How are emails currently sent in this codebase?
- What notification patterns already exist?
- Where should new notification logic live based on the current architecture?
Summarize findings, then we'll plan the implementation together.
```

主会话收到的是综合摘要而非 20 个文件的原始内容。

### 6.2 并行修改（Parallel Modifications）

相同模式需要在多个文件中更新时，并行 subagent 比串行快数倍：

```
Use parallel subagents to update the error handling in these files:
- src/api/users.ts
- src/api/orders.ts
- src/api/products.ts
Each should follow the pattern established in src/api/auth.ts.
```

### 6.3 独立审查（Independent Review）

用一个**不继承实现历史**的 subagent 做代码审查，避免"知道太多"导致的盲点：

```
Use a fresh subagent with read-only access to review my implementation
of the payment flow. It should not see our previous discussion.
Check for: security vulnerabilities, unhandled edge cases, and error handling gaps.
```

### 6.4 流水线（Pipeline Workflow）

多阶段任务中，每个阶段用独立 subagent，通过文件作为阶段间的交接物：

```
1. First subagent: Design the API contract → write to docs/api-spec.md
2. Second subagent: Implement backend endpoints based on that spec
3. Third subagent: Write integration tests for the implementation
Each stage should complete before the next begins.
```

### 6.5 三路并行审查（Skill 组合）

用 Skill 编排多个 subagent 做全方位审查[^claude-blog-2026]：

```markdown
# .claude/skills/deep-review/SKILL.md
---
name: deep-review
description: Comprehensive code review. Use when reviewing staged
  changes before a commit or PR.
---
Run three parallel subagent reviews on the staged changes:
1. Security review - vulnerabilities, injection risks, auth issues
2. Performance review - N+1 queries, memory leaks, blocking operations
3. Style review - consistency with project patterns in /docs/style-guide.md
Synthesize findings into a single summary with priority-ranked issues.
```

### 6.6 条件验证（Hooks + Subagent）

用 PreToolUse hook 对 subagent 的工具调用做运行时验证，例如只允许只读 SQL：

```yaml
name: db-reader
description: Execute read-only database queries
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
```

验证脚本拦截 `INSERT/UPDATE/DELETE/DROP` 等写操作（exit code 2 = 阻止执行）。这提供了比 `tools` 字段更细粒度的控制。

---

## 7. 反模式：何时不该用 Subagent

| 反模式 | 问题 | 替代方案 |
|--------|------|----------|
| **顺序强依赖任务** | 步骤 B 需要步骤 A 的完整输出，subagent 间无法直接通信 | 在主会话中串行执行 |
| **同文件并行编辑** | 两个 subagent 同时编辑同一文件会产生冲突 | 保持在一个上下文中处理 |
| **小任务** | 委派的开销（新建上下文、预授权）超过任务本身 | 直接在主会话中完成 |
| **定义过多专家 Agent** | Agent 选择器面临太多候选，自动委派变得不可靠 | 团队收敛到少量精心设计的 subagent |
| **需要 subagent 间协调** | Subagent 只向主会话汇报，不能相互通信 | 使用 Agent Teams（跨会话协调） |

**经验法则**：当任务需要探索 10+ 个文件，或涉及 3+ 个独立子任务时，subagent 的收益明显[^claude-blog-2026]。

---

## 8. Subagent vs Agent Teams

| 维度 | Subagent | Agent Teams |
|------|----------|-------------|
| **执行范围** | 单一会话内 | 跨独立会话 |
| **通信方式** | 只向主会话返回结果 | Agent 间可以互相通信 |
| **上下文** | 共享同一会话的 token 预算 | 每个 Agent 有完全独立的上下文 |
| **成本** | 较低（共享会话基础设施） | 较高（每个 Agent 是独立会话） |
| **适用场景** | 任务分解、并行探索、独立审查 | 持续协作、需要 Agent 间协调的工作流 |

---

## 9. 各产品 Subagent 实现对比

Subagent 已成为 Agent 工程的通用架构模式，但各产品的实现路径差异显著。

### 9.1 总览对比

| 维度 | Claude Code | Devin | OpenAI Codex (Symphony) | LangGraph | AutoGen | CrewAI |
|------|-------------|-------|------------------------|-----------|---------|--------|
| **架构类型** | 内置 tool call | 内置 tool call | 集中编排层 | 图的子节点/子图 | 多 Agent 对话 | 角色扮演 Agent |
| **上下文隔离** | 独立窗口，摘要回传 | 独立窗口，摘要回传 | 独立 Agent 实例 | 子图有独立状态 | 各 Agent 独立 | 各 Agent 独立 |
| **调用方式** | 自然语言 + @-mention + 自动委派 | 自然语言 + 自动委派 | 编排层 API 调度 | 代码定义图结构 | 代码定义对话流 | 代码定义角色和任务 |
| **并行执行** | 原生支持，前台/后台 | 原生支持 | 大规模并行（生产级） | 支持并行分支 | 支持并发对话 | 顺序为主 |
| **嵌套能力** | 不可嵌套 | 不可嵌套 | 多级编排 | 子图可嵌套 | Agent 可嵌套调用 | 支持层级委派 |
| **自定义程度** | Markdown 文件配置 | 配置文件 | 内部系统，未公开 | Python 代码完全控制 | Python 代码完全控制 | Python 代码 + YAML |
| **Hook/回调** | 25+ 生命周期事件 | 生命周期钩子 | 未公开 | Python callbacks | 事件驱动消息 | 回调/Step callback |
| **成本控制** | 按 subagent 选模型 | 按任务选模型 | ~10 亿 token/天 | 开发者自控 | 开发者自控 | 开发者自控 |

### 9.2 编程 Agent 产品（端到端方案）

#### Claude Code

最成熟的 subagent 落地实现，核心创新在于**声明式配置 + LLM 自主委派**[^anthropic-docs-2026]：

- 用 Markdown + YAML frontmatter 定义 subagent，零代码
- 主 Agent 根据 `description` 字段自动判断何时委派，无需硬编码路由
- 内置 Explore（Haiku 只读）、Plan（调研）、General-purpose（读写）三种分工
- 工具权限白名单/黑名单、MCP 服务器隔离、持久化记忆等完整工程能力
- 与 Agent Teams（跨会话协调）形成两级并行体系

#### Devin

Cognition 的 Devin 同样采用 subagent 并行架构，核心设计选择：

- 面向**独立子任务**的并发执行，每个 subagent 拥有独立上下文窗口
- 内置 `subagent_explore`（只读探索）和 `subagent_general`（完整工具访问）两种 profile
- 主 Agent 通过 `run_subagent` tool call 生成 subagent，可指定前台/后台模式
- 支持给 subagent 提供详细任务描述、文件路径、已知上下文等前置信息
- 无状态设计——subagent 不能问澄清问题，必须在 prompt 中前置所有上下文

#### OpenAI Codex + Symphony

OpenAI 的 Dark Factory 模式代表了 subagent 在生产环境的极端应用[^latentspace-2026-harness]：

- **Symphony**：基于 Elixir 的多 Agent 编排层，非公开的内部基础设施
- 核心差异：不是"一个主 Agent 委派子任务"，而是**集中式编排器调度大量 Agent 实例**
- 规模：>100 万行代码库，~10 亿 token/天，0% 人工参与
- **Harness Engineering** 思维：当 Agent 失败时，不优化 prompt，而是补全 Agent 需要的能力和上下文
- Agent 可读性优先：代码为模型而写，Skills/文档/测试/质量分数编码"工程品味"

### 9.3 Agent 框架（开发者工具）

#### LangGraph 子图（Subgraph）

在基于图的 Agent 框架中，子图是 subagent 的编程抽象：

```python
# 子图封装为独立执行单元
sub_graph = StateGraph(SubState)
sub_graph.add_node("research", research_node)
sub_graph.add_node("summarize", summarize_node)

# 主图引用子图
main_graph = StateGraph(MainState)
main_graph.add_node("sub_task", sub_graph.compile())
```

- 子图有独立状态（state），通过输入/输出映射与主图交换数据
- 支持子图嵌套（与 Claude Code 的不可嵌套约束不同）
- 并行分支通过图的分支结构实现
- 完全由开发者代码控制路由逻辑，没有 LLM 自主委派

#### AutoGen

Microsoft 的多 Agent 对话框架，subagent 以"对话参与者"形式存在：

- 每个 Agent 是独立实例，通过**消息传递**通信（而非摘要回传）
- GroupChat 管理器路由消息到合适的 Agent
- 支持嵌套对话（nested chat）——Agent A 在处理任务时启动与 Agent B 的子对话
- 更适合需要 Agent 间讨论/辩论的场景

#### CrewAI

角色扮演框架，subagent 以"团队成员"身份运作：

- 每个 Agent 有角色（Role）、目标（Goal）、背景故事（Backstory）
- 任务（Task）分配给特定 Agent，支持层级委派
- 默认顺序执行，可配置并行
- 重点在角色设计和任务编排，而非上下文隔离

### 9.4 关键设计差异总结

| 设计选择 | 产品级方案 (Claude Code / Devin) | 框架级方案 (LangGraph / AutoGen) |
|----------|-------------------------------|-------------------------------|
| **谁做委派决策** | LLM 自主判断 + 人类可覆盖 | 开发者硬编码路由逻辑 |
| **配置方式** | 声明式（Markdown/YAML） | 命令式（Python 代码） |
| **通信模型** | 摘要回传（信息压缩） | 完整消息传递（信息保留） |
| **适用场景** | 终端用户直接使用 | 开发者构建自定义系统 |
| **灵活性** | 受限于产品设计边界 | 完全可编程 |

共性：**用上下文隔离换取并行性和专注度，用信息压缩控制上下文膨胀**。

---

## 参考资料

[^claude-blog-2026]: Anthropic. "How and when to use subagents in Claude Code". 2026. https://claude.com/blog/subagents-in-claude-code
[^anthropic-docs-2026]: Anthropic. "Create custom subagents - Claude Code Docs". 2026. https://docs.anthropic.com/en/docs/claude-code/sub-agents
[^claude-code-product]: Claude Code 产品技术分析，见本库 `docs/coding-agents/claude-code.md`
[^latentspace-2026-harness]: Latent Space. "Extreme Harness Engineering for Token Billionaires — Ryan Lopopolo, OpenAI Frontier & Symphony". 2026. https://www.latent.space/p/harness-eng
