---
title: "OpenAI Codex"
description: OpenAI 的编码 Agent，云端（ChatGPT 内）与本地 CLI 双形态，以 microVM 沙箱隔离和 codex-1 专用模型为核心差异。
created: 2026-04-08
updated: 2026-04-08
tags: [product, openai, coding, cli, agent]
---

# OpenAI Codex

> OpenAI 的编码 Agent，云端（ChatGPT 内）与本地 CLI 双形态，以 microVM 沙箱隔离和 codex-1 专用模型为核心差异。

| 属性 | 值 |
|------|-----|
| 厂商 | OpenAI |
| 形态 | 云端 Agent（ChatGPT 侧栏）+ CLI |
| 开源 | CLI 开源，Apache 2.0 ([GitHub](https://github.com/openai/codex))；云端闭源 |
| 技术栈 | TypeScript, Node.js |
| 底座模型 | CLI 默认 o4-mini（可切换 o3、GPT-4.1）；云端使用 codex-1（o3 代码微调版） |
| 官网 | [openai.com/codex](https://openai.com/index/introducing-codex/) |

## 技术亮点

- **每任务 microVM 沙箱 + 断网隔离**：云端每个编码任务在独立的 microVM/容器中运行，且执行期间完全切断网络。断网是关键安全决策——防止 Agent 在自主执行时触发供应链攻击（恶意依赖安装、数据外泄等）。任务完成后生成可审计的终端日志和 diff，人类审查后再合并
- **codex-1 专用模型**：基于 o3，使用强化学习（RL）在真实编码任务上微调。区别于一般的指令微调（instruction tuning），RL 微调让模型学会"在沙箱里反复尝试-验证-修正"的策略，更贴合 Agent 的工作模式（写代码→跑测试→看报错→修复）
- **三级自主度**：suggest（只建议，不修改文件）→ auto-edit（自动编辑文件，但命令执行需审批）→ full-auto（全自主沙箱执行）。这是信任校准的 UX 工程——用户可以从保守模式逐步升级，而非二选一的"完全手动/完全自主"
- **CLI 平台特定沙箱**：macOS 使用 `sandbox-exec`（Seatbelt profile）限制文件系统和网络访问，Linux 使用 Docker 容器隔离。有趣的是选择了操作系统原生沙箱机制而非统一方案，在安全性和部署便利性之间取得平衡
- **AGENTS.md 约定**：读取项目根目录的 `AGENTS.md` 获取构建指令、代码风格和架构上下文。与 Claude Code 的 `CLAUDE.md` 异曲同工——两家头部厂商不约而同收敛到"项目级纯文本 Agent 配置"这一设计模式
- **云端 + CLI 双运行时**：同一个 Agent 概念有两种架构截然不同的实现——云端（异步、并行多任务、microVM）和 CLI（同步、交互式、本地沙箱）。这意味着同一个团队可以用 CLI 做即时交互，用云端批量处理 Issue backlog

## 定价

| 形态 | 说明 |
|------|------|
| CLI | 免费开源，按 OpenAI API 用量计费 |
| 云端 | 包含在 ChatGPT Pro / Plus / Team / Enterprise 订阅中 |

## 参考资料

- [Introducing Codex](https://openai.com/index/introducing-codex/)
- [GitHub 仓库 (CLI)](https://github.com/openai/codex)
