# TODO — 待解决问题

---

## 开放的设计问题

- [ ] **没有权限/安全模型**：Impl 访问外部系统的凭证和权限边界未涉及（暂缓）
- [ ] **目标用户与技术深度之间的鸿沟**：Task URI、DSL 语法等开发者概念需要区分对用户暴露 vs 内部实现（暂缓）

---

## 已解决（归档）

<details>
<summary>点击展开</summary>

### 架构层面

- [x] **Task Type - Impl 模型**：去掉 Agent Type，直接用 Task Type + Impl（1:N）
- [x] **Planner 设计**：规划能力内化为 Impl 的 can_expand_to_plan
- [x] **术语统一**：Agent → Task Type + Impl
- [x] **parallel/map 的 Context 合并策略**：parallel 各 Task 写不同 key、冲突报错；loop/map 由 items Task 定义合并策略

### 设计一致性

- [x] **DSL "无副作用"表述不准确**：当前文档仅声明"声明式"
- [x] **Task ID 的 URI query 与 Task input 字段重复**：query 是 input 的序列化
- [x] **Plan DSL 转换为 YAML 格式**
- [x] **key 中嵌套括号需要平衡解析**：标准括号平衡即可
- [x] **condition 的 then/else 值有两种形态**：YAML 类型直接区分
- [x] **context 原语有两种 value 形态**：不存在此问题
- [x] **loop/map 是否也应统一为映射形式**：不需要
- [x] **task.md 示例中 id 与 type 矛盾**

### 缺失的设计

- [x] **Redo Strategy 核心逻辑**：always_redo / context_aware（depends_on）/ input_driven，partial_redo = 带 prior_result 的重新执行
- [x] **超时/截止时间机制**：plan-lifecycle.md
- [x] **资源/并发控制**：parallel/map 的 max_concurrency
- [x] **loop 和 map 语义高度重叠**：不重叠（顺序 vs 并行）
- [x] **done 状态混合了成功和失败**：state/result 分离

### 清理与去重

- [x] **移除实施/阶段计划相关内容**
- [x] **Evaluation 中的主观指标难以自动化**：只保留可自动采集的指标
- [x] **core-concepts.md 瘦身**：Plan Executor 部分从 ~240 行精简为 ~30 行，删除重复的流程图/状态表/执行流程，改为交叉链接
- [x] **plan.md 去重**：Plan 状态表和版本切换流程改为引用 plan-lifecycle.md 和 task-type.md
- [x] **task.md 对齐**：生命周期 sub-status 与 plan-lifecycle.md 一致，result 字段独立
- [x] **product-design.md 去重**：技术细节精简为摘要+链接，移除过时的状态流转和 Task Context
- [x] **plan-dsl.md 修正 parallel 合并描述**：parallel 各 Task 写不同 key、冲突报错，不需要合并策略
- [x] **IDEA.md 更新索引**：补充 plan-lifecycle.md，修正各文档描述

</details>
