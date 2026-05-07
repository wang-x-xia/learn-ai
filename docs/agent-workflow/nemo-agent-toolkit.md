---
title: NeMo Agent Toolkit
description: NVIDIA 的跨框架 Agent 元工具包——可观测性、安全沙箱、本地推理，解决"Agent 怎么安全运行和优化"的工程问题。
created: 2026-04-10
updated: 2026-05-07
tags: [framework, nvidia, agent, python, observability, security]
review: 2026-05-07
---

# NeMo Agent Toolkit

> NVIDIA 出品，定位不是"又一个 Agent 框架"，而是坐在 LangChain/CrewAI 之上的**元框架**——解决"Agent 怎么安全运行、跨框架优化"的工程问题。

| 属性 | 值 |
|------|-----|
| 厂商 | NVIDIA |
| 语言 | Python |
| 开源 | 是 |
| GitHub | [NVIDIA/NeMo-Agent-Toolkit](https://github.com/NVIDIA/NeMo-Agent-Toolkit) |

## 技术亮点

- **Function-as-a-Service 统一抽象**[^nvidia-agent-toolkit]：将 Agent、工具、子 Agent、整个工作流统一抽象为 `fn(input) → output` 的可调用函数，无论底层是 LangChain、CrewAI 还是原生 Python 都表现为同一接口。这使得跨框架 Agent 系统的 **token 用量、延迟、成本** 可以在统一的 profiling 链路中追踪，工作流通过 YAML 配置组合，替换组件无需改代码

## 执行模型

### YAML 配置驱动的函数编排

NeMo Agent Toolkit 的 workflow 不是图结构，而是**YAML 配置驱动的函数编排系统**[^nemo-workflow]。所有组件（functions、llms、embedders、workflow）都在 YAML 配置文件中声明，通过 `nat run --config_file config.yml --input "..."` 执行。

### 核心概念

#### 统一函数抽象

所有组件都抽象为 `fn(input) → output` 的可调用函数：

```yaml
functions:
  wikipedia_search:
    _type: wiki_search
    max_results: 2
  current_datetime:
    _type: current_datetime

llms:
  nim_llm:
    _type: nim
    model_name: nvidia/nemotron-3-nano-30b-a3b
    temperature: 0.0

workflow:
  _type: react_agent
  tool_names: [wikipedia_search, current_datetime]
  llm_name: nim_llm
```

这种抽象使得：
- 跨框架组件（LangChain Agent、CrewAI Agent、原生 Python 函数）可以无缝组合
- 统一的 profiling 链路可以追踪 token 用量、延迟、成本
- 替换组件只需修改 YAML 配置，无需改代码

#### 控制流模式

NeMo Agent Toolkit 提供多种预定义的控制流组件[^nemo-control-flow]：

- **router_agent**：单次路由架构，Router Agent Node 分析请求并选择分支，Branch Node 执行选中的分支。适合根据请求类型路由到不同 Agent/工具的场景
- **sequential_executor**：线性工具执行管道，每个函数的输出成为下一个函数的输入，支持类型兼容性检查和错误处理
- **parallel_executor**：并行执行，支持独立分支的并发执行和部分失败处理
- **hybrid_control_flow**：混合控制流，组合路由代理和顺序执行器模式

与 LangGraph/MAF 的图-based workflow 不同，NeMo Agent Toolkit 的控制流是**声明式的组件组合**，而非显式的图结构定义。

### Workflow 生命周期

1. **配置**：通过 YAML 文件定义 functions、llms、workflow 等组件
2. **加载**：`nat run --config_file config.yml` 加载配置并实例化组件
3. **执行**：根据 workflow 类型（如 react_agent、router_agent）执行函数调用链
4. **监控**：通过内置的 observability 系统追踪执行过程
5. **优化**：通过 profiler、optimizer 等工具分析瓶颈并优化

### 参数覆盖与热更新

支持通过 `--override` 标志在运行时覆盖配置参数[^nemo-customize]：

```bash
nat run --config_file config.yml --input "..." \
  --override llms.nim_llm.temperature 0.7 \
  --override llms.nim_llm.model_name meta/llama-3.3-70b-instruct
```

这使得无需修改 YAML 文件即可快速实验不同配置。

### 与 LangGraph/MAF 的对比

| 维度 | LangGraph | MAF | NeMo Agent Toolkit |
|------|----------|-----|-------------------|
| 架构模式 | 静态图定义 | 双模式（functional + graph-based） | YAML 配置驱动的函数编排 |
| 核心抽象 | StateGraph + 节点 | Executor + Edge | Function-as-a-Service |
| 定义方式 | Python 代码构建图 | Python 代码或装饰器 | YAML 配置文件 |
| 控制流 | 条件边、Send 机制 | 条件边、switch-case | 预定义组件（router、sequential、parallel） |
| 跨框架 | 仅 LangChain 生态 | 独立框架 | 跨框架（LangChain、CrewAI、原生 Python） |
| 主要目标 | 图-based Agent 编排 | 生产级多 Agent 系统 | 可观测性、安全、跨框架优化 |

## 参考资料

[^nvidia-agent-toolkit]: NVIDIA. *NeMo Agent Toolkit*. https://github.com/NVIDIA/NeMo-Agent-Toolkit
[^nemo-workflow]: NVIDIA. *NeMo Agent Toolkit Workflow Configuration*. https://github.com/NVIDIA/NeMo-Agent-Toolkit
[^nemo-control-flow]: NVIDIA. *NeMo Agent Toolkit Control Flow Examples*. https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/main/examples/control_flow
[^nemo-customize]: NVIDIA. *Customize a Workflow Tutorial*. https://github.com/NVIDIA/NeMo-Agent-Toolkit
[^nvidia-openshell]: NVIDIA. *OpenShell — Safe, private runtime for autonomous AI agents*. https://github.com/NVIDIA/OpenShell
[^nvidia-nemoclaw]: NVIDIA. *NemoClaw — Open source reference stack for always-on assistants*. https://github.com/NVIDIA/NemoClaw

### OpenShell：Agent 安全运行时

核心问题：自主 Agent 拥有文件访问、网络请求、代码执行等能力，如何防止越权？OpenShell 的方案是**声明式策略驱动的沙箱**[^nvidia-openshell]：

- **策略文件**：Agent 在隔离容器中运行，通过策略文件声明允许的文件路径、网络出口、可调用的 API
- **推理路由**：将 API 调用透明路由到本地/自托管后端，避免敏感数据泄露到外部服务
- **OCSF 日志**：沙箱内所有 Agent 行为（文件操作、网络请求、推理调用）以 [OCSF](https://ocsf.io/) 标准格式记录，可对接企业安全信息系统
- 支持主流 Agent：Claude Code、Codex 等

### NemoClaw：参考栈

OpenShell 之上的一键启动方案[^nvidia-nemoclaw]，将 OpenClaw（always-on 助手 Agent）+ OpenShell（安全沙箱）+ Nemotron（开源推理模型）打包为完整栈：

```
NemoClaw（参考栈）
  ├── OpenClaw（always-on 助手 Agent）
  ├── OpenShell（安全沙箱 + 策略引擎）
  └── Nemotron（本地推理模型）
```
