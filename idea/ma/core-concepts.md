# 核心概念定义

## 词汇表

| 词汇 | 定义 |
|------|------|
| **Task** | 最小执行单元，代表一个原子化的工作项。Task可以按需展开为Plan。详见 [Task 定义](task.md) |
| **Task Retry** | Task的语义级重试机制：Plan Executor 从原始 Task 克隆出新的 Retry Task 和其 Context 快照执行，并按策略将结果合并回原始 Task。详见 [Task Retry](task-retry.md) |
| **Task Type** | Task的类型，定义能力契约（输入/输出、redo_strategy、uri_params）。每个Task Type可以有多个Impl |
| **Impl** | Task Type的具体执行者，可以是LLM、脚本、预定义流程等（通过kind区分）。Impl决定是否将Task展开为Plan（can_expand_to_plan）以及可协作的partners。评价体系针对Impl级别运作 |
| **Plan Executor** | Plan执行器，负责执行Plan，管理Task调度、Impl选择和Context传递 |
| **Plan** | 由编排原语组合而成的执行计划，类似程序代码。Plan可以嵌套 |
| **Context** | Task和Plan执行时的输入数据和依赖信息，由Plan Executor管理。Context可以分层：Global Context、Plan Context（嵌套） |
| **Plan Context** | Plan调度Task时共享的数据，支持嵌套。Plan Context可以被Task修改 |
| **Global Context** | 全局共享的上下文，指向main branch的特定commit，为Task执行提供确定的背景，只读 |

## Context设计

**Context层次结构**（支持嵌套）：

```
Global Context (全局)
  ├── Plan Context (Root Plan)
  │   ├── Plan Context (Sub Plan 1)
  │   │   └── Plan Context (Sub Plan 1.1)
  │   └── Plan Context (Sub Plan 2)
```

**当前Context层次**：

| 层次 | 描述 | 内容示例 | 生命周期 |
|------|------|----------|----------|
| **Global Context** | 全局共享的上下文，指向main branch的特定commit，为Task执行提供确定的背景 | 系统配置、全局知识库、企业策略、全局偏好 | 系统级别，通过main branch持续演进，每次执行基于确定的commit |
| **Plan Context** | Plan调度Task时共享的数据，支持嵌套 | Plan输入、中间结果、Task间共享数据 | Plan级别，Plan完成后归档 |

**各层次的具体内容**：

**Global Context**：
```yaml
# Global Context 指向 main branch 的特定 commit
# Global Context 本质上是 main branch（持续演进）
# 但每次 Task 执行需要记录使用的 commit hash 来确定工作在哪个确定的 base 上
repository:
  url: "https://github.com/org/global-context-repo"
  commit: "abc123def456"  # Task执行时使用的特定 commit hash
  branch: "main"         # Global Context 持续演进在 main branch

# 仓库内容示例
system:
  version: "1.0.0"
  config:
    max_retry: 3
    timeout: 3600

global_preferences:
  language: "zh-CN"
  notification_channel: "slack"
  output_format: "markdown"

knowledge_base:
  company_policies: [...]
  best_practices: [...]
  domain_models: [...]

shared_resources:
  common_data: [...]
  templates: [...]
```

**Global Context 的 commit 记录机制**：

Global Context 本质上是 main branch（持续演进），但整个任务执行框架需要一个确定的背景。因此：

1. **Plan 执行时记录 commit**：每个 Plan 在执行时记录使用的 Global Context commit hash（如 Plan Context 中的 `global_commit` 字段）
2. **可追溯性**：通过 commit hash 可以追溯某个 Task/Plan 是基于哪个版本的 Global Context 执行的
3. **可重现性**：基于确定的 commit 可以重现相同的执行环境
4. **版本对比**：可以对比不同 commit 之间的 Global Context 变化，分析其对 Task 执行的影响

**Plan Context**（如"准备Sprint Review"的Plan）：
```yaml
plan:
  id: "plan-123"
  parent_plan: null  # 根Plan为null，子Plan指向父Plan
  state: "working"

input:
  sprint: "Sprint 23"
  template: "standard_review"
  requester: "xia.wang@dell.com"

execution:
  started_at: "2026-04-17T10:00:00Z"
  current_step: "analyzing_completion"
  steps_completed: ["collect_jira", "collect_test_results"]
  global_commit: "abc123def456"  # 该Plan基于哪个Global Context commit执行

shared_data:
  jira_data: {...}      # Task间共享的数据
  test_results: {...}   # Task间共享的数据
  data_structure: {...} # Plan定义的数据结构
```

**Context访问规则**：

