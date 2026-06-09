# scripts/ — 自动化脚本

## 依赖管理

所有依赖统一在 `pyproject.toml` 中管理，**不要使用 PEP 723 inline script metadata**。新增依赖用 `uv add <pkg>`。

## 验证脚本

`validate_docs.py` 检查所有 `.md` 文件的格式规范：

```bash
uv run scripts/validate_docs.py             # 检查 docs/ 目录
uv run scripts/validate_docs.py --auto-fix  # 检查并自动修复（如 changelog 超限自动截断）
```

检查项（错误，阻断 CI）：
- Frontmatter 存在性和必填字段（含 `review`）
- 脚注引用与定义的匹配（无孤立引用、无未使用的定义）
- 内容行数超限（>500 行，不计 frontmatter 和 `## 参考资料` 以下部分）
- `docs/changelog.yaml` 条目数超限（>5 条，`--auto-fix` 时自动截断旧条目）

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
