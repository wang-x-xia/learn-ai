---
title: Honcho
description: plastic-labs 开源的记忆库，通过辩证用户建模让 Agent 构建动态、可推理的用户心智模型，而非静态偏好列表。
created: 2026-04-15
updated: 2026-04-15
tags: [memory, personalization, plastic-labs, open-source]
review: 2026-04-15
---

# Honcho

> plastic-labs 出品的开源记忆库，核心区分点是**辩证用户建模**——通过多轮交互让 Agent 构建用户的动态心智模型，而非维护一份静态偏好列表。

| 属性 | 值 |
|------|-----|
| 厂商 | plastic-labs |
| 语言 | Python / TypeScript |
| 开源 | 是（AGPL-3.0） |
| GitHub | [plastic-labs/honcho](https://github.com/plastic-labs/honcho)（2.4K stars） |
| 官网 | [honcho.dev](https://honcho.dev) |
| 托管服务 | [app.honcho.dev](https://app.honcho.dev)（$100 免费额度） |

---

## 核心问题：现有方案不够用

传统方案有两种缺陷：

**偏好列表**：静态 key-value（"用户喜欢简洁回复"），Agent 只能检索已有条目，无法推断新场景。

**普通 RAG**：检索"用户说了什么"，但无法推理出"用户是什么样的人"。例如用户问"有什么适合老人的家电"，RAG 只能召回"用户说要买洗碗机"，而 Honcho 能召回"用户购买家电时优先考虑人体工学（免弯腰），决策以收礼者需求为中心"。

Honcho 的解法是**辩证用户建模**：通过多轮交互逐步构建和修正"用户心智模型"，用 LLM 做形式逻辑推理，从对话中提取结论而非只做语义检索。

| | 偏好列表 | 普通 RAG | Honcho |
|--|---------|---------|--------|
| 数据结构 | 静态 key-value | 向量 chunks | 推理结论文本 |
| 泛化能力 | 无 | 有限 | 可推断新场景 |
| 更新方式 | 显式告知 | 被动检索 | 对话隐式发现 |
| 本质 | 记录"是什么" | 检索说过的话 | 建模"为什么" |

---

## 架构设计

### Peer 范式

Honcho 的核心抽象是 **Peer**——用户和 Agent 在系统中都是 Peer，不做区分。这一统一模型支持：

- 多参与者会话（人类用户 + 多个 Agent）
- 可配置的观察设置（谁观察谁）
- 灵活的跨会话身份管理

### 观察机制

每个 Peer 存储两类信息：

```
Peer: Alice
├── representation        # Honcho 对 Alice 的理解（observe_me）
└── observed_representations
    ├── representation_of_Bob   # Alice 观察 Bob 得出的结论
    └── representation_of_Carol
```

**两种观察模式**：

| 配置 | 默认值 | 说明 |
|-----|-------|------|
| `observe_me` | true | Honcho 系统观察该 Peer，形成对它的 Representation |
| `observe_others` | false（会话级别） | 该 Peer 观察其他 Peer，形成对他们的 Representation |

当 `observe_others` 开启时，Peer A 对 Peer B 的理解**只基于 A 观察到的话语**，不受 B 没参与的会话影响。这解决了"全知 Agent"问题——如果 Bob 和 Alice 在 Session 1 聊过私事，Charlie 没有参与 Session 1，那么 Charlie 对 Alice 的理解不会包含那些私事。

### 推理层（Reasoning）

消息进入后，Honcho 异步执行推理任务：

1. **representation**：更新 Peer 的表示（理解用户是谁）
2. **summary**：生成 Session 摘要
3. **deriver**：后台 worker，生成结论和洞察

结果存储在 reserved Collections 中，供后续检索使用。

---

## 单用户场景

对话示例：

```
1. AI: "有什么我可以帮你的？"
2. 用户: "我想给我妈买台洗碗机，预算 5000 左右"
3. AI: "这个预算推荐海尔或美的，有兴趣吗？"
4. 用户: "我妈腰不太好，最好操作不用弯腰的"
5. AI: "理解，那要看免安装或台式的，对腰更友好"
```

存储后形成的结论：

| observer | observed | content |
|----------|----------|---------|
| Honcho (系统) | 用户 | "用户购买家电时优先考虑人体工学（免弯腰），决策以收礼者需求为中心" |

查询时返回的 `PeerContext`：

```python
class PeerContext(BaseModel):
    peer_id: str
    target_id: str
    representation: str | None
    peer_card: list[str] | None
```

---

## 多 Peer 场景

同一个 Workspace 中，多个 Peer 可以互相观察，形成各自独立的认知。

**场景：项目讨论**

参与者：Alice（用户）、DevAgent（开发 Agent）、PMAgent（产品 Agent）

```
Alice: "我要做一个外卖比价 App，目标用户是大学生"
DevAgent: "推荐用 Flutter，跨平台开发快"
PMAgent: "大学生可能更在意省流量，要考虑离线功能"
Alice: "对，而且大学生晚上点夜宵多，可能要做个定时下单功能"
```

**各 Peer 的结论**

```
Peer: Alice
├── representation              # Honcho 对 Alice 的理解
└── observed_representations
    ├── representation_of_DevAgent   # Alice 听到 DevAgent 说"推荐 Flutter"
    └── representation_of_PMAgent

Peer: DevAgent
├── representation              # Honcho 对 DevAgent 的理解
└── observed_representations
    └── representation_of_Alice     # DevAgent 听到 Alice 说"面向大学生"
```

各 Peer 存储的结论：

实际数据库里存的是一条条 Conclusion 记录：

| observer | observed | content |
|----------|----------|---------|
| Honcho (系统) | Alice | "用户提到面向大学生、关注省流量" |
| DevAgent | Alice | "Alice产品思维偏实用性，关注成本敏感型用户" |
| Alice | DevAgent | "DevAgent优先考虑开发效率而非极致性能" |

查询 Alice 对 DevAgent 的理解时，返回的 `PeerContext.representation` 是这些记录的文本拼接，类似：

> "DevAgent优先考虑开发效率而非极致性能"

**为什么这有用**

如果不区分观察视角，所有 Agent 都是"全知的"——Agent A 知道 Agent B 和用户的私密对话，用户也记得 Agent A 和 Agent B 之间没带上他的对话。这在多 Agent 协作场景会造成信息泄露和角色混乱。`observe_others` 机制让每个 Peer 只记得自己观察到的东西。

---

## 与 Hermes Agent 的关系

[Hermes Agent](../personal-agents/hermes-agent.md) 使用 Honcho 做用户建模，两者相互独立：

- **Honcho**：负责用户记忆和心智模型构建
- **Atropos RL**（Hermes 内置）：负责 RL 训练轨迹生成


