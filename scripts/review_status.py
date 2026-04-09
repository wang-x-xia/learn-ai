# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Show which docs need review.

A document needs review when:
  1. It has never been reviewed (review is empty/null)
  2. It was updated after the last review (updated > review)

Usage:
    uv run scripts/review_status.py            # default: all needing review
    uv run scripts/review_status.py --all      # show every doc with review status
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FM_FENCE_STR = "---"


def parse_frontmatter(text: str) -> dict | None:
    lines = text.split("\n")
    if not lines or lines[0].strip() != _FM_FENCE_STR:
        return None
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == _FM_FENCE_STR:
            end = i
            break
    if end is None:
        return None
    try:
        return yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError:
        return None


def to_date(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Collect docs
# ---------------------------------------------------------------------------

STATUS_NEVER = "never"       # never reviewed
STATUS_STALE = "stale"       # updated after last review
STATUS_OK = "ok"             # review >= updated


def collect(docs_dir: Path) -> list[dict]:
    results = []
    for path in sorted(docs_dir.rglob("*.md")):
        if path.name in ("index.md", "AGENTS.md"):
            continue
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            continue

        review_date = to_date(fm.get("review"))
        updated_date = to_date(fm.get("updated"))
        created_date = to_date(fm.get("created"))
        title = fm.get("title", path.stem)

        if review_date is None:
            status = STATUS_NEVER
        elif updated_date and updated_date > review_date:
            status = STATUS_STALE
        else:
            status = STATUS_OK

        results.append({
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "title": title,
            "updated": updated_date,
            "review": review_date,
            "status": status,
        })
    return results


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

_STATUS_LABEL = {
    STATUS_NEVER: "NEVER",
    STATUS_STALE: "STALE",
    STATUS_OK: "  ok ",
}


def print_table(docs: list[dict], show_all: bool) -> int:
    if not show_all:
        docs = [d for d in docs if d["status"] != STATUS_OK]

    if not docs:
        print("All docs are up to date!")
        return 0

    # Sort: never first, then stale (oldest review first), then ok
    order = {STATUS_NEVER: 0, STATUS_STALE: 1, STATUS_OK: 2}
    docs.sort(key=lambda d: (order[d["status"]], d.get("review") or date.min))

    # Column widths
    path_w = max(len(d["path"]) for d in docs)
    path_w = max(path_w, 4)

    print(f"{'Status':<7} {'Updated':<12} {'Reviewed':<12} {'Path':<{path_w}}  Title")
    print(f"{'------':<7} {'-------':<12} {'--------':<12} {'-' * path_w}  -----")

    need_review = 0
    for d in docs:
        status = _STATUS_LABEL[d["status"]]
        updated = str(d["updated"] or "—")
        review = str(d["review"] or "—")
        if d["status"] != STATUS_OK:
            need_review += 1
        print(f"{status:<7} {updated:<12} {review:<12} {d['path']:<{path_w}}  {d['title']}")

    print(f"\n{need_review} doc(s) need review, {len(docs) - need_review} up to date.")
    return need_review


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Show docs needing review.")
    parser.add_argument("--all", action="store_true", help="Show all docs, not just those needing review.")
    args = parser.parse_args()

    docs = collect(REPO_ROOT / "docs")
    need = print_table(docs, show_all=args.all)
    return 1 if need > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
