# scripts/ — 自动化脚本

## 依赖管理

所有依赖统一在 `pyproject.toml` 中管理，**不要使用 PEP 723 inline script metadata**。新增依赖用 `uv add <pkg>`。

## 验证脚本

`validate_docs.py` 检查所有 `.md` 文件的格式规范：

```bash
uv run scripts/validate_docs.py          # 检查 docs/ 目录
```

检查项：
- Frontmatter 存在性和必填字段（含 `review`）
- 脚注引用与定义的匹配（无孤立引用、无未使用的定义）

## Review 清单

`review_status.py` 输出需要 review 的文档清单：

```bash
uv run scripts/review_status.py          # 只显示需要 review 的
uv run scripts/review_status.py --all    # 显示所有文档的 review 状态
```

判定逻辑：
- **NEVER**：`review` 为空，从未 review 过
- **STALE**：`updated > review`，内容在上次 review 后有更新
- **ok**：`review >= updated`，已是最新
