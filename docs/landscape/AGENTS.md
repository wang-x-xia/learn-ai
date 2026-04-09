# docs/landscape/ — 行业全景

跟踪主流 AI 模型的发布与行业动态。

## 文件列表

| 文件 | 主题 |
|------|------|
| `model-tracker.md` | 闭源/开源模型发布时间线、关键参数与亮点 |

## 更新 model-tracker.md 的流程

有新模型发布或重大更新时：

1. 在对应的闭源/开源表格中添加新行
2. 在 `## 最近更新` 下追加条目
3. 更新 frontmatter 的 `updated` 字段

## Frontmatter

```yaml
---
title: 文档标题
description: 一句话描述
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
review: YYYY-MM-DD
---
```

六个字段必填（`review` 留空表示从未 review）。每次修改内容时更新 `updated`，每次阅读审校后更新 `review`。
