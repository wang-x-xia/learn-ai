"""
anthropic.py — 爬取 Anthropic News 页面。

目标页面: https://www.anthropic.com/news
提取所有 /news/<slug> 格式的文章链接。
"""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

NAME = "Anthropic"
SLUG = "anthropic"
CATEGORY = "industry"

_URL = "https://www.anthropic.com/news"
_LINK_RE = re.compile(r"^/news/[\w-]+$")
_CTA_RE = re.compile(r"^(Read more|Learn more|See more|View more|View)$", re.IGNORECASE)
_HEADERS = {"User-Agent": "Mozilla/5.0 learn-ai-bot"}


def scrape() -> list[dict]:
    """爬取 Anthropic News，返回条目列表。"""
    resp = httpx.get(_URL, follow_redirects=True, timeout=30, headers=_HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 收集每个匹配链接对应的最佳标题
    # 策略：过滤 CTA 文本 → 选最长的（最可能是真实标题）
    best: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not _LINK_RE.match(href):
            continue
        text = a.get_text(" ", strip=True)
        if len(text) < 4 or _CTA_RE.match(text):
            continue
        prev = best.get(href, "")
        if not prev or (len(text) > len(prev) and len(text) <= 200):
            best[href] = text

    entries: list[dict] = []
    for href, title in best.items():
        link = f"https://www.anthropic.com{href}"
        entries.append({
            "title": title,
            "link": link,
            "summary": "",
            "source": NAME,
            "slug": SLUG,
            "cat": CATEGORY,
        })
    return entries
