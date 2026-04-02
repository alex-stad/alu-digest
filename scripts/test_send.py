#!/usr/bin/env python3
"""
End-to-end test: renders a sample digest and creates a Buttondown draft.
Verifies the full rendering + API pipeline before the scheduled task goes live.

Usage:
    python3 scripts/test_send.py          # creates a draft (default, safe)
    python3 scripts/test_send.py --send   # sends to all subscribers (use with care)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Load .env file so BUTTONDOWN_API_KEY is available without manually exporting it
_env_file = REPO_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

from scripts.render_html import render_email
from scripts.send_email import send_digest, send_draft

SAMPLE_DIGEST = {
    "date": datetime.now().strftime("%A, %d %B %Y"),
    "lme_price": "$2,485/t",
    "lme_change": "+$12 (+0.5%)",
    "lme_change_positive": True,
    "ecdp_price": "$360\u2013390/t",
    "ecdp_change": "+$15",
    "ecdp_change_positive": True,
    "articles": [
        {
            "title": "Novelis Announces \u20ac300M Investment in G\u00f6ttingen Recycling Facility",
            "url": "https://www.alcircle.com/news/novelis-announces-300m-investment-gottingen-recycling-102345",
            "source": "AlCircle",
            "date": datetime.now().strftime("%d %b"),
            "category": "Novelis / Hindalco",
            "summary": (
                "Novelis has announced a \u20ac300 million expansion of its G\u00f6ttingen plant to double "
                "closed-loop aluminium recycling capacity by 2027. The investment supports the "
                "company's target of achieving 80% recycled content across its European operations."
            ),
        },
        {
            "title": "Constellium Reports Record Q4 Automotive Sheet Demand",
            "url": "https://www.fastmarkets.com/insights/constellium-q4-automotive-sheet-demand-2024",
            "source": "Fastmarkets",
            "date": datetime.now().strftime("%d %b"),
            "category": "Competitor",
            "summary": (
                "Constellium posted a 12% year-on-year increase in automotive sheet shipments "
                "in Q4 2024, driven by EV lightweighting demand across German OEMs. "
                "The company is expanding its Neuf-Brisach facility to meet growing demand."
            ),
        },
        {
            "title": "Aluminium Recycling Rates Hit Record 76% in EU, Report Finds",
            "url": "https://www.aluminiumtoday.com/news/eu-recycling-rates-record-76-percent-2024",
            "source": "Aluminium International Today",
            "date": datetime.now().strftime("%d %b"),
            "category": "Recycling & ESG",
            "summary": (
                "A new report from European Aluminium shows recycling rates for flat-rolled "
                "products reached 76% in 2024, up from 71% in 2022. The beverage can segment "
                "led with a 90% recycling rate, reinforcing the closed-loop narrative central "
                "to Novelis's sustainability strategy."
            ),
        },
        {
            "title": "EU CBAM Aluminium Compliance: First Declarant Fines Issued",
            "url": "https://www.reuters.com/business/eu-cbam-aluminium-compliance-first-fines-2024-03",
            "source": "Reuters",
            "date": datetime.now().strftime("%d %b"),
            "category": "Trade Policy",
            "summary": (
                "The European Commission issued its first CBAM non-compliance fines totalling "
                "\u20ac4.2 million to aluminium importers who failed to submit 2024 transition period "
                "reports. Industry bodies warn the full mechanism in 2026 will add \u20ac180\u2013220/t to "
                "primary aluminium import costs."
            ),
        },
        {
            "title": "LME Aluminium Climbs on Tight Scrap Supply and Dollar Weakness",
            "url": "https://www.metalbulletin.com/article/lme-aluminium-scrap-supply-dollar-weakness-2024",
            "source": "Metal Bulletin",
            "date": datetime.now().strftime("%d %b"),
            "category": "Market Data",
            "summary": (
                "LME three-month aluminium rose $18 to $2,497/t as scrap availability tightened "
                "ahead of summer construction season in Europe. Analysts note that European P1020 "
                "premiums have widened to $175/t over LME, the highest since Q3 2023."
            ),
        },
    ],
    "archive_url": "https://alex-stad.github.io/alu-digest/",
}


def main():
    api_key = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not api_key:
        print("ERROR: Set BUTTONDOWN_API_KEY environment variable first.")
        print("       Or add it to .env in the project root.")
        sys.exit(1)

    send_live = "--send" in sys.argv

    print("Rendering HTML digest...")
    html = render_email(SAMPLE_DIGEST)

    # Save preview locally
    preview_path = REPO_ROOT / "output" / "preview_email.html"
    preview_path.parent.mkdir(exist_ok=True)
    preview_path.write_text(html, encoding="utf-8")
    print(f"Preview saved to: {preview_path}")

    subject = f"[TEST] Alex's Daily Alu Digest — {SAMPLE_DIGEST['date']}"

    if send_live:
        print("Sending test newsletter to ALL subscribers...")
        success = send_digest(html, subject)
    else:
        print("Creating draft in Buttondown (not sending to subscribers)...")
        success = send_draft(html, subject)

    if success:
        if send_live:
            print("\nTest passed. Check subscriber inboxes — the digest should arrive shortly.")
        else:
            print("\nDraft created. Check Buttondown dashboard to preview and optionally send.")
            print("To send to subscribers, re-run with: python3 scripts/test_send.py --send")
    else:
        print("\nTest FAILED. Check the error above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
