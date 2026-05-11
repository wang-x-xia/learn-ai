---
title: Ruflo
description: RuvNet 的 Agent 控制平面与双前端产品：flo.ruv.io 负责多模型 Chat + MCP 工具调用，goal.ruv.io 负责 GOAP 目标规划与 live agents。
created: 2026-05-06
updated: 2026-05-06
tags: [framework, ruvnet, agent, typescript, claude-code]
review: 2026-05-06
---

# Ruflo

??? note "背景知识"
    - **Agent 执行循环**：思考→行动→观察的迭代 → [详见](../agent/ai-agents.md)
    - **MCP (Model Context Protocol)**：Agent 与工具之间的标准连接协议 → [详见](../agent/agent-tools.md#2-mcpmodel-context-protocol)
    - **GOAP (Goal-Oriented Action Planning)**：从目标状态反向搜索行动序列的规划方法
    - **Agent 记忆系统**：跨会话的知识持久化与检索 → [详见](../agent/memory-systems.md)

> RuvNet 出品，值得关注的不是"又一个 Agent SDK"，而是把多 Agent 编排拆成三个层面：**本地控制平面、浏览器里的多模型 Chat 前端、以及独立的目标规划前端**。[^ruflo-readme-2026][^ruflo-init-2026]

| 属性 | 值 |
|------|-----|
| 厂商 | RuvNet |
| 语言 | TypeScript |
| 开源 | 是 |
| GitHub | [ruvnet/ruflo](https://github.com/ruvnet/ruflo) |
| 官网 | [flo.ruv.io](https://flo.ruv.io/) / [goal.ruv.io](https://goal.ruv.io/) |

## 技术亮点

- **完整的 CLI 编排控制平面**：Ruflo 不是简单的 Claude Code 插件，而是独立的 orchestration layer。CLI 提供 `task`（创建/分配/重试/取消）、`agent`（spawn 15 种类型）、`memory`（存储/检索/语义搜索）等完整管理命令，通过 MCP tools 调用，独立于任何前端运行。[^ruflo-task-2026][^ruflo-agent-2026][^ruflo-memory-2026]
- **多拓扑 Agent 协调**：支持 6 种通信拓扑（hierarchical、mesh、ring、star、hybrid、hierarchical-mesh），其中 `hierarchical-mesh` 是 V3 推荐配置（15-agent queen + peer communication）。拓扑决定 agent 间消息传递路径和协调机制。[^ruflo-swarm-2026]
- **动态进度计算**：进度百分比不是硬编码在 state.json，而是通过扫描 `.swarm/tasks/*.json` 实时计算：`progress = (completedTasks / totalTasks) * 100`。Swarm 状态（running/completed/ready/idle）也基于任务状态和 agent 活跃度动态判断。[^ruflo-swarm-2026]
- **向量记忆层**：Memory 支持多后端（AgentDB、SQLite、Hybrid、In-Memory）、namespace、TTL、tags、vector embedding、语义搜索（HNSW 索引，150x-12,500x 加速）、SmartRetrieval（query expansion、RRF、MMR、recency）。[^ruflo-memory-2026]
- **同一能力面多前端复用**：README 明说 `flo.ruv.io` 的 Web UI 会直接调用与 CLI 相同的 MCP tools。这说明 Ruflo 的核心不是某个单一界面，而是一层可被不同前端复用的 orchestration substrate。[^ruflo-readme-2026]
- **把"聊天"和"规划"拆成两个产品入口**：`flo.ruv.io` 负责多模型 chat + tool use；`goal.ruv.io` 负责 plain-English goal → GOAP / A* plan → live agents。这种拆法比"支持多 Agent"更有产品区分度，因为它把对话式交互和显式规划变成了两个独立 surface。[^ruflo-readme-2026]

## 历史用户故事：Claude Code 增强层

Ruflo 最早、也最容易理解的切入口，是给 Claude Code 加一层多 Agent orchestration。它当时的叙事是：程序员继续在 Claude Code 里写代码，Ruflo 在旁边补上 swarm、memory、session、hooks、MCP 和后台协调能力。[^ruflo-readme-2026][^ruflo-init-2026]

这条线现在更适合被看作**历史用户故事 / 早期分发路径**，而不是文档的主叙事，原因有两点：

1. README 已经把能力面拆成多个入口，Claude Code 不再是唯一 front door。`flo.ruv.io` 和 `goal.ruv.io` 都被单独抬成产品级入口。[^ruflo-readme-2026]
2. Claude Code plugin 路径本身是一个明显被简化过的 lite 版本：它主要提供 slash commands 和 agent definitions；真正完整的运行环路仍然要靠 `npx ruflo init` 落地到本地控制平面。[^ruflo-readme-2026]

因此，Claude Code 相关的 plugin、hooks、MCP，更适合被理解为 Ruflo 早期最重要的**集成渠道**，而不是它今天最有知识价值的产品本体。[^ruflo-readme-2026][^ruflo-mcp-2026]

## 主要用户故事 1：flo.ruv.io 把"Agent 控制平面"变成可直接试用的 Chat 产品

直觉上，`flo.ruv.io` 解决的是一个很实际的问题：如果多 Agent orchestration 只能通过本地 CLI + init + hook 才能体验，门槛太高，也很难让人快速理解"这套系统到底比普通 Chat 多了什么"。Ruflo 的做法是把这层能力直接搬到浏览器里。[^ruflo-readme-2026]

README 对它的定义很明确：这是一个**多模型 Chat 界面，但内置了 MCP tool calling**。用户一边和 Claude、Gemini、OpenAI、Qwen 等模型对话，一边让系统在同一轮对话中调用 Ruflo 的 orchestration、memory、swarm coordination、code review、GitHub ops 等工具。[^ruflo-readme-2026]

这里真正值得记的不是"又一个聊天 UI"，而是两个系统设计点：

1. **工具层和界面层解耦**：同一套 MCP tools 既能被 CLI 调，也能被 Web Chat 调，说明 Ruflo 的核心资产在后面的 orchestration layer，而不是某个前端。[^ruflo-readme-2026][^ruflo-mcp-2026]
2. **把"可试用性"产品化**：README 直接把 `flo.ruv.io` 定位成 hosted demo，强调无安装即可体验。这意味着它在把本来偏开发者基础设施的东西，包装成可直接感知的终端产品。[^ruflo-readme-2026]

如果用一句话概括这个用户故事：**用户不是先安装一个 agent framework，再去理解它；而是先在浏览器里看到并行 tool use、共享 memory 和 swarm coordination 的效果，再回头接受背后的控制平面。**

## 主要用户故事 2：goal.ruv.io 把"目标规划"从隐式提示流程抬成显式规划系统

`goal.ruv.io` 更值得单独写，因为它表达的不是"聊天时顺便调工具"，而是另一种完全不同的交互范式：用户先给一个高层目标，系统再把目标拆成可执行计划。README 给的例子很直观：输入类似"把认证重构做完，补测试并发 PR"这样的自然语言目标，Ruflo 会提取成功条件、约束和隐含前置条件，然后做 GOAP + A* 状态空间搜索，生成一条可执行路径。[^ruflo-readme-2026]

这条用户故事的重要性在于，它把 Agent 系统里通常被藏在 prompt / planner chain 里的东西显式化了：

- **目标**：不是"下一步做什么"，而是"最终要达到什么状态"
- **计划**：不是自由生成文本，而是带 preconditions / effects 的 GOAP action graph
- **求解**：不是单轮推理，而是 A* 在状态空间里找一条可行路径
- **执行**：计划不是停留在图上，而是继续派发给 live agents
- **观测**：`goal.ruv.io/agents` 把 agent 的角色、当前步骤、memory namespace、token budget、status 暴露成 dashboard[^ruflo-readme-2026]

这比"通过 Claude Code 调度多个 agent"更值得写进知识库，因为它代表了一种更明确的产品判断：**把 planner 独立出来，变成用户可直接操纵、可直接观察的前台系统**。

## 核心资源 / 概念

真正支撑上述三个入口的，还是同一组核心对象。

### Swarm

`swarm` 是 Ruflo 的协作运行单元：一组 agent、一个目标、一个拓扑，以及持续更新的执行状态。**一个项目对应一个 swarm**，一个 swarm 内可以包含多个任务。文件组织如下：[^ruflo-swarm-2026]

```
.swarm/
├── state.json          # swarm 级别元数据
├── tasks/
│   ├── task-001.json   # 任务状态
│   ├── task-002.json
│   └── task-003.json
├── agents/
│   ├── agent-001.json
│   └── agent-002.json
└── coordination/
    ├── coord-001.json
    └── coord-002.json
```

**state.json 示例**：
```json
{
  "id": "swarm-xxx",
  "topology": "hierarchical-mesh",
  "maxAgents": 15,
  "strategy": "development",
  "objective": "Build REST API",
  "status": "running",
  "startedAt": "2026-05-06T10:00:00Z",
  "tokensUsed": 12345,
  "coordination": {
    "consensusRounds": 10,
    "messagesSent": 50,
    "conflictsResolved": 2
  }
}
```

**通信拓扑**（topology）决定 agent 间如何协调和消息传递。Ruflo 支持 6 种拓扑，其中 `hierarchical-mesh` 是 V3 的默认推荐配置（15-agent queen + peer communication）。其他包括 `hierarchical`（Queen-led 层级）、`mesh`（全连接点对点）、`ring`（环形）、`star`（星形）和 `hybrid`（混合）。[^ruflo-swarm-2026]

**进度计算**：进度百分比不是直接存储在 `state.json`，而是通过扫描 `.swarm/tasks/*.json` 动态计算：`progress = (completedTasks / totalTasks) * 100`。Swarm 状态（running/completed/ready/idle）也基于任务状态和 agent 活跃度实时判断。[^ruflo-swarm-2026]

### Task

`task` 是 swarm 内部真正被分配和追踪的工作单元，带类型、优先级、依赖、负责人和运行状态。Ruflo 的 CLI 把它显式暴露成 `create / assign / retry / cancel` 这一类操作面。[^ruflo-task-2026]

**task-*.json 示例**：
```json
{
  "id": "task-001",
  "type": "implementation",
  "description": "Implement user authentication",
  "priority": "high",
  "status": "in_progress",
  "progress": 60,
  "assignedTo": ["coder-001"],
  "parentId": "task-auth",
  "dependencies": ["task-design"],
  "dependents": ["task-004"],
  "tags": ["auth", "security"],
  "createdAt": "2026-05-06T10:00:00Z",
  "startedAt": "2026-05-06T10:05:00Z",
  "completedAt": null,
  "result": null,
  "error": null,
  "logs": [
    {
      "timestamp": "2026-05-06T10:05:00Z",
      "level": "info",
      "message": "Task started"
    }
  ],
  "metrics": {
    "executionTime": 120000,
    "retries": 0,
    "tokensUsed": 5000
  }
}
```

**关键字段**：
- `type`：任务类型（implementation/bug-fix/refactoring/testing/documentation/research/review/optimization/security/custom）
- `priority`：优先级（critical/high/normal/low）
- `parentId`：父任务 ID（任务分解层级）
- `dependencies`：前置任务 ID 列表（执行约束）
- `assignedTo`：分配的 agent ID 数组

### Agent

`agent` 在这里不是单纯 prompt 模板，而是被 orchestration layer 管理的角色化 worker：可以 spawn、列出、控制、分配任务，并被纳入 swarm 状态统计。[^ruflo-agent-2026][^ruflo-swarm-2026]

**agent-*.json 示例**：
```json
{
  "id": "coder-001",
  "agentType": "coder",
  "status": "active",
  "createdAt": "2026-05-06T10:00:00Z",
  "lastActivityAt": "2026-05-06T10:30:00Z",
  "config": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-6",
    "task": "Implement user auth",
    "timeout": 300,
    "autoTools": true
  },
  "metrics": {
    "tasksCompleted": 5,
    "tasksInProgress": 2,
    "tasksFailed": 0,
    "averageExecutionTime": 120000,
    "uptime": 3600000
  }
}
```

**关键字段**：
- `agentType`：agent 类型（coder/researcher/tester/reviewer/architect/coordinator/analyst/optimizer/security-architect/security-auditor/memory-specialist/swarm-specialist/performance-engineer/core-architect/test-architect）
- `status`：状态（active/idle/terminated）
- `config`：配置（provider、model、timeout、autoTools）
- `metrics`：执行指标（完成任务数、平均执行时间、运行时间）

### Memory

`memory` 是 Ruflo 最像基础设施层的一部分：它支持 backend 选择、namespace、TTL、tags、vector embedding、semantic search、import/export、cleanup / optimize。它决定了 agent 协作是不是"每次从零开始"。[^ruflo-memory-2026]

### Session

`session` 则更像工作快照：保存某次协作过程中的 agent 数、task 数、memory size 和整体状态，方便恢复、归档和删除。[^ruflo-session-2026][^ruflo-swarm-2026]

## 参考资料

[^ruflo-readme-2026]: RuvNet. *Ruflo README*. GitHub. https://github.com/ruvnet/ruflo
[^ruflo-init-2026]: RuvNet. *v3/@claude-flow/cli/src/commands/init.ts*. GitHub. https://raw.githubusercontent.com/ruvnet/ruflo/main/v3/@claude-flow/cli/src/commands/init.ts
[^ruflo-swarm-2026]: RuvNet. *v3/@claude-flow/cli/src/commands/swarm.ts*. GitHub. https://raw.githubusercontent.com/ruvnet/ruflo/main/v3/@claude-flow/cli/src/commands/swarm.ts
[^ruflo-task-2026]: RuvNet. *v3/@claude-flow/cli/src/commands/task.ts*. GitHub. https://raw.githubusercontent.com/ruvnet/ruflo/main/v3/@claude-flow/cli/src/commands/task.ts
[^ruflo-agent-2026]: RuvNet. *v3/@claude-flow/cli/src/commands/agent.ts*. GitHub. https://raw.githubusercontent.com/ruvnet/ruflo/main/v3/@claude-flow/cli/src/commands/agent.ts
[^ruflo-session-2026]: RuvNet. *v3/@claude-flow/cli/src/commands/session.ts*. GitHub. https://raw.githubusercontent.com/ruvnet/ruflo/main/v3/@claude-flow/cli/src/commands/session.ts
[^ruflo-memory-2026]: RuvNet. *v3/@claude-flow/cli/src/commands/memory.ts*. GitHub. https://raw.githubusercontent.com/ruvnet/ruflo/main/v3/@claude-flow/cli/src/commands/memory.ts
[^ruflo-mcp-2026]: RuvNet. *v3/@claude-flow/cli/src/commands/mcp.ts*. GitHub. https://raw.githubusercontent.com/ruvnet/ruflo/main/v3/@claude-flow/cli/src/commands/mcp.ts
