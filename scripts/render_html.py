#!/usr/bin/env python3
"""
Renders the HTML digest from structured article data.
Used by both test_send.py and the scheduled task.

Usage:
    from scripts.render_html import render_email, render_archive_page
"""

import sys
import os
import re
import html as _html
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


def _safe_url(url: str) -> str:
    """
    Defence against URL-scheme injection from Claude-generated content.
    Jinja2 autoescape blocks HTML injection but does NOT block javascript: or
    data: URLs used as href targets. Return only http(s) URLs; anything else
    is replaced with '#' and logged.
    """
    if not url or not isinstance(url, str):
        return "#"
    stripped = url.strip().lower()
    if stripped.startswith(("http://", "https://")):
        return url.strip()
    print(f"[WARN] Rejected non-http(s) URL: {url!r} — replaced with '#'")
    return "#"


def _sanitize_articles(articles: list) -> list:
    """Return a copy of articles with URL fields safety-checked."""
    safe = []
    for art in articles:
        a = dict(art)
        a["url"] = _safe_url(a.get("url", ""))
        safe.append(a)
    return safe


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
    articles = _sanitize_articles(digest_data.get("articles", []))
    template = env.get_template("email_template.html")
    return template.render(
        digest_date=digest_data.get("date", datetime.now().strftime("%A, %d %B %Y")),
        lme_price=digest_data.get("lme_price"),
        lme_change=digest_data.get("lme_change"),
        lme_change_positive=digest_data.get("lme_change_positive", True),
        ecdp_price=digest_data.get("ecdp_price"),
        ecdp_change=digest_data.get("ecdp_change"),
        ecdp_change_positive=digest_data.get("ecdp_change_positive", True),
        articles=articles,
        article_count=len(articles),
        archive_url=_safe_url(digest_data.get("archive_url") or "https://alex-stad.github.io/alu-digest/"),
    )


def render_archive_page(digest_data: dict, date_slug: str) -> str:
    """
    Render a standalone archive HTML page for GitHub Pages.
    date_slug: "2025-03-20"
    """
    # Build inline archive page. All Claude-generated fields are HTML-escaped
    # (f-strings don't autoescape like Jinja2 does) and URLs are scheme-checked.
    def esc(s):
        return _html.escape(str(s or ""), quote=True)

    articles_html = ""
    for i, art in enumerate(digest_data.get("articles", []), 1):
        tag_class = CATEGORY_TAG_CLASS.get(art.get("category", ""), "tag-industry")
        novelis_angle_html = ""
        if art.get("novelis_angle") and art.get("category") != "Novelis / Hindalco":
            novelis_angle_html = f"""
          <div class="novelis-angle">
            <span class="label">Novelis angle</span>
            <p>{esc(art['novelis_angle'])}</p>
          </div>"""
        date_html = f'<span class="article-source">{esc(art["date"])}</span>' if art.get("date") else ""
        safe_url = _safe_url(art.get("url", ""))
        articles_html += f"""
        <article class="article">
          <div class="article-meta">
            <span class="tag {tag_class}">{esc(art.get('category', 'General'))}</span>
            {date_html}
            <span class="article-num">#{i}</span>
          </div>
          <h3>{esc(art.get('title', ''))}</h3>
          <p>{esc(art.get('summary', ''))}</p>{novelis_angle_html}
          <a href="{esc(safe_url)}" class="read-more" target="_blank" rel="noopener">READ FULL STORY ↗</a>
        </article>"""

    lme_bar = ""
    if digest_data.get("lme_price"):
        change_class = "change-pos" if digest_data.get("lme_change_positive", True) else "change-neg"
        change_html = f'<span class="{change_class}">{esc(digest_data["lme_change"])}</span>' if digest_data.get("lme_change") else ""
        lme_bar = f"""
        <div class="price-bar">
          <span class="label">LME Aluminium</span>
          <span class="price">{esc(digest_data['lme_price'])}</span>
          {change_html}
          <span class="unit">Cash settlement · USD/t</span>
        </div>"""
        if digest_data.get("ecdp_price"):
            ecdp_change_class = "change-pos" if digest_data.get("ecdp_change_positive", True) else "change-neg"
            ecdp_change_html = f'<span class="{ecdp_change_class}">{esc(digest_data["ecdp_change"])}</span>' if digest_data.get("ecdp_change") else ""
            lme_bar += f"""
        <div class="price-bar">
          <span class="label">ECDP</span>
          <span class="price">{esc(digest_data['ecdp_price'])}</span>
          {ecdp_change_html}
          <span class="unit">P1020A in-whs dp Rotterdam · USD/t</span>
        </div>"""

    template = env.get_template("archive_template.html")
    # Render with injected content block
    date_display = esc(digest_data.get('date', date_slug))
    content = f"""
    <div class="container">
      <div class="digest-header">
        <a href="https://alex-stad.github.io/alu-digest/" class="back">← Back to archive</a>
        <h2>{date_display}</h2>
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
        f"Alu Digest — {date_display}"
    )


def render_archive_index(entries: list) -> str:
    """
    Render the index.html for the GitHub Pages archive.

    entries: list of dicts, newest first:
    [{"date_slug": "2025-03-20", "date_display": "Thursday, 20 March 2025", "lead_headline": "..."}, ...]
    """
    def esc(s):
        return _html.escape(str(s or ""), quote=True)

    items_html = ""
    for entry in entries:
        # date_slug is YYYY-MM-DD — validate strictly before building the path,
        # so a malformed slug can't inject into the href attribute.
        slug = str(entry.get("date_slug", ""))
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", slug):
            print(f"[WARN] Skipping archive index entry with invalid date_slug: {slug!r}")
            continue
        path = f"{slug.replace('-', '/')}.html"
        items_html += f"""
        <li class="digest-list">
          <a href="{esc(path)}">
            <div>
              <div class="date">{esc(entry.get('date_display', ''))}</div>
              <div class="headline">{esc(entry.get('lead_headline', ''))}</div>
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
