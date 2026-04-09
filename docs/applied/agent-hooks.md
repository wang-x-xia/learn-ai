---
title: Agent Hooks：生命周期钩子机制
description: Agent Hook 是在 Agent 执行循环的关键节点插入用户自定义逻辑的机制——验证、拦截、注入、观测。本文梳理主流产品和框架中的 Hook 设计及实战模式。
created: 2026-04-09
updated: 2026-04-09
tags: [agents, hooks, lifecycle, automation, safety]
review:
---

# Agent Hooks：生命周期钩子机制

> Agent Hook 是在 Agent 执行循环的关键节点插入用户自定义逻辑的机制。它不驱动 Agent 行为，而是**验证、拦截、注入、观测** Agent 的每一步动作。

---

## 1. 为什么需要 Hook

Agent 的核心循环是 Think → Tool Use → Observe → Think（ReAct 模式）。这个循环中有大量"接缝"需要外部干预：

| 需求 | 没有 Hook 时 | 有 Hook 时 |
|------|-------------|-----------|
| 阻止危险命令 | 只能靠权限提示逐个确认 | PreToolUse hook 自动拦截 `rm -rf` |
| 代码编辑后自动 lint | 手动提醒 Agent 跑 linter | PostToolUse hook 自动触发 |
| 测试不过不许结束 | Agent 可能跳过测试就声明完成 | Stop hook 阻塞直到测试通过 |
| 记录所有操作审计 | 无内置审计机制 | 每个事件点都可注入日志 |
| 环境变量注入 | 手动配置 | SessionStart hook 自动加载 |

核心价值：**将"工程约束"从自然语言提示（不可靠）转为代码执行（确定性）**。

---

## 2. Hook 的通用模型

不同产品/框架的命名各异，但 Hook 的本质结构是统一的：

```
事件触发 (Event)
  → 匹配过滤 (Matcher)
  → 处理器执行 (Handler)
  → 返回决策 (Decision)
  → Agent 据此行动或被阻塞
```

### 2.1 Handler 类型

| 类型 | 机制 | 确定性 | 适用场景 |
|------|------|--------|----------|
| **Shell 命令** | 执行脚本，通过 exit code + stdout JSON 返回决策 | 高 | 规则明确的验证（拦截 SQL 写操作、检查文件路径） |
| **HTTP 端点** | POST 请求发送到外部服务，响应体返回决策 | 高 | 集成外部系统（审计服务、CI 系统、企业策略引擎） |
| **LLM Prompt** | 将事件上下文发送给 LLM 做单轮判断 | 中 | 需要语义理解的验证（代码质量评审、安全风险评估） |
| **Agent** | 生成一个可使用工具的 subagent 来验证条件 | 低 | 复杂验证（需要读文件、搜索代码库才能判断） |

从 Shell 到 Agent，**确定性递减、能力递增**。实践中应优先使用确定性高的类型。

### 2.2 Decision 控制

Hook 处理器的返回值决定 Agent 的下一步行为：

| 决策 | 效果 |
|------|------|
| **allow** / exit 0 | 放行，Agent 继续 |
| **block** / exit 2 | 阻止当前操作，reason 反馈给 Agent |
| **deny** | 拒绝权限请求 |
| **approve** | 自动批准权限请求 |
| **modify** | 修改 Agent 的输入/输出后继续 |

---

## 3. Claude Code 的 Hook 体系（最完整的参考实现）

Claude Code 拥有目前最完善的 Agent Hook 系统，覆盖 25+ 生命周期事件[^anthropic-hooks-2026]。

### 3.1 事件全景

按 Agent 执行循环的阶段分类：

#### 会话管理

| 事件 | 触发时机 | 典型用途 |
|------|----------|----------|
| `SessionStart` | 会话启动或恢复 | 注入环境变量、初始化工具、加载配置 |
| `SessionEnd` | 会话终止 | 清理资源、上报统计 |
| `InstructionsLoaded` | CLAUDE.md 或规则文件被加载 | 动态修改指令、条件注入规则 |
| `ConfigChange` | 配置文件变更 | 热重载配置 |

#### Agentic Loop 核心

