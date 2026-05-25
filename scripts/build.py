#!/usr/bin/env python3
"""
Build a single-file HTML bundle from the multi-file source.

Usage:
    python3 scripts/build.py            # produces dist/arrahman-discography.html
    python3 scripts/build.py --output custom.html
"""

import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
APP_JS = ROOT / "app.js"
INDEX_HTML = ROOT / "index.html"
DEFAULT_OUT = ROOT / "dist" / "arrahman-discography.html"

# Data files must be loaded in this order so SECTIONS can reference the arrays.
DATA_FILES = [
    "01-films.js",
    "02-nonfilm.js",
    "03-ads.js",
    "04-other.js",
    "05-videos.js",
    "index.js",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", default=str(DEFAULT_OUT),
        help="Output path for the bundled HTML"
    )
    args = parser.parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Read source files
    html = INDEX_HTML.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")
    data_blocks = []
    for fname in DATA_FILES:
        path = DATA_DIR / fname
        if not path.exists():
            print(f"ERROR: missing {path}", file=sys.stderr)
            sys.exit(1)
        data_blocks.append(f"// ----- {fname} -----\n{path.read_text(encoding='utf-8')}")

    # Build replacement block
    bundled = "<script>\n" + "\n\n".join(data_blocks) + "\n</script>\n<script>\n" + app_js + "\n</script>"

    # Find the script-tag block in index.html and replace it.
    # Use string operations (not regex) so we don't have to worry about backslash escaping.
    start_marker = "<!-- data files: edit any of these to add/remove entries -->"
    end_marker = '<script src="./app.js"></script>'
    start = html.find(start_marker)
    end = html.find(end_marker)
    if start == -1 or end == -1:
        print("ERROR: could not find script-tag block in index.html", file=sys.stderr)
        sys.exit(1)
    end += len(end_marker)

    bundled_html = html[:start] + bundled + html[end:]

    out_path.write_text(bundled_html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"✓ Built {out_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
