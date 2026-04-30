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
  
  # Plan 定义（编排原语组合，YAML 格式）
  definition:
    - "collect_data(source=jira)":
    - "collect_data(source=monitor)":
    - "analyze_results()":
  
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

Plan 和 Task 的状态机、进度管理、重试策略和超时机制的完整定义见 [Plan 与 Task 生命周期](plan-lifecycle.md)。

核心设计：**state 和 result 分离**——生命周期状态（new/running/done/switched）只管"执行到哪了"，成功/失败由独立的 `result` 字段记录。

## Plan 版本管理

### 版本化规则

- 每个Plan版本是不可变的（immutable）
- 修改Plan时，基于当前版本创建新版本
- 版本号：v1, v2, v3（简单递增）

### 版本切换

典型场景：Plan执行错误时，负责规划的 Impl 重新订正 Plan（生成新版本），Plan Executor 遍历新版本中的每个 Task，调用 Task Type 的 redo_strategy 判断复用/重做/带参考重做。

重做策略的详细定义见 [Task 类型 - 重做策略](task-type.md#重做策略)。

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
分配 Task 给 Task Type，选择 Impl
  ↓
Impl 的 can_expand_to_plan?
  ↓ Yes
  Impl 生成子 Plan
  - Plan Executor 校验子 Plan（partners、参数、DSL）
  - 校验通过：创建子 Plan Context（继承父 Plan Context），递归执行子 Plan
  - 校验不通过：打回重新生成或标记失败
  ↓ No
  Impl 直接执行 Task
  - Impl 返回结果 + Context 更新
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
Task 分配给 Task Type，选择 Impl
  ↓
Impl 接收 Task + Context
  ↓
Impl 执行 Task（直接执行或展开为 Plan）
  ↓
Impl 返回 Result + Context Updates
  ↓
Plan Executor 更新 Plan Context
  ↓
Task 状态变为 done
  ↓
继续 Plan 的下一个原语
```

## Context 更新规则

1. **Task输出更新Context**：Impl返回的Context Updates合并到Plan Context
2. **子Plan继承父Context**：子Plan创建时继承父Plan的Context
3. **子Plan结果合并**：子Plan完成后，其Context更新合并到父Plan Context
4. **并发Context合并**：
   - **parallel**：各 Task 在隔离 Context 中执行，应写入不同的 key，完成后直接合并。同 key 冲突报错（parallel 是独立任务，需要合并同 key 应使用 map）
   - **loop/map**：由 items Task 定义合并策略（items Task 了解数据结构，由它定义如何合并）

## 异常处理

### Task失败

- 如果Task配置了retry，按策略重试
- 如果retry耗尽，标记Plan为failed
- 如果Plan配置了fallback，执行fallback逻辑

### 子Plan失败

- 子Plan失败传递到父Task
- 父Task失败，父Plan按异常处理逻辑处理

### Context更新冲突

- 对于同一个 Context，同一时间只有一个 Task 在工作，逐步修改，不存在并发写入冲突
- parallel 中每个 Task 在独立的隔离 Context 中执行，应写入不同的 key，完成后直接合并（同 key 冲突报错）
- loop/map 中每个 Task 在独立的隔离 Context 中执行，完成后由 items Task 定义的合并策略合并到父 Context

## 设计原则

- **职责分离**：Impl 负责执行（或规划+执行），Plan Executor 负责调度和校验
- **状态透明**：Plan和Task的状态变化可追踪
- **Context隔离**：不同Plan的Context相互隔离
- **可恢复**：Plan执行失败后可以从断点恢复
- **可观测**：Plan执行过程可监控和调试