| 事件 | 触发时机 | 典型用途 |
|------|----------|----------|
| `UserPromptSubmit` | 用户提交 prompt，Agent 处理前 | 输入验证、prompt 改写、敏感词过滤 |
| `PreToolUse` | 工具调用执行前 | **最高频使用**——拦截危险命令、验证参数、条件放行 |
| `PermissionRequest` | 权限弹窗出现时 | 自动批准/拒绝、记录权限请求 |
| `PermissionDenied` | Auto mode 拒绝了工具调用 | 允许 Agent 重试被拒的操作 |
| `PostToolUse` | 工具调用成功后 | 自动 lint、运行测试、格式化、日志记录 |
| `PostToolUseFailure` | 工具调用失败后 | 错误追踪、自动重试策略 |
| `Stop` | Agent 完成回复 | **质量门禁**——阻塞直到测试通过/代码审查完成 |
| `StopFailure` | 因 API 错误中断 | 错误报告、告警 |

#### Subagent 生命周期

| 事件 | 触发时机 | 典型用途 |
|------|----------|----------|
| `SubagentStart` | subagent 生成时 | 环境准备（数据库连接、服务启动） |
| `SubagentStop` | subagent 完成时 | 资源清理、结果验证 |

#### Agent Teams

| 事件 | 触发时机 | 典型用途 |
|------|----------|----------|
| `TaskCreated` | 任务被创建 | 验证任务范围、记录任务分配 |
| `TaskCompleted` | 任务被标记完成 | 验证完成标准、触发下游流程 |
| `TeammateIdle` | 队友即将空闲 | 分配新任务、触发汇报 |

#### 上下文管理

| 事件 | 触发时机 | 典型用途 |
|------|----------|----------|
| `PreCompact` | 上下文压缩前 | 保存关键信息、记录压缩前状态 |
| `PostCompact` | 上下文压缩后 | 注入被压缩掉的关键上下文 |
| `CwdChanged` | 工作目录变更 | 环境管理（如 direnv 集成） |
| `FileChanged` | 被监视的文件变更 | 自动重载配置、触发构建 |

#### 其他

| 事件 | 触发时机 | 典型用途 |
|------|----------|----------|
| `Notification` | 通知发送时 | 自定义通知渠道（Slack、邮件） |
| `WorktreeCreate` / `WorktreeRemove` | git worktree 操作 | 自定义 worktree 管理逻辑 |
| `Elicitation` / `ElicitationResult` | MCP 服务器请求用户输入 | 自动回复、输入验证 |

### 3.2 配置结构

三层嵌套：事件 → 匹配器组 → 处理器[^anthropic-hooks-2026]：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm *)",
            "command": ".claude/hooks/block-rm.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

- `matcher`：正则匹配事件元数据（工具名、Agent 类型等），缺省匹配所有
- `if`：更精细的条件过滤，使用权限规则语法（如 `Bash(git *)` 只匹配 git 命令）
- 所有匹配的 handler 并行执行，相同 handler 自动去重

### 3.3 配置作用域

| 位置 | 作用域 | 可共享 |
|------|--------|--------|
| `~/.claude/settings.json` | 用户级，所有项目 | 否 |
| `.claude/settings.json` | 项目级 | 是，可提交到 Git |
| `.claude/settings.local.json` | 项目级，本地 | 否，gitignored |
| Managed policy | 组织级 | 是，管理员控制 |
| Plugin `hooks/hooks.json` | 插件启用范围 | 是，随插件分发 |
| Subagent/Skill frontmatter | 组件激活期间 | 是，定义在组件文件中 |

企业管理员可通过 `allowManagedHooksOnly` 禁止用户和项目级 hook，只允许组织策略 hook。

### 3.4 异步 Hook

标记 `async: true` 的 hook 在后台执行，不阻塞 Agent 循环：

```json
{
  "hooks": {
    "FileChanged": [
      {
        "matcher": ".envrc",
        "hooks": [{
          "type": "command",
          "command": "direnv allow",
          "async": true
        }]
      }
    ]
  }
}
```

适用于不需要决策反馈的场景：日志记录、通知发送、后台测试。

---

## 4. 其他产品的 Hook 机制

### 4.1 Devin

Cognition 的 Devin 也实现了生命周期钩子，设计更精简：

- 支持 `user-prompt-submit-hook` 等事件点
- Hook 是 shell 命令，在事件触发时执行
- Hook 的反馈被视为用户输入，Agent 据此调整行为
- 如果 hook 阻塞了操作，Agent 会尝试调整行为或请求用户检查 hook 配置

与 Claude Code 的关键差异：Devin 的 hook 反馈直接注入对话流（作为用户消息），而非结构化的 JSON 决策。

### 4.2 OpenAI Codex

Codex 的 hook 机制（基于公开信息推断）：

