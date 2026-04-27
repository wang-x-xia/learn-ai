# TODO — 待解决问题

Review 产出的问题清单，按优先级排列。

---

## 明确的错误

- [x] **task.md 示例中 id 与 type 矛盾**：Task_A 的 `id` 是 `task:/collect_data?...` 但 `type` 写成了 `analyze`，应改为 `collect_data`

## 架构层面

- [x] **Task Type - Impl 模型**：去掉 Agent Type 概念，直接用 Task Type + Impl（1:N）。Impl 有 `kind`（llm/script/predefined）区分执行者类型。评价体系针对 Impl 级别运作
- [x] **Planner 设计**：Planner 不是独立角色，而是 Impl 的规划能力（can_expand_to_plan）。Impl 声明 partners 定义可协作范围，Plan 生成后由 Plan Executor 做结构校验，语义正确性通过评价体系感知
- [x] **术语统一**：全部文档中 Agent/Agent Type/Agent Implementation 统一为 Task Type + Impl
- [ ] **parallel/map 的 Context 合并策略有不确定性**："最后写入优先"在并行场景下不可重现。需要确定性方案（命名空间隔离 or 禁止并行写同一 key）

## 设计一致性

- [ ] **DSL "无副作用"表述不准确**：编排层是声明式的，副作用发生在 Impl 执行层，需要区分清楚
- [ ] **Task ID 的 URI query 与 Task input 字段重复**：谁是 source of truth？不一致怎么办？URI 是 input 的序列化还是纯标识符？
- [ ] **Plan 数据结构混用 YAML 和 DSL 语法**：plan.md 的 `definition` 字段在 YAML 里嵌入 DSL，需要明确序列化格式

## 缺失的设计

- [ ] **Redo Strategy 核心逻辑全是 TODO**：三种策略的 logic 待设计，`partial_redo` 的具体含义未定义
- [ ] **没有超时/截止时间机制**：Task 和 Plan 都缺少 timeout/deadline，Impl 挂死时系统无法感知
- [ ] **没有资源/并发控制**：parallel/map 无 max_concurrency，大列表会同时启动过多 Impl
- [ ] **没有权限/安全模型**：Impl 访问外部系统的凭证和权限边界未涉及

## 产品定位

- [ ] **目标用户与技术深度之间的鸿沟**：Git commit、DSL 语法规范、Task URI 格式都是开发者概念，需要区分对用户暴露的概念 vs 内部实现细节

## 清理

- [ ] **移除实施/阶段计划相关内容**：文档只保留设计，清理掉 MVP 范围、Phase 分期、实施建议等实现规划内容（涉及 product-design.md、task-evaluation.md 等）

## 小问题

- [ ] **loop 和 map 语义高度重叠**：考虑合并为一个原语 + concurrency 参数
- [ ] **done 状态混合了成功和失败**：上层只看 `done` 可能误判，至少 Plan 级别应区分 completed/failed
- [ ] **Evaluation 中的主观指标难以自动化**：readability、insight_depth 等收集率低，Phase 1 建议只保留可自动采集的指标
