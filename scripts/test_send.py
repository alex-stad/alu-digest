#!/usr/bin/env python3
"""
End-to-end test: renders a sample digest and sends it via Resend.
Verifies the full email pipeline before the scheduled task goes live.

Usage:
    RESEND_API_KEY=re_... python3 scripts/test_send.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.render_html import render_email
from scripts.send_email import send_digest

SAMPLE_DIGEST = {
    "date": datetime.now().strftime("%A, %d %B %Y"),
    "lme_price": "$2,485/t",
    "lme_change": "+$12 (+0.5%)",
    "lme_change_positive": True,
    "articles": [
        {
            "title": "Novelis Announces €300M Investment in Göttingen Recycling Facility",
            "url": "https://alcircle.com",
            "source": "AlCircle",
            "date": datetime.now().strftime("%d %b"),
            "category": "Novelis / Hindalco",
            "summary": (
                "Novelis has announced a €300 million expansion of its Göttingen plant to double "
                "closed-loop aluminium recycling capacity by 2027. The investment supports the "
                "company's target of achieving 80% recycled content across its European operations."
            ),
        },
        {
            "title": "Constellium Reports Record Q4 Automotive Sheet Demand",
            "url": "https://fastmarkets.com",
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
            "title": "EU CBAM Aluminium Compliance: First Declarant Fines Issued",
            "url": "https://reuters.com",
            "source": "Reuters",
            "date": datetime.now().strftime("%d %b"),
            "category": "Trade Policy",
            "summary": (
                "The European Commission issued its first CBAM non-compliance fines totalling "
                "€4.2 million to aluminium importers who failed to submit 2024 transition period "
                "reports. Industry bodies warn the full mechanism in 2026 will add €180–220/t to "
                "primary aluminium import costs."
            ),
        },
        {
            "title": "LME Aluminium Climbs on Tight Scrap Supply and Dollar Weakness",
            "url": "https://alcircle.com",
            "source": "Metal Bulletin",
            "date": datetime.now().strftime("%d %b"),
            "category": "Market Data",
            "summary": (
                "LME three-month aluminium rose $18 to $2,497/t as scrap availability tightened "
                "ahead of summer construction season in Europe. Analysts note that European P1020 "
                "premiums have widened to $175/t over LME, the highest since Q3 2023."
            ),
        },
        {
            "title": "Aluminium Recycling Rates Hit Record 76% in EU, Report Finds",
            "url": "https://aluminiumtoday.com",
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
    ],
    "archive_url": "https://alex-stad.github.io/alu-digest/",
}


def main():
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        print("ERROR: Set RESEND_API_KEY environment variable first.")
        print("Usage: RESEND_API_KEY=re_... python3 scripts/test_send.py")
        sys.exit(1)

    print("Rendering HTML digest...")
    html = render_email(SAMPLE_DIGEST)

    # Save preview locally
    preview_path = REPO_ROOT / "output" / "preview_email.html"
    preview_path.parent.mkdir(exist_ok=True)
    preview_path.write_text(html, encoding="utf-8")
    print(f"Preview saved to: {preview_path}")

    subject = f"[TEST] Alex's Daily Alu Digest — {SAMPLE_DIGEST['date']}"
    recipients = ["stadelmann.alexander@gmail.com"]

    print(f"Sending test email to: {', '.join(recipients)}")
    success = send_digest(html, subject, recipients)

    if success:
        print("\nTest passed. Check your inbox — the digest should arrive within 30 seconds.")
        print("Review the email and confirm it looks correct before the scheduled task goes live.")
    else:
        print("\nTest FAILED. Check the error above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
