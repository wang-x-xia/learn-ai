"""Manage the reference/ document archive.

Commands:
    uv run reference/pdf_to_md.py convert <pdf-path> <slug>
        Convert a PDF to Markdown + images in reference/<slug>/

    uv run reference/pdf_to_md.py serve [--port PORT]
        Serve all reference documents as a local website (default port 8100)

Examples:
    uv run reference/pdf_to_md.py convert ~/downloads/paper.pdf my-paper
    uv run reference/pdf_to_md.py serve
    uv run reference/pdf_to_md.py serve --port 9000
"""

# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf4llm", "markdown"]
# ///

import re
import sys
from pathlib import Path

REF_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Convert
# ---------------------------------------------------------------------------


def cmd_convert(args: list[str]) -> None:
    if len(args) != 2:
        print("Usage: uv run reference/pdf_to_md.py convert <pdf-path> <slug>")
        sys.exit(1)

    pdf_path = Path(args[0])
    slug = args[1]

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    out_dir = REF_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    image_path = str(out_dir) + "/"
    out_file = out_dir / "index.md"

    import pymupdf4llm

    print(f"Converting {pdf_path} ...")
    md = pymupdf4llm.to_markdown(
        str(pdf_path),
        write_images=True,
        image_path=image_path,
        image_format="png",
        image_size_limit=0.01,
    )

    md = md.replace(image_path, "")
    md = re.sub(r"\n\d{1,3} \n", "\n", md)

    out_file.write_text(md, encoding="utf-8")

    img_count = len(list(out_dir.glob("*.png")))
    print(f"Done: {out_file} ({len(md):,} chars, {img_count} images)")


# ---------------------------------------------------------------------------
# Serve
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --bg: #fff; --fg: #222; --muted: #666; --border: #e0e0e0;
           --code-bg: #f5f5f5; --link: #1a73e8; --max-w: 960px; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #1e1e1e; --fg: #d4d4d4; --muted: #999; --border: #444;
             --code-bg: #2d2d2d; --link: #6cb6ff; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
          max-width: var(--max-w); margin: 0 auto; padding: 2rem 1.5rem;
          background: var(--bg); color: var(--fg); line-height: 1.7; }}
  a {{ color: var(--link); }}
  img {{ max-width: 100%; height: auto; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  th, td {{ border: 1px solid var(--border); padding: .5em .8em; text-align: left; }}
  th {{ background: var(--code-bg); }}
  code {{ background: var(--code-bg); padding: .15em .3em; border-radius: 3px;
          font-size: .9em; }}
  pre {{ background: var(--code-bg); padding: 1em; overflow-x: auto;
         border-radius: 6px; }}
  pre code {{ background: none; padding: 0; }}
  blockquote {{ border-left: 4px solid var(--border); margin-left: 0;
                padding-left: 1em; color: var(--muted); }}
  h1 {{ border-bottom: 2px solid var(--border); padding-bottom: .3em; }}
  .breadcrumb {{ margin-bottom: 1.5em; color: var(--muted); font-size: .9em; }}
  .breadcrumb a {{ color: var(--link); text-decoration: none; }}
  .card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 1rem; }}
  .card {{ border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem;
           transition: box-shadow .15s; }}
  .card:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
  .card h3 {{ margin: 0 0 .3em; }}
  .card p {{ margin: 0; color: var(--muted); font-size: .9em; }}
  .card a {{ text-decoration: none; }}
</style>
</head>
<body>
{breadcrumb}
{body}
</body>
</html>
"""


def _discover_docs() -> list[dict]:
    """Find all reference documents (directories with index.md)."""
    docs = []
    for d in sorted(REF_DIR.iterdir()):
        idx = d / "index.md"
        if d.is_dir() and idx.exists():
            # Extract title from first H1
            text = idx.read_text(encoding="utf-8")
            m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
            title = m.group(1).strip() if m else d.name
            img_count = len(list(d.glob("*.png")))
            line_count = text.count("\n")
            docs.append(
                {"slug": d.name, "title": title, "images": img_count, "lines": line_count}
            )
    return docs


def _render_index(docs: list[dict]) -> str:
    cards = []
    for doc in docs:
        cards.append(
            f'<div class="card"><h3><a href="/{doc["slug"]}/">{doc["title"]}</a></h3>'
            f'<p>{doc["lines"]:,} lines, {doc["images"]} images</p></div>'
        )
    body = "<h1>Reference Documents</h1>\n<div class=\"card-grid\">\n" + "\n".join(cards) + "\n</div>"
    return HTML_TEMPLATE.format(title="Reference", breadcrumb="", body=body)


def _render_doc(slug: str) -> str | None:
    idx = REF_DIR / slug / "index.md"
    if not idx.exists():
        return None

    import markdown

    text = idx.read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "footnotes"])
    html_body = md.convert(text)

    m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    title = m.group(1).strip() if m else slug

    breadcrumb = '<div class="breadcrumb"><a href="/">Reference</a> / {}</div>'.format(title)
    return HTML_TEMPLATE.format(title=title, breadcrumb=breadcrumb, body=html_body)


def cmd_serve(args: list[str]) -> None:
    port = 8100
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        else:
            i += 1

    import http.server

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = self.path.split("?")[0].rstrip("/") or "/"

            # Index page
            if path == "/":
                html = _render_index(_discover_docs())
                self._send(html.encode(), "text/html")
                return

            parts = path.strip("/").split("/")
            slug = parts[0]
            doc_dir = REF_DIR / slug

            # Image / static file
            if len(parts) >= 2:
                file_path = doc_dir / "/".join(parts[1:])
                if file_path.exists() and file_path.is_file():
                    suffix = file_path.suffix.lower()
                    ct = {
                        ".png": "image/png", ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg", ".gif": "image/gif",
                        ".svg": "image/svg+xml", ".pdf": "application/pdf",
                    }.get(suffix, "application/octet-stream")
                    self._send(file_path.read_bytes(), ct)
                    return

            # Document page
            html = _render_doc(slug)
            if html:
                self._send(html.encode(), "text/html")
                return

            self.send_error(404)

        def _send(self, data: bytes, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: object) -> None:
            # Quieter logging
            sys.stderr.write(f"  {args[0]}\n")

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving reference docs at http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd == "convert":
        cmd_convert(rest)
    elif cmd == "serve":
        cmd_serve(rest)
    else:
        # Backward compat: treat as convert if first arg looks like a file
        if Path(cmd).exists() and len(rest) == 1:
            cmd_convert([cmd] + rest)
        else:
            print(__doc__.strip())
            sys.exit(1)


if __name__ == "__main__":
    main()
