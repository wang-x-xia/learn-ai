---
title: 具身算法
description: 具身智能算法——机器人基础模型、视觉-语言-动作模型（VLA）、世界模型。
---

# 具身算法

机器人基础模型与学习算法，涵盖 VLA 微调框架和世界模型。

<div class="grid cards" markdown>

- :material-swap-horizontal: **[OpenVLA-OFT](openvla-oft.md)**

    ---

    VLA 优化微调方法论——并行解码替代自回归、MLP action head 直接回归连续动作、L1 loss 简胜 diffusion，微调策略比预训练数据覆盖更重要

- :material-robot: **[OpenPI 微调框架](openpi.md)**

    ---

    Physical Intelligence 开源 VLA 模型框架——双专家架构、三层 Transform 数据管线、位置语义化的固定观测结构

- :material-earth: **[τ₀-World Model](tau-0-wm.md)**

    ---

    5B 视频-动作统一世界模型——视频扩散骨干联合生成未来帧与动作序列，异构数据模态级监督掩码，推理时 Propose-Evaluate-Revise

- :material-puzzle: **[StarVLA](starvla.md)**

    ---

    模块化 VLA 统一实验平台——Backbone–Action Head 解耦统一四种动作解码范式，StarVLA-α 极简基线证明强 VLM 下复杂设计收益有限

- :material-link-variant: **[Qwen-RobotManip](qwen-robotmanip.md)**

    ---

    三维度跨形态对齐框架——80 维 canonical space + 相机系 delta pose + 行为级上下文适应，实验证明对齐是数据 scaling 的前提条件

</div>
