"""
daily_update.py — 拉取 AI 社区 RSS + 网页爬虫，写入 journal 原始素材。

用法:
    uv run scripts/daily_update.py                    # 拉取过去 48h
    uv run scripts/daily_update.py --hours 24         # 拉取过去 24h
    uv run scripts/daily_update.py --only simon-willison  # 只拉取指定源

输出:
    journal/YYYY/MM/DD/<source>.md  — 每个订阅源一个文件

RSS 源配置在 feeds.yaml；网页爬虫在 scrapers/ 目录下，每个网站一个脚本。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import io
import re
import sys
import textwrap
from pathlib import Path

# Windows 控制台默认编码不支持中文，强制使用 UTF-8
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import yaml
import feedparser

# 爬虫模块（每个网站一个独立脚本）
from scrapers import run_scraper

REPO_ROOT = Path(__file__).resolve().parent.parent
FEEDS_FILE = REPO_ROOT / "scripts" / "feeds.yaml"
JOURNAL_DIR = REPO_ROOT / "journal"

TODAY = dt.date.today()

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """去除 HTML 标签，反转义。"""
    return html.unescape(TAG_RE.sub("", text)).strip()


# ──────────────────────────────────────────────
# 拉取
# ──────────────────────────────────────────────
def fetch_feed(cfg: dict, since: dt.datetime) -> list[dict]:
    entries: list[dict] = []
    try:
        parsed = feedparser.parse(cfg["url"])
        for e in parsed.entries[:30]:
            pub = None
            for attr in ("published_parsed", "updated_parsed"):
                ts = getattr(e, attr, None)
                if ts:
                    pub = dt.datetime(*ts[:6])
                    break
            if pub and pub < since:
                continue
            summary = strip_html(getattr(e, "summary", ""))[:200]
            entries.append({
                "title": getattr(e, "title", "Untitled").strip(),
                "link": getattr(e, "link", ""),
                "summary": summary,
                "published": pub.strftime("%Y-%m-%d") if pub else "",
                "source": cfg["name"],
                "slug": cfg["slug"],
                "cat": cfg["cat"],
            })
    except Exception as exc:
        print(f"  [WARN] {cfg['name']}: {exc}")
    return entries


def load_feeds() -> list[dict]:
    """从 feeds.yaml 加载订阅源列表（只加载 verified: true 的）。"""
    with open(FEEDS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    feeds: list[dict] = []
    for cat, items in data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not item.get("verified", False):
                continue
            feeds.append({
                "name": item["name"],
                "slug": item["slug"],
                "url": item.get("url", ""),
                "cat": cat,
                "type": item.get("type", "rss"),
            })
    return feeds


def fetch_all(since: dt.datetime, only: str | None = None) -> list[dict]:
    """拉取 RSS 源 + 爬虫，返回汇总条目。

    Args:
        since: 只返回该时间之后的条目。
        only: 若指定，只拉取 slug 匹配的那一个源。
    """
    feeds = load_feeds()
    if only:
        feeds = [f for f in feeds if f["slug"] == only]
        if not feeds:
            print(f"  [ERROR] 未找到 slug={only!r} 的订阅源")
            return []
    all_entries: list[dict] = []
    for cfg in feeds:
        print(f"  {cfg['name']} ...", end=" ", flush=True)
        if cfg["type"] == "scrape":
            items = run_scraper(cfg, since=since)
        else:
            items = fetch_feed(cfg, since)
        all_entries.extend(items)
        print(f"{len(items)} 条")
    return all_entries


# ──────────────────────────────────────────────
# 格式化
# ──────────────────────────────────────────────
CAT_LABELS = {
    "papers": "论文",
    "industry": "厂商动态",
    "community": "社区",
}


def format_source_entries(entries: list[dict]) -> str:
    """格式化单个订阅源的条目列表。"""
    lines: list[str] = []
    for e in entries:
        date_tag = f"[{e['published']}] " if e.get("published") else ""
        line = f"- {date_tag}**{e['title']}**"
        if e["summary"]:
            line += f" — {e['summary']}"
        if e["link"]:
            line += f"  \n  {e['link']}"
        lines.append(line)
    return "\n".join(lines)


def group_by_source(entries: list[dict]) -> dict[str, list[dict]]:
    """按订阅源 slug 分组。"""
    by_slug: dict[str, list[dict]] = {}
    for e in entries:
        by_slug.setdefault(e["slug"], []).append(e)
    return by_slug


# ──────────────────────────────────────────────
# 写入
# ──────────────────────────────────────────────
def write_journal(date: dt.date, entries: list[dict]) -> list[Path]:
    """按订阅源拆分，每个源写一个文件到 journal/YYYY/MM/DD/<slug>.md。"""
    day_dir = JOURNAL_DIR / str(date.year) / f"{date.month:02d}" / f"{date.day:02d}"
    day_dir.mkdir(parents=True, exist_ok=True)

    by_slug = group_by_source(entries)
    written: list[Path] = []

    for slug, items in by_slug.items():
        source_name = items[0]["source"]
        cat = items[0]["cat"]
        cat_label = CAT_LABELS.get(cat, cat)
        body = format_source_entries(items)

        content = textwrap.dedent(f"""\
            ---
            date: {date.isoformat()}
            type: daily
            source: {source_name}
            category: {cat_label}
            ---

            # {source_name}

        """)
        content += body + "\n"

        p = day_dir / f"{slug}.md"
        p.write_text(content, encoding="utf-8")
        written.append(p)

    return written


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="拉取 AI RSS 写入 journal")
    ap.add_argument("--hours", type=int, default=48, help="回溯小时数 (默认 48)")
    ap.add_argument("--only", type=str, default=None,
                    help="只拉取指定 slug 的订阅源，如 simon-willison")
    args = ap.parse_args()

    since = dt.datetime.now() - dt.timedelta(hours=args.hours)
    print(f"[{TODAY}] 拉取过去 {args.hours}h ...\n")

    entries = fetch_all(since, only=args.only)
    total = len(entries)
    print(f"\n共 {total} 条\n")

    if not entries:
        print("无新条目。")
        return

    paths = write_journal(TODAY, entries)
    for p in paths:
        print(f"  => {p}")
    print(f"\n共写入 {len(paths)} 个文件")


if __name__ == "__main__":
    main()
