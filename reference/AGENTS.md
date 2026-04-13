# reference/ — 重要文档原文存档

存放重要技术文档的 Markdown 转换版（含图片），供离线阅读和交叉参考。

## 目录约定

- 每个文档一个子目录：`reference/<slug>/`
- 子目录内 `index.md` 为主文件，图片与 `index.md` 同级
- 图片由 `pymupdf4llm` 自动提取，命名格式为 `<source>-<page>-<idx>.png`
- 此目录**不纳入 MkDocs 构建**（在 `docs/` 之外）

## 文件列表

| 子目录 | 来源 | 说明 |
|--------|------|------|
| `mythos-system-card/` | Anthropic, 2026-04-07 | Claude Mythos Preview System Card (245 页) |

## 重新生成已有文档

已有子目录在 `.gitignore` 中，不提交到 Git。用以下命令从原始 PDF 重新生成：

```bash
# mythos-system-card（245 页，约 110 张图）
curl -L -o /tmp/mythos_system_card.pdf https://anthropic.com/claude-mythos-preview-system-card
uv run reference/pdf_to_md.py convert /tmp/mythos_system_card.pdf mythos-system-card
```

## 如何添加新文档

```bash
# 1. 转换 PDF → Markdown + 图片（自动创建子目录、修正图片路径）
uv run reference/pdf_to_md.py convert <pdf-path> <slug>

# 2. 更新本文件的文件列表
# 3. 将子目录加入 .gitignore
```

## 本地浏览

```bash
uv run reference/pdf_to_md.py serve              # http://127.0.0.1:8100
uv run reference/pdf_to_md.py serve --port 9000  # 自定义端口
```

独立于主站 MkDocs 的轻量 HTTP 服务器，支持暗色模式、Markdown 渲染和图片展示。
