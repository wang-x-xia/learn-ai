# scripts/ — 自动化脚本

## 验证脚本

`validate_docs.py` 检查所有 `.md` 文件的格式规范：

```bash
uv run scripts/validate_docs.py          # 检查 docs/ 目录
uv run scripts/validate_docs.py --all    # 同时检查 journal/
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

## 日更脚本

- 入口：`daily_update.py`
- 只做一件事：拉 RSS + 爬虫 → 按订阅源写入 `journal/YYYY/MM/DD/<source>.md`
- 依赖管理：统一在 `pyproject.toml`，通过 `uv` 管理

### 运行

```bash
# 拉取过去 48h（默认）
uv run scripts/daily_update.py

# 拉取过去 24h
uv run scripts/daily_update.py --hours 24

# 只拉取指定源（用 slug 指定）
uv run scripts/daily_update.py --only simon-willison

# 快速验证新加的源（拉 1h）
uv run scripts/daily_update.py --hours 1
```

## feeds.yaml 结构

所有订阅源在 `feeds.yaml` 中登记，按分类组织：

```yaml
# 顶层 key: papers / industry / community
papers:
  - name: arXiv cs.AI          # 显示名称
    slug: arxiv-cs-ai          # 输出文件名（不含 .md）
    url: https://...            # RSS 地址（type: rss 时必填）
    verified: true              # true = 已验证可用

industry:
  - name: Anthropic
    slug: anthropic
    type: scrape                # 网页爬虫（默认 rss）
    verified: true
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 显示名称，出现在 journal 条目的来源标签中 |
| `slug` | 是 | 输出文件名（不含 .md），也是爬虫模块的匹配 key |
| `url` | `type: rss` 时 | RSS/Atom 地址 |
| `type` | 否 | `rss`（默认）或 `scrape` |
| `verified` | 是 | 只有 `true` 的源才会被拉取 |

## 添加新 RSS 源

1. 在 `feeds.yaml` 对应分类下添加条目，设 `verified: false`
2. 运行 `uv run scripts/daily_update.py --hours 1 --only <slug>` 验证
3. 确认无报错后改为 `verified: true`

## 添加新爬虫源

1. 在 `scrapers/` 下新建 `<slug>.py`（文件名 `snake_case`，SLUG 用 `kebab-case`）
2. 实现必需接口：

```python
NAME = "显示名称"           # str
SLUG = "kebab-slug"        # str，与 feeds.yaml 中的 slug 一致
CATEGORY = "industry"       # str，分类 key

def scrape(since=None) -> list[dict]:
    """
    返回条目列表。

    Args:
        since: datetime | None，只返回该时间之后的文章

    Returns:
        list[dict]，每个 dict 包含:
            - title: str
            - link: str
            - summary: str
            - published: str ("YYYY-MM-DD")
            - source: str (= NAME)
            - slug: str (= SLUG)
            - cat: str (= CATEGORY)
    """
```

3. 在 `feeds.yaml` 中登记（`type: scrape`）
4. 运行 `uv run scripts/daily_update.py --hours 1 --only <slug>` 验证

`scrapers/__init__.py` 会自动发现包内所有模块（`pkgutil.iter_modules`），按 `SLUG` 属性建立索引，无需手动注册。
