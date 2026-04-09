---
title: "Aider"
description: 开源终端 AI 结对编程工具，以 Edit Format 自适应和 tree-sitter Repo Map 为核心技术，Claude Code 的主要开源竞品。
created: 2026-04-08
updated: 2026-04-08
tags: [product, coding, cli, open-source]
review:
---

# Aider

> 开源终端 AI 结对编程工具，以 Edit Format 自适应和 tree-sitter Repo Map 为核心技术，Claude Code 的主要开源竞品。

| 属性 | 值 |
|------|-----|
| 厂商 | 独立开发者（Paul Gauthier） |
| 形态 | CLI |
| 开源 | 是，Apache 2.0 ([GitHub](https://github.com/Aider-AI/aider)) |
| 技术栈 | Python |
| 底座模型 | 模型无关 — Claude, GPT-4o, Gemini, DeepSeek, Ollama 本地模型等 |
| 官网 | [aider.chat](https://aider.chat/) |

## 技术亮点

- **Edit Format 自适应**：支持 whole-file、diff、udiff 等多种编辑格式，并根据模型能力自动选择最优格式。这是一个精妙的工程决策——不同 LLM 生成 diff 的准确率差异巨大（如 GPT-4o 擅长 udiff，Claude 擅长 whole-file），自适应策略让 Aider 能在各模型上都获得接近最优的编辑成功率
- **tree-sitter Repo Map**：基于 tree-sitter 对整个仓库进行语义解析，生成包含函数签名、类定义、导入关系的结构化仓库地图（而非简单的文件列表）。这为模型提供了代码库的"骨架视图"，在有限上下文窗口内传递最大信息量。Repo Map 会根据当前编辑文件动态调整权重，优先展示相关符号
- **Git 原子提交**：每次 AI 编辑自动生成独立 git commit 并附带语义化提交信息。这不仅是便利功能——它将 AI 编辑的撤销粒度与 git 的版本控制对齐，任何一步都可通过 `git revert` 精确回滚。当 AI 在多文件间做了复杂修改时，原子提交让人类审查和回滚成本大幅降低
- **SWE-bench 验证**：在 SWE-bench 代码修复基准上持续取得高分，以实际指标验证了 Edit Format + Repo Map 这套架构的有效性
- **纯 Python 单命令安装**：`pip install aider-chat` 即完成部署，无 Node.js 依赖、无编译步骤。对于 Python 生态的开发者而言是零摩擦接入

## 定价

- 完全免费开源，仅按模型 API 用量付费

## 参考资料

- [Aider 官网](https://aider.chat/)
- [GitHub 仓库](https://github.com/Aider-AI/aider)
