#!/usr/bin/env python3
"""
Updates the GitHub Pages archive index.html with a new digest entry.
Called from the scheduled task after publishing a new digest.

Usage:
    python3 scripts/update_archive_index.py --date-slug 2025-03-20 [--lead "Headline"]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


def date_slug_to_display(slug: str) -> str:
    dt = datetime.strptime(slug, "%Y-%m-%d")
    return dt.strftime("%A, %d %B %Y")


def load_entries(index_file: Path) -> list:
    data_file = index_file.parent / "entries.json"
    if data_file.exists():
        return json.loads(data_file.read_text())
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date-slug", required=True, help="e.g. 2025-03-20")
    parser.add_argument("--lead", default="", help="Lead headline for the index")
    args = parser.parse_args()

    date_slug = args.date_slug
    date_display = date_slug_to_display(date_slug)

    # Load existing entries
    entries_file = REPO_ROOT / "entries.json"
    entries = []
    if entries_file.exists():
        try:
            entries = json.loads(entries_file.read_text())
        except Exception:
            entries = []

    # Add new entry at front (newest first), avoid duplicates
    entries = [e for e in entries if e.get("date_slug") != date_slug]
    entries.insert(0, {
        "date_slug": date_slug,
        "date_display": date_display,
        "lead_headline": args.lead,
    })

    # Keep last 90 entries
    entries = entries[:90]
    entries_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

    # Render index.html
    from scripts.render_html import render_archive_index
    index_html = render_archive_index(entries)
    index_file = REPO_ROOT / "index.html"
    index_file.write_text(index_html, encoding="utf-8")
    print(f"Archive index updated: {len(entries)} entries")


if __name__ == "__main__":
    main()
