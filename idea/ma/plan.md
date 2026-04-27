# Plan DSL 定义

## Plan 概述

Plan 是由编排原语组合而成的执行计划，类似程序代码。Plan 可以嵌套。

详细的 DSL 语法定义见 [Plan DSL 语法](plan-dsl.md)。

## Plan 数据结构

```yaml
plan:
  id: "plan-123"
  version: "v2"
  parent_version: "v1"  # 父版本，如果是初始版本则为null
  state: "running"
  
  # Plan 定义（编排原语组合）
  definition:
    sequence([
      collect_data(source="jira"),
      collect_data(source="monitor"),
      analyze_results()
    ])
  
  # Plan Context
  context:
    input:
      sprint: "Sprint 23"
      template: "standard_review"
      requester: "xia.wang@dell.com"
    
    execution:
      started_at: "2026-04-17T10:00:00Z"
      current_step: "analyzing_completion"
      steps_completed: ["collect_jira", "collect_test_results"]
      global_commit: "abc123def456"
    
    shared_data:
      jira_data: {...}
      test_results: {...}
      data_structure: {...}
  
  # 版本差异
  version_diff:
    - type: "task_added"
      task_id: "task-456"
    - type: "task_modified"
      task_id: "task-123"
      changes: {...}
    - type: "task_removed"
      task_id: "task-789"
```

## Plan 状态

| 状态 | 描述 | 触发条件 |
|------|------|----------|
| `new` | Plan已创建，等待执行 | Planner生成Plan后 |
| `running` | Plan正在执行中 | Plan Executor开始执行Plan |
| `waiting` | Plan等待子Plan完成 | 展开的Task正在执行子Plan |
| `done` | Plan执行完成（成功或失败） | 所有Task完成或失败 |
| `switched` | Plan已切换到新版本 | Planner生成新版本，Plan Executor切换 |

## Plan 版本管理

### 版本化规则

- 每个Plan版本是不可变的（immutable）
- 修改Plan时，基于当前版本创建新版本
- 版本号：v1, v2, v3（简单递增）

### 版本切换场景

典型场景：Plan执行错误时，Planner重新订正Plan

```
Plan v1 执行中
  ↓
某个Task失败
  ↓
Planner重新订正Plan（生成v2）
  ↓
Plan Executor处理版本切换：
  - 遍历v2中的每个Task
  - 调用Task类型的redo_strategy判断是否重做
  - 复用v1中已成功Task的结果
  - 重新执行需要重做的Task
```

### 版本切换流程

```
Plan v1 → Plan v2
  ↓
Plan Executor 遍历 v2 中的每个 Task
  ↓
获取 Task 的类型
  ↓
调用该 Task 类型的 redo_strategy
  - 传入：v1中对应Task的信息、v2中Task的参数、Context变化
  - 执行：该类型定义的策略逻辑
  - 返回：reuse / redo / partial_redo
  ↓
Plan Executor 根据决策执行
  - reuse：复用v1的结果
  - redo：重新执行
  - partial_redo：部分重做
```

## Plan 执行流程

```
Plan Executor 接收 Plan
  ↓
创建 Plan Context
  ↓
遍历 Plan 的原语
  ↓
遇到 Task
  ↓
Task 有 plan 字段？
  ↓ Yes
  展开 Task 为子 Plan
  - 创建子 Plan Context（继承父 Plan Context）
  - 递归执行子 Plan
  - 等待子 Plan 完成
  ↓ No
  分配 Task 给 Agent
  - Agent 执行 Task
  - Agent 返回结果 + Context 更新
  - 更新 Plan Context
  ↓
所有 Task 完成？
  ↓ Yes
Plan 完成
  ↓ No
继续下一个 Task
```

## Task 执行流程

```
Task 分配给 Agent
  ↓
Agent 接收 Task + Context
  ↓
Agent 执行 Task
  ↓
Agent 返回 Result + Context Updates
  ↓
Plan Executor 更新 Plan Context
  ↓
Task 状态变为 done
  ↓
继续 Plan 的下一个原语
```

## Context 更新规则

1. **Task输出更新Context**：Agent返回的Context Updates合并到Plan Context
2. **子Plan继承父Context**：子Plan创建时继承父Plan的Context
3. **子Plan结果合并**：子Plan完成后，其Context更新合并到父Plan Context
4. **并发冲突解决**：parallel/map原语执行时，多个Task并发更新Context，采用合并策略

## 异常处理

### Task失败

- 如果Task配置了retry，按策略重试
- 如果retry耗尽，标记Plan为failed
- 如果Plan配置了fallback，执行fallback逻辑

### 子Plan失败

- 子Plan失败传递到父Task
- 父Task失败，父Plan按异常处理逻辑处理

### Context更新冲突

- 采用"最后写入优先"策略
- 或配置自定义合并策略

## 设计原则

- **职责分离**：Planner负责规划，Plan Executor负责执行
- **状态透明**：Plan和Task的状态变化可追踪
- **Context隔离**：不同Plan的Context相互隔离
- **可恢复**：Plan执行失败后可以从断点恢复
- **可观测**：Plan执行过程可监控和调试
