"""MkDocs hooks for dynamic content generation.

This file is loaded by MkDocs via the 'hooks' configuration in mkdocs.yml.
"""

from pathlib import Path

DOCS_DIR = Path(__file__).parent
CHANGELOG_PATH = DOCS_DIR / "changelog.yaml"


def on_page_markdown(markdown: str, page, **kwargs) -> str:
    """Inject the '最近更新' section into the homepage.

    This hook runs for every page. We only modify the homepage (index.md).
    """
    # Only process the root homepage (index.md in docs/)
    if page.file.name != "index" or page.file.src_uri != "index.md":
        return markdown

    # Load changelog entries
    import yaml

    if not CHANGELOG_PATH.exists():
        return markdown

    try:
        data = yaml.safe_load(CHANGELOG_PATH.read_text(encoding="utf-8"))
        if not data or "entries" not in data:
            return markdown
        entries = data["entries"]
    except yaml.YAMLError:
        return markdown

    # Generate recent updates section
    if not entries:
        recent_updates_md = "## 最近更新\n\n暂无更新记录。\n"
    else:
        # Sort by date (most recent first) and take limit
        sorted_entries = sorted(entries, key=lambda x: x["date"], reverse=True)[:5]

        lines = ["## 最近更新", "", '<div class="grid cards" markdown>', ""]

        for entry in sorted_entries:
            date = entry["date"]
            title = entry["title"]
            description = entry["description"]
            link = entry.get("link")

            # Format title with link if available
            if link:
                title_md = f"[{title}]({link})"
            else:
                title_md = title

            lines.append(f"- **{date} — {title_md}**")
            lines.append("")
            lines.append(f"    {description}")
            lines.append("")

        lines.append("</div>")
        lines.append("")
        recent_updates_md = "\n".join(lines)

    # Insert before "## 知识体系" (exact line match)
    lines = markdown.split("\n")
    for i, line in enumerate(lines):
        if line == "## 知识体系":
            lines.insert(i, recent_updates_md.rstrip())
            lines.insert(i + 1, "---")
            lines.insert(i + 2, "")
            return "\n".join(lines)

    return markdown
