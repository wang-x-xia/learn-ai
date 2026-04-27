# 核心概念定义

## 词汇表

| 词汇 | 定义 |
|------|------|
| **Task** | 最小执行单元，代表一个原子化的工作项。Task可以按需展开为Plan。详见 [Task 定义](task.md) |
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

Task Type 定义能力契约，Impl 是具体执行者。

**Task Type**：定义"这类工作是什么"
- **输入**：Task + Context
- **输出**：Result + 新Context
- **redo_strategy**：定义该类型的重做策略（描述任务本身的性质，与Impl无关）

**Impl**：定义"这类工作怎么做"

同一个Task Type可以有多个Impl，通过 `kind` 区分执行者类型：

```
Task Type ← 1:N → Impl
  collect_data ←──┬── collect_data/jira-script  (kind: script)
                   │     can_expand_to_plan: false
                   │     partners: []
                   │
                   ├── collect_data/gpt-4o-mini  (kind: llm)
                   │     can_expand_to_plan: true
                   │     partners: [query_jira, query_monitor]
                   │
                   └── collect_data/predefined   (kind: predefined)
                         can_expand_to_plan: true
                         partners: [query_jira]
```

每个Impl声明：
- **kind**：执行者类型（llm、script、predefined等）
- **can_expand_to_plan**：是否将Task展开为Plan。强模型可能直接完成，脚本直接执行，弱模型需要拆分为子任务
- **partners**：可协作的Task Type列表。当Impl生成Plan时，Plan中只能引用partners范围内的Task Type

**Plan生成与校验**：当Impl将Task展开为Plan时，该Impl承担了规划职责。Plan生成后、执行前进行结构校验：
1. Plan中引用的每个Task Type是否都在该Impl的partners范围内？
2. 每个Task的参数是否符合对应Task Type的定义？
3. DSL结构本身是否合法？

结构校验只能捕捉结构性错误。语义错误（Plan逻辑是否正确）通过执行后的评价体系（见 [任务评价体系](task-evaluation.md)）来感知。

**Impl选择**：Plan Executor将Task分配给Task Type时，由选择策略决定使用哪个Impl。评价体系在Impl级别运作，为选择策略提供数据支持（如：不合格的Impl降权、优秀的Impl优先选用、成本敏感场景选用更便宜的Impl）。

## Plan Executor

Plan Executor负责执行Plan，管理Task的调度和执行流程。

**职责**：
1. **Plan调度**：按Plan的原语顺序调度Task执行
2. **Impl选择**：将Task分配给Task Type，由选择策略决定使用哪个Impl
3. **状态跟踪**：跟踪Task和Plan的执行状态
4. **Context管理**：管理Plan Context的传递和更新
5. **Plan校验**：校验Impl生成的Plan是否合法（partners范围、参数合法性、DSL结构）
6. **Task展开**：当选中的Impl将Task展开为Plan时，递归执行子Plan
7. **异常处理**：处理Task执行失败、重试、fallback
8. **版本管理**：管理Plan的版本，处理版本切换

**Plan版本化**：

- 每个Plan版本是不可变的（immutable）
- 修改Plan时，基于当前版本创建新版本
- 版本号：v1, v2, v3（简单递增）

**版本切换场景**：

典型场景：Plan执行错误时，负责规划的Impl重新订正Plan
```
Plan v1 执行中
  ↓
某个Task失败
  ↓
Impl重新订正Plan（生成v2）
  ↓
Plan Executor处理版本切换：
  - 遍历v2中的每个Task
  - 调用Task类型的redo_strategy判断是否重做
  - 复用v1中已成功Task的结果
  - 重新执行需要重做的Task
```

**Task类型的重做策略定义**：

每个Task类型在注册时定义自己的redo_strategy：

```yaml
task_types:
  collect_data:
    description: "数据收集"
    redo_strategy:
      type: "context_aware"
      logic: "TODO"  # 待设计：根据上下文判断是否重做

  analyze:
    description: "数据分析"
    redo_strategy:
      type: "input_driven"
      logic: "TODO"  # 待设计：根据输入变化判断是否重做

  generate_doc:
    description: "文档生成"
    redo_strategy:
      type: "always_redo"
      logic: "TODO"  # 待设计：总是重新执行
```

**版本切换流程**：

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

**Plan执行流程**：

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

**原语执行逻辑**：

| 原语 | 执行逻辑 | Context传递 |
|------|---------|------------|
| `sequence` | 顺序执行Task，前一个Task完成后执行下一个 | 后续Task继承前面Task的Context更新 |
| `parallel` | 并行执行多个Task，等待所有Task完成 | 合并所有Task的Context更新 |
| `condition` | 根据条件选择执行哪个分支 | 选中的分支继承当前Context |
| `loop` | 对列表中的每个item执行Task | 先执行items Task获取列表，每次迭代创建新的context包含当前item，如何绑定由items Task决定，迭代完成后合并到父context |
| `map` | 对列表中的每个item并行执行Task | 先执行items Task获取列表，每个元素创建新的context包含当前item，如何绑定由items Task决定，完成后合并到父context |
| `context` | 创建新的Context作用域，在指定Context中执行Task | body执行完成后Context修改合并到父Context |

**Task执行流程**：

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

**Plan状态管理**：

| 状态 | 描述 | 触发条件 |
|------|------|----------|
| `new` | Plan已创建，等待执行 | Impl生成Plan后 |
| `running` | Plan正在执行中 | Plan Executor开始执行Plan |
| `waiting` | Plan等待子Plan完成 | 展开的Task正在执行子Plan |
| `done` | Plan执行完成（成功或失败） | 所有Task完成或失败 |
| `switched` | Plan已切换到新版本 | Impl生成新版本，Plan Executor切换 |

**Plan版本信息**：

每个Plan包含版本信息：
```yaml
plan:
  id: "plan-123"
  version: "v2"
  parent_version: "v1"  # 父版本，如果是初始版本则为null
  state: "running"

version_diff:
  - type: "task_added"
    task_id: "task-456"
  - type: "task_modified"
    task_id: "task-123"
    changes: {...}
  - type: "task_removed"
    task_id: "task-789"
```

**Context更新规则**：

1. **Task输出更新Context**：Impl返回的Context Updates合并到Plan Context
2. **子Plan继承父Context**：子Plan创建时继承父Plan的Context
3. **子Plan结果合并**：子Plan完成后，其Context更新合并到父Plan Context
4. **并发冲突解决**：parallel/map原语执行时，多个Task并发更新Context，采用合并策略

**异常处理**：

1. **Task失败**：
   - 如果Task配置了retry，按策略重试
   - 如果retry耗尽，标记Plan为failed
   - 如果Plan配置了fallback，执行fallback逻辑

2. **子Plan失败**：
   - 子Plan失败传递到父Task
   - 父Task失败，父Plan按异常处理逻辑处理

3. **Context更新冲突**：
   - 采用"最后写入优先"策略
   - 或配置自定义合并策略

**设计原则**：
- **职责分离**：Impl负责执行（或规划+执行），Plan Executor负责调度和校验
- **状态透明**：Plan和Task的状态变化可追踪
- **Context隔离**：不同Plan的Context相互隔离
- **可恢复**：Plan执行失败后可以从断点恢复
- **可观测**：Plan执行过程可监控和调试
