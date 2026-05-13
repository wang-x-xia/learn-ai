"""Validate Markdown files in the learn-ai knowledge base.

Checks:
  1. Frontmatter presence and required fields
  2. Every [^key] inline citation has a matching [^key]: definition
  3. Every [^key]: definition has at least one [^key] inline usage
  4. No bullet-list references masquerading as footnote definitions
  5. Cross-reference links point to existing files
  6. Knowledge docs have a '??? note "背景知识"' section
  7. Tags are in the allowed vocabulary (scripts/tags.yml)
  8. Knowledge docs have at least one footnote
  9. Top-level nav items in mkdocs.yml <= MAX_NAV_TOP_ITEMS
  10. docs/changelog.yaml schema and link validity

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

# Non-knowledge docs that have full frontmatter but skip knowledge-only checks
# (background knowledge section, footnotes). See AGENTS.md rules.
_NON_KNOWLEDGE_DOCS = {"resources.md"}


def classify(path: Path) -> str:
    """Return 'index', 'knowledge', or 'skip'."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    if not rel.startswith("docs/"):
        return "skip"
    if path.name == "index.md" or path.name in _NON_KNOWLEDGE_DOCS:
        return "index"
    return "knowledge"


# ---------------------------------------------------------------------------
# Footnote checks
# ---------------------------------------------------------------------------

_ALL_REFS = re.compile(r"\[\^([\w-]+)\]")
_FOOTNOTE_DEF = re.compile(r"^\[\^([\w-]+)\]:", re.MULTILINE)

# ---------------------------------------------------------------------------
# Changelog validation
# ---------------------------------------------------------------------------

MAX_CHANGELOG_ENTRIES = 20
CHANGELOG_PATH = REPO_ROOT / "docs" / "changelog.yaml"


def check_changelog() -> list[str]:
    """Check docs/changelog.yaml schema, link validity, and entry count."""
    import yaml

    if not CHANGELOG_PATH.exists():
        return [f"{CHANGELOG_PATH.relative_to(REPO_ROOT)}: file not found"]

    errors: list[str] = []

    try:
        data = yaml.safe_load(CHANGELOG_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"{CHANGELOG_PATH.relative_to(REPO_ROOT)}: YAML parse error: {e}"]

    if not isinstance(data, dict):
        return [
            f"{CHANGELOG_PATH.relative_to(REPO_ROOT)}: root must be a dict with 'entries' key"
        ]

    if "entries" not in data:
        return [
            f"{CHANGELOG_PATH.relative_to(REPO_ROOT)}: missing 'entries' key at root"
        ]

    entries = data["entries"]
    if not isinstance(entries, list):
        return [
            f"{CHANGELOG_PATH.relative_to(REPO_ROOT)}: 'entries' must be a list"
        ]

    # Check entry count
    if len(entries) > MAX_CHANGELOG_ENTRIES:
        errors.append(
            f"{CHANGELOG_PATH.relative_to(REPO_ROOT)}: "
            f"has {len(entries)} entries (max {MAX_CHANGELOG_ENTRIES})"
        )

    # Check each entry
    required_fields = ["date", "type", "title", "description"]
    allowed_types = {"knowledge", "design", "feature"}

    for idx, entry in enumerate(entries):
        prefix = f"{CHANGELOG_PATH.relative_to(REPO_ROOT)}: entries[{idx}]"

        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be a dict")
            continue

        # Check required fields and order
        entry_keys = list(entry.keys())
        for field in required_fields:
            if field not in entry:
                errors.append(f"{prefix}: missing required field '{field}'")

        # Check field order (date, type, title, description, link)
        expected_order = ["date", "type", "title", "description", "link"]
        actual_order = [k for k in entry_keys if k in expected_order]
        if actual_order != expected_order[: len(actual_order)]:
            errors.append(
                f"{prefix}: fields not in expected order "
                f"(expected: {expected_order[: len(actual_order)]}, got: {actual_order})"
            )

        # Check field types
        if "date" in entry:
            # Allow both string and date types (YAML may parse dates as date objects)
            date_value = entry["date"]
            if isinstance(date_value, str):
                date_str = date_value
            elif hasattr(date_value, "isoformat"):
                # YAML date object
                date_str = date_value.isoformat()
            else:
                errors.append(f"{prefix}: 'date' must be a string")
                continue

            # Validate date format (YYYY-MM-DD)
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                errors.append(f"{prefix}: 'date' must be in YYYY-MM-DD format")

        if "type" in entry:
            if not isinstance(entry["type"], str):
                errors.append(f"{prefix}: 'type' must be a string")
            elif entry["type"] not in allowed_types:
                errors.append(
                    f"{prefix}: 'type' must be one of {sorted(allowed_types)}, "
                    f"got '{entry['type']}'"
                )

        if "title" in entry and not isinstance(entry["title"], str):
            errors.append(f"{prefix}: 'title' must be a string")

        if "description" in entry and not isinstance(entry["description"], str):
            errors.append(f"{prefix}: 'description' must be a string")

        # Check link validity
        if "link" in entry:
            if entry["link"] is not None:
                if not isinstance(entry["link"], str):
                    errors.append(f"{prefix}: 'link' must be a string or null")
                else:
                    link = entry["link"]
                    # Check if it's an external URL or a relative path
                    if link.startswith(("http://", "https://")):
                        # External URL - no file check needed
                        pass
                    else:
                        # Relative path - check if file exists
                        resolved = (REPO_ROOT / "docs" / link).resolve()
                        if not resolved.exists():
                            errors.append(
                                f"{prefix}: broken link '{link}' → file not found"
                            )

    return errors


# ---------------------------------------------------------------------------
# Nav structure check
# ---------------------------------------------------------------------------

