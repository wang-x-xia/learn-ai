---
title: Learn AI
description: 个人 AI 前沿知识库。系统梳理 AI 核心技术，每日自动追踪社区与行业动态。
---

# Learn AI

个人 AI 前沿知识库。系统梳理 AI 核心技术，每日自动追踪社区与行业动态。

## 网站主题

本知识库聚焦 **AI 技术方案革新与工程亮点**，记录值得长期关注的技术突破，而非功能清单或通用知识。

### 知识体系拓扑

```mermaid
graph TD
    A[Learn AI 知识库] --> B[基础理论<br/>what]
    A --> C[应用技术<br/>how]
    A --> D[研究、模型与产品<br/>reference]

    C --> C1[Agent 技术栈]
    C --> C2[通用技术]
    C --> C3[基础设施]

    D --> D1[前沿研究]
    D --> D2[模型档案]
    D --> D3[AI 个人软件]
    D --> D4[开源库]
    D --> D5[Agent Workflow]

    click B href "foundations/"
    click C1 href "agent/"
    click C2 href "applied/"
    click C3 href "infrastructure/"
    click D1 href "research/"
    click D2 href "model/"
    click D3 href "ai-personal-software/"
    click D4 href "libraries/"
    click D5 href "agent-workflow/"

    style A fill:#FF5C77,stroke:#E84862,stroke-width:2px,color:#fff
    style B fill:#FF8A9E,stroke:#E84862,stroke-width:1px
    style C fill:#FF8A9E,stroke:#E84862,stroke-width:1px
    style D fill:#FF8A9E,stroke:#E84862,stroke-width:1px
```

---

## 最近更新

<div class="grid cards" markdown>

{% for entry in changelog.entries[:5] %}
- **{{ entry.date }} — {% if entry.link %}[{{ entry.title }}]({{ entry.link }}){% else %}{{ entry.title }}{% endif %}**

    {{ entry.description }}

{% endfor %}

</div>