- 通过 `AGENTS.md` 配置约束（声明式，非事件驱动）
- Sandbox 环境提供系统级安全边界（替代 PreToolUse 验证的部分需求）
- Harness Engineering 思路中，约束和反馈更多通过环境结构化（文档、测试、质量分数）实现，而非运行时 hook

### 4.3 LangGraph Callbacks

LangGraph 基于 LangChain 的 callback 体系，面向开发者的 Python API[^langchain-docs]：

```python
from langchain_core.callbacks import BaseCallbackHandler

class MyHookHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        # 等价于 PreToolUse
        if "rm -rf" in input_str:
            raise ValueError("Dangerous command blocked")

    def on_tool_end(self, output, **kwargs):
        # 等价于 PostToolUse
        log_tool_output(output)

    def on_chain_start(self, serialized, inputs, **kwargs):
        # Agent 推理开始
        pass

    def on_chain_end(self, outputs, **kwargs):
        # Agent 推理结束
        pass
```

| LangGraph Callback | Claude Code 等价事件 |
|--------------------|---------------------|
| `on_tool_start` | `PreToolUse` |
| `on_tool_end` | `PostToolUse` |
| `on_tool_error` | `PostToolUseFailure` |
| `on_chain_start` | 无直接等价（Agent 推理级别） |
| `on_chain_end` | `Stop` |
| `on_llm_start` / `on_llm_end` | 无等价（LLM 调用级别） |

关键差异：
- LangGraph callback 是 **Python 代码内嵌**，需要编程；Claude Code hook 是**外部脚本/HTTP**，声明式配置
- LangGraph callback 可以抛异常中断执行；Claude Code hook 通过 JSON 决策控制
- LangGraph 有 `on_llm_start/end`（LLM 调用级别），这在产品级 Agent 中通常不暴露

### 4.4 AutoGen 事件系统

AutoGen 通过消息和事件驱动 Agent 交互：

```python
# AutoGen 的 hook 通过注册消息拦截器实现
@agent.register_hook(hookable_method="process_message_before_send")
def my_hook(sender, message, recipient, silent):
    # 拦截消息，可修改或阻止
    if "sensitive" in message:
        return None  # 阻止发送
    return message
```

- 以消息拦截为核心（而非工具调用拦截）
- `process_message_before_send`：消息发送前拦截
- `process_all_messages_before_reply`：回复前处理所有消息
- 更适合多 Agent 对话场景中的消息级控制

### 4.5 CrewAI Callbacks

CrewAI 的回调机制面向任务执行流程：

```python
from crewai import Task

def my_callback(output):
    # 任务完成后的回调
    print(f"Task completed: {output.raw}")

task = Task(
    description="Research the topic",
    agent=researcher,
    callback=my_callback  # 任务级回调
)
```

- `step_callback`：每一步推理后触发
- `task_callback`：任务完成后触发
- 粒度较粗，主要用于监控和日志，不擅长拦截

---

## 5. 实战模式

### 5.1 安全门禁（PreToolUse）

拦截危险的 shell 命令：

```bash
#!/bin/bash
# .claude/hooks/block-destructive.sh
COMMAND=$(jq -r '.tool_input.command' < /dev/stdin)

# 拦截破坏性操作
if echo "$COMMAND" | grep -qE '\b(rm -rf|DROP TABLE|FORMAT|mkfs)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked by safety hook"
    }
  }'
else
  exit 0
fi
```

### 5.2 质量门禁（Stop）

Agent 结束前强制通过测试：

```bash
#!/bin/bash
# .claude/hooks/require-tests.sh
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# 防止无限循环——已被阻塞过一次就放行
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

if ! npm test --silent > /dev/null 2>&1; then
  jq -n '{
    decision: "block",
    reason: "Tests are failing. Fix them before finishing."
  }'
  exit 0
fi

exit 0
```

注意 `stop_hook_active` 防循环机制：如果 Stop hook 已经阻塞过一次，第二次放行，避免 Agent 陷入死循环。

### 5.3 自动格式化（PostToolUse）

每次文件编辑后自动运行 formatter：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "if": "Edit(*.ts)|Write(*.ts)",
          "command": "npx prettier --write \"$TOOL_INPUT_FILE_PATH\""
        }]
      }
    ]
  }
}
```

### 5.4 环境自动配置（SessionStart）

会话启动时自动加载环境变量：

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "cat .env | jq -R 'split(\"=\") | {(.[0]): .[1:] | join(\"=\")}' | jq -s 'add | {env: .}'"
      }]
    }]
  }
}
```

