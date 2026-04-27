# 任务评价体系

## 评价目标

对Task执行结果进行量化评价，用于：
- 判断Task是否达到基本要求（合格/不合格）
- 识别Task执行中的优秀表现（哪些指标达到优秀标准）
- 为模型选择和Agent优化提供数据支持
- 决策：不合格的Task需要换模型或换Agent

## 评价指标设计

每个指标包含两个阈值：
- **合格阈值**：达到此阈值表示Task基本可用
- **优秀阈值**：达到此阈值表示Task在经济性或质量上表现突出

## 评级逻辑

```
if 所有指标 ≥ 合格阈值:
    评级 = "合格"
    标记达到优秀阈值的指标
else:
    评级 = "不合格"
```

## 评级结果

| 情况 | 输出示例 |
|------|---------|
| 不合格 | 不合格 |
| 合格，无优秀指标 | 合格 |
| 合格，有优秀指标 | 合格（优秀：Token效率、洞察深度） |

## 指标示例（按Task类型）

### Task类型：generate_doc（生成文档）

| 指标 | 合格阈值 | 优秀阈值 | 说明 |
|------|---------|---------|------|
| content_completeness | 100% | - | 内容完整性：包含所有必需章节 |
| data_accuracy | >90% | >95% | 数据准确性：与源数据误差 |
| format_correctness | 100% | - | 格式正确性：符合模板要求 |
| no_critical_errors | true | - | 无致命错误：无明显错误或矛盾 |
| token_efficiency | 节省>10% | 节省>30% | Token效率：相比历史平均节省比例 |
| execution_speed | <10分钟 | <5分钟 | 执行速度：任务完成时间 |
| insight_depth | basic | deep | 洞察深度：是否提供超出基础的分析 |
| readability | >3分 | >4分 | 可读性：用户评分（1-5分） |

### Task类型：collect_data（数据收集）

| 指标 | 合格阈值 | 优秀阈值 | 说明 |
|------|---------|---------|------|
| data_completeness | 100% | - | 数据完整性：返回所有请求字段 |
| data_accuracy | 100% | - | 数据准确性：与源数据完全一致 |
| api_success_rate | >95% | >99% | API成功率：无错误或超时 |
| api_call_count | ≤基准值 | <基准值×0.8 | API调用次数：是否用最少调用获取数据 |
| response_time | <30秒 | <10秒 | 响应时间：从请求到数据返回 |

### Task类型：analyze（数据分析）

| 指标 | 合格阈值 | 优秀阈值 | 说明 |
|------|---------|---------|------|
| error_identification_rate | >90% | >95% | 错误识别率：识别出实际错误的比例 |
| root_cause_relevance | relevant | highly_relevant | 根因相关性：与实际问题相关程度 |
| no_misleading_conclusions | true | - | 无误导性结论：不给出错误诊断方向 |
| token_efficiency | <基准值 | <基准值×0.7 | Token效率：每单位数据的token消耗 |
| diagnostic_speed | <5分钟 | <2分钟 | 诊断速度：从输入到结论输出时间 |
| actionability | actionable | highly_actionable | 可操作性：建议是否可直接执行 |

## 指标定义配置

每个Task类型在Agent注册时声明自己的指标配置：

```yaml
task_type_metrics:
  generate_doc:
    - name: content_completeness
      qualified_threshold: 100
      excellent_threshold: null
      type: percentage
      description: "包含所有必需章节"
      
    - name: data_accuracy
      qualified_threshold: 90
      excellent_threshold: 95
      type: percentage
      description: "与源数据误差"
      
    - name: token_efficiency
      qualified_threshold: "节省>10%"
      excellent_threshold: "节省>30%"
      type: percentage
      description: "相比历史平均节省比例"
      
    - name: insight_depth
      qualified_threshold: "basic"
      excellent_threshold: "deep"
      type: enum
      description: "是否提供超出基础的分析"
```

## 评价数据结构

```yaml
task_evaluation:
  task_id: "task-123"
  task_type: "generate_doc"
  
  rating: "qualified"  # qualified | unqualified
  
  metrics:
    - name: content_completeness
      qualified_threshold: 100
      excellent_threshold: null
      actual: 100
      is_qualified: true
      is_excellent: false
      
    - name: data_accuracy
      qualified_threshold: 90
      excellent_threshold: 95
      actual: 96
      is_qualified: true
      is_excellent: true
      
    - name: token_efficiency
      qualified_threshold: 10
      excellent_threshold: 30
      actual: 35
      is_qualified: true
      is_excellent: true
      
  excellent_metrics:
    - data_accuracy
    - token_efficiency
```

## 数据收集机制

**自动化指标**（系统自动收集）：
- API成功率、响应时间、Token消耗
- 执行时长、错误日志

**用户反馈指标**（需用户主动提供）：
- 可读性评分（1-5分）
- 洞察深度评价（basic/deep）
- 可操作性评价（actionable/highly_actionable）
- 根因相关性评价（relevant/highly_relevant）

**历史对比指标**：
- Token效率、API调用次数：与历史同类任务平均值对比
- 需要积累历史数据作为基准值

## 评价结果的应用

- **实时决策**：不合格的Task触发模型/Agent切换
- **Agent优化**：识别Agent的弱点指标，针对性改进
- **成本优化**：如果"Token效率"达到优秀，可以考虑用更便宜的模型
- **用户信任**：展示评价结果，帮助用户判断是否信任AI执行结果
- **系统演进**：长期趋势分析，指导产品迭代

## 实施建议

**分阶段落地**：
- **Phase 1**：先实现合格性评价，收集基础数据
- **Phase 2**：加入优秀性指标，建立历史基准
- **Phase 3**：实现自动模型/Agent切换逻辑

**关键问题**：
- 初期没有历史基准，Token效率等指标如何设定？建议先使用经验值或相对比较
- 用户反馈指标如何收集？建议在Task完成后弹出简短评价表单
