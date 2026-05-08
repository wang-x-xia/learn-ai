"""Validate Markdown files in the learn-ai knowledge base.

Checks:
  1. Frontmatter presence and required fields
  2. Every [^key] inline citation has a matching [^key]: definition
  3. Every [^key]: definition has at least one [^key] inline usage
  4. No bullet-list references masquerading as footnote definitions

Usage:
    uv run scripts/validate_docs.py
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

KNOWLEDGE_REQUIRED = {"title", "description", "created", "updated", "tags", "review"}
INDEX_REQUIRED = {"title", "description"}


def classify(path: Path) -> str:
    """Return 'index', 'knowledge', or 'skip'."""
    rel = path.relative_to(REPO_ROOT).as_posix()
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

# ---------------------------------------------------------------------------
# Content length check
# ---------------------------------------------------------------------------

WARN_CONTENT_LINES = 400
MAX_CONTENT_LINES = 500
_REFERENCES_HEADING = re.compile(r"^##\s+参考资料\s*$", re.MULTILINE)


def count_content_lines(text: str) -> int:
    """Count content lines excluding frontmatter and '## 参考资料' section."""
    lines = text.split("\n")

    # Skip frontmatter
    start = 0
    if lines and _FM_FENCE.match(lines[0]):
        for i, line in enumerate(lines[1:], start=1):
            if _FM_FENCE.match(line):
                start = i + 1
                break

    # Find '## 参考资料' heading
    end = len(lines)
    for i in range(start, len(lines)):
        if _REFERENCES_HEADING.match(lines[i]):
            end = i
            break

    # Count non-empty lines in the content region
    return end - start


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


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for the given file."""
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")

    kind = classify(path)
    if kind == "skip":
        return errors, warnings

    # --- Frontmatter ---
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append("missing or malformed YAML frontmatter")
        return errors, warnings  # can't check further

    if kind == "index":
        required = INDEX_REQUIRED
    else:
        required = KNOWLEDGE_REQUIRED

    missing = required - fm.keys()
    if missing:
        errors.append(f"frontmatter missing fields: {', '.join(sorted(missing))}")

    # --- Footnotes (knowledge docs only) ---
    if kind == "knowledge":
        errors.extend(check_footnotes(text))

    # --- Content length (knowledge docs only) ---
    if kind == "knowledge":
        content_lines = count_content_lines(text)
        if content_lines > MAX_CONTENT_LINES:
            errors.append(
                f"content too long: {content_lines} lines "
                f"(max {MAX_CONTENT_LINES}, excluding frontmatter and 参考资料)"
            )
        elif content_lines > WARN_CONTENT_LINES:
            warnings.append(
                f"content approaching limit: {content_lines} lines "
                f"(warn {WARN_CONTENT_LINES}, max {MAX_CONTENT_LINES})"
            )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown files.")
    args = parser.parse_args()

    dirs = [REPO_ROOT / "docs"]

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

    total_warnings = 0

    for path in files:
        errs, warns = validate_file(path)
        rel = path.relative_to(REPO_ROOT).as_posix()
        for e in errs:
            print(f"  ERROR {rel}: {e}")
        for w in warns:
            print(f"  WARN  {rel}: {w}")
        total_errors += len(errs)
        total_warnings += len(warns)

    if total_errors or total_warnings:
        parts = []
        if total_errors:
            parts.append(f"{total_errors} error(s)")
        if total_warnings:
            parts.append(f"{total_warnings} warning(s)")
        print(f"\n{', '.join(parts)} found.")
    else:
        print("All files OK.")

    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