SessionStart hook 可以通过返回 `{ "env": { "KEY": "VALUE" } }` 来持久化环境变量到整个会话。

### 5.5 只读数据库（PreToolUse + Subagent Hook）

在 subagent 配置中用 hook 实现细粒度权限：

```yaml
# .claude/agents/db-reader.md
---
name: db-reader
description: Execute read-only database queries
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---
```

验证脚本解析 Bash 命令，用正则拦截 `INSERT/UPDATE/DELETE/DROP` 等写操作（exit 2 阻止）。这比单纯限制 `tools` 更精细——允许 Bash 但只允许 SELECT。

### 5.6 LLM 辅助审查（Prompt Hook）

用 LLM 做代码变更的语义级审查：

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Review the following changes for security issues. The changes are: $ARGUMENTS. Respond with {\"decision\": \"block\", \"reason\": \"...\"} if there are critical security issues, or {\"decision\": \"allow\"} if the changes are safe.",
        "model": "haiku"
      }]
    }]
  }
}
```

Prompt hook 用于需要语义理解但不需要工具访问的判断。用 Haiku 等小模型控制成本。

---

## 6. 各产品 Hook 能力对比

| 能力 | Claude Code | Devin | LangGraph | AutoGen | CrewAI |
|------|-------------|-------|-----------|---------|--------|
| **事件数量** | 25+ | 少量核心事件 | ~10 (callback types) | ~5 (message hooks) | ~3 (callbacks) |
| **Handler 类型** | Shell / HTTP / Prompt / Agent | Shell | Python 代码 | Python 代码 | Python 代码 |
| **拦截能力** | 完整（block/deny/approve/modify） | block | 抛异常中断 | 返回 None 阻止 | 无拦截 |
| **异步执行** | 原生支持 | 未公开 | 通过 async Python | 异步消息 | 无 |
| **配置方式** | JSON 声明式 | 配置文件 | Python 命令式 | Python 命令式 | Python 命令式 |
| **MCP 工具匹配** | 支持 `mcp__*` 模式 | N/A | N/A | N/A | N/A |
| **组织级管控** | Managed policy + 企业锁定 | 未公开 | 无（开发者自建） | 无 | 无 |
| **Subagent 集成** | SubagentStart/Stop 事件 | 有 | 通过 graph 结构 | 通过消息 | 通过 callback |
| **上下文压缩** | PreCompact/PostCompact | 无 | 无 | 无 | 无 |

### 设计哲学差异

- **Claude Code / Devin**：面向终端用户，声明式配置，强调安全和可审计性，hook 是产品功能
- **LangGraph / AutoGen / CrewAI**：面向开发者，命令式编程，强调灵活性和可编程性，hook 是 SDK 能力

Claude Code 的 hook 系统之所以最完善，是因为它解决了一个产品级问题：**如何让非开发者也能给 Agent 加约束？**答案是声明式 JSON + 外部脚本，而非嵌入式代码。

---

## 7. Hook 设计的经验法则

### 应该用 Hook 的场景

- 安全约束（拦截危险操作、敏感数据过滤）
- 质量门禁（测试通过、lint 通过、代码审查）
- 自动化流程（格式化、日志、通知）
- 环境管理（变量注入、工具初始化、资源清理）

### 不应该用 Hook 的场景

- 替代 Agent 的核心推理（Hook 是约束，不是驱动力）
- 复杂的业务逻辑编排（用 Agent 框架的编排能力）
- 需要多轮交互的验证（Hook 是单轮响应）

### 关键原则

1. **优先确定性**：能用 Shell 脚本解决的，不要用 LLM Prompt Hook
2. **防死循环**：Stop hook 必须有递归退出机制（如 `stop_hook_active` 标记）
3. **超时控制**：所有 Hook 设置合理的 timeout，避免阻塞 Agent
4. **最小权限**：Hook 脚本只访问它需要的信息，不暴露完整会话上下文
5. **渐进自动化**：先手动验证 Hook 行为，再部署到团队/组织级别[^anthropic-hooks-guide-2026]

---

## 参考资料

[^anthropic-hooks-2026]: Anthropic. "Hooks reference - Claude Code Docs". 2026. https://docs.anthropic.com/en/docs/claude-code/hooks
[^anthropic-hooks-guide-2026]: Anthropic. "Automate workflows with hooks". 2026. https://docs.anthropic.com/en/docs/claude-code/hooks-guide
[^langchain-docs]: LangChain. "Callbacks". https://python.langchain.com/docs/concepts/callbacks/
