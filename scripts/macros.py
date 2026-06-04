"""Macros for Zensical/MkDocs site generation."""

from pathlib import Path

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class _ConfigLoader(yaml.SafeLoader):
    """YAML loader that tolerates unknown tags (``!ENV``, ``!!python/…``)."""


def _ignore_unknown(loader, _suffix, node):
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_scalar(node)


_ConfigLoader.add_multi_constructor("!", _ignore_unknown)
_ConfigLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/", _ignore_unknown
)


def define_env(env):
    """Define template macros available in Markdown files."""

    # Annotations for top-level nav sections (displayed as <br/>suffix)
    SECTION_ANNOTATIONS = {
        "基础理论": "what",
        "应用技术": "how",
        "研究、模型与产品": "reference",
    }

    SKIP_SECTIONS = {"首页"}

    @env.macro
    def nav_topology():
        """Generate mermaid topology graph from the nav configuration.

        Reads ``mkdocs.yml`` and produces a two-level mermaid ``graph TD``
        string.  Top-level sections that contain sub-sections (nested dicts
        with list values) are expanded; leaf sections get a ``click`` link to
        their index page.
        """
        with open(_PROJECT_ROOT / "mkdocs.yml", encoding="utf-8") as f:
            config = yaml.load(f, Loader=_ConfigLoader)  # noqa: S506
        nav = config["nav"]

        edges = ["graph TD"]
        click_lines = []
        style_lines = []

        # Root node
        edges.append("    A[Learn AI 知识库]")
        style_lines.append(
            "    style A fill:#FF5C77,stroke:#E84862,stroke-width:2px,color:#fff"
        )

        top_idx = 0
        for item in nav:
            if not isinstance(item, dict):
                continue
            name = next(iter(item))
            children = item[name]
            if name in SKIP_SECTIONS:
                continue

            top_idx += 1
            node = chr(ord("A") + top_idx)

            ann = SECTION_ANNOTATIONS.get(name)
            label = f"{name}<br/>{ann}" if ann else name
            edges.append(f"    A --> {node}[{label}]")
            style_lines.append(
                f"    style {node} fill:#FF8A9E,stroke:#E84862,stroke-width:1px"
            )

            # Collect sub-sections and the section's own index URL
            sub_sections = []
            index_url = None

            if isinstance(children, list):
                for child in children:
                    if isinstance(child, str) and child.endswith("index.md"):
                        index_url = child.rsplit("index.md", 1)[0]
                    elif isinstance(child, dict):
                        sub_name = next(iter(child))
                        sub_val = child[sub_name]
                        if isinstance(sub_val, list):
                            sub_url = None
                            for sc in sub_val:
                                if (
                                    isinstance(sc, str)
                                    and sc.endswith("index.md")
                                ):
                                    sub_url = sc.rsplit("index.md", 1)[0]
                                    break
                            sub_sections.append((sub_name, sub_url))

            if sub_sections:
                for i, (sub_name, sub_url) in enumerate(sub_sections, 1):
                    sub_node = f"{node}{i}"
                    edges.append(f"    {node} --> {sub_node}[{sub_name}]")
                    if sub_url:
                        click_lines.append(
                            f'    click {sub_node} href "{sub_url}"'
                        )
            elif index_url:
                click_lines.append(f'    click {node} href "{index_url}"')

        parts = ["\n".join(edges)]
        if click_lines:
            parts.append("\n".join(click_lines))
        if style_lines:
            parts.append("\n".join(style_lines))
        mermaid_body = "\n\n".join(parts)
        return f"```mermaid\n{mermaid_body}\n```"
