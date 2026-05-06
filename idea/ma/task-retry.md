# Task Retry

## 概述

Task Retry 用于处理**语义级重试**：当一个 Task 需要换 Impl、调整策略、带着当前结果重新尝试，或在人工介入后重新执行时，Plan Executor 不在原 Task 上直接覆盖执行，而是从原 Task 克隆出一个新的 Retry Task 和其 Context 快照，作为一次独立尝试。

Task Retry 的目标：

- 保持 **Task 本位**：用户主要看到的仍然是原始 Task，而不是若干次执行记录
- 为不同 Impl、不同重试策略提供可比较的候选结果
- 避免在原 Task 上反复覆盖状态和 Context，降低调试难度
- 允许 Retry Task 的结果按策略合并回原 Task

## 两类重试

### 执行级重试

执行级重试处理基础设施层的临时失败，例如网络抖动、API 超时、工具偶发错误。

- 不创建新的 Task
- 仍属于同一个 Task 的执行过程
- 由执行器按退避策略自动处理

### Task Retry

Task Retry 处理语义级重试，例如：

- 切换到另一个 Impl
- 修改输入参数后重试
- 使用当前结果作为参考重新生成
- 从失败点重新展开 Plan
- 人工介入后重新尝试一版

这类场景会创建一个新的 Retry Task。

## 基本模型

原始 Task 是主对象，Retry Task 是其派生分支：

```text
Task A (原始 Task)
 ├── Retry Task A#1
 ├── Retry Task A#2
 └── 选择其中一个结果合并回 A
```

设计原则：

- 原始 Task 始终是用户感知的主要工作对象
- Retry Task 默认折叠，不作为一级对象展示
- Retry Task 可以独立执行、独立评价
- 原始 Task 最终只采纳一个生效结果

## 克隆规则

创建 Retry Task 时，默认从原始 Task 克隆：

- Task Type
- Task input
- 创建 Retry 时刻的 Context 快照
- 当前采用的 Plan 或 Plan 版本引用
- 必要的执行元信息

Retry Task 与原始 Task 在创建后**独立演化**，不保持持续同步。它代表的是“基于某个时间点快照分叉出去的一次新尝试”。

## Retry Task 的关系字段

Retry Task 本质上仍然是 Task，只是增加派生关系字段：

```yaml
task:
  id: "task:/generate_doc?type=review_summary#retry-2"
  type: "generate_doc"
  retry_of: "task:/generate_doc?type=review_summary"
  retry_root: "task:/generate_doc?type=review_summary"
  retry_reason: "switch_impl"
  merge_policy: "result_only"
```

字段含义：

| 字段 | 描述 |
|------|------|
| `retry_of` | 当前 Retry Task 直接来源于哪个 Task |
| `retry_root` | 当前重试链路的根 Task，便于聚合比较 |
| `retry_reason` | 触发重试的原因，如切换 Impl、人工修正、从失败点重试 |
| `merge_policy` | Retry Task 完成后如何合并回原始 Task |

原始 Task 可选记录：

- `retry_children`：派生出的 Retry Task 列表
- `adopted_retry`：当前采纳的是哪个 Retry Task 的结果

## 合并回原始 Task

Retry Task 执行完成后，结果可以按策略合并回原始 Task。

默认支持三类合并策略：

### 1. result_only

只回写最终结果和评价结果，不回写整个 Context。

适用：

- 文档生成
- 汇总报告
- 分析结论

这是推荐的默认策略。

### 2. result_and_selected_context

除了最终结果，还回写一小部分显式声明的 Context key。

```yaml
merge_policy:
  type: result_and_selected_context
  keys:
    - shared_data.analysis_summary
    - output.final_doc
```

适用：

- 部分中间产物有复用价值
- 但不希望整棵 Context 树都被覆盖

### 3. manual_review

Retry Task 完成后不自动合并，由人工决定是否采纳。

适用：

- 高风险 Task
- 多个 Retry Task 需要人工比较
- 输出质量存在主观判断

## Context 合并原则

Task Retry 的合并应尽量窄，不做默认的全量 Context 替换。

建议 Retry Task 在执行过程中记录自己的 Context 写入集合（write-set）或增量变更（delta），合并时仅处理这些明确写过的 key，而不是对整个 Context 做全量覆盖。

不建议默认支持：

- 整体 Context 替换
- 原始 Task 与 Retry Task 的持续双向同步

这样可以减少冲突，也更符合 Retry 作为“独立候选尝试”的语义。

## 与评价体系的关系

Retry Task 是比较不同 Impl 和不同策略的自然单位。

在同一个 `retry_root` 下，可以比较：

- 使用了哪个 Impl
- 是否成功
- 成本和耗时
- 输出质量
- 是否最终被采纳

评价结果仍然落在 Task 实例级别；原始 Task 则只需要记录当前采纳的结果来自哪一个 Retry Task。

## 展示原则

默认产品界面以原始 Task 为主：

- 当前状态
- 当前结果
- 是否发生过 Retry
- 当前采纳的是哪次 Retry 结果

只有在失败排查、质量比较、人工审阅等高级场景下，才展开 Retry Task 列表和差异信息。
