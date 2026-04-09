# docs/coding-agents/ — 编码 Agent 产品档案

每个产品一个 `.md` 文件，聚焦**技术区分度**。

## 写法指南

- **属性表 + 一句话定位**：保留，用于快速识别
- **技术亮点**：只写该产品**独有或领先**的能力，跳过行业标配（代码补全、Chat 等）
- **定价**：保留，简明即可
- 不写"支持代码补全"、"支持 Chat"等所有同类产品都有的东西

## Frontmatter

```yaml
---
title: "产品名"
description: 一句话定位
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [product, vendor-name, coding, form-factor, agent]
review: YYYY-MM-DD
---
```

`title` 用引号包裹（产品名通常是英文专有名词）。六个字段必填（`review` 留空表示从未 review）。

## 模板

```markdown
---
title: "产品名"
description: 一句话定位
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [product, vendor-name, coding, form-factor, agent]
review:
---

# 产品名

> 一句话定位（厂商 + 核心形态 + 最大区分点）

| 属性 | 值 |
|------|-----|
| 厂商 | ... |
| 形态 | ... |
| 开源 | 是/否 |
| 技术栈 | ... |
| 底座模型 | ... |
| 官网 | [链接](url) |

## 技术亮点

- **亮点一**：（只写该产品独有或领先的能力，不写行业标配）
- **亮点二**：...

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| ... | ... | ... |

## 参考资料

[^key]: Author. "Title". Year. URL
```

## 新增品类目录

当出现一个新的产品品类（如搜索 Agent、数据工具）需要收录多个产品档案时：

1. 在 `docs/` 下新建扁平目录（如 `docs/search-agents/`），不嵌套
2. 目录内每个产品一个 `.md` 文件，写法同上
3. 在 `mkdocs.yml` 的 `nav:` 中添加对应条目
4. 在根 `AGENTS.md` 的目录约定中登记新目录
5. 如有品类共性，在 `docs/applied/` 下写一篇品类概述文档