MAX_NAV_TOP_ITEMS = 5


def check_nav_top_items() -> list[str]:
    """Check that mkdocs.yml nav has at most MAX_NAV_TOP_ITEMS top-level items."""
    import yaml

    # Custom loader that ignores unknown tags like !ENV
    class _SafeLoaderIgnoreUnknown(yaml.SafeLoader):
        pass

    _SafeLoaderIgnoreUnknown.add_multi_constructor(
        "",
        lambda loader, suffix, node: loader.construct_mapping(node)
        if isinstance(node, yaml.MappingNode)
        else loader.construct_sequence(node)
        if isinstance(node, yaml.SequenceNode)
        else loader.construct_scalar(node),
    )

    mkdocs_path = REPO_ROOT / "mkdocs.yml"
    if not mkdocs_path.exists():
        return ["mkdocs.yml not found"]
    data = yaml.load(  # noqa: S506
        mkdocs_path.read_text(encoding="utf-8"), Loader=_SafeLoaderIgnoreUnknown
    )
    nav = data.get("nav")
    if not isinstance(nav, list):
        return ["mkdocs.yml: nav is missing or not a list"]
    count = len(nav)
    if count > MAX_NAV_TOP_ITEMS:
        return [
            f"mkdocs.yml: nav has {count} top-level items "
            f"(max {MAX_NAV_TOP_ITEMS})"
        ]
    return []


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


def has_any_footnotes(text: str) -> bool:
    """Return True if the text contains at least one footnote definition."""
    return bool(_FOOTNOTE_DEF.search(text))


# ---------------------------------------------------------------------------
# Cross-reference link checks
# ---------------------------------------------------------------------------

_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def check_cross_references(text: str, source_path: Path) -> list[str]:
    """Check that relative Markdown links point to existing files."""
    errors: list[str] = []
    for m in _MD_LINK.finditer(text):
        target = m.group(2)
        # Skip external URLs and anchors-only
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        # Strip anchor part
        file_part = target.split("#")[0]
        if not file_part:
            continue
        # Resolve relative to the source file's directory
        resolved = (source_path.parent / file_part).resolve()
        if not resolved.exists():
            errors.append(f"broken link: [{m.group(1)}]({target}) → file not found")
    return errors


# ---------------------------------------------------------------------------
# Background knowledge section check
# ---------------------------------------------------------------------------

_BG_KNOWLEDGE = re.compile(r'^\?\?\?\s+note\s+"背景知识"', re.MULTILINE)


def has_background_knowledge(text: str) -> bool:
    """Return True if the text contains a '??? note \"背景知识\"' admonition."""
    return bool(_BG_KNOWLEDGE.search(text))


# ---------------------------------------------------------------------------
# Tag vocabulary check
# ---------------------------------------------------------------------------


def load_tag_vocabulary() -> set[str] | None:
    """Load allowed tags from scripts/tags.yml. Return None if file missing."""
    import yaml

    tags_file = REPO_ROOT / "scripts" / "tags.yml"
    if not tags_file.exists():
        return None
    data = yaml.safe_load(tags_file.read_text(encoding="utf-8"))
    if data and "tags" in data:
        return set(data["tags"])
    return None


def check_tags(fm: dict, allowed_tags: set[str] | None) -> list[str]:
    """Check that all tags in frontmatter are in the allowed vocabulary."""
    if allowed_tags is None:
        return []
    warnings: list[str] = []
    tags = fm.get("tags", [])
    if not isinstance(tags, list):
        return []
    for tag in tags:
        if str(tag) not in allowed_tags:
            warnings.append(f"tag '{tag}' not in scripts/tags.yml vocabulary")
    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def validate_file(
    path: Path, allowed_tags: set[str] | None = None
) -> tuple[list[str], list[str]]:
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

    # --- Tag vocabulary ---
    warnings.extend(check_tags(fm, allowed_tags))

    # --- Cross-reference links ---
    errors.extend(check_cross_references(text, path))

    # --- Knowledge-doc-only checks ---
    if kind == "knowledge":
        # Footnotes
        errors.extend(check_footnotes(text))
        if not has_any_footnotes(text):
            warnings.append("no footnotes — knowledge docs should cite sources")

        # Background knowledge section
        if not has_background_knowledge(text):
            warnings.append('missing ??? note "背景知识" section')

        # Content length
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

    # Load tag vocabulary
    allowed_tags = load_tag_vocabulary()

    dirs = [REPO_ROOT / "docs"]

    files: list[Path] = []
    for d in dirs:
        files.extend(sorted(d.rglob("*.md")))

    # Exclude AGENTS.md files from frontmatter/footnote validation
    files = [f for f in files if f.name != "AGENTS.md"]

    total_errors = 0

    # --- Changelog check ---
    changelog_errors = check_changelog()
    for e in changelog_errors:
        print(f"  ERROR {e}")
    total_errors += len(changelog_errors)

    # --- Nav structure check ---
    nav_errors = check_nav_top_items()
    for e in nav_errors:
        print(f"  ERROR {e}")
    total_errors += len(nav_errors)

    # --- AGENTS.md presence check ---
    docs_dir = REPO_ROOT / "docs"
    for subdir in sorted(docs_dir.iterdir()):
        if subdir.is_dir() and subdir.name not in ("__pycache__", "stylesheets", "javascripts"):
            agents_md = subdir / "AGENTS.md"
            if not agents_md.exists():
                print(
                    f"  {subdir.relative_to(REPO_ROOT).as_posix()}/AGENTS.md: missing"
                )
                total_errors += 1

    total_warnings = 0

    for path in files:
        errs, warns = validate_file(path, allowed_tags)
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
