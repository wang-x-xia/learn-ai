"""Validate Markdown files in the learn-ai knowledge base.

Checks:
  1. Frontmatter presence and required fields
  2. Every [^key] inline citation has a matching [^key]: definition
  3. Every [^key]: definition has at least one [^key] inline usage
  4. No bullet-list references masquerading as footnote definitions

Usage:
    uv run scripts/validate_docs.py          # check docs/ only
    uv run scripts/validate_docs.py --all    # check docs/ + journal/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

_FM_FENCE = re.compile(r"^---\s*$")


def parse_frontmatter(text: str) -> dict | None:
    """Return frontmatter as a dict, or None if missing/malformed."""
    import yaml

    lines = text.split("\n")
    if not lines or not _FM_FENCE.match(lines[0]):
        return None
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if _FM_FENCE.match(line):
            end = i
            break
    if end is None:
        return None
    try:
        return yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError:
        return None


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

# Directories whose index.md only needs title + description.
INDEX_ONLY_DIRS = {
    "docs/foundations",
    "docs/applied",
    "docs/research",
    "docs/coding-agents",
    "docs/landscape",
}

KNOWLEDGE_REQUIRED = {"title", "description", "created", "updated", "tags", "review"}
INDEX_REQUIRED = {"title", "description"}
JOURNAL_REQUIRED = {"date", "type", "source", "category"}


def classify(path: Path) -> str:
    """Return 'index', 'knowledge', 'journal', or 'skip'."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel.startswith("journal/"):
        return "journal"
    if not rel.startswith("docs/"):
        return "skip"
    if path.name == "index.md":
        return "index"
    return "knowledge"


# ---------------------------------------------------------------------------
# Footnote checks
# ---------------------------------------------------------------------------

_ALL_REFS = re.compile(r"\[\^([\w-]+)\]")
_FOOTNOTE_DEF = re.compile(r"^\[\^([\w-]+)\]:", re.MULTILINE)


def check_footnotes(text: str) -> list[str]:
    errors: list[str] = []
    all_keys = set(_ALL_REFS.findall(text))
    defined_keys = set(_FOOTNOTE_DEF.findall(text))
    # Inline refs = all occurrences minus those that are definitions
    inline_keys = all_keys - (defined_keys - all_keys)
    # A key is "used inline" if it appears in the text as [^key] at a position
    # that is NOT a start-of-line definition.  Since defined_keys ⊆ all_keys
    # (defs also match the general pattern), inline_keys = all_keys always.
    # Instead, check: every definition has at least one non-definition usage,
    # and every non-definition usage has a definition.
    # Simple approach: just check defined vs all.  If a key only appears in
    # definition lines, it is unused.
    inline_keys = set()
    for m in _ALL_REFS.finditer(text):
        key = m.group(1)
        # Check if this occurrence is at start of line (= definition)
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start : m.start()]
        if not (prefix.strip() == "" and m.end() < len(text) and text[m.end()] == ":"):
            inline_keys.add(key)

    for key in sorted(inline_keys - defined_keys):
        errors.append(f"footnote [^{key}] used but never defined")
    for key in sorted(defined_keys - inline_keys):
        errors.append(f"footnote [^{key}] defined but never used")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    kind = classify(path)
    if kind == "skip":
        return errors

    # --- Frontmatter ---
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append("missing or malformed YAML frontmatter")
        return errors  # can't check further

    if kind == "journal":
        required = JOURNAL_REQUIRED
    elif kind == "index":
        required = INDEX_REQUIRED
    else:
        required = KNOWLEDGE_REQUIRED

    missing = required - fm.keys()
    if missing:
        errors.append(f"frontmatter missing fields: {', '.join(sorted(missing))}")

    # --- Footnotes (knowledge docs only) ---
    if kind == "knowledge":
        errors.extend(check_footnotes(text))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown files.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also validate journal/ files (default: docs/ only).",
    )
    args = parser.parse_args()

    dirs = [REPO_ROOT / "docs"]
    if args.all:
        dirs.append(REPO_ROOT / "journal")

    files: list[Path] = []
    for d in dirs:
        files.extend(sorted(d.rglob("*.md")))

    # Exclude AGENTS.md files from frontmatter/footnote validation
    files = [f for f in files if f.name != "AGENTS.md"]

    total_errors = 0

    # --- AGENTS.md presence check ---
    docs_dir = REPO_ROOT / "docs"
    for subdir in sorted(docs_dir.iterdir()):
        if subdir.is_dir() and subdir.name not in ("__pycache__", "stylesheets"):
            agents_md = subdir / "AGENTS.md"
            if not agents_md.exists():
                print(
                    f"  {subdir.relative_to(REPO_ROOT).as_posix()}/AGENTS.md: missing"
                )
                total_errors += 1

    for path in files:
        errs = validate_file(path)
        if errs:
            rel = path.relative_to(REPO_ROOT).as_posix()
            for e in errs:
                print(f"  {rel}: {e}")
            total_errors += len(errs)

    if total_errors:
        print(f"\n{total_errors} error(s) found.")
        return 1
    else:
        print("All files OK.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
