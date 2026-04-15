---
title: OpenClaw
description: Peter Steinberger 开发的自托管 AI 网关，核心差异化是 Heartbeat 主动汇报、多 Agent 隔离和 ClawHub 生态。
created: 2026-04-15
updated: 2026-04-15
tags: [product, openclaw, personal-agent, open-source]
review: 2026-04-15
---

# OpenClaw

> 自托管 AI 网关，连接聊天渠道和 AI Agent。核心差异化是 Heartbeat 主动汇报、多 Agent 隔离和 ClawHub 生态。

| 属性 | 值 |
|------|-----|
| 开发者 | Peter Steinberger + 社区 |
| 语言 | TypeScript / Node.js |
| 开源 | 是（MIT） |
| GitHub | [openclaw/openclaw](https://github.com/openclaw/openclaw)（358K stars） |
| 官网 | [openclaw.ai](https://openclaw.ai) |

---

## 技术亮点

### 1. Heartbeat 主动汇报

大多数 Agent 是"被动应答"模式——用户问，Agent 答。Heartbeat 打破了这一范式：Agent **主动**在后台运行，定期检查收件箱、日历、提醒事项，有需要时主动推送给你。

**配置示例**：

```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "30m",
        "target": "last"
      }
    }
  }
}
```

**工作方式**：
- 每 30 分钟运行一次完整 Agent Turn
- 读取工作目录下的 `HEARTBEAT.md` 检查清单
- 没事回复 `HEARTBEAT_OK`，有情况才推送
- 可设置活跃时间段（如 9:00-22:00）

**和 Cron 的区别**：

| | Heartbeat | Cron |
|--|-----------|------|
| 时机 | 近似（每 30 分钟） | 精确（cron 表达式） |
| 上下文 | 完整主会话历史 | 独立或共享 |
| 任务记录 | 无 | 有 |
| 推送方式 | 内联到主会话 | 渠道、webhook 或静默 |

### 2. 多 Agent 隔离路由

OpenClaw 支持同时运行多个完全隔离的 Agent，每个 Agent 有自己的：

- **Workspace**：文件、`AGENTS.md`、`SOUL.md`、`USER.md`
- **Auth profiles**：独立的认证配置
- **Session store**：聊天历史和路由状态
- **Tools**：独立的工具允许/拒绝列表

**路由规则**：

```json
{
  "agents": {
    "list": [
      { "id": "main", "workspace": "~/.openclaw/workspace-main" },
      { "id": "coding", "workspace": "~/.openclaw/workspace-coding" }
    ]
  },
  "bindings": [
    { "agentId": "main", "match": { "channel": "whatsapp" } },
    { "agentId": "coding", "match": { "channel": "telegram" } }
  ]
}
```

绑定匹配是**确定性**的，遵循"最具体优先"原则：peer > guildId > channel > fallback。

### 3. Skills 系统与 ClawHub

**层级结构**：

| 位置 | 作用域 |
|------|--------|
| `<workspace>/skills` | 单个 Agent |
| `~/.openclaw/skills` | 所有 Agent 共享 |
| bundled skills | 内置 |

同名 Skill 优先级：workspace > 个人 > managed > bundled。

**ClawHub** 是社区驱动的 Skill 市场，安装命令：

```bash
openclaw skills install <skill-slug>
openclaw skills update --all
```

**Skill 格式**（AgentSkills 兼容）：

```markdown
---
name: image-lab
description: Generate or edit images via provider workflow
metadata:
  {
    "openclaw": {
      "requires": { "bins": ["uv"], "env": ["API_KEY"] },
      "primaryEnv": "API_KEY"
    }
  }
---
```

**加载时过滤**：Skill 可根据平台（darwin/linux/win32）、依赖二进制、 环境变量、配置文件等条件自动过滤，不满足时不加载。

---

## 架构

```
聊天渠道 → Gateway（控制平面）→ Pi Agent（RPC 模式）
                    ↓
            CLI / WebChat / macOS app / iOS&Android nodes
```

- **Gateway**：单一控制平面，管理 sessions、路由、渠道连接
- **Pi Agent**：RPC 模式运行，tool streaming 和 block streaming
- **Session 模型**：主会话直接聊天，群组隔离，激活模式和队列模式


