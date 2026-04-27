<!-- 
  需要头脑风暴一下产品怎么做：
    1. 不讨论实现的细节，当涉及细节时，只需要考虑到可行性即可。
    2. 尽量避免引入边界case的讨论，优先以主要的用户故事为主。
 -->

# 多Agent工程任务框架

---

这是一个多Agent协作框架的产品设计文档，包含技术架构、产品设计和质量评价三个部分。

## 文档结构

### [核心概念定义](core-concepts.md)
技术架构设计，包含：
- 词汇表
- Context设计（层次结构、访问规则、扩展机制）
- Agent能力
- Planner职责
- Plan Executor（版本管理、执行流程、异常处理）

### [Plan DSL 语法](plan-dsl.md)
Plan DSL 语法定义，包含：
- 基本语法
- 编排原语（sequence、parallel、condition、loop、map、context）
- 嵌套组合
- Context 引用
- Task 参数传递
- 完整示例

### [Plan 执行机制](plan.md)
Plan 执行机制，包含：
- Plan 数据结构
- Plan 状态管理
- Plan 版本管理
- Plan 执行流程
- Task 执行流程
- Context 更新规则
- 异常处理

### [Task 定义](task.md)
Task 的完整定义，包含：
- Task 概述
- Task ID（URI 格式、解析规则）
- Task 实例（字段结构）
- Task 生命周期
- Task 展开为 Plan
- Task 与 Agent 的关系

### [Task 类型](task-type.md)
Task 类型定义，包含：
- Task 类型定义（can_expand_to_plan、redo_strategy、URI 参数解析）
- 重做策略类型
- 版本切换时的判断逻辑
- Task 类型与 Agent 的映射

### [产品设计笔记](product-design.md)
产品设计思路，包含：
- 产品定位和目标用户
- 主要用户故事
- 核心功能模块（任务编排、上下文管理、Agent能力、用户交互、知识记忆）
- MVP范围建议
- 技术可行性考虑
- 风险和挑战
- 成功指标

### [任务评价体系](task-evaluation.md)
质量评价机制，包含：
- 评价目标和指标设计
- 评级逻辑和结果
- 按Task类型的指标示例
- 指标定义配置和数据结构
- 数据收集机制
- 评价结果的应用
- 实施建议
