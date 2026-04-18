#!/usr/bin/env python3
"""
Renders the HTML digest from structured article data.
Used by both test_send.py and the scheduled task.

Usage:
    from scripts.render_html import render_email, render_archive_page
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Allow running from any directory
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("jinja2 not installed. Run: pip3 install jinja2")
    sys.exit(1)

TEMPLATES_DIR = REPO_ROOT / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)

CATEGORY_TAG_CLASS = {
    "Novelis / Hindalco": "tag-novelis",
    "Competitors": "tag-competitors",
    "End Markets": "tag-end-markets",
    "Sustainability & Recycling": "tag-sustainability",
    "Trade & Regulation": "tag-trade",
    "Industry News": "tag-industry",
}


def render_email(digest_data: dict) -> str:
    """
    Render the HTML email from digest data.

    digest_data structure:
    {
        "date": "Thursday, 20 March 2025",
        "lme_price": "$2,485/t",          # optional
        "lme_change": "+$12 (+0.5%)",     # optional
        "lme_change_positive": True,       # optional
        "articles": [
            {
                "title": "...",
                "url": "https://...",
                "source": "AlCircle",
                "date": "20 Mar",          # optional
                "category": "Competitor",
                "summary": "Two sentence summary."
            },
            ...
        ],
        "archive_url": "https://alex-stad.github.io/alu-digest/"  # optional
    }
    """
    template = env.get_template("email_template.html")
    return template.render(
        digest_date=digest_data.get("date", datetime.now().strftime("%A, %d %B %Y")),
        lme_price=digest_data.get("lme_price"),
        lme_change=digest_data.get("lme_change"),
        lme_change_positive=digest_data.get("lme_change_positive", True),
        ecdp_price=digest_data.get("ecdp_price"),
        ecdp_change=digest_data.get("ecdp_change"),
        ecdp_change_positive=digest_data.get("ecdp_change_positive", True),
        articles=digest_data.get("articles", []),
        article_count=len(digest_data.get("articles", [])),
        archive_url=digest_data.get("archive_url", "https://alex-stad.github.io/alu-digest/"),
    )


def render_archive_page(digest_data: dict, date_slug: str) -> str:
    """
    Render a standalone archive HTML page for GitHub Pages.
    date_slug: "2025-03-20"
    """
    # Build inline archive page (extends archive_template logic)
    articles_html = ""
    for i, art in enumerate(digest_data.get("articles", []), 1):
        tag_class = CATEGORY_TAG_CLASS.get(art.get("category", ""), "tag-industry")
        novelis_angle_html = ""
        if art.get("novelis_angle") and art.get("category") != "Novelis / Hindalco":
            novelis_angle_html = f"""
          <div class="novelis-angle">
            <span class="label">Novelis angle</span>
            <p>{art['novelis_angle']}</p>
          </div>"""
        date_html = f'<span class="article-source">{art["date"]}</span>' if art.get("date") else ""
        articles_html += f"""
        <article class="article">
          <div class="article-meta">
            <span class="tag {tag_class}">{art.get('category', 'General')}</span>
            {date_html}
            <span class="article-num">#{i}</span>
          </div>
          <h3>{art.get('title', '')}</h3>
          <p>{art.get('summary', '')}</p>{novelis_angle_html}
          <a href="{art.get('url', '#')}" class="read-more" target="_blank" rel="noopener">READ FULL STORY ↗</a>
        </article>"""

    lme_bar = ""
    if digest_data.get("lme_price"):
        change_class = "change-pos" if digest_data.get("lme_change_positive", True) else "change-neg"
        change_html = f'<span class="{change_class}">{digest_data["lme_change"]}</span>' if digest_data.get("lme_change") else ""
        lme_bar = f"""
        <div class="price-bar">
          <span class="label">LME Aluminium</span>
          <span class="price">{digest_data['lme_price']}</span>
          {change_html}
          <span class="unit">Cash settlement · USD/t</span>
        </div>"""
        if digest_data.get("ecdp_price"):
            ecdp_change_class = "change-pos" if digest_data.get("ecdp_change_positive", True) else "change-neg"
            ecdp_change_html = f'<span class="{ecdp_change_class}">{digest_data["ecdp_change"]}</span>' if digest_data.get("ecdp_change") else ""
            lme_bar += f"""
        <div class="price-bar">
          <span class="label">ECDP</span>
          <span class="price">{digest_data['ecdp_price']}</span>
          {ecdp_change_html}
          <span class="unit">P1020A in-whs dp Rotterdam · USD/t</span>
        </div>"""

    template = env.get_template("archive_template.html")
    # Render with injected content block
    content = f"""
    <div class="container">
      <div class="digest-header">
        <a href="https://alex-stad.github.io/alu-digest/" class="back">← Back to archive</a>
        <h2>{digest_data.get('date', date_slug)}</h2>
        <p class="meta">{len(digest_data.get('articles', []))} stories · Alex's Daily Alu Digest</p>
      </div>
      {lme_bar}
      <div class="articles">
        {articles_html}
      </div>
    </div>"""

    # Simple injection since Jinja2 blocks don't work well for standalone rendering
    base_html = template.render()
    return base_html.replace("<!-- CONTENT_PLACEHOLDER -->", content).replace(
        "<!-- TITLE_PLACEHOLDER -->",
        f"Alu Digest — {digest_data.get('date', date_slug)}"
    )


def render_archive_index(entries: list) -> str:
    """
    Render the index.html for the GitHub Pages archive.

    entries: list of dicts, newest first:
    [{"date_slug": "2025-03-20", "date_display": "Thursday, 20 March 2025", "lead_headline": "..."}, ...]
    """
    items_html = ""
    for entry in entries:
        path = f"{entry['date_slug'].replace('-', '/')}.html"
        items_html += f"""
        <li class="digest-list">
          <a href="{path}">
            <div>
              <div class="date">{entry['date_display']}</div>
              <div class="headline">{entry.get('lead_headline', '')}</div>
            </div>
            <span class="arrow">›</span>
          </a>
        </li>"""

    template = env.get_template("archive_template.html")
    content = f"""
    <div class="container">
      <h2 style="font-size:18px;font-weight:700;color:var(--text);margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border);">
        Archive
      </h2>
      <ul class="digest-list" style="list-style:none;">
        {items_html}
      </ul>
    </div>"""

    base_html = template.render()
    return base_html.replace("<!-- CONTENT_PLACEHOLDER -->", content).replace(
        "<!-- TITLE_PLACEHOLDER -->", "Alex's Daily Alu Digest — Archive"
    )


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = {
        "date": "Thursday, 20 March 2025",
        "lme_price": "$2,485/t",
        "lme_change": "+$12 (+0.5%)",
        "lme_change_positive": True,
        "articles": [
            {
                "title": "Novelis Announces €300M Investment in Göttingen Recycling Facility",
                "url": "https://example.com/1",
                "source": "AlCircle",
                "date": "20 Mar",
                "category": "Novelis / Hindalco",
                "summary": "Novelis has announced a €300 million expansion of its Göttingen plant to double closed-loop aluminium recycling capacity by 2027. The investment supports the company's target of achieving 80% recycled content across its European operations."
            },
            {
                "title": "Constellium Reports Record Q4 Automotive Sheet Demand",
                "url": "https://example.com/2",
                "source": "Fastmarkets",
                "date": "19 Mar",
                "category": "Competitor",
                "summary": "Constellium posted a 12% year-on-year increase in automotive sheet shipments in Q4 2024, driven by EV lightweighting demand across German OEMs. The company is expanding its Neuf-Brisach facility to meet growing demand."
            },
            {
                "title": "EU CBAM Aluminium Compliance: First Declarant Fines Issued",
                "url": "https://example.com/3",
                "source": "Reuters",
                "date": "19 Mar",
                "category": "Trade Policy",
                "summary": "The European Commission issued its first CBAM non-compliance fines totalling €4.2 million to aluminium importers who failed to submit 2024 transition period reports. Industry bodies warn the full mechanism in 2026 will add €180-220/t to primary aluminium import costs."
            },
            {
                "title": "LME Aluminium Climbs on Tight Scrap Supply and Dollar Weakness",
                "url": "https://example.com/4",
                "source": "Metal Bulletin",
                "date": "20 Mar",
                "category": "Market Data",
                "summary": "LME three-month aluminium rose $18 to $2,497/t as scrap availability tightened ahead of summer construction season in Europe. Analysts note that European P1020 premiums have widened to $175/t over LME, the highest since Q3 2023."
            },
        ],
        "archive_url": "https://alex-stad.github.io/alu-digest/"
    }

    out_dir = REPO_ROOT / "output"
    out_dir.mkdir(exist_ok=True)

    email_html = render_email(sample)
    email_path = out_dir / "preview_email.html"
    email_path.write_text(email_html, encoding="utf-8")
    print(f"Email preview written to: {email_path}")

    archive_html = render_archive_page(sample, "2025-03-20")
    archive_path = out_dir / "preview_archive.html"
    archive_path.write_text(archive_html, encoding="utf-8")
    print(f"Archive preview written to: {archive_path}")
