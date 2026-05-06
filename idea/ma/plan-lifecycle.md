# Plan 与 Task 生命周期

## 概述

本文档定义 Plan 和 Task 的状态机、进度管理、重试策略和超时机制。

**核心原则**：生命周期状态只管"执行到哪了"，成功/失败是执行结果（result），不是生命周期状态。两个维度分开。

## Task 状态机

### 生命周期状态

```
new → working → done
         ↓
      delegated → done
```

4 个状态，编排逻辑只关心这一层：

| 状态 | 描述 | 进入条件 |
|------|------|----------|
| `new` | 已创建，等待执行 | Plan 生成后 Task 被创建 |
| `working` | 正在执行中 | Impl 开始处理 |
| `delegated` | 已展开为子 Plan | Impl 生成子 Plan，交由 Plan Executor 执行 |
| `done` | 执行结束 | Impl 返回结果/错误，或子 Plan 完成 |

### 执行结果

Task 进入 `done` 时，由独立的 `result` 字段记录结果：

| result | 描述 |
|--------|------|
| `success` | 成功完成 |
| `failed` | 执行失败（重试耗尽） |
| `cancelled` | 被取消 |

### Sub-status

Sub-status 用于内部跟踪和监控，不影响编排逻辑。格式：`宏观状态.子状态`。

**working**：

| Sub-status | 描述 |
|------------|------|
| `working.running` | 正在执行（默认） |
| `working.waiting` | 等待依赖 Task 完成 |
| `working.retrying` | 执行失败，正在重试 |

**delegated**：

| Sub-status | 描述 |
|------------|------|
| `delegated.planning` | Impl 正在生成子 Plan |
| `delegated.validating` | Plan Executor 正在校验子 Plan |
| `delegated.executing` | 子 Plan 正在执行 |

### 状态转换图

```
new
 │
 ├─→ working.running
 │     │
 │     ├─→ working.retrying ──→ working.running  (重试)
 │     │                    ──→ done              (重试耗尽, result=failed)
 │     │
 │     ├─→ working.waiting ───→ working.running   (依赖就绪)
 │     │
 │     └─→ done  (result=success / failed / cancelled)
 │
 └─→ delegated.planning
       │
       ├─→ delegated.validating
       │     ├─→ delegated.executing ──→ done  (result=success / failed)
       │     └─→ done                          (校验不通过, result=failed)
       │
       └─→ done                                (生成 Plan 失败, result=failed)
```

## Plan 状态机

### 生命周期状态

| 状态 | 描述 | 进入条件 |
|------|------|----------|
| `new` | 已创建，等待执行 | Impl 生成 Plan 后 |
| `running` | 正在执行中 | Plan Executor 开始执行 |
| `done` | 执行结束 | 所有 Task 完成，或某个 Task 失败且无法恢复 |
| `switched` | 已切换到新版本 | Impl 生成新版本 Plan |

### 执行结果

Plan 进入 `done` 时，由独立的 `result` 字段记录结果：

| result | 描述 |
|--------|------|
| `completed` | 所有 Task 成功完成 |
| `failed` | 某个 Task 失败且无法恢复 |

### 状态转换

```
new → running → done (result=completed / failed)
             → switched → (新版本 Plan: new → running → ...)
```

## 进度管理

### Task 进度

Task 实例增加进度相关字段：

```yaml
Task_A:
  id: "task:/collect_data?source=jira"
  state: "working"
  sub_status: "working.running"
  result: null               # 仅 done 时有值

  # 进度信息
  progress:
    percentage: 60           # 0-100，由 Impl 上报
    message: "已收集 3/5 个数据源"  # 可选，人类可读的进度描述

  # 重试信息
  retry:
    attempt: 2               # 当前是第几次尝试（从 1 开始）
    max_attempts: 3          # 最大尝试次数
    last_error: "API timeout"  # 上一次失败的原因

  # 时间信息
  created_at: "2026-04-17T10:00:00Z"
  started_at: "2026-04-17T10:01:00Z"
  completed_at: null
  deadline: "2026-04-17T10:30:00Z"  # 可选，超时截止时间
```

