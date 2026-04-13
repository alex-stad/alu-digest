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
    "date": "Friday, 10 April 2026",
    "lme_price": "$3,526/t",
    "lme_change": "+$31.50 (+0.90%)",
    "lme_change_positive": True,
    "ecdp_price": "$583/t",
    "ecdp_change": "+$5 (+0.90%)",
    "ecdp_change_positive": True,
    "articles": [
        {
            "title": "Ten Novelis plants achieve new level of manufacturing maturity",
            "url": "https://www.prnewswire.com/news-releases/ten-novelis-plants-achieve-new-level-of-manufacturing-maturity-302738332.html",
            "source": "PR Newswire",
            "date": "9 Apr",
            "category": "Novelis / Hindalco",
            "summary": (
                "Ten of Novelis's 29 manufacturing plants achieved Level 1 certification in the "
                "Novelis Operating System (NOS) by the end of fiscal year 2026. Novelis plans to "
                "advance all 29 facilities through four progressive NOS certification levels to "
                "strengthen operational reliability and service consistency globally."
            ),
            "novelis_angle": None,
        },
        {
            "title": "Aluminium stock surge prompts JPMorgan's bullish call on Vedanta, Hindalco",
            "url": "https://www.alcircle.com/news/aluminium-stock-surge-prompts-jpmorgans-bullish-call-on-vedanta-hindalco-117943",
            "source": "AlCircle",
            "date": "8 Apr",
            "category": "Novelis / Hindalco",
            "summary": (
                "JPMorgan upgraded Hindalco Industries to 'overweight' on 7 April, raising its "
                "price target from INR 875 to INR 1,125, citing improving Novelis prospects as "
                "the Oswego plant restarts and scrap spreads improve, with LME aluminium trading "
                "around $3,500/t well above the ~$2,900/t implied by current share valuations."
            ),
            "novelis_angle": None,
        },
        {
            "title": "Aluminium beverage can sector to receive a boost with AMP's Bonn laboratory",
            "url": "https://www.alcircle.com/news/aluminium-beverage-can-sector-to-receive-a-boost-with-amps-bonn-laboratory-117989",
            "source": "AlCircle",
            "date": "7 Apr",
            "category": "End Markets",
            "summary": (
                "Ardagh Metal Packaging Europe has opened a technical laboratory in Bonn, Germany, "
                "providing testing and analytical services including material compatibility, coating "
                "performance, and food safety compliance for its European beverage can production "
                "network and customers."
            ),
            "novelis_angle": (
                "Ardagh's investment in premium can-sheet testing infrastructure signals continued "
                "commitment to high-specification aluminium body stock, a positive demand indicator "
                "for Novelis's beverage packaging segment which accounts for approximately 60% of "
                "its shipment volume."
            ),
        },
        {
            "title": "United States modifies steel, aluminum, and copper Section 232 tariffs",
            "url": "https://www.whitecase.com/insight-alert/united-states-modifies-steel-aluminum-and-copper-section-232-tariffs",
            "source": "White & Case",
            "date": "6 Apr",
            "category": "Trade & Regulation",
            "summary": (
                "A US presidential proclamation effective 6 April 2026 restructured Section 232 "
                "tariffs on aluminium, applying the duty to the full customs value of imports rather "
                "than metal content alone; aluminium articles including sheet face a 50% rate "
                "(Annex I-A) or 25% (Annex I-B), with a 90-day Commerce and USTR review due by "
                "1 July 2026."
            ),
            "novelis_angle": (
                "Applying the 50% rate to full customs value sharply raises the effective duty "
                "burden on imported aluminium sheet, strengthening the competitive moat around "
                "Novelis's US domestic plants while adding cross-border cost complexity for "
                "products moving within its North American network."
            ),
        },
        {
            "title": "EGA says full production recovery from Al Taweelah attack could take 12 months",
            "url": "https://www.bloomberg.com/news/articles/2026-04-03/ega-says-may-take-a-year-to-restore-abu-dhabi-aluminum-output",
            "source": "Bloomberg",
            "date": "3 Apr",
            "category": "Industry News",
            "summary": (
                "Emirates Global Aluminium confirmed that restoring primary aluminium production "
                "at its Al Taweelah smelter — which produced 1.6 million tonnes in 2025 — could "
                "take up to 12 months following Iranian missile and drone strikes on 28 March. "
                "The alumina refinery and recycling plant may restart earlier, and EGA has existing "
                "metal stocks to partially mitigate near-term supply disruption."
            ),
            "novelis_angle": (
                "Removing 1.6 Mt/yr of primary aluminium from global supply for up to a year "
                "tightens P1020 availability and is already pushing European duty-paid premiums "
                "higher, increasing the raw material cost base for all European FRP producers "
                "including Novelis."
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