| Context类型 | 访问权限 | 读写规则 |
|-------------|----------|----------|
| Global Context | 所有Impl可读 | 只读，基于main branch的特定commit执行，修改需提交新commit到main branch |
| Plan Context | Plan内的所有Task可读写，支持嵌套继承 | Plan级别隔离，子Plan可访问父Plan Context |

**预留扩展空间的设计**：

1. **命名空间预留**：Context支持命名空间，未来可添加中间层
   ```yaml
   # 当前设计
   plan:
     id: "plan-123"

   # 未来可能的扩展
   project.product_development.plan:
     id: "plan-123"
   ```

2. **继承机制预留**：Context支持继承，未来中间层可覆盖Global配置
   ```yaml
   # 当前设计：Plan直接使用Global配置
   # 未来可能的扩展：Project层覆盖Global配置
   ```

3. **访问控制可扩展**：当前简单的读写规则，未来可支持更细粒度的权限控制

4. **Context引用机制**：Task可以引用Global Context和Plan Context中的资源，未来可引用中间层资源

**扩展指南**（未来添加中间层时）：

| 扩展场景 | 建议的中间层 | 插入位置 |
|----------|-------------|----------|
| 多项目环境 | Project Context | Global与Plan之间 |
| 多团队协作 | Team Context | Global与Plan之间 |
| 领域知识隔离 | Domain Context | Global与Plan之间 |
| 会话级别上下文 | Session Context | Global与Plan之间 |

**扩展原则**：
- 新层次插入到Global和Plan之间
- 保持层次间的单向依赖（上层不依赖下层）
- 新层次可以覆盖Global的配置
- 访问权限遵循"最小权限"原则

**Context更新机制**：

1. **增量更新**：Context支持增量更新，避免全量替换
2. **版本控制**：重要Context有版本历史，支持回滚
3. **事件通知**：Context变更触发事件，相关Impl收到通知
4. **冲突解决**：多Impl并发更新时的冲突解决策略
5. **Task修改Context**：Task可以修改Plan Context，Global Context为只读（基于main branch的特定commit执行）

**设计原则**：
- **分层隔离**：不同层次Context相互隔离，避免污染
- **最小权限**：Impl只能访问必要的Context层次
- **全局偏好**：偏好配置固化在Global Context，不针对个人
- **可扩展**：通过命名空间、继承机制预留扩展空间
- **可追溯**：所有Context变更可追溯（who/when/what）
- **可恢复**：Global Context通过main branch的commit历史支持版本回滚，可追溯每个Task基于哪个commit执行

## Task Type 与 Impl

Task Type 定义能力契约，Impl 是具体执行者。详见 [Task 类型](task-type.md)。

- **Task Type**：定义"这类工作是什么"（输入/输出、redo_strategy）
- **Impl**：定义"这类工作怎么做"（kind: llm/script/predefined）
- 每个 Task Type 可有多个 Impl，由 Plan Executor 选择策略决定使用哪个
- Impl 可以将 Task 展开为 Plan（`can_expand_to_plan`），此时承担规划职责
- Plan 生成后由 Plan Executor 做结构校验（partners 范围、参数合法性、DSL 结构），语义正确性通过[评价体系](task-evaluation.md)感知

## Plan Executor

Plan Executor 负责执行 Plan，管理 Task 的调度和执行流程。

**职责**：

1. **Plan 调度**：按 Plan 的编排原语调度 Task 执行（原语定义见 [Plan DSL 语法](plan-dsl.md)）
2. **Impl 选择**：将 Task 分配给 Task Type，由选择策略决定使用哪个 Impl
3. **状态跟踪**：跟踪 Task 和 Plan 的执行状态（详见 [Plan 与 Task 生命周期](plan-lifecycle.md)）
4. **Context 管理**：管理 Plan Context 的传递和更新
5. **Plan 校验**：校验 Impl 生成的 Plan 是否合法（partners 范围、参数合法性、DSL 结构）
6. **Task 展开**：当选中的 Impl 将 Task 展开为 Plan 时，递归执行子 Plan
7. **异常处理**：处理 Task 执行失败、执行级重试、Task Retry 和 fallback
8. **版本管理**：管理 Plan 的版本，处理版本切换（重做策略详见 [Task 类型 - 重做策略](task-type.md#重做策略)）

Plan 数据结构、执行流程和异常处理的详细定义见 [Plan 执行机制](plan.md)。

**设计原则**：

- **职责分离**：Impl 负责执行（或规划+执行），Plan Executor 负责调度和校验
- **状态透明**：Plan 和 Task 的状态变化可追踪
- **Context 隔离**：不同 Plan 的 Context 相互隔离
- **可恢复**：Plan 执行失败后可以从断点恢复
- **可观测**：Plan 执行过程可监控和调试
