<!-- 
  需要头脑风暴一下产品怎么做：
    1. 不讨论实现的细节，当涉及细节时，只需要考虑到可行性即可。
    2. 尽量避免引入边界case的讨论，优先以主要的用户故事为主。
 -->

# 多任务协作框架

---

这是一个多任务协作框架的产品设计文档，包含技术架构、产品设计和质量评价三个部分。

## 文档结构

### [核心概念定义](core-concepts.md)
技术架构概览，包含：
- 词汇表
- Context 设计（层次结构、访问规则、扩展机制）
- Task Type 与 Impl（概要 + 链接）
- Plan Executor（职责清单 + 设计原则）

### [Plan DSL 语法](plan-dsl.md)
Plan DSL 语法定义，包含：
- 核心规则（key-as-call、value 按类型分派）
- 编排原语（sequence、parallel、condition、loop、map、context）
- Task 参数传递与自动绑定
- DSL 辅助方法
- 完整示例

### [Plan 执行机制](plan.md)
Plan 数据结构与执行流程，包含：
- Plan 数据结构（含版本信息）
- Plan 版本管理
- Plan 执行流程
- Task 执行流程
- Context 更新规则
- 异常处理

### [Plan 与 Task 生命周期](plan-lifecycle.md)
状态机与运行时机制，包含：
- Task 状态机（state/result 分离、sub-status）
- Plan 状态机
- 进度管理
- 重试策略（配置、退避策略、流程）
- 超时机制

### [Task 定义](task.md)
Task 的完整定义，包含：
- Task ID（URI 格式、解析规则）
- Task 实例（字段结构）
- Task 生命周期（摘要，引用 plan-lifecycle.md）
- Task 展开为 Plan
- Task 与 Impl 的关系

### [Task 类型](task-type.md)
Task 类型与 Impl 定义，包含：
- Task 类型定义（redo_strategy、URI 参数解析）
- Impl 定义（kind、can_expand_to_plan、partners）
- DSL 辅助方法
- 重做策略（always_redo、context_aware、input_driven）
- 版本切换流程

### [产品设计笔记](product-design.md)
产品设计思路，包含：
- 产品定位和目标用户
- 主要用户故事
- 核心设计决策（编排原语、规划能力、理论/实践参考）
- 用户交互、知识记忆
- 风险和挑战
- 成功指标

### [任务评价体系](task-evaluation.md)
质量评价机制，包含：
- 评价目标和指标设计
- 评级逻辑和结果
- 按 Task 类型的指标示例（仅可自动采集的指标）
- 指标定义配置和数据结构
- 数据收集机制
- 评价结果的应用
