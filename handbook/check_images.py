"""Fails when a page in the built site points at an image or video that is not there (the strict build checks links only)."""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
missing = []
for page in site.rglob("*.html"):
    for ref in re.findall(r'(?:src|poster)="([^"#?]+)"', page.read_text(encoding="utf-8")):
        if ref.startswith(("http:", "https:", "data:", "//")) or not ref.endswith((".png", ".jpg", ".svg", ".mp4", ".webp", ".gif")):
            continue
        target = (site / ref.lstrip("/").removeprefix("langgraph-studio/")) if ref.startswith("/") else page.parent / unquote(ref)
        if not target.resolve().exists():
            missing.append(f"{page.relative_to(site)}: {ref}")
print("\n".join(missing) or "all images found")
sys.exit(1 if missing else 0)