### Plan 进度

Plan 的进度由其 Task 的状态聚合得出：

```yaml
plan:
  id: "plan-123"
  state: "running"
  result: null
  progress:
    total_tasks: 5
    completed: 3
    failed: 0
    running: 1
    pending: 1
```

## 重试策略

### 两类重试

系统区分两类重试：

- **执行级重试**：处理网络抖动、API 超时、工具偶发错误等基础设施层失败，不创建新的 Task，仍属于当前 Task 的执行过程
- **Task Retry**：处理切换 Impl、调整输入、从失败点重新展开、人工介入后再试一版等语义级重试，会创建新的 Retry Task。详细定义见 [Task Retry](task-retry.md)

本节的 `retry` 配置和退避策略，默认都指**执行级重试**。

### 配置

执行级重试策略在 Task Type 级别定义，Impl 执行时遵守：

```yaml
task_types:
  collect_data:
    retry:
      max_attempts: 3           # 最大尝试次数（含首次）
      backoff: exponential      # 退避策略：none / fixed / exponential
      base_delay: 1s            # 基础延迟
      max_delay: 30s            # 最大延迟
      retryable_errors:         # 可重试的错误类型（可选，默认全部重试）
        - "timeout"
        - "rate_limit"
        - "transient"
```

### 退避策略

| 策略 | 公式 | 示例（base_delay=1s） |
|------|------|----------------------|
| `none` | 无延迟，立即重试 | 0, 0, 0 |
| `fixed` | 固定延迟 | 1s, 1s, 1s |
| `exponential` | base_delay × 2^(attempt-1)，上限 max_delay | 1s, 2s, 4s |

### 重试流程

```
Task 执行失败
  ↓
是否 retryable？（检查 retryable_errors，默认全部可重试）
  ↓ No → done (result=failed)
  ↓ Yes
attempt < max_attempts？
  ↓ No → done (result=failed)
  ↓ Yes
sub_status → working.retrying
等待退避延迟
sub_status → working.running
重新执行
```

### Task Retry 触发

当失败不是临时基础设施问题，而是需要换 Impl、修改输入、调整策略或人工介入后重新尝试时，Plan Executor 不继续在原 Task 上覆盖执行，而是创建新的 Retry Task：

```text
原始 Task 失败或结果不理想
  ↓
是否属于语义级重试？
  ↓ No → 继续执行级重试流程
  ↓ Yes
克隆原始 Task + Context 快照
  ↓
创建 Retry Task
  ↓
独立执行并产出候选结果
  ↓
按 merge_policy 合并回原始 Task 或等待人工采纳
```

## 超时机制

### Task 超时

Task Type 可以定义默认超时时间，Plan 中也可以逐 Task 覆盖：

```yaml
task_types:
  collect_data:
    timeout: 5m               # 默认超时

  analyze:
    timeout: 10m
```

### 超时处理

```
Task 开始执行，启动超时计时器
  ↓
到达 deadline？
  ↓ Yes
视为执行失败（error = "timeout"）
  ↓
进入重试流程（如果 timeout 在 retryable_errors 中）
```

### Plan 超时

Plan 级别可设置整体 deadline，所有未完成的 Task 在 deadline 到达时标记为 `done` (result=cancelled)：

```yaml
plan:
  id: "plan-123"
  deadline: "2026-04-17T12:00:00Z"  # Plan 整体截止时间
```

## 设计原则

- **状态与结果分离**：生命周期状态（state）只管执行到哪了，成功/失败由独立的 result 字段记录
- **宏观简单，细节可选**：编排逻辑只关心宏观状态，sub-status 用于监控和调试
- **重试分层**：执行级重试处理临时失败，Task Retry 处理语义级重试，两者边界清晰
- **重试内聚**：执行级重试策略由 Task Type 定义，Plan Executor 执行，Impl 无需关心重试逻辑
- **超时兜底**：防止 Impl 挂死，Task 和 Plan 都有超时机制
- **进度可观测**：Impl 上报进度，Plan 聚合 Task 状态，用户可实时查看